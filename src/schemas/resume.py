"""Pydantic models for parsing and validating a YAML-based resume."""

import yaml
from pydantic import BaseModel, EmailStr, Field, HttpUrl


class PersonalInformation(BaseModel):
    name: str | None = None
    surname: str | None = None
    date_of_birth: str | None = None
    country: str | None = None
    city: str | None = None
    address: str | None = None
    zip_code: str | None = Field(None, min_length=5, max_length=10)
    phone_prefix: str | None = None
    phone: str | None = None
    email: EmailStr | None = None
    github: HttpUrl | None = None
    linkedin: HttpUrl | None = None


class EducationDetails(BaseModel):
    education_level: str | None = None
    institution: str | None = None
    field_of_study: str | None = None
    final_evaluation_grade: str | None = None
    start_date: str | None = None
    year_of_completion: int | None = None
    exam: list[dict[str, str]] | dict[str, str] | None = None


class ExperienceDetails(BaseModel):
    position: str | None = None
    company: str | None = None
    employment_period: str | None = None
    location: str | None = None
    industry: str | None = None
    key_responsibilities: list[dict[str, str]] | None = None
    skills_acquired: list[str] | None = None


class Project(BaseModel):
    name: str | None = None
    link: HttpUrl | None = None
    date_start: str | None = None
    date_end: str | None = None
    summary: str | None = None
    highlights: list[str] | None = None
    tech_stack: list[str] | None = None


class Achievement(BaseModel):
    name: str | None = None
    description: str | None = None


class Certifications(BaseModel):
    name: str | None = None
    description: str | None = None


class Language(BaseModel):
    language: str | None = None
    proficiency: str | None = None


class Resume(BaseModel):
    personal_information: PersonalInformation | None = None
    education_details: list[EducationDetails] | None = None
    experience_details: list[ExperienceDetails] | None = None
    projects: list[Project] | None = None
    achievements: list[Achievement] | None = None
    certifications: list[Certifications] | None = None
    languages: list[Language] | None = None
    interests: list[str] | None = None

    @staticmethod
    def normalize_exam_format(exam):
        if isinstance(exam, dict):
            return [{k: v} for k, v in exam.items()]
        return exam

    def __init__(self, yaml_str: str):
        try:
            data = yaml.safe_load(yaml_str)

            if "education_details" in data:
                for ed in data["education_details"]:
                    if "exam" in ed:
                        ed["exam"] = Resume.normalize_exam_format(ed["exam"])

            super().__init__(**data)
        except yaml.YAMLError as e:
            raise ValueError("Error parsing YAML file.") from e
        except Exception as e:
            raise ValueError(f"Unexpected error while parsing YAML: {e}") from e
