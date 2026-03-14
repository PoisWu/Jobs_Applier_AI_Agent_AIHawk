"""Generate a resume from structured data using an LLM."""

import types
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TYPE_CHECKING, Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from loguru import logger

from src.libs.resume_and_cover_builder.utils import preprocess_template_string
from src.schemas.resume import Resume

if TYPE_CHECKING:
    from src.libs.llm.llm_provider import LLMProvider


class LLMResumer:
    def __init__(self, llm_provider: "LLMProvider", strings: types.ModuleType) -> None:
        self.llm_cheap = llm_provider.chat_model
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

    def generate_header(self) -> str:
        """Build the resume header HTML directly from personal information — no LLM call."""
        p = self.resume.personal_information
        if p is None:
            return ""

        SEP = '<span class="separator">◇</span>'

        # Full name
        name_parts = [part for part in [p.name, p.surname] if part]
        full_name = " ".join(name_parts) if name_parts else ""

        # Contact line 1: phone [◇ nationality]
        line1_items = []
        phone_parts = [part for part in [p.phone_prefix, p.phone] if part]
        if phone_parts:
            line1_items.append(" ".join(phone_parts))
        if p.country:
            line1_items.append(p.country)
        line1_html = f" {SEP} ".join(line1_items)

        # Contact line 2: email [◇ linkedin] [◇ github]
        line2_items = []
        if p.email:
            line2_items.append(f'<a href="mailto:{p.email}">{p.email}</a>')
        if p.linkedin:
            url = str(p.linkedin).rstrip("/")
            display = url.replace("https://", "").replace("http://", "")
            line2_items.append(f'<a href="{url}">{display}</a>')
        if p.github:
            url = str(p.github).rstrip("/")
            display = url.replace("https://", "").replace("http://", "")
            line2_items.append(f'<a href="{url}">{display}</a>')
        line2_html = f" {SEP} ".join(line2_items)

        contact_lines = ""
        if line1_html:
            contact_lines += f'\n    <p class="contact-line">{line1_html}</p>'
        if line2_html:
            contact_lines += f'\n    <p class="contact-line">{line2_html}</p>'

        return f'<header>\n  <h1>{full_name}</h1>\n  <div class="contact-info">{contact_lines}\n  </div>\n</header>'

    def generate_summary_section(self, data: dict[str, Any] | None = None) -> str:
        """
        Generate the professional summary section of the resume.
        Args:
            data (dict): Optional override data for the prompt variables.
        Returns:
            str: The generated summary section HTML.
        """
        summary_prompt_template = preprocess_template_string(self.strings.prompt_summary)
        prompt = ChatPromptTemplate.from_template(summary_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        if data is None:
            input_data: dict[str, Any] = {
                "personal_information": self.resume.personal_information,
                "experience_details": self.resume.experience_details,
                "education_details": self.resume.education_details,
            }
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
        """Gather skills from experience details (skills_acquired per job entry)."""
        skills: set[str] = set()
        if self.resume.experience_details:
            for exp in self.resume.experience_details:
                if exp.skills_acquired:
                    skills.update(exp.skills_acquired)
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

    def generate_html_resume_single_query(self) -> str:
        """
        Generate the full HTML resume with a single LLM query.

        Returns:
            str: The generated HTML resume body.
        """
        logger.debug("Starting single-query full resume generation")
        full_resume_prompt_template = preprocess_template_string(self.strings.prompt_full_resume)
        prompt = ChatPromptTemplate.from_template(full_resume_prompt_template)
        chain = prompt | self.llm_cheap | StrOutputParser()
        input_data: dict[str, Any] = {
            "personal_information": self.resume.personal_information,
            "education_details": self.resume.education_details,
            "experience_details": self.resume.experience_details,
            "projects": self.resume.projects,
            "achievements": self.resume.achievements,
            "certifications": self.resume.certifications,
            "languages": self.resume.languages,
            "interests": self.resume.interests,
            "skills": self._collect_skills(),
        }
        if self.job_description is not None:
            input_data["job_description"] = self.job_description
        output = chain.invoke(input_data)
        logger.debug("Single-query full resume generation completed")
        header_html = self.generate_header()
        return f"<body>\n  {header_html}\n  {output}\n</body>"

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

        def summary_fn():
            if self.resume.personal_information or self.resume.experience_details:
                return self.generate_summary_section()
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
            "summary": summary_fn,
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
        full_resume += f"    {results.get('summary', '')}\n"
        full_resume += f"    {results.get('work_experience', '')}\n"
        full_resume += f"    {results.get('education', '')}\n"
        full_resume += f"    {results.get('projects', '')}\n"
        # full_resume += f"    {results.get('achievements', '')}\n"
        # full_resume += f"    {results.get('certifications', '')}\n"
        full_resume += f"    {results.get('additional_skills', '')}\n"
        full_resume += "  </main>\n"
        full_resume += "</body>"
        return full_resume
