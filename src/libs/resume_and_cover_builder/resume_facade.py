"""Facade managing the interaction between user, LLM, and PDF generation."""

import hashlib
from pathlib import Path

import inquirer
from loguru import logger
from selenium import webdriver

from config import settings
from src.job import Job
from src.libs.resume_and_cover_builder.llm.llm_job_parser import LLMParser
from src.libs.resume_and_cover_builder.resume_generator import ResumeGenerator
from src.libs.resume_and_cover_builder.style_manager import StyleManager
from src.schemas.resume import Resume
from src.utils.chrome_utils import html_to_pdf

from .config import global_config


class ResumeFacade:
    def __init__(
        self,
        api_key: str,
        style_manager: StyleManager,
        resume_generator: ResumeGenerator,
        resume_object: Resume,
        output_path: Path,
    ) -> None:
        """Initialise the facade and configure the global builder config.

        Args:
            api_key: The OpenAI API key.
            style_manager: Manages available CSS styles.
            resume_generator: Generates HTML resumes / cover letters.
            resume_object: Parsed resume data.
            output_path: Directory for generated artefacts.
        """
        lib_directory = Path(__file__).resolve().parent
        global_config.STYLES_DIRECTORY = lib_directory / "resume_style"
        global_config.LOG_OUTPUT_FILE_PATH = output_path
        global_config.API_KEY = api_key
        self.style_manager = style_manager
        self.resume_generator = resume_generator
        self.resume_generator.set_resume_object(resume_object)
        self.selected_style = None  # Property to store the selected style

    def set_driver(self, driver: webdriver.Chrome) -> None:
        self.driver = driver

    def prompt_user(self, choices: list[str], message: str) -> str:
        """
        Prompt the user with the given message and choices.
        Args:
            choices (list[str]): The list of choices to present to the user.
            message (str): The message to display to the user.
        Returns:
            str: The choice selected by the user.
        """
        questions = [
            inquirer.List("selection", message=message, choices=choices),
        ]
        return inquirer.prompt(questions)["selection"]

    def prompt_for_text(self, message: str) -> str:
        """
        Prompt the user to enter text with the given message.
        Args:
            message (str): The message to display to the user.
        Returns:
            str: The text entered by the user.
        """
        questions = [
            inquirer.Text("text", message=message),
        ]
        return inquirer.prompt(questions)["text"]

    def link_to_job(self, job_url: str) -> None:
        self.driver.get(job_url)
        self.driver.implicitly_wait(10)
        body_element = self.driver.find_element("tag name", "body")
        body_element = body_element.get_attribute("outerHTML")
        self.llm_job_parser = LLMParser(openai_api_key=global_config.API_KEY)
        self.llm_job_parser.set_body_html(body_element)

        self.job = Job()
        self.job.role = self.llm_job_parser.extract_role()
        self.job.company = self.llm_job_parser.extract_company_name()
        self.job.description = self.llm_job_parser.extract_job_description()
        self.job.location = self.llm_job_parser.extract_location()
        self.job.link = job_url
        logger.info(f"Extracting job details from URL: {job_url}")

    def create_resume_pdf_job_tailored(self) -> tuple[bytes, str]:
        """Create a job-tailored resume PDF.

        Returns:
            tuple: (PDF base64 string, suggested output folder name).
        """
        style_path = self.style_manager.get_style_path()
        if style_path is None:
            raise ValueError("You must choose a style before generating the PDF.")

        html_resume = self.resume_generator.create_resume_job_description_text(style_path, self.job.description)

        suggested_name = hashlib.md5(self.job.link.encode()).hexdigest()[: settings.HASH_PREFIX_LENGTH]

        result = html_to_pdf(html_resume, self.driver)
        self.driver.quit()
        return result, suggested_name

    def create_resume_pdf(self) -> bytes:
        """Create a base resume PDF (no job tailoring).

        Returns:
            bytes: PDF content as a base64-encoded string.
        """
        style_path = self.style_manager.get_style_path()
        if style_path is None:
            raise ValueError("You must choose a style before generating the PDF.")

        html_resume = self.resume_generator.create_resume(style_path)
        result = html_to_pdf(html_resume, self.driver)
        self.driver.quit()
        return result

    def create_cover_letter(self) -> tuple[bytes, str]:
        """Create a cover letter PDF tailored to the linked job.

        Returns:
            tuple: (PDF base64 string, suggested output folder name).
        """
        style_path = self.style_manager.get_style_path()
        if style_path is None:
            raise ValueError("You must choose a style before generating the PDF.")

        cover_letter_html = self.resume_generator.create_cover_letter_job_description(style_path, self.job.description)

        suggested_name = hashlib.md5(self.job.link.encode()).hexdigest()[: settings.HASH_PREFIX_LENGTH]

        result = html_to_pdf(cover_letter_html, self.driver)
        self.driver.quit()
        return result, suggested_name
