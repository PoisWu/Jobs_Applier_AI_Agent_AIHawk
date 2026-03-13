"""Service responsible for generating resume and cover letter PDFs."""

import hashlib
from pathlib import Path

from loguru import logger
from selenium import webdriver

from config import settings
from src.job import Job
from src.libs.resume_and_cover_builder.resume_generator import ResumeGenerator
from src.libs.resume_and_cover_builder.style_manager import StyleManager
from src.schemas.resume import Resume
from src.utils.chrome_utils import html_to_pdf

from .builder_config import builder_config


class ResumeService:
    """Generates resume and cover letter PDFs.

    This service is the single owner of all document-generation logic:
    invoking ``ResumeGenerator`` to produce HTML, rendering that HTML to PDF
    via ``html_to_pdf`` (Selenium), and returning the result to the caller.

    It has no knowledge of how or where a ``Job`` was obtained.
    """

    def __init__(
        self,
        api_key: str,
        style_manager: StyleManager,
        resume_generator: ResumeGenerator,
        resume_object: Resume,
        output_path: Path,
    ) -> None:
        """Initialise the service and configure the global builder config.

        Args:
            api_key: OpenAI API key forwarded to the LLM generator.
            style_manager: Manages available CSS styles.
            resume_generator: Generates HTML resumes / cover letters.
            resume_object: Parsed resume data.
            output_path: Directory for generated artefacts (used by builder_config).
        """
        lib_directory = Path(__file__).resolve().parent
        builder_config.STYLES_DIRECTORY = lib_directory / "resume_style"
        builder_config.LOG_OUTPUT_FILE_PATH = output_path
        builder_config.API_KEY = api_key

        self.style_manager = style_manager
        self.resume_generator = resume_generator
        self.resume_generator.set_resume_object(resume_object)
        self.driver: webdriver.Chrome | None = None

    def set_driver(self, driver: webdriver.Chrome) -> None:
        """Provide the Selenium Chrome driver used for HTML-to-PDF rendering."""
        self.driver = driver

    def _get_style_path(self) -> Path:
        style_path = self.style_manager.get_style_path()
        if style_path is None:
            raise ValueError("You must choose a style before generating the PDF.")
        return style_path

    def _render_pdf(self, html: str) -> bytes:
        if self.driver is None:
            raise RuntimeError("A Selenium driver must be set before rendering PDF. Call set_driver() first.")
        result = html_to_pdf(html, self.driver)
        self.driver.quit()
        return result

    def create_resume_pdf(self) -> bytes:
        """Create a base resume PDF (no job tailoring).

        Returns:
            PDF content as a base64-encoded string.
        """
        html_resume = self.resume_generator.create_resume(self._get_style_path())
        logger.info("Generated base resume HTML.")
        return self._render_pdf(html_resume)

    def create_resume_pdf_tailored(self, job: Job) -> tuple[bytes, str]:
        """Create a job-tailored resume PDF.

        Args:
            job: The parsed job posting to tailor the resume against.

        Returns:
            Tuple of (PDF base64 string, suggested output folder name).
        """
        html_resume = self.resume_generator.create_resume_job_description_text(self._get_style_path(), job.description)
        suggested_name = hashlib.md5(job.link.encode()).hexdigest()[: settings.HASH_PREFIX_LENGTH]
        logger.info(f"Generated tailored resume HTML for job: {job.role} at {job.company}.")
        return self._render_pdf(html_resume), suggested_name

    def create_cover_letter(self, job: Job) -> tuple[bytes, str]:
        """Create a cover letter PDF tailored to the given job.

        Args:
            job: The parsed job posting used to tailor the cover letter.

        Returns:
            Tuple of (PDF base64 string, suggested output folder name).
        """
        cover_letter_html = self.resume_generator.create_cover_letter_job_description(
            self._get_style_path(), job.description
        )
        suggested_name = hashlib.md5(job.link.encode()).hexdigest()[: settings.HASH_PREFIX_LENGTH]
        logger.info(f"Generated cover letter HTML for job: {job.role} at {job.company}.")
        return self._render_pdf(cover_letter_html), suggested_name
