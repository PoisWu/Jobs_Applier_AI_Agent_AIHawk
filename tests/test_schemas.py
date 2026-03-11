"""Tests for Resume and JobApplicationProfile schema parsing."""

import pytest

from src.resume_schemas.job_application_profile import JobApplicationProfile
from src.resume_schemas.resume import Resume


class TestResume:
    def test_parse_valid_yaml(self, sample_resume_yaml: str):
        resume = Resume(sample_resume_yaml)
        assert resume.personal_information is not None
        assert resume.personal_information.name == "Jane"
        assert resume.personal_information.surname == "Doe"
        assert resume.personal_information.email == "jane@example.com"

    def test_education_details(self, sample_resume_yaml: str):
        resume = Resume(sample_resume_yaml)
        assert resume.education_details is not None
        assert len(resume.education_details) == 1
        assert resume.education_details[0].institution == "MIT"

    def test_experience_details(self, sample_resume_yaml: str):
        resume = Resume(sample_resume_yaml)
        assert resume.experience_details is not None
        assert len(resume.experience_details) == 1
        assert resume.experience_details[0].company == "Acme Corp"

    def test_projects(self, sample_resume_yaml: str):
        resume = Resume(sample_resume_yaml)
        assert resume.projects is not None
        assert len(resume.projects) == 1
        assert resume.projects[0].name == "OpenWidget"

    def test_languages(self, sample_resume_yaml: str):
        resume = Resume(sample_resume_yaml)
        assert resume.languages is not None
        assert len(resume.languages) == 2

    def test_interests(self, sample_resume_yaml: str):
        resume = Resume(sample_resume_yaml)
        assert resume.interests == ["Open source", "Machine learning"]

    def test_invalid_yaml_raises(self):
        with pytest.raises(ValueError, match="Error parsing YAML"):
            Resume("{{invalid yaml:: ]]")

    def test_normalize_exam_format_dict(self):
        exam = {"Math": "A", "Physics": "B"}
        result = Resume.normalize_exam_format(exam)
        assert result == [{"Math": "A"}, {"Physics": "B"}]

    def test_normalize_exam_format_list(self):
        exam = [{"Math": "A"}]
        result = Resume.normalize_exam_format(exam)
        assert result == [{"Math": "A"}]


class TestJobApplicationProfile:
    def test_parse_valid_yaml(self, sample_work_preferences_yaml: str):
        profile = JobApplicationProfile(sample_work_preferences_yaml)
        assert profile.self_identification.gender == "Male"
        assert profile.legal_authorization.us_work_authorization == "Yes"
        assert profile.work_preferences.remote_work == "Yes"
        assert profile.availability.notice_period == "2 weeks"
        assert profile.salary_expectations.salary_range_usd == "120000 - 160000"

    def test_str_representation(self, sample_work_preferences_yaml: str):
        profile = JobApplicationProfile(sample_work_preferences_yaml)
        text = str(profile)
        assert "Self Identification" in text
        assert "Legal Authorization" in text
        assert "Work Preferences" in text
        assert "2 weeks" in text
        assert "120000 - 160000" in text

    def test_invalid_yaml_raises(self):
        with pytest.raises(ValueError, match="Error parsing YAML"):
            JobApplicationProfile("{{invalid yaml:: ]]")

    def test_non_dict_yaml_raises(self):
        with pytest.raises(TypeError, match="must be a dictionary"):
            JobApplicationProfile("- just a list item")

    def test_canada_uk_authorization(self, sample_work_preferences_yaml: str):
        profile = JobApplicationProfile(sample_work_preferences_yaml)
        assert profile.legal_authorization.canada_work_authorization == "No"
        assert profile.legal_authorization.uk_work_authorization == "No"
        assert profile.legal_authorization.requires_canada_visa == "Yes"
        assert profile.legal_authorization.requires_uk_visa == "Yes"
