"""Generate a cover letter matching a job description using an LLM."""

import types
from typing import TYPE_CHECKING

from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from src.libs.resume_and_cover_builder.utils import preprocess_template_string
from src.schemas.resume import Resume

if TYPE_CHECKING:
    from src.libs.llm.llm_provider import LLMProvider


class LLMCoverLetterJobDescription:
    def __init__(self, llm_provider: "LLMProvider", strings: types.ModuleType) -> None:
        self.llm_cheap = llm_provider.chat_model
        self.strings = strings

    def set_resume(self, resume: Resume) -> None:
        """
        Set the resume text to be used for generating the cover letter.
        Args:
            resume (str): The plain text resume to be used.
        """
        self.resume = resume

    def set_job_description_from_text(self, job_description_text: str) -> None:
        """
        Set the job description text to be used for generating the cover letter.
        Args:
            job_description_text (str): The plain text job description to be used.
        """
        logger.debug("Starting job description summarization...")
        prompt = ChatPromptTemplate.from_template(self.strings.summarize_prompt_template)
        self.job_description = self.llm_cheap.invoke(prompt.format_messages(text=job_description_text))
        logger.debug(f"Job description summarization complete: {self.job_description}")

    def generate_cover_letter(self) -> str:
        """
        Generate the cover letter based on the job description and resume.
        Returns:
            str: The generated cover letter
        """
        logger.debug("Starting cover letter generation...")
        prompt_template = preprocess_template_string(self.strings.cover_letter_template)
        logger.debug(f"Cover letter template after preprocessing: {prompt_template}")

        prompt = ChatPromptTemplate.from_template(prompt_template)
        logger.debug(f"Prompt created: {prompt}")

        input_data = {"job_description": self.job_description, "resume": self.resume}
        logger.debug(f"Input data: {input_data}")

        output = self.llm_cheap.invoke(prompt.format_messages(**input_data))
        logger.debug(f"Cover letter generation result: {output}")

        logger.debug("Cover letter generation completed")
        return output
