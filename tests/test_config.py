"""Tests for config.py centralized constants."""

from config import settings


def test_llm_model_defaults():
    assert settings.LLM_MODEL == "gpt-4o-mini"
    assert settings.LLM_MODEL_TYPE == "openai"
    assert settings.LLM_TEMPERATURE == 0.4


def test_token_pricing():
    assert settings.PROMPT_PRICE_PER_TOKEN > 0
    assert settings.COMPLETION_PRICE_PER_TOKEN > 0


def test_retry_defaults():
    assert settings.MAX_LLM_RETRIES == 15
    assert settings.BASE_RETRY_DELAY == 10


def test_output_dir():
    assert settings.OUTPUT_DIR == "data_folder/output"


def test_hash_prefix_length():
    assert settings.HASH_PREFIX_LENGTH == 10
