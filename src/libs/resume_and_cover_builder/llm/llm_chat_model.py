"""LLM chat-model wrapper with retry logic and request logging."""

import json
import re
import time
from datetime import datetime
from typing import Any

import openai
from langchain_core.messages.ai import AIMessage
from langchain_core.prompt_values import StringPromptValue
from langchain_openai import ChatOpenAI
from loguru import logger
from requests.exceptions import HTTPError as HTTPStatusError

from config import settings
from src.libs.resume_and_cover_builder.builder_config import builder_config


def _log_request(prompts: Any, parsed_reply: dict[str, dict]) -> None:
    """Persist an LLM request/response pair to the JSON call log."""
    calls_log = builder_config.LOG_OUTPUT_FILE_PATH / "open_ai_calls.json"

    if isinstance(prompts, StringPromptValue):
        prompts = prompts.text
    elif isinstance(prompts, dict):
        prompts = {f"prompt_{i + 1}": prompt.content for i, prompt in enumerate(prompts.messages)}
    else:
        prompts = {f"prompt_{i + 1}": prompt.content for i, prompt in enumerate(prompts.messages)}

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    token_usage = parsed_reply["usage_metadata"]
    output_tokens = token_usage["output_tokens"]
    input_tokens = token_usage["input_tokens"]
    total_tokens = token_usage["total_tokens"]

    model_name = parsed_reply["response_metadata"]["model_name"]
    prompt_price_per_token = settings.PROMPT_PRICE_PER_TOKEN
    completion_price_per_token = settings.COMPLETION_PRICE_PER_TOKEN

    total_cost = (input_tokens * prompt_price_per_token) + (output_tokens * completion_price_per_token)

    log_entry = {
        "model": model_name,
        "time": current_time,
        "prompts": prompts,
        "replies": parsed_reply["content"],
        "total_tokens": total_tokens,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_cost": total_cost,
    }

    with open(calls_log, "a", encoding="utf-8") as f:
        json_string = json.dumps(log_entry, ensure_ascii=False, indent=4)
        f.write(json_string + "\n")


class LoggerChatModel:
    """Wrapper around ``ChatOpenAI`` that adds retry logic and call logging."""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm

    @staticmethod
    def parse_wait_time_from_error_message(error_message: str) -> int:
        """Extract wait time from rate-limit error messages, defaulting to 60s."""
        match = re.search(r"try again in (\d+)s", error_message)
        if match:
            return int(match.group(1))
        match = re.search(r"retry after (\d+)", error_message, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 60

    def __call__(self, messages: list[dict[str, str]]) -> str:
        max_retries = 15
        retry_delay = 10

        for attempt in range(max_retries):
            try:
                reply = self.llm.invoke(messages)
                parsed_reply = self._parse_llm_result(reply)
                _log_request(prompts=messages, parsed_reply=parsed_reply)
                return reply
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
