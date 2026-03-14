"""Tests for the BuilderConfig model."""

from src.libs.resume_and_cover_builder.builder_config import _DEFAULT_HTML_TEMPLATE, BuilderConfig


def test_builder_config_defaults():
    config = BuilderConfig()
    assert config.STYLES_DIRECTORY is None
    assert config.LOG_OUTPUT_FILE_PATH is None
    assert config.html_template == _DEFAULT_HTML_TEMPLATE


def test_builder_config_with_values():
    from pathlib import Path

    config = BuilderConfig(
        STYLES_DIRECTORY=Path("/tmp/styles"),
    )
    assert config.STYLES_DIRECTORY == Path("/tmp/styles")


def test_html_template_contains_body_placeholder():
    assert "$body" in _DEFAULT_HTML_TEMPLATE
    assert "$style_css" in _DEFAULT_HTML_TEMPLATE
