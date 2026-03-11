"""Tests for the GlobalConfig model."""

from src.libs.resume_and_cover_builder.config import _DEFAULT_HTML_TEMPLATE, GlobalConfig


def test_global_config_defaults():
    config = GlobalConfig()
    assert config.STYLES_DIRECTORY is None
    assert config.LOG_OUTPUT_FILE_PATH is None
    assert config.API_KEY is None
    assert config.html_template == _DEFAULT_HTML_TEMPLATE


def test_global_config_with_values():
    from pathlib import Path

    config = GlobalConfig(
        STYLES_DIRECTORY=Path("/tmp/styles"),
        API_KEY="test-key",
    )
    assert config.STYLES_DIRECTORY == Path("/tmp/styles")
    assert config.API_KEY == "test-key"


def test_html_template_contains_body_placeholder():
    assert "$body" in _DEFAULT_HTML_TEMPLATE
    assert "$style_css" in _DEFAULT_HTML_TEMPLATE
