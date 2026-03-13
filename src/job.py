from datetime import datetime

from pydantic import BaseModel

from src.logging import logger


class Job(BaseModel):
    role: str = ""
    company: str = ""
    location: str = ""
    link: str = ""
    apply_method: str = ""
    description: str = ""
    summarize_job_description: str = ""
    recruiter_link: str = ""
    resume_path: str = ""
    cover_letter_path: str = ""

    # --- new structured fields ---
    salary_range: str = ""
    employment_type: str = ""
    experience_level: str = ""
    required_skills: list[str] = []
    recruiter_email: str = ""

    # --- source / persistence metadata ---
    raw_content_path: str = ""
    source_type: str = ""  # "html", "pdf", "text", "screenshot"
    parsed_at: datetime | None = None

    def formatted_job_information(self) -> str:
        """
        Formats the job information as a markdown string.
        """
        logger.debug(f"Formatting job information for job: {self.role} at {self.company}")

        skills_text = ", ".join(self.required_skills) if self.required_skills else "Not specified"

        job_information = f"""
        # Job Description
        ## Job Information
        - Position: {self.role}
        - At: {self.company}
        - Location: {self.location}
        - Employment Type: {self.employment_type or "Not specified"}
        - Experience Level: {self.experience_level or "Not specified"}
        - Salary Range: {self.salary_range or "Not specified"}
        - Required Skills: {skills_text}
        - Recruiter Profile: {self.recruiter_link or "Not available"}
        - Recruiter Email: {self.recruiter_email or "Not available"}

        ## Description
        {self.description or "No description provided."}
        """
        formatted_information = job_information.strip()
        logger.debug(f"Formatted job information: {formatted_information}")
        return formatted_information
