"""Tests for the LangChain-based LLMParser."""

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import HumanMessage, SystemMessage

from src.job import Job
from src.libs.job_fetch_pipeline.job_parser import LLMParser
from src.libs.llm.llm_config import LLMConfig
from src.libs.llm.llm_provider import LLMProvider
from src.schemas.job_parse_output import JobParseOutput

# A pre-built JobParseOutput that structured_invoke would return.
_SAMPLE_OUTPUT = JobParseOutput(
    role="Backend Engineer",
    company="WidgetCo",
    location="Remote",
    description="Build and maintain backend services for our widget platform.",
    salary_range="$130k–$170k",
    employment_type="full-time",
    experience_level="mid-level",
    required_skills=["Python", "FastAPI", "PostgreSQL", "Docker"],
    recruiter_email="hr@widgetco.com",
)


@pytest.fixture
def parser() -> LLMParser:
    """Return an ``LLMParser`` with a dummy API key (API calls are mocked)."""
    llm_provider = LLMProvider(LLMConfig(API_KEY="sk-test-dummy-key"))
    return LLMParser(llm_provider=llm_provider)


class TestLLMProvider:
    """Verify LLMProvider interface after openai_client removal."""

    def test_no_openai_client_attribute(self) -> None:
        """LLMProvider must no longer expose a raw openai_client attribute."""
        provider = LLMProvider(LLMConfig(API_KEY="sk-test-dummy-key"))
        assert not hasattr(provider, "openai_client")

    def test_has_chat_model(self) -> None:
        provider = LLMProvider(LLMConfig(API_KEY="sk-test-dummy-key"))
        assert hasattr(provider, "chat_model")


class TestLLMParserParse:
    """Verify that ``LLMParser.parse()`` correctly hydrates a ``Job``."""

    def test_parse_html(self, parser: LLMParser) -> None:
        parser.llm_chat.structured_invoke = MagicMock(return_value=_SAMPLE_OUTPUT)

        job = parser.parse(content="<html><body>Some job page</body></html>", source_type="html")

        assert isinstance(job, Job)
        assert job.role == "Backend Engineer"
        assert job.company == "WidgetCo"
        assert job.location == "Remote"
        assert job.salary_range == "$130k–$170k"
        assert job.required_skills == ["Python", "FastAPI", "PostgreSQL", "Docker"]
        assert job.recruiter_email == "hr@widgetco.com"
        assert job.parsed_at is not None

        # structured_invoke called once with (messages, JobParseOutput)
        parser.llm_chat.structured_invoke.assert_called_once()
        _messages, _schema = parser.llm_chat.structured_invoke.call_args.args
        assert _schema is JobParseOutput

    def test_parse_text(self, parser: LLMParser) -> None:
        parser.llm_chat.structured_invoke = MagicMock(return_value=_SAMPLE_OUTPUT)

        job = parser.parse(content="Plain text job description", source_type="text")

        assert job.role == "Backend Engineer"

    def test_parse_pdf(self, parser: LLMParser) -> None:
        parser.llm_chat.structured_invoke = MagicMock(return_value=_SAMPLE_OUTPUT)

        job = parser.parse(content=b"%PDF-1.4 fake pdf bytes", source_type="pdf")

        assert job.role == "Backend Engineer"

        messages, _schema = parser.llm_chat.structured_invoke.call_args.args
        human_msg = messages[1]
        assert isinstance(human_msg.content, list)
        file_block = next(b for b in human_msg.content if b.get("type") == "file")
        assert file_block["media_type"] == "application/pdf"
        assert file_block["filename"] == "job_posting.pdf"

    def test_parse_screenshot(self, parser: LLMParser) -> None:
        parser.llm_chat.structured_invoke = MagicMock(return_value=_SAMPLE_OUTPUT)

        job = parser.parse(
            content=b"\x89PNG fake image",
            source_type="screenshot",
            filename="job_screenshot.png",
        )

        assert job.company == "WidgetCo"

        messages, _schema = parser.llm_chat.structured_invoke.call_args.args
        human_msg = messages[1]
        image_block = next(b for b in human_msg.content if b.get("type") == "image")
        assert image_block["mime_type"] == "image/png"


class TestBuildMessages:
    """Verify LangChain message construction for different source types."""

    def test_html_produces_system_and_human_string(self, parser: LLMParser) -> None:
        messages = parser._build_messages("<html>hi</html>", "html", None)

        assert len(messages) == 2
        assert isinstance(messages[0], SystemMessage)
        assert isinstance(messages[1], HumanMessage)
        # HTML/text → plain string content (not a list of blocks)
        assert isinstance(messages[1].content, str)
        assert "<html>hi</html>" in messages[1].content

    def test_text_produces_plain_string(self, parser: LLMParser) -> None:
        messages = parser._build_messages("plain text job", "text", None)
        assert isinstance(messages[1].content, str)

    def test_pdf_produces_file_block(self, parser: LLMParser) -> None:
        messages = parser._build_messages(b"%PDF", "pdf", "resume.pdf")
        human = messages[1]

        assert isinstance(human.content, list)
        file_block = next(b for b in human.content if b.get("type") == "file")
        assert file_block["filename"] == "resume.pdf"
        assert file_block["media_type"] == "application/pdf"
        assert "data" in file_block  # base64-encoded content

    def test_pdf_default_filename(self, parser: LLMParser) -> None:
        messages = parser._build_messages(b"%PDF", "pdf", None)
        file_block = next(b for b in messages[1].content if b.get("type") == "file")
        assert file_block["filename"] == "job_posting.pdf"

    def test_screenshot_produces_image_block(self, parser: LLMParser) -> None:
        messages = parser._build_messages(b"\x89PNG", "screenshot", None)
        human = messages[1]

        image_block = next(b for b in human.content if b.get("type") == "image")
        assert image_block["mime_type"] == "image/png"
        assert "data" in image_block

    def test_custom_filename_for_pdf(self, parser: LLMParser) -> None:
        messages = parser._build_messages(b"%PDF", "pdf", "custom_job.pdf")
        file_block = next(b for b in messages[1].content if b.get("type") == "file")
        assert file_block["filename"] == "custom_job.pdf"


class TestOutputToJob:
    """Verify JobParseOutput → Job field mapping."""

    def test_all_fields_mapped(self) -> None:
        job = LLMParser._output_to_job(_SAMPLE_OUTPUT)

        assert job.role == "Backend Engineer"
        assert job.company == "WidgetCo"
        assert job.location == "Remote"
        assert job.description == "Build and maintain backend services for our widget platform."
        assert job.salary_range == "$130k–$170k"
        assert job.employment_type == "full-time"
        assert job.experience_level == "mid-level"
        assert job.required_skills == ["Python", "FastAPI", "PostgreSQL", "Docker"]
        assert job.recruiter_email == "hr@widgetco.com"
        # pipeline-level fields stay at their defaults
        assert job.link == ""
        assert job.parsed_at is None

    def test_empty_output_gives_blank_job(self) -> None:
        empty_output = JobParseOutput()
        job = LLMParser._output_to_job(empty_output)

        assert job.role == ""
        assert job.company == ""
        assert job.required_skills == []
