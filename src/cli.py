"""CLI interaction helpers using inquirer prompts."""

import base64
from pathlib import Path

import inquirer

from src.app_config import AppConfig
from src.libs.job_fetch_pipeline import JobService
from src.libs.llm import LLMProvider
from src.libs.llm.llm_config import LLMConfig
from src.libs.resume_and_cover_builder import ResumeGenerator, ResumeService, StyleManager
from src.logging import logger
from src.utils.chrome_utils import init_browser

_OUTPUT_PATH = Path("data_folder/output")


def _select_style(style_manager: StyleManager) -> None:
    """Present style choices to the user and set the selection."""
    available_styles = style_manager.get_styles()

    if not available_styles:
        logger.warning("No styles available. Proceeding without style selection.")
        return

    choices = style_manager.format_choices(available_styles)
    questions = [
        inquirer.List(
            "style",
            message="Select a style for the resume:",
            choices=choices,
        )
    ]
    style_answer = inquirer.prompt(questions)
    if style_answer and "style" in style_answer:
        selected_choice = style_answer["style"]
        for style_name, (_file_name, _author_link) in available_styles.items():
            if selected_choice.startswith(style_name):
                style_manager.set_selected_style(style_name)
                logger.info(f"Selected style: {style_name}")
                break
    else:
        logger.warning("No style selected. Proceeding with default style.")


def _build_job_service(app_config: AppConfig) -> JobService:
    """Build a ``JobService`` wired up with its own Selenium driver."""
    llm_provider = LLMProvider(LLMConfig(API_KEY=app_config.secrets.llm_api_key, LOG_OUTPUT_FILE_PATH=_OUTPUT_PATH))
    job_service = JobService(
        llm_provider=llm_provider,
        output_path=_OUTPUT_PATH,
    )
    job_service.set_driver(init_browser())
    return job_service


def _build_job_service_only(app_config: AppConfig) -> JobService:
    """Build a ``JobService`` without a Selenium driver (for file/text input)."""
    llm_provider = LLMProvider(LLMConfig(API_KEY=app_config.secrets.llm_api_key, LOG_OUTPUT_FILE_PATH=_OUTPUT_PATH))
    return JobService(
        llm_provider=llm_provider,
        output_path=_OUTPUT_PATH,
    )


def _build_resume_service(app_config: AppConfig, style_manager: StyleManager) -> ResumeService:
    """Build a ``ResumeService`` wired up with its own Selenium driver."""
    llm_provider = LLMProvider(LLMConfig(API_KEY=app_config.secrets.llm_api_key, LOG_OUTPUT_FILE_PATH=_OUTPUT_PATH))
    resume_generator = ResumeGenerator(llm_provider=llm_provider)
    resume_service = ResumeService(
        style_manager=style_manager,
        resume_generator=resume_generator,
        resume_object=app_config.resume_object,
        output_path=_OUTPUT_PATH,
    )
    resume_service.set_driver(init_browser())
    return resume_service


def _write_pdf(pdf_base64: str, output_path: Path) -> None:
    """Decode base64 PDF data and write to disk."""
    try:
        pdf_data = base64.b64decode(pdf_base64)
    except base64.binascii.Error as e:
        logger.error("Error decoding Base64: %s", e)
        raise

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as file:
            file.write(pdf_data)
        logger.info(f"PDF saved at: {output_path}")
    except OSError as e:
        logger.error("Error writing file: %s", e)
        raise


def _print_job_summary(job) -> None:
    """Print a short summary of a parsed job to the console."""
    print("\n--- Job Stored Successfully ---")
    print(f"  Role       : {job.role or '(unknown)'}")
    print(f"  Company    : {job.company or '(unknown)'}")
    print(f"  Location   : {job.location or '(unknown)'}")
    print(f"  Type       : {job.employment_type or '(unknown)'}")
    print(f"  Experience : {job.experience_level or '(unknown)'}")
    print(f"  Link       : {job.link}")
    print("------------------------------\n")


def fetch_job_from_url(app_config: AppConfig) -> None:
    """Fetch a job from a URL, parse it, and store it in the database."""
    try:
        questions = [inquirer.Text("job_url", message="Enter the job posting URL:")]
        answers = inquirer.prompt(questions)
        job_url = (answers or {}).get("job_url", "").strip()
        if not job_url:
            logger.warning("No URL provided. Aborting.")
            return

        job_service = _build_job_service(app_config)
        job = job_service.fetch_from_url(job_url)
        _print_job_summary(job)
    except Exception as e:
        logger.exception(f"An error occurred while fetching the job from URL: {e}")
        raise


def fetch_job_from_file(app_config: AppConfig) -> None:
    """Parse a local job file (PDF, screenshot, HTML, text) and store it."""
    try:
        questions = [
            inquirer.Text(
                "file_path",
                message="Enter the path to the job file (PDF, screenshot, HTML, or text):",
            )
        ]
        answers = inquirer.prompt(questions)
        file_path = (answers or {}).get("file_path", "").strip()
        if not file_path:
            logger.warning("No file path provided. Aborting.")
            return

        job_service = _build_job_service_only(app_config)
        job = job_service.fetch_from_file(file_path)
        _print_job_summary(job)
    except Exception as e:
        logger.exception(f"An error occurred while fetching the job from file: {e}")
        raise


def fetch_job_from_text(app_config: AppConfig) -> None:
    """Accept a pasted plain-text job description, parse it, and store it."""
    try:
        print("Paste the job description below. Enter a blank line when done:")
        lines: list[str] = []
        while True:
            line = input()
            if line == "":
                break
            lines.append(line)

        text = "\n".join(lines)
        if not text.strip():
            logger.warning("No text provided. Aborting.")
            return

        job_service = _build_job_service_only(app_config)
        job = job_service.fetch_from_text(text)
        _print_job_summary(job)
    except Exception as e:
        logger.exception(f"An error occurred while fetching the job from text: {e}")
        raise


def list_stored_jobs(app_config: AppConfig) -> None:
    """Display all jobs currently stored in the database."""
    try:
        job_service = _build_job_service_only(app_config)
        jobs = job_service.job_store.list_all()

        if not jobs:
            print("No jobs stored yet.")
            return

        print(f"\n{'#':<4} {'Role':<30} {'Company':<25} {'Location':<20} {'Type':<15} {'Parsed At'}")
        print("-" * 110)
        for i, job in enumerate(jobs, start=1):
            parsed = job.parsed_at.strftime("%Y-%m-%d %H:%M") if job.parsed_at else ""
            print(
                f"{i:<4} {(job.role or ''):<30} {(job.company or ''):<25} "
                f"{(job.location or ''):<20} {(job.employment_type or ''):<15} {parsed}"
            )
        print()
    except Exception as e:
        logger.exception(f"An error occurred while listing jobs: {e}")
        raise


def create_cover_letter(app_config: AppConfig) -> None:
    """Generate a tailored cover letter PDF."""
    try:
        logger.info("Generating a cover letter based on provided parameters.")
        style_manager = StyleManager()
        _select_style(style_manager)

        questions = [inquirer.Text("job_url", message="Please enter the URL of the job description:")]
        answers = inquirer.prompt(questions)
        job_url = answers.get("job_url")

        job_service = _build_job_service(app_config)
        job = job_service.fetch_from_url(job_url)

        resume_service = _build_resume_service(app_config, style_manager)
        result_base64, suggested_name = resume_service.create_cover_letter(job)

        output_dir = app_config.output_dir / suggested_name
        _write_pdf(result_base64, output_dir / "cover_letter_tailored.pdf")
    except Exception as e:
        logger.exception(f"An error occurred while creating the cover letter: {e}")
        raise


def create_resume_pdf_from_file(app_config: AppConfig) -> None:
    """Generate a job-tailored resume from a local file (PDF, screenshot, text)."""
    try:
        logger.info("Generating a tailored resume from a local job file.")
        style_manager = StyleManager()
        _select_style(style_manager)

        questions = [
            inquirer.Text(
                "file_path",
                message="Enter the path to the job file (PDF, screenshot, HTML, or text):",
            )
        ]
        answers = inquirer.prompt(questions)
        file_path = answers.get("file_path", "").strip()

        job_service = _build_job_service(app_config)
        job = job_service.fetch_from_file(file_path)

        resume_service = _build_resume_service(app_config, style_manager)
        result_base64, suggested_name = resume_service.create_resume_pdf_tailored(job)

        output_dir = app_config.output_dir / suggested_name
        _write_pdf(result_base64, output_dir / "resume_tailored.pdf")
    except Exception as e:
        logger.exception(f"An error occurred while creating the resume from file: {e}")
        raise


def create_resume_pdf_job_tailored(app_config: AppConfig) -> None:
    """Generate a job-tailored resume PDF."""
    try:
        logger.info("Generating a tailored resume based on provided parameters.")
        style_manager = StyleManager()
        _select_style(style_manager)

        questions = [inquirer.Text("job_url", message="Please enter the URL of the job description:")]
        answers = inquirer.prompt(questions)
        job_url = answers.get("job_url")

        job_service = _build_job_service(app_config)
        job = job_service.fetch_from_url(job_url)

        resume_service = _build_resume_service(app_config, style_manager)
        result_base64, suggested_name = resume_service.create_resume_pdf_tailored(job)

        output_dir = app_config.output_dir / suggested_name
        _write_pdf(result_base64, output_dir / "resume_tailored.pdf")
    except Exception as e:
        logger.exception(f"An error occurred while creating the tailored resume: {e}")
        raise


def create_resume_pdf(app_config: AppConfig) -> None:
    """Generate a base resume PDF (no job tailoring)."""
    try:
        logger.info("Generating a base resume based on provided parameters.")
        style_manager = StyleManager()
        _select_style(style_manager)

        resume_service = _build_resume_service(app_config, style_manager)
        result_base64 = resume_service.create_resume_pdf()

        output_dir = app_config.output_dir
        _write_pdf(result_base64, output_dir / "resume_base.pdf")
    except Exception as e:
        logger.exception(f"An error occurred while creating the resume: {e}")
        raise


def handle_inquiries(selected_actions: list[str], app_config: AppConfig) -> None:
    """Dispatch user-selected actions to the appropriate generation function."""
    try:
        if not selected_actions:
            logger.warning("No actions selected. Nothing to execute.")
            return

        action_map = {
            "Generate Resume": create_resume_pdf,
            "Generate Resume Tailored for Job Description": create_resume_pdf_job_tailored,
            "Generate Tailored Cover Letter for Job Description": create_cover_letter,
            "Generate Resume from Local Job File (PDF/Screenshot/Text)": create_resume_pdf_from_file,
            "Fetch Job from URL": fetch_job_from_url,
            "Fetch Job from File": fetch_job_from_file,
            "Fetch Job from Plain Text": fetch_job_from_text,
            "List Stored Jobs": list_stored_jobs,
        }

        handler = action_map.get(selected_actions)
        if handler:
            logger.info(f"Executing: {selected_actions}")
            handler(app_config)
        else:
            logger.warning(f"Unknown action: {selected_actions}")
    except Exception as e:
        logger.exception(f"An error occurred while handling inquiries: {e}")
        raise


def prompt_user_action() -> str:
    """Use inquirer to ask the user which action they want to perform."""
    try:
        questions = [
            inquirer.List(
                "action",
                message="Select the action you want to perform:",
                choices=[
                    "Generate Resume",
                    "Generate Resume Tailored for Job Description",
                    "Generate Tailored Cover Letter for Job Description",
                    "Generate Resume from Local Job File (PDF/Screenshot/Text)",
                    "Fetch Job from URL",
                    "Fetch Job from File",
                    "Fetch Job from Plain Text",
                    "List Stored Jobs",
                ],
            ),
        ]
        answer = inquirer.prompt(questions)
        if answer is None:
            print("No answer provided. The user may have interrupted.")
            return ""
        return answer.get("action", "")
    except Exception as e:
        print(f"An error occurred: {e}")
        return ""
