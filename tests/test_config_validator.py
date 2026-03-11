"""Tests for ConfigValidator Pydantic-based validation."""

from pathlib import Path

import pytest
import yaml

from src.app_config import (
    ConfigError,
    SecretsConfig,
    WorkPreferencesConfig,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def write_yaml(tmp_path: Path, name: str, data: dict) -> Path:
    """Write a dict as a YAML file and return its path."""
    p = tmp_path / name
    p.write_text(yaml.dump(data))
    return p


def _base_preferences() -> dict:
    """Return a complete, valid work-preferences dict."""
    return {
        "remote": True,
        "hybrid": True,
        "onsite": False,
        "apply_once_at_company": False,
        "experience_level": {
            "internship": False,
            "entry": True,
            "associate": True,
            "mid_senior_level": True,
            "director": False,
            "executive": False,
        },
        "job_types": {
            "full_time": True,
            "contract": False,
            "part_time": False,
            "temporary": False,
            "internship": False,
            "other": False,
            "volunteer": False,
        },
        "date": {
            "all_time": False,
            "month": False,
            "week": True,
            "past_day": False,
        },
        "positions": ["Software Engineer"],
        "locations": ["Germany"],
        "distance": 25,
        "company_blacklist": ["ExampleCorp"],
        "title_blacklist": [],
        "location_blacklist": [],
    }


# ---------------------------------------------------------------------------
# TestLoadYaml
# ---------------------------------------------------------------------------


class TestLoadYaml:
    def test_load_valid_yaml_via_from_yaml(self, tmp_path):
        p = write_yaml(tmp_path, "cfg.yaml", {"llm_api_key": "sk-test"})
        model = SecretsConfig.from_yaml(p)
        assert model.llm_api_key == "sk-test"

    def test_missing_file_raises_config_error(self, tmp_path):
        with pytest.raises(ConfigError, match="not found"):
            WorkPreferencesConfig.from_yaml(tmp_path / "nonexistent.yaml")


# ---------------------------------------------------------------------------
# TestWorkPreferencesConfig (model unit tests)
# ---------------------------------------------------------------------------


class TestWorkPreferencesConfig:
    def test_valid_config_parses(self):
        model = WorkPreferencesConfig(**_base_preferences())
        assert model.remote is True
        assert model.distance == 25
        assert model.date.past_day is False
        assert model.date.week is True
        assert model.experience_level.entry is True
        assert model.job_types.full_time is True

    def test_blacklists_default_to_empty_list(self):
        data = _base_preferences()
        del data["company_blacklist"]
        del data["title_blacklist"]
        del data["location_blacklist"]
        model = WorkPreferencesConfig(**data)
        assert model.company_blacklist == []
        assert model.title_blacklist == []
        assert model.location_blacklist == []

    def test_none_blacklists_coerced_to_empty_list(self):
        data = _base_preferences()
        data["company_blacklist"] = None
        data["title_blacklist"] = None
        data["location_blacklist"] = None
        model = WorkPreferencesConfig(**data)
        assert model.company_blacklist == []

    def test_invalid_distance_raises(self):
        from pydantic import ValidationError

        data = _base_preferences()
        data["distance"] = 7
        with pytest.raises(ValidationError, match="Invalid distance"):
            WorkPreferencesConfig(**data)

    def test_extra_keys_ignored(self):
        data = _base_preferences()
        data["unknown_future_key"] = "ignored"
        model = WorkPreferencesConfig(**data)
        assert not hasattr(model, "unknown_future_key")


# ---------------------------------------------------------------------------
# TestValidateConfig (file-based)
# ---------------------------------------------------------------------------


class TestWorkPreferencesConfigFromYaml:
    def test_valid_file_returns_model(self, tmp_path, valid_work_preferences_yaml):
        p = tmp_path / "work_preferences.yaml"
        p.write_text(valid_work_preferences_yaml)
        model = WorkPreferencesConfig.from_yaml(p)
        assert isinstance(model, WorkPreferencesConfig)
        assert model.positions == ["Software Engineer"]
        assert model.date.week is True

    def test_missing_required_key_raises_config_error(self, tmp_path):
        data = _base_preferences()
        del data["remote"]
        p = write_yaml(tmp_path, "cfg.yaml", data)
        with pytest.raises(ConfigError):
            WorkPreferencesConfig.from_yaml(p)

    def test_invalid_distance_raises_config_error(self, tmp_path):
        data = _base_preferences()
        data["distance"] = 999
        p = write_yaml(tmp_path, "cfg.yaml", data)
        with pytest.raises(ConfigError, match="Invalid distance"):
            WorkPreferencesConfig.from_yaml(p)

    def test_missing_experience_level_field_raises_config_error(self, tmp_path):
        data = _base_preferences()
        del data["experience_level"]["entry"]
        p = write_yaml(tmp_path, "cfg.yaml", data)
        with pytest.raises(ConfigError):
            WorkPreferencesConfig.from_yaml(p)

    def test_missing_file_raises_config_error(self, tmp_path):
        with pytest.raises(ConfigError, match="not found"):
            WorkPreferencesConfig.from_yaml(tmp_path / "missing.yaml")

    def test_model_dump_contains_expected_keys(self, tmp_path, valid_work_preferences_yaml):
        p = tmp_path / "work_preferences.yaml"
        p.write_text(valid_work_preferences_yaml)
        result = WorkPreferencesConfig.from_yaml(p).model_dump()
        assert isinstance(result, dict)
        for key in ("remote", "hybrid", "onsite", "distance", "positions", "locations"):
            assert key in result


# ---------------------------------------------------------------------------
# TestSecretsConfig (model unit tests)
# ---------------------------------------------------------------------------


class TestSecretsConfig:
    def test_valid_key(self):
        model = SecretsConfig(llm_api_key="sk-abc123")
        assert model.llm_api_key == "sk-abc123"

    def test_empty_key_raises(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="cannot be empty"):
            SecretsConfig(llm_api_key="")

    def test_whitespace_only_key_raises(self):
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="cannot be empty"):
            SecretsConfig(llm_api_key="   ")


# ---------------------------------------------------------------------------
# TestValidateSecrets (file-based)
# ---------------------------------------------------------------------------


class TestSecretsConfigFromYaml:
    def test_valid_secrets_returns_model(self, tmp_path):
        p = write_yaml(tmp_path, "secrets.yaml", {"llm_api_key": "sk-test"})
        secrets = SecretsConfig.from_yaml(p)
        assert secrets.llm_api_key == "sk-test"

    def test_missing_key_raises_config_error(self, tmp_path):
        p = write_yaml(tmp_path, "secrets.yaml", {"other_key": "value"})
        with pytest.raises(ConfigError):
            SecretsConfig.from_yaml(p)

    def test_empty_key_raises_config_error(self, tmp_path):
        p = write_yaml(tmp_path, "secrets.yaml", {"llm_api_key": ""})
        with pytest.raises(ConfigError, match="cannot be empty"):
            SecretsConfig.from_yaml(p)

    def test_missing_file_raises_config_error(self, tmp_path):
        with pytest.raises(ConfigError, match="not found"):
            SecretsConfig.from_yaml(tmp_path / "missing.yaml")
