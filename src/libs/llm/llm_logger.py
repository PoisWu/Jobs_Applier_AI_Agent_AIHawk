"""LLM call logging — persists request/response pairs to a JSON log file.

This module has a single responsibility: serialise an LLM call (prompt +
reply + token counts) and append it to ``open_ai_calls.json``.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.prompt_values import StringPromptValue

from config import settings


def log_llm_call(
    model: str,
    prompts: Any,
    reply: str,
    input_tokens: int,
    output_tokens: int,
    log_output_file_path: Path,
) -> None:
    """Persist an LLM request/response pair to the JSON call log.

    Handles prompt normalisation for all prompt types (``StringPromptValue``,
    plain lists, and LangChain message containers) before writing to
    ``open_ai_calls.json``.
    """
    if isinstance(prompts, StringPromptValue):
        prompts = prompts.text
    elif isinstance(prompts, list):
        # Plain list (Responses API) or list of LangChain messages — keep as-is
        pass
    else:
        # LangChain ChatPromptValue or similar container
        prompts = {f"prompt_{i + 1}": prompt.content for i, prompt in enumerate(prompts.messages)}

    calls_log = log_output_file_path / "open_ai_calls.json"
    total_cost = input_tokens * settings.PROMPT_PRICE_PER_TOKEN + output_tokens * settings.COMPLETION_PRICE_PER_TOKEN

    log_entry = {
        "model": model,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "prompts": prompts,
        "replies": reply,
        "total_tokens": input_tokens + output_tokens,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_cost": total_cost,
    }

    with open(calls_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False, indent=4) + "\n")
