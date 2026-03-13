"""Tests for the rewritten LLMParser (Responses API)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.job import Job
from src.libs.resume_and_cover_builder.llm.llm_job_parser import LLMParser

# A realistic JSON blob the LLM is expected to return.
_SAMPLE_LLM_JSON = json.dumps(
    {
        "role": "Backend Engineer",
        "company": "WidgetCo",
        "location": "Remote",
        "description": "Build and maintain backend services for our widget platform.",
        "salary_range": "$130k–$170k",
        "employment_type": "full-time",
        "experience_level": "mid-level",
        "required_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "recruiter_email": "hr@widgetco.com",
    }
)


def _make_mock_response(text: str, model: str = "gpt-5.4") -> MagicMock:
    """Build a mock object that mimics the OpenAI Responses API return value."""
    content_block = MagicMock()
    content_block.type = "output_text"
    content_block.text = text

    message_item = MagicMock()
    message_item.type = "message"
    message_item.content = [content_block]

    usage = MagicMock()
    usage.input_tokens = 500
    usage.output_tokens = 200

    response = MagicMock()
    response.output = [message_item]
    response.usage = usage
    response.model = model
    return response


@pytest.fixture
def parser() -> LLMParser:
    """Return an ``LLMParser`` with a dummy API key (API calls are mocked)."""
    return LLMParser(api_key="sk-test-dummy-key", model="gpt-5.4")


class TestLLMParserParse:
    """Verify that ``LLMParser.parse()`` correctly hydrates a ``Job``."""

    @patch("src.libs.resume_and_cover_builder.llm.llm_job_parser.log_llm_call")
    def test_parse_html(self, mock_log: MagicMock, parser: LLMParser) -> None:
        mock_resp = _make_mock_response(_SAMPLE_LLM_JSON)
        parser.client = MagicMock()
        parser.client.responses.create.return_value = mock_resp

        job = parser.parse(content="<html><body>Some job page</body></html>", source_type="html")

        assert isinstance(job, Job)
        assert job.role == "Backend Engineer"
        assert job.company == "WidgetCo"
        assert job.location == "Remote"
        assert job.salary_range == "$130k–$170k"
        assert job.required_skills == ["Python", "FastAPI", "PostgreSQL", "Docker"]
        assert job.recruiter_email == "hr@widgetco.com"
        assert job.parsed_at is not None

        # Verify the API was called once
        parser.client.responses.create.assert_called_once()

    @patch("src.libs.resume_and_cover_builder.llm.llm_job_parser.log_llm_call")
    def test_parse_pdf(self, mock_log: MagicMock, parser: LLMParser) -> None:
        mock_resp = _make_mock_response(_SAMPLE_LLM_JSON)
        parser.client = MagicMock()
        parser.client.responses.create.return_value = mock_resp

        job = parser.parse(content=b"%PDF-1.4 fake pdf bytes", source_type="pdf")

        assert job.role == "Backend Engineer"
        # Verify input_file block was used (not input_text for the content)
        call_args = parser.client.responses.create.call_args
        content_blocks = call_args.kwargs["input"][0]["content"]
        # First block is system prompt (input_text), second is the file
        assert content_blocks[1]["type"] == "input_file"
        assert content_blocks[1]["filename"] == "job_posting.pdf"

    @patch("src.libs.resume_and_cover_builder.llm.llm_job_parser.log_llm_call")
    def test_parse_screenshot(self, mock_log: MagicMock, parser: LLMParser) -> None:
        mock_resp = _make_mock_response(_SAMPLE_LLM_JSON)
        parser.client = MagicMock()
        parser.client.responses.create.return_value = mock_resp

        job = parser.parse(content=b"\x89PNG fake image", source_type="screenshot", filename="job_screenshot.png")

        assert job.company == "WidgetCo"
        call_args = parser.client.responses.create.call_args
        content_blocks = call_args.kwargs["input"][0]["content"]
        assert content_blocks[1]["type"] == "input_file"
        assert content_blocks[1]["filename"] == "job_screenshot.png"


class TestLLMParserEdgeCases:
    """Verify graceful handling of malformed / unexpected LLM output."""

    @patch("src.libs.resume_and_cover_builder.llm.llm_job_parser.log_llm_call")
    def test_markdown_fenced_json(self, mock_log: MagicMock, parser: LLMParser) -> None:
        """The model wraps its JSON in ```json ... ``` — should still parse."""
        fenced = f"```json\n{_SAMPLE_LLM_JSON}\n```"
        mock_resp = _make_mock_response(fenced)
        parser.client = MagicMock()
        parser.client.responses.create.return_value = mock_resp

        job = parser.parse(content="<html>test</html>", source_type="html")
        assert job.role == "Backend Engineer"

    @patch("src.libs.resume_and_cover_builder.llm.llm_job_parser.log_llm_call")
    def test_invalid_json_returns_blank_job(self, mock_log: MagicMock, parser: LLMParser) -> None:
        mock_resp = _make_mock_response("This is not JSON at all.")
        parser.client = MagicMock()
        parser.client.responses.create.return_value = mock_resp

        job = parser.parse(content="<html>test</html>", source_type="html")
        assert job.role == ""
        assert job.company == ""

    @patch("src.libs.resume_and_cover_builder.llm.llm_job_parser.log_llm_call")
    def test_empty_response(self, mock_log: MagicMock, parser: LLMParser) -> None:
        mock_resp = _make_mock_response("")
        parser.client = MagicMock()
        parser.client.responses.create.return_value = mock_resp

        job = parser.parse(content="<html/>", source_type="html")
        assert job.role == ""

    @patch("src.libs.resume_and_cover_builder.llm.llm_job_parser.log_llm_call")
    def test_skills_as_csv_string(self, mock_log: MagicMock, parser: LLMParser) -> None:
        """The model returns required_skills as a comma-separated string."""
        data = {
            "role": "Dev",
            "company": "X",
            "location": "",
            "description": "",
            "salary_range": "",
            "employment_type": "",
            "experience_level": "",
            "required_skills": "Python, Docker, K8s",
            "recruiter_email": "",
        }
        mock_resp = _make_mock_response(json.dumps(data))
        parser.client = MagicMock()
        parser.client.responses.create.return_value = mock_resp

        job = parser.parse(content="text", source_type="text")
        assert job.required_skills == ["Python", "Docker", "K8s"]


class TestBuildContentBlocks:
    """Verify content block construction for different source types."""

    def test_html_produces_two_text_blocks(self, parser: LLMParser) -> None:
        blocks = parser._build_content_blocks("<html>hi</html>", "html", None)
        assert len(blocks) == 2
        assert all(b["type"] == "input_text" for b in blocks)

    def test_pdf_produces_text_plus_file_block(self, parser: LLMParser) -> None:
        blocks = parser._build_content_blocks(b"%PDF", "pdf", "resume.pdf")
        assert len(blocks) == 2
        assert blocks[0]["type"] == "input_text"
        assert blocks[1]["type"] == "input_file"
        assert blocks[1]["filename"] == "resume.pdf"
        assert blocks[1]["file_data"].startswith("data:application/pdf;base64,")

    def test_screenshot_produces_file_block(self, parser: LLMParser) -> None:
        blocks = parser._build_content_blocks(b"\x89PNG", "screenshot", None)
        assert blocks[1]["type"] == "input_file"
        assert blocks[1]["filename"] == "screenshot.png"
        assert "image/png" in blocks[1]["file_data"]
