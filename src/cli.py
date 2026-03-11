"""CLI interaction helpers using inquirer prompts."""

import base64
from pathlib import Path

import inquirer

from src.app_config import AppConfig
from src.libs.resume_and_cover_builder import ResumeFacade, ResumeGenerator, StyleManager
from src.logging import logger
from src.utils.chrome_utils import init_browser


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


def _build_facade(app_config: AppConfig, style_manager: StyleManager) -> tuple[ResumeFacade, ResumeGenerator]:
    """Build and return a configured ResumeFacade with shared setup logic."""
    resume_generator = ResumeGenerator()
    driver = init_browser()
    resume_generator.set_resume_object(app_config.resume_object)

    resume_facade = ResumeFacade(
        api_key=app_config.secrets.llm_api_key,
        style_manager=style_manager,
        resume_generator=resume_generator,
        resume_object=app_config.resume_object,
        output_path=Path("data_folder/output"),
    )
    resume_facade.set_driver(driver)
    return resume_facade, resume_generator


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


def create_cover_letter(app_config: AppConfig) -> None:
    """Generate a tailored cover letter PDF."""
    try:
        logger.info("Generating a cover letter based on provided parameters.")
        style_manager = StyleManager()
        _select_style(style_manager)

        questions = [inquirer.Text("job_url", message="Please enter the URL of the job description:")]
        answers = inquirer.prompt(questions)
        job_url = answers.get("job_url")

        resume_facade, _ = _build_facade(app_config, style_manager)
        resume_facade.link_to_job(job_url)
        result_base64, suggested_name = resume_facade.create_cover_letter()

        output_dir = app_config.output_dir / suggested_name
        _write_pdf(result_base64, output_dir / "cover_letter_tailored.pdf")
    except Exception as e:
        logger.exception(f"An error occurred while creating the cover letter: {e}")
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

        resume_facade, _ = _build_facade(app_config, style_manager)
        resume_facade.link_to_job(job_url)
        result_base64, suggested_name = resume_facade.create_resume_pdf_job_tailored()

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

        resume_facade, _ = _build_facade(app_config, style_manager)
        result_base64 = resume_facade.create_resume_pdf()

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
