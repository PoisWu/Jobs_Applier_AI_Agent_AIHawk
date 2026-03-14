"""Central LLM provider — the only place where credentials touch LLM object construction.

All modules that need LLM access should accept an ``LLMProvider`` instance via
their constructor (dependency injection) rather than receiving a raw API key.

Usage::

    provider = LLMProvider(LLMConfig(API_KEY="sk-...", LOG_OUTPUT_FILE_PATH=output_path))

    # Prompt-chain consumers (resume / cover-letter generators):
    resumer = LLMResumer(llm_provider=provider, strings=resume_strings)

    # Structured-output consumers (job parser):
    parser = LLMParser(llm_provider=provider)
"""

import re
import time
from pathlib import Path
from typing import Any

import openai
from langchain_core.messages.ai import AIMessage
from langchain_openai import ChatOpenAI
from loguru import logger
from requests.exceptions import HTTPError as HTTPStatusError

from config import settings
from src.libs.llm.llm_config import LLMConfig
from src.libs.llm.llm_logger import log_llm_call


def parse_rate_limit_wait_time(error_message: str) -> int:
    """Extract a wait-time in seconds from a rate-limit error string, defaulting to 60."""
    match = re.search(r"try again in (\d+)s", error_message)
    if match:
        return int(match.group(1))
    match = re.search(r"retry after (\d+)", error_message, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return 60


class LoggerChatModel:
    """Wrapper around ``ChatOpenAI`` that adds retry logic and call logging."""

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.llm = ChatOpenAI(
            model_name=settings.LLM_MODEL,
            openai_api_key=llm_config.API_KEY,
            temperature=settings.LLM_TEMPERATURE,
        )

    @staticmethod
    def parse_wait_time_from_error_message(error_message: str) -> int:
        """Extract wait time from rate-limit error messages, defaulting to 60s."""
        return parse_rate_limit_wait_time(error_message)

    # ------------------------------------------------------------------
    # Retry helper
    # ------------------------------------------------------------------

    def _invoke_with_retry(self, invoke_fn) -> Any:
        """Execute *invoke_fn()* inside a retry / back-off loop."""
        max_retries = 15
        retry_delay = 10

        for attempt in range(max_retries):
            try:
                return invoke_fn()
            except (openai.RateLimitError, HTTPStatusError) as err:
                if isinstance(err, HTTPStatusError) and err.response.status_code == 429:
                    logger.warning(
                        f"HTTP 429 Too Many Requests: Waiting for {retry_delay} seconds before retrying (Attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    wait_time = self.parse_wait_time_from_error_message(str(err))
                    logger.warning(
                        f"Rate limit exceeded or API error. Waiting for {wait_time} seconds before retrying (Attempt {attempt + 1}/{max_retries})..."
                    )
                    time.sleep(wait_time)
            except Exception as e:
                logger.error(
                    f"Unexpected error occurred: {str(e)}, retrying in {retry_delay} seconds... (Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(retry_delay)
                retry_delay *= 2

        logger.critical("Failed to get a response from the model after multiple attempts.")
        raise Exception("Failed to get a response from the model after multiple attempts.")

    # ------------------------------------------------------------------
    # Public invoke interface
    # ------------------------------------------------------------------

    def invoke(self, messages: list) -> str:
        """Invoke the model and return the reply as a plain string."""

        def _invoke():
            reply = self.llm.invoke(messages)
            parsed_reply = self._parse_llm_result(reply)
            log_llm_call(
                model=parsed_reply["response_metadata"]["model_name"],
                prompts=messages,
                reply=parsed_reply["content"],
                input_tokens=parsed_reply["usage_metadata"]["input_tokens"],
                output_tokens=parsed_reply["usage_metadata"]["output_tokens"],
                log_output_file_path=self.llm_config.LOG_OUTPUT_FILE_PATH,
            )
            return parsed_reply["content"]

        return self._invoke_with_retry(_invoke)

    # ------------------------------------------------------------------
    # Structured-output interface (used by parser consumers)
    # ------------------------------------------------------------------

    def structured_invoke(self, messages: list, schema: type) -> Any:
        """Invoke the model with *schema* as structured output.

        Uses ``ChatOpenAI.with_structured_output(schema, include_raw=True)`` so
        that token-usage metadata is still available for logging, then returns
        only the validated ``schema`` instance.
        """
        structured_llm = self.llm.with_structured_output(schema, include_raw=True)

        def _invoke():
            result = structured_llm.invoke(messages)
            raw: AIMessage = result["raw"]
            parsed = result["parsed"]
            parsed_meta = self._parse_llm_result(raw)
            log_llm_call(
                model=parsed_meta["response_metadata"]["model_name"],
                prompts=messages,
                reply=str(parsed),
                input_tokens=parsed_meta["usage_metadata"]["input_tokens"],
                output_tokens=parsed_meta["usage_metadata"]["output_tokens"],
                log_output_file_path=self.llm_config.LOG_OUTPUT_FILE_PATH,
            )
            return parsed

        return self._invoke_with_retry(_invoke)

    @staticmethod
    def _parse_llm_result(llmresult: AIMessage) -> dict[str, dict]:
        """Parse the LLM result into a structured format."""
        return {
            "content": llmresult.content,
            "response_metadata": {
                "model_name": llmresult.response_metadata.get("model_name", ""),
                "system_fingerprint": llmresult.response_metadata.get("system_fingerprint", ""),
                "finish_reason": llmresult.response_metadata.get("finish_reason", ""),
                "logprobs": llmresult.response_metadata.get("logprobs", None),
            },
            "id": llmresult.id,
            "usage_metadata": {
                "input_tokens": llmresult.usage_metadata.get("input_tokens", 0),
                "output_tokens": llmresult.usage_metadata.get("output_tokens", 0),
                "total_tokens": llmresult.usage_metadata.get("total_tokens", 0),
            },
        }


class LLMProvider:
    """Holds all LLM objects and credentials.

    Instantiate once at the application boundary (e.g. the CLI wiring function)
    and inject the instance wherever LLM access is needed.

    Attributes:
        model: The model name used for all LLM calls (taken from ``settings``).
        chat_model: A ``LoggerChatModel`` wrapping a LangChain ``ChatOpenAI``
            instance.  All consumers — prompt-chain generators *and* the
            structured-output job parser — share this single object, which
            centralises retry logic and call logging.
    """

    def __init__(self, llm_config: LLMConfig) -> None:
        self.model: str = settings.LLM_MODEL
        self.log_output_file_path: Path | None = llm_config.LOG_OUTPUT_FILE_PATH
        self.chat_model = LoggerChatModel(llm_config)
