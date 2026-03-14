"""Parse job postings using LangChain ``ChatOpenAI`` with structured output.

Supports HTML, plain text, PDF, and screenshot/image inputs.

For text-based inputs (HTML, plain text) the content is passed directly as a
``HumanMessage`` string.  For binary inputs (PDF, images) LangChain's
cross-provider multimodal content-block format is used so that ``ChatOpenAI``
can transmit the data to the model.
"""

import base64
from datetime import datetime
from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage, SystemMessage
from loguru import logger

from src.job import Job
from src.libs.resume_and_cover_builder.prompts.strings_feder_cr import (
    job_parser_system_prompt,
)
from src.schemas.job_parse_output import JobParseOutput

if TYPE_CHECKING:
    from src.libs.llm.llm_provider import LLMProvider

# Maps source_type → MIME type for image content blocks.
_IMAGE_MIME: dict[str, str] = {
    "screenshot": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
}

# Default filenames when the caller does not supply one.
_DEFAULT_FILENAME: dict[str, str] = {
    "pdf": "job_posting.pdf",
    "screenshot": "screenshot.png",
}


class LLMParser:
    """Extract structured job information via a single LangChain structured-output call.

    Uses ``LoggerChatModel.structured_invoke()`` which handles retry logic,
    back-off, and call logging in one place — shared with all other LLM
    consumers in the application.
    """

    def __init__(self, llm_provider: "LLMProvider") -> None:
        self.llm_chat = llm_provider.chat_model

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
            filename: Optional human-readable filename hint sent to the model.

        Returns:
            A :class:`Job` instance with as many fields filled as the LLM
            could extract.
        """
        logger.info(f"Parsing job content (source_type={source_type}, {self._content_size(content)} bytes)")
        messages = self._build_messages(content, source_type, filename)
        result: JobParseOutput = self.llm_chat.structured_invoke(messages, JobParseOutput)
        job = self._output_to_job(result)
        job.parsed_at = datetime.now()
        return job

    # ------------------------------------------------------------------
    # Internal: build LangChain message list
    # ------------------------------------------------------------------

    def _build_messages(
        self,
        content: str | bytes,
        source_type: str,
        filename: str | None,
    ) -> list:
        """Return a ``[SystemMessage, HumanMessage]`` list for the given input."""
        system = SystemMessage(content=job_parser_system_prompt)

        if source_type in ("html", "text"):
            text = content if isinstance(content, str) else content.decode("utf-8", errors="replace")
            return [system, HumanMessage(content=text)]

        if source_type == "pdf":
            raw_bytes = content if isinstance(content, bytes) else content.encode("utf-8")
            b64_data = base64.b64encode(raw_bytes).decode("ascii")
            fname = filename or _DEFAULT_FILENAME.get("pdf", "file.pdf")
            return [
                system,
                HumanMessage(
                    content=[
                        {"type": "text", "text": "Parse the job posting in the attached PDF."},
                        {
                            "type": "file",
                            "source_type": "base64",
                            "data": b64_data,
                            "media_type": "application/pdf",
                            "filename": fname,
                        },
                    ]
                ),
            ]

        # screenshot / jpg / jpeg / png
        raw_bytes = content if isinstance(content, bytes) else content.encode("utf-8")
        b64_data = base64.b64encode(raw_bytes).decode("ascii")
        mime = _IMAGE_MIME.get(source_type, "image/png")
        return [
            system,
            HumanMessage(
                content=[
                    {"type": "text", "text": "Parse the job posting in the attached image."},
                    {
                        "type": "image",
                        "source_type": "base64",
                        "data": b64_data,
                        "mime_type": mime,
                    },
                ]
            ),
        ]

    # ------------------------------------------------------------------
    # Internal: map output schema → Job
    # ------------------------------------------------------------------

    @staticmethod
    def _output_to_job(output: JobParseOutput) -> Job:
        """Convert a ``JobParseOutput`` into a ``Job`` data object."""
        return Job(
            role=output.role,
            company=output.company,
            location=output.location,
            description=output.description,
            salary_range=output.salary_range,
            employment_type=output.employment_type,
            experience_level=output.experience_level,
            required_skills=output.required_skills,
            recruiter_email=output.recruiter_email,
        )

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    @staticmethod
    def _content_size(content: str | bytes) -> int:
        return len(content.encode("utf-8")) if isinstance(content, str) else len(content)
