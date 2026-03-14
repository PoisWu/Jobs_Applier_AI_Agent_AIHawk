"""Parse job postings using the OpenAI Responses API.

Supports HTML, plain text, PDF, and screenshot/image inputs.
The Responses API handles PDF text+image extraction server-side —
no local conversion is required.
"""

import base64
import json
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

import openai
from loguru import logger

from config import settings
from src.job import Job

if TYPE_CHECKING:
    from src.libs.llm.llm_provider import LLMProvider
from src.libs.llm.llm_provider import log_llm_call
from src.libs.resume_and_cover_builder.prompts.strings_feder_cr import (
    job_parser_system_prompt,
)

# Maps source_type → MIME-type used by the Responses API ``input_file`` block.
_MIME_MAP: dict[str, str] = {
    "pdf": "application/pdf",
    "screenshot": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "html": "text/html",
    "text": "text/plain",
}

# Default filenames when the caller does not supply one.
_DEFAULT_FILENAME: dict[str, str] = {
    "pdf": "job_posting.pdf",
    "screenshot": "screenshot.png",
    "html": "page.html",
    "text": "posting.txt",
}


class LLMParser:
    """Extract structured job information via a *single* OpenAI Responses API call.

    This replaces the previous FAISS/RAG pipeline.  For PDF and image inputs
    the API natively processes the binary content — no local conversion
    (e.g. pdf2image) is needed.
    """

    def __init__(self, llm_provider: "LLMProvider") -> None:
        self.client = llm_provider.openai_client
        self.model = llm_provider.model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def parse(
        self,
        content: str | bytes,
        source_type: str,
        filename: str | None = None,
    ) -> Job:
        """Parse *content* and return a populated :class:`Job`.

        Args:
            content: Raw content — a UTF-8 string for html/text sources, or
                     raw ``bytes`` for pdf/screenshot sources.
            source_type: One of ``"html"``, ``"text"``, ``"pdf"``,
                         ``"screenshot"``.
            filename: Optional human-readable filename hint sent to the API.

        Returns:
            A :class:`Job` instance with as many fields filled as the LLM
            could extract.
        """
        logger.info(f"Parsing job content (source_type={source_type}, {self._content_size(content)} bytes)")
        content_blocks = self._build_content_blocks(content, source_type, filename)

        response = self._call_api(content_blocks)
        job = self._parse_response(response)
        job.parsed_at = datetime.now()
        return job

    # ------------------------------------------------------------------
    # Internal: build request
    # ------------------------------------------------------------------

    def _build_content_blocks(
        self,
        content: str | bytes,
        source_type: str,
        filename: str | None,
    ) -> list[dict[str, Any]]:
        """Assemble the ``content`` list for the Responses API ``input`` message."""
        blocks: list[dict[str, Any]] = [
            {"type": "input_text", "text": job_parser_system_prompt},
        ]

        if source_type in ("html", "text"):
            # Send raw text directly
            text = content if isinstance(content, str) else content.decode("utf-8", errors="replace")
            blocks.append({"type": "input_text", "text": text})
        else:
            # Binary content — use input_file with base64 encoding
            raw_bytes = content if isinstance(content, bytes) else content.encode("utf-8")
            b64_data = base64.b64encode(raw_bytes).decode("ascii")
            fname = filename or _DEFAULT_FILENAME.get(source_type, "file.bin")
            blocks.append(
                {
                    "type": "input_file",
                    "filename": fname,
                    "file_data": f"data:{_MIME_MAP.get(source_type, 'application/octet-stream')};base64,{b64_data}",
                }
            )

        return blocks

    # ------------------------------------------------------------------
    # Internal: call the API
    # ------------------------------------------------------------------

    def _call_api(self, content_blocks: list[dict[str, Any]]) -> Any:
        """Send a single request to the OpenAI Responses API with retry."""
        import time as _time

        max_retries = settings.MAX_LLM_RETRIES
        retry_delay = settings.BASE_RETRY_DELAY

        for attempt in range(1, max_retries + 1):
            try:
                response = self.client.responses.create(
                    model=self.model,
                    input=[
                        {
                            "role": "user",
                            "content": content_blocks,
                        }
                    ],
                )

                # Log the call (token usage, cost, etc.)
                self._log_response(content_blocks, response)
                return response

            except openai.RateLimitError as err:
                wait = self._parse_wait_time(str(err))
                logger.warning(f"Rate limit hit. Waiting {wait}s before retry (attempt {attempt}/{max_retries})…")
                _time.sleep(wait)
            except openai.APIError as err:
                logger.error(f"OpenAI API error: {err}. Retrying in {retry_delay}s (attempt {attempt}/{max_retries})…")
                _time.sleep(retry_delay)
                retry_delay *= 2
            except Exception as err:
                logger.error(f"Unexpected error: {err}. Retrying in {retry_delay}s (attempt {attempt}/{max_retries})…")
                _time.sleep(retry_delay)
                retry_delay *= 2

        raise RuntimeError("Failed to get a response from the model after multiple attempts.")

    # ------------------------------------------------------------------
    # Internal: parse the response
    # ------------------------------------------------------------------

    def _parse_response(self, response: Any) -> Job:
        """Extract JSON from the Responses API reply and hydrate a ``Job``."""
        # The Responses API returns an object with .output
        # containing message items; collect all text.
        raw_text = ""
        for item in response.output:
            if item.type == "message":
                for content_block in item.content:
                    if content_block.type == "output_text":
                        raw_text += content_block.text

        if not raw_text:
            logger.warning("Empty response from the model — returning blank Job.")
            return Job()

        # Strip markdown code fences if the model wrapped the JSON
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text.strip())
        cleaned = re.sub(r"\s*```$", "", cleaned)

        try:
            data: dict[str, Any] = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            logger.warning(f"Failed to parse JSON from LLM response: {exc}")
            logger.debug(f"Raw response text:\n{raw_text[:500]}")
            return Job()

        return self._dict_to_job(data)

    @staticmethod
    def _dict_to_job(data: dict[str, Any]) -> Job:
        """Safely map *data* (from the LLM) to a ``Job``, ignoring unknown keys."""
        skills = data.get("required_skills", [])
        if isinstance(skills, str):
            # Gracefully handle the model returning a comma-separated string
            skills = [s.strip() for s in skills.split(",") if s.strip()]

        return Job(
            role=str(data.get("role", "")),
            company=str(data.get("company", "")),
            location=str(data.get("location", "")),
            description=str(data.get("description", "")),
            salary_range=str(data.get("salary_range", "")),
            employment_type=str(data.get("employment_type", "")),
            experience_level=str(data.get("experience_level", "")),
            required_skills=skills,
            recruiter_email=str(data.get("recruiter_email", "")),
        )

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log_response(self, content_blocks: list[dict[str, Any]], response: Any) -> None:
        """Log token usage and cost for the Responses API call."""
        usage = response.usage
        input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0

        # Build a serialisable summary of the prompt (avoid dumping base64)
        prompt_summary: list[str] = []
        for block in content_blocks:
            if block.get("type") == "input_text":
                text = block["text"]
                prompt_summary.append(text[:300] + "…" if len(text) > 300 else text)
            elif block.get("type") == "input_file":
                prompt_summary.append(f"[file: {block.get('filename', '?')}]")

        # Collect reply text
        reply_text = ""
        for item in response.output:
            if item.type == "message":
                for cb in item.content:
                    if cb.type == "output_text":
                        reply_text += cb.text

        log_llm_call(
            model=response.model or self.model,
            prompts=prompt_summary,
            reply=reply_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
        )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_wait_time(error_message: str) -> int:
        """Extract a wait-time (seconds) from a rate-limit error string."""
        match = re.search(r"try again in (\d+)s", error_message)
        if match:
            return int(match.group(1))
        match = re.search(r"retry after (\d+)", error_message, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 60

    @staticmethod
    def _content_size(content: str | bytes) -> int:
        return len(content.encode("utf-8")) if isinstance(content, str) else len(content)
