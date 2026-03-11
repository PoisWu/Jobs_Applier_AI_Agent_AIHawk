"""Pydantic model for parsing and validating a YAML-based job application profile."""

import yaml
from pydantic import BaseModel

from src.logging import logger
from src.resume_schemas.common import (
    Availability,
    LegalAuthorization,
    SalaryExpectations,
    SelfIdentification,
    WorkPreferences,
)


class JobApplicationProfile(BaseModel):
    self_identification: SelfIdentification
    legal_authorization: LegalAuthorization
    work_preferences: WorkPreferences
    availability: Availability
    salary_expectations: SalaryExpectations

    def __init__(self, yaml_str: str):
        logger.debug("Initializing JobApplicationProfile with provided YAML string")
        try:
            data = yaml.safe_load(yaml_str)
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {e}")
            raise ValueError("Error parsing YAML file.") from e

        if not isinstance(data, dict):
            raise TypeError(f"YAML data must be a dictionary, received: {type(data)}")

        try:
            super().__init__(**data)
        except Exception as e:
            logger.error(f"Validation error in JobApplicationProfile: {e}")
            raise

        logger.debug("JobApplicationProfile initialization completed successfully.")

    def __str__(self) -> str:
        sections = [
            ("Self Identification", self.self_identification),
            ("Legal Authorization", self.legal_authorization),
            ("Work Preferences", self.work_preferences),
        ]
        parts = [f"{title}:\n" + "\n".join(f"{k}: {v}" for k, v in obj.model_dump().items()) for title, obj in sections]
        parts.append(f"Availability: {self.availability.notice_period}")
        parts.append(f"Salary Expectations: {self.salary_expectations.salary_range_usd}")
        return "\n\n".join(parts)
