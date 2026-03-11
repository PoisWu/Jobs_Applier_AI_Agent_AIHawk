"""Tests for config.py centralized constants."""

import config as cfg


def test_llm_model_defaults():
    assert cfg.LLM_MODEL == "gpt-4o-mini"
    assert cfg.LLM_MODEL_TYPE == "openai"
    assert cfg.LLM_TEMPERATURE == 0.4


def test_token_pricing():
    assert cfg.PROMPT_PRICE_PER_TOKEN > 0
    assert cfg.COMPLETION_PRICE_PER_TOKEN > 0


def test_retry_defaults():
    assert cfg.MAX_LLM_RETRIES == 15
    assert cfg.BASE_RETRY_DELAY == 10


def test_output_dir():
    assert cfg.OUTPUT_DIR == "data_folder/output"


def test_hash_prefix_length():
    assert cfg.HASH_PREFIX_LENGTH == 10
