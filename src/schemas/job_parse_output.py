"""Pydantic schema for the LLM-structured job-parsing output.

This is intentionally separate from :class:`src.job.Job` so that only the
fields the LLM is expected to populate are included in the JSON schema sent
to ``ChatOpenAI.with_structured_output()``.  The broader ``Job`` model
contains pipeline-level metadata (``link``, ``resume_path``, ``source_type``,
…) that must not appear in the LLM's output schema.
"""

from pydantic import BaseModel, Field


class JobParseOutput(BaseModel):
    """Structured output returned by the LLM when parsing a job posting."""

    role: str = Field(default="", description="Job title / role name.")
    company: str = Field(default="", description="Company name.")
    location: str = Field(default="", description="Job location (city, country, or 'Remote').")
    description: str = Field(default="", description="Full job description text.")
    salary_range: str = Field(default="", description="Salary range if mentioned, e.g. '$120k–$160k'.")
    employment_type: str = Field(
        default="",
        description="Employment type, e.g. 'full-time', 'part-time', 'contract'.",
    )
    experience_level: str = Field(
        default="",
        description="Required experience level, e.g. 'junior', 'mid-level', 'senior'.",
    )
    required_skills: list[str] = Field(
        default_factory=list,
        description="List of required or preferred technical skills.",
    )
    recruiter_email: str = Field(
        default="",
        description="Recruiter or HR contact e-mail address if present.",
    )
