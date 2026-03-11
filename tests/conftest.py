"""Shared fixtures for the test suite."""

from pathlib import Path

import pytest

# Project root for resolving test data paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_resume_yaml() -> str:
    """Minimal valid YAML for a Resume object."""
    return """\
personal_information:
  name: Jane
  surname: Doe
  date_of_birth: "1990-01-01"
  country: US
  city: San Francisco
  address: "123 Main St"
  zip_code: "94102"
  phone_prefix: "+1"
  phone: "5551234567"
  email: jane@example.com
  github: https://github.com/janedoe
  linkedin: https://linkedin.com/in/janedoe

education_details:
  - education_level: Master
    institution: MIT
    field_of_study: Computer Science
    final_evaluation_grade: "3.9"
    start_date: "2015-09-01"
    year_of_completion: 2017

experience_details:
  - position: Software Engineer
    company: Acme Corp
    employment_period: "2018-01 to 2023-06"
    location: San Francisco, CA
    industry: Technology
    key_responsibilities:
      - responsibility_1: Built distributed systems
    skills_acquired:
      - Python
      - Kubernetes

projects:
  - name: OpenWidget
    description: An open-source widget library
    link: https://github.com/janedoe/openwidget

achievements:
  - name: Hackathon Winner
    description: Won first place at HackSF 2022

certifications:
  - name: AWS Solutions Architect
    description: Associate level certification

languages:
  - language: English
    proficiency: Native
  - language: Spanish
    proficiency: Intermediate

interests:
  - Open source
  - Machine learning
"""


@pytest.fixture
def sample_work_preferences_yaml() -> str:
    """Minimal valid YAML for a JobApplicationProfile."""
    return """\
self_identification:
  gender: Male
  pronouns: He/Him
  veteran: "No"
  disability: "No"
  ethnicity: Asian

legal_authorization:
  eu_work_authorization: "Yes"
  us_work_authorization: "Yes"
  requires_us_visa: "No"
  legally_allowed_to_work_in_us: "Yes"
  requires_us_sponsorship: "No"
  requires_eu_visa: "No"
  legally_allowed_to_work_in_eu: "Yes"
  requires_eu_sponsorship: "No"
  canada_work_authorization: "No"
  requires_canada_visa: "Yes"
  legally_allowed_to_work_in_canada: "No"
  requires_canada_sponsorship: "Yes"
  uk_work_authorization: "No"
  requires_uk_visa: "Yes"
  legally_allowed_to_work_in_uk: "No"
  requires_uk_sponsorship: "Yes"

work_preferences:
  remote_work: "Yes"
  in_person_work: "No"
  open_to_relocation: "Yes"
  willing_to_complete_assessments: "Yes"
  willing_to_undergo_drug_tests: "Yes"
  willing_to_undergo_background_checks: "Yes"

availability:
  notice_period: "2 weeks"

salary_expectations:
  salary_range_usd: "120000 - 160000"
"""


@pytest.fixture
def valid_work_preferences_yaml() -> str:
    """Minimal valid YAML for WorkPreferencesConfig."""
    return """\
remote: true
hybrid: true
onsite: false
apply_once_at_company: false

experience_level:
  internship: false
  entry: true
  associate: true
  mid_senior_level: true
  director: false
  executive: false

job_types:
  full_time: true
  contract: false
  part_time: false
  temporary: false
  internship: false
  other: false
  volunteer: false

date:
  all_time: false
  month: false
  week: true
  past_day: false

positions:
  - Software Engineer

locations:
  - Germany

distance: 25

company_blacklist:
  - ExampleCorp

title_blacklist: []
location_blacklist: []
"""
