"""Shared Pydantic models used by both Resume and JobApplicationProfile."""

from pydantic import BaseModel


class SelfIdentification(BaseModel):
    gender: str | None = None
    pronouns: str | None = None
    veteran: str | None = None
    disability: str | None = None
    ethnicity: str | None = None


class LegalAuthorization(BaseModel):
    eu_work_authorization: str | None = None
    us_work_authorization: str | None = None
    requires_us_visa: str | None = None
    requires_us_sponsorship: str | None = None
    requires_eu_visa: str | None = None
    legally_allowed_to_work_in_eu: str | None = None
    legally_allowed_to_work_in_us: str | None = None
    requires_eu_sponsorship: str | None = None
    # Extended fields (Canada, UK)
    canada_work_authorization: str | None = None
    requires_canada_visa: str | None = None
    legally_allowed_to_work_in_canada: str | None = None
    requires_canada_sponsorship: str | None = None
    uk_work_authorization: str | None = None
    requires_uk_visa: str | None = None
    legally_allowed_to_work_in_uk: str | None = None
    requires_uk_sponsorship: str | None = None


class WorkPreferences(BaseModel):
    remote_work: str | None = None
    in_person_work: str | None = None
    open_to_relocation: str | None = None
    willing_to_complete_assessments: str | None = None
    willing_to_undergo_drug_tests: str | None = None
    willing_to_undergo_background_checks: str | None = None


class Availability(BaseModel):
    notice_period: str | None = None


class SalaryExpectations(BaseModel):
    salary_range_usd: str | None = None
