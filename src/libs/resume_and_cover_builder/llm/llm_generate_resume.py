"""Generate a resume from structured data using an LLM."""

import types
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from loguru import logger

from config import settings
from src.libs.resume_and_cover_builder.llm.llm_chat_model import LoggerChatModel
from src.libs.resume_and_cover_builder.utils import preprocess_template_string
from src.schemas.resume import Resume


class LLMResumer:
    def __init__(self, openai_api_key: str, strings: types.ModuleType) -> None:
        self.llm_cheap = LoggerChatModel(
            ChatOpenAI(
                model_name=settings.LLM_MODEL,
                openai_api_key=openai_api_key,
                temperature=settings.LLM_TEMPERATURE,
            )
        )
        self.strings = strings
        self.job_description: str | None = None

    def set_resume(self, resume: Resume) -> None:
        """
        Set the resume object to be used for generating the resume.
        Args:
            resume (Resume): The resume object to be used.
        """
        self.resume = resume

    def set_job_description_from_text(self, job_description_text: str) -> None:
        """
        Summarize and store a job description for use in resume generation.
        Args:
            job_description_text (str): The plain text job description to summarize.
        """
        prompt = ChatPromptTemplate.from_template(self.strings.summarize_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        self.job_description = chain.invoke({"text": job_description_text})

    def generate_header(self, data: dict[str, Any] | None = None) -> str:
        """
        Generate the header section of the resume.
        Args:
            data (dict): The personal information to use for generating the header.
        Returns:
            str: The generated header section.
        """
        header_prompt_template = preprocess_template_string(self.strings.prompt_header)
        prompt = ChatPromptTemplate.from_template(header_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        if data is None:
            input_data: dict[str, Any] = {"personal_information": self.resume.personal_information}
            if self.job_description is not None:
                input_data["job_description"] = self.job_description
        else:
            input_data = data
        output = chain.invoke(input_data)
        return output

    def generate_education_section(self, data: dict[str, Any] | None = None) -> str:
        """
        Generate the education section of the resume.
        Args:
            data (dict): The education details to use for generating the education section.
        Returns:
            str: The generated education section.
        """
        logger.debug("Starting education section generation")

        education_prompt_template = preprocess_template_string(self.strings.prompt_education)
        logger.debug(f"Education template: {education_prompt_template}")

        prompt = ChatPromptTemplate.from_template(education_prompt_template)
        logger.debug(f"Prompt: {prompt}")

        chain = prompt | self.llm_cheap | StrOutputParser()
        logger.debug(f"Chain created: {chain}")

        if data is None:
            input_data: dict[str, Any] = {"education_details": self.resume.education_details}
            if self.job_description is not None:
                input_data["job_description"] = self.job_description
        else:
            input_data = data
        output = chain.invoke(input_data)
        logger.debug(f"Chain invocation result: {output}")

        logger.debug("Education section generation completed")
        return output

    def generate_work_experience_section(self, data: dict[str, Any] | None = None) -> str:
        """
        Generate the work experience section of the resume.
        Args:
            data (dict): The work experience details to use for generating the work experience section.
        Returns:
            str: The generated work experience section.
        """
        logger.debug("Starting work experience section generation")

        work_experience_prompt_template = preprocess_template_string(self.strings.prompt_working_experience)
        logger.debug(f"Work experience template: {work_experience_prompt_template}")

        prompt = ChatPromptTemplate.from_template(work_experience_prompt_template)
        logger.debug(f"Prompt: {prompt}")

        chain = prompt | self.llm_cheap | StrOutputParser()
        logger.debug(f"Chain created: {chain}")

        if data is None:
            input_data: dict[str, Any] = {"experience_details": self.resume.experience_details}
            if self.job_description is not None:
                input_data["job_description"] = self.job_description
        else:
            input_data = data
        output = chain.invoke(input_data)
        logger.debug(f"Chain invocation result: {output}")

        logger.debug("Work experience section generation completed")
        return output

    def generate_projects_section(self, data: dict[str, Any] | None = None) -> str:
        """
        Generate the side projects section of the resume.
        Args:
            data (dict): The side projects to use for generating the side projects section.
        Returns:
            str: The generated side projects section.
        """
        logger.debug("Starting side projects section generation")

        projects_prompt_template = preprocess_template_string(self.strings.prompt_projects)
        logger.debug(f"Side projects template: {projects_prompt_template}")

        prompt = ChatPromptTemplate.from_template(projects_prompt_template)
        logger.debug(f"Prompt: {prompt}")

        chain = prompt | self.llm_cheap | StrOutputParser()
        logger.debug(f"Chain created: {chain}")

        if data is None:
            input_data: dict[str, Any] = {"projects": self.resume.projects}
            if self.job_description is not None:
                input_data["job_description"] = self.job_description
        else:
            input_data = data
        output = chain.invoke(input_data)
        logger.debug(f"Chain invocation result: {output}")

        logger.debug("Side projects section generation completed")
        return output

    def generate_achievements_section(self, data: dict[str, Any] | None = None) -> str:
        """
        Generate the achievements section of the resume.
        Args:
            data (dict): The achievements to use for generating the achievements section.
        Returns:
            str: The generated achievements section.
        """
        logger.debug("Starting achievements section generation")

        achievements_prompt_template = preprocess_template_string(self.strings.prompt_achievements)
        logger.debug(f"Achievements template: {achievements_prompt_template}")

        prompt = ChatPromptTemplate.from_template(achievements_prompt_template)
        logger.debug(f"Prompt: {prompt}")

        chain = prompt | self.llm_cheap | StrOutputParser()
        logger.debug(f"Chain created: {chain}")

        if data is None:
            input_data: dict[str, Any] = {
                "achievements": self.resume.achievements,
                "certifications": self.resume.certifications,
            }
            if self.job_description is not None:
                input_data["job_description"] = self.job_description
        else:
            input_data = data
        logger.debug(f"Input data for the chain: {input_data}")

        output = chain.invoke(input_data)
        logger.debug(f"Chain invocation result: {output}")

        logger.debug("Achievements section generation completed")
        return output

    def generate_certifications_section(self, data: dict[str, Any] | None = None) -> str:
        """
        Generate the certifications section of the resume.
        Returns:
            str: The generated certifications section.
        """
        logger.debug("Starting Certifications section generation")

        certifications_prompt_template = preprocess_template_string(self.strings.prompt_certifications)
        logger.debug(f"Certifications template: {certifications_prompt_template}")

        prompt = ChatPromptTemplate.from_template(certifications_prompt_template)
        logger.debug(f"Prompt: {prompt}")

        chain = prompt | self.llm_cheap | StrOutputParser()
        logger.debug(f"Chain created: {chain}")

        if data is None:
            input_data: dict[str, Any] = {"certifications": self.resume.certifications}
            if self.job_description is not None:
                input_data["job_description"] = self.job_description
        else:
            input_data = data
        logger.debug(f"Input data for the chain: {input_data}")

        output = chain.invoke(input_data)
        logger.debug(f"Chain invocation result: {output}")

        logger.debug("Certifications section generation completed")
        return output

    def _collect_skills(self) -> set[str]:
        """Gather skills from experience and education details."""
        skills: set[str] = set()
        if self.resume.experience_details:
            for exp in self.resume.experience_details:
                if exp.skills_acquired:
                    skills.update(exp.skills_acquired)
        if self.resume.education_details:
            for edu in self.resume.education_details:
                if edu.exam:
                    for exam in edu.exam:
                        skills.update(exam.keys())
        return skills

    def generate_additional_skills_section(self, data: dict[str, Any] | None = None) -> str:
        """Generate the additional skills section of the resume."""
        additional_skills_prompt_template = preprocess_template_string(self.strings.prompt_additional_skills)

        prompt = ChatPromptTemplate.from_template(additional_skills_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        if data is None:
            input_data: dict[str, Any] = {
                "languages": self.resume.languages,
                "interests": self.resume.interests,
                "skills": self._collect_skills(),
            }
            if self.job_description is not None:
                input_data["job_description"] = self.job_description
        else:
            input_data = data
        output = chain.invoke(input_data)

        return output

    def generate_html_resume(self) -> str:
        """
        Generate the full HTML resume based on the resume object.
        Returns:
            str: The generated HTML resume.
        """

        def header_fn():
            if self.resume.personal_information:
                return self.generate_header()
            return ""

        def education_fn():
            if self.resume.education_details:
                return self.generate_education_section()
            return ""

        def work_experience_fn():
            if self.resume.experience_details:
                return self.generate_work_experience_section()
            return ""

        def projects_fn():
            if self.resume.projects:
                return self.generate_projects_section()
            return ""

        def achievements_fn():
            if self.resume.achievements:
                return self.generate_achievements_section()
            return ""

        def certifications_fn():
            if self.resume.certifications:
                return self.generate_certifications_section()
            return ""

        def additional_skills_fn():
            if (
                self.resume.experience_details
                or self.resume.education_details
                or self.resume.languages
                or self.resume.interests
            ):
                return self.generate_additional_skills_section()
            return ""

        # Create a dictionary to map the function names to their respective callables
        functions = {
            "header": header_fn,
            "education": education_fn,
            "work_experience": work_experience_fn,
            "projects": projects_fn,
            "achievements": achievements_fn,
            "certifications": certifications_fn,
            "additional_skills": additional_skills_fn,
        }

        # Use ThreadPoolExecutor to run the functions in parallel
        with ThreadPoolExecutor() as executor:
            future_to_section = {executor.submit(fn): section for section, fn in functions.items()}
            results = {}
            for future in as_completed(future_to_section):
                section = future_to_section[future]
                try:
                    result = future.result()
                    if result:
                        results[section] = result
                except Exception as exc:
                    logger.error(f"{section} raised an exception: {exc}")
        full_resume = "<body>\n"
        full_resume += f"  {results.get('header', '')}\n"
        full_resume += "  <main>\n"
        full_resume += f"    {results.get('work_experience', '')}\n"
        full_resume += f"    {results.get('education', '')}\n"
        full_resume += f"    {results.get('projects', '')}\n"
        # full_resume += f"    {results.get('achievements', '')}\n"
        # full_resume += f"    {results.get('certifications', '')}\n"
        full_resume += f"    {results.get('additional_skills', '')}\n"
        full_resume += "  </main>\n"
        full_resume += "</body>"
        return full_resume
