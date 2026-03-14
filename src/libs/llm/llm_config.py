from pathlib import Path

from pydantic import BaseModel


class LLMConfig(BaseModel):
    LOG_OUTPUT_FILE_PATH: Path | None = None
    API_KEY: str | None = None


llm_config = LLMConfig()
