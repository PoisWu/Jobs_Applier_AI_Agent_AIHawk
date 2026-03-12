# In this file, you can set the configurations of the app.
# Values can be overridden via environment variables or a .env file.

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings. All fields can be overridden by environment
    variables with the same name (case-sensitive) or via a .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Logging — fields prefixed LOG_ are consumed by src/logging.py
    LOG_LEVEL: str = "DEBUG"
    LOG_SELENIUM_LEVEL: str = "ERROR"
    LOG_TO_FILE: bool = True
    LOG_TO_CONSOLE: bool = True

    MINIMUM_WAIT_TIME_IN_SECONDS: int = 60

    JOB_APPLICATIONS_DIR: str = "job_applications"
    JOB_SUITABILITY_SCORE: int = 7

    JOB_MAX_APPLICATIONS: int = 5
    JOB_MIN_APPLICATIONS: int = 1

    LLM_MODEL_TYPE: str = "openai"
    LLM_MODEL: str = "gpt-5-mini"
    # Only required for OLLAMA models
    LLM_API_URL: str = ""

    # LLM tuning
    LLM_TEMPERATURE: float = 1

    # Token pricing (for cost tracking)
    PROMPT_PRICE_PER_TOKEN: float = 0.00000015
    COMPLETION_PRICE_PER_TOKEN: float = 0.0000006

    # Retry configuration
    MAX_LLM_RETRIES: int = 15
    BASE_RETRY_DELAY: int = 10

    # Output
    OUTPUT_DIR: str = "data_folder/output"
    HASH_PREFIX_LENGTH: int = 10


settings = Settings()
