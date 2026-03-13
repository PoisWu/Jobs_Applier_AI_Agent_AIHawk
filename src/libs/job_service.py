"""Service responsible for acquiring and persisting job postings."""

import uuid
from datetime import datetime
from pathlib import Path

from loguru import logger
from selenium import webdriver

from src.job import Job
from src.libs.job_store import JobStore
from src.libs.resume_and_cover_builder.llm.llm_job_parser import LLMParser

# Maps file extensions to source_type identifiers.
_EXT_TO_SOURCE: dict[str, str] = {
    ".html": "html",
    ".htm": "html",
    ".txt": "text",
    ".md": "text",
    ".pdf": "pdf",
    ".png": "screenshot",
    ".jpg": "screenshot",
    ".jpeg": "screenshot",
    ".webp": "screenshot",
}


class JobService:
    """Fetches, parses, and persists job postings.

    This service is the single owner of all job-acquisition logic:
    Selenium-based web scraping, local file ingestion, LLM parsing via
    ``LLMParser``, and SQLite persistence via ``JobStore``.

    It has no knowledge of resume or cover letter generation.
    """

    def __init__(self, api_key: str, output_path: Path) -> None:
        """Initialise the service.

        Args:
            api_key: OpenAI API key forwarded to ``LLMParser``.
            output_path: Directory used for the jobs database and raw assets.
        """
        self.llm_job_parser = LLMParser(api_key=api_key)
        self.job_store = JobStore(
            db_path=output_path / "jobs.db",
            assets_dir=output_path / "jobs_assets",
        )
        self.driver: webdriver.Chrome | None = None

    def set_driver(self, driver: webdriver.Chrome) -> None:
        """Provide the Selenium Chrome driver used for web scraping."""
        self.driver = driver

    def fetch_from_url(self, job_url: str) -> Job:
        """Fetch a job page by URL, parse it via the LLM, and persist it.

        If the same URL was parsed previously, the cached ``Job`` is returned
        without making any extra API calls.

        Args:
            job_url: Public URL of the job posting.

        Returns:
            Parsed and persisted ``Job`` instance.
        """
        # 1. Check the cache
        cached = self.job_store.get_by_url(job_url)
        if cached:
            logger.info(f"Loaded cached job: {cached.role} at {cached.company}")
            return cached

        if self.driver is None:
            raise RuntimeError("A Selenium driver must be set before fetching from URL. Call set_driver() first.")

        # 2. Fetch with Selenium
        self.driver.get(job_url)
        self.driver.implicitly_wait(10)
        body_element = self.driver.find_element("tag name", "body")
        raw_html = body_element.get_attribute("outerHTML")

        # 3. Parse with a single LLM call (Responses API)
        job = self.llm_job_parser.parse(content=raw_html, source_type="html")
        job.link = job_url
        job.source_type = "html"
        job.parsed_at = datetime.now()

        # 4. Persist to SQLite + save raw asset
        self.job_store.save(job, raw_content=raw_html, source_type="html")
        logger.info(f"Extracted job details from URL: {job_url}")
        return job

    def fetch_from_file(self, file_path: str) -> Job:
        """Parse a local job file (PDF, screenshot, HTML, or plain text).

        The file's binary content is sent directly to the LLM (PDFs and
        images are handled natively by the Responses API).

        A ``local://<uuid>`` identifier is generated as the ``link`` since
        there is no URL.

        Args:
            file_path: Absolute or relative path to the local job file.

        Returns:
            Parsed and persisted ``Job`` instance.
        """
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(f"Job file not found: {file_path}")

        ext = path.suffix.lower()
        source_type = _EXT_TO_SOURCE.get(ext)
        if source_type is None:
            raise ValueError(f"Unsupported file extension '{ext}'. Supported: {', '.join(sorted(_EXT_TO_SOURCE))}")

        # Read file content
        if source_type in ("html", "text"):
            content: str | bytes = path.read_text(encoding="utf-8")
        else:
            content = path.read_bytes()

        # Parse via the LLM
        job = self.llm_job_parser.parse(
            content=content,
            source_type=source_type,
            filename=path.name,
        )
        job.link = f"local://{uuid.uuid4()}"
        job.source_type = source_type
        job.parsed_at = datetime.now()

        # Persist
        self.job_store.save(job, raw_content=content, source_type=source_type)
        logger.info(f"Extracted job details from file: {file_path}")
        return job
