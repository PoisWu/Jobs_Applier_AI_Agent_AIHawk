"""Application configuration: validation models and runtime app config."""

from pathlib import Path
from typing import Annotated, ClassVar

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from src.schemas.resume import Resume
from src.utils.constants import PLAIN_TEXT_RESUME_YAML, SECRETS_YAML, WORK_PREFERENCES_YAML


class ConfigError(Exception):
    """Custom exception for configuration-related errors."""

    pass


# ---------------------------------------------------------------------------
# Private YAML loader
# ---------------------------------------------------------------------------


def _load_yaml(yaml_path: Path) -> dict:
    """Load and parse a YAML file, raising ConfigError on failure."""
    try:
        with open(yaml_path) as stream:
            return yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        raise ConfigError(f"Error reading YAML file {yaml_path}: {exc}")
    except FileNotFoundError:
        raise ConfigError(f"YAML file not found: {yaml_path}")


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class ExperienceLevelConfig(BaseModel):
    """Boolean flags for each LinkedIn experience level."""

    model_config = ConfigDict(extra="ignore")

    internship: bool
    entry: bool
    associate: bool
    mid_senior_level: bool
    director: bool
    executive: bool


class JobTypesConfig(BaseModel):
    """Boolean flags for each LinkedIn job type."""

    model_config = ConfigDict(extra="ignore")

    full_time: bool
    contract: bool
    part_time: bool
    temporary: bool
    internship: bool
    other: bool
    volunteer: bool


class DateConfig(BaseModel):
    """Boolean flags for LinkedIn date-posted filters."""

    model_config = ConfigDict(extra="ignore")

    all_time: bool
    month: bool
    week: bool
    past_day: bool


# ---------------------------------------------------------------------------
# Top-level config models
# ---------------------------------------------------------------------------

_APPROVED_DISTANCES = {0, 5, 10, 25, 50, 100}


class WorkPreferencesConfig(BaseModel):
    """Validated representation of work_preferences.yaml."""

    model_config = ConfigDict(extra="ignore")

    remote: bool
    hybrid: bool
    onsite: bool
    apply_once_at_company: bool

    experience_level: ExperienceLevelConfig
    job_types: JobTypesConfig
    date: DateConfig

    positions: list[str]
    locations: list[str]
    distance: Annotated[int, Field(ge=0)]

    company_blacklist: list[str] = Field(default_factory=list)
    title_blacklist: list[str] = Field(default_factory=list)
    location_blacklist: list[str] = Field(default_factory=list)

    @field_validator("distance")
    @classmethod
    def distance_must_be_approved(cls, v: int) -> int:
        if v not in _APPROVED_DISTANCES:
            raise ValueError(f"Invalid distance '{v}'. Must be one of: {sorted(_APPROVED_DISTANCES)}")
        return v

    @field_validator("company_blacklist", "title_blacklist", "location_blacklist", mode="before")
    @classmethod
    def coerce_none_to_empty_list(cls, v):
        return v if v is not None else []

    @classmethod
    def from_yaml(cls, path: Path) -> "WorkPreferencesConfig":
        """Load and validate work preferences from a YAML file."""
        data = _load_yaml(path)
        try:
            return cls(**data)
        except ValidationError as exc:
            raise ConfigError(f"Configuration error in {path}:\n{exc}") from exc


class SecretsConfig(BaseModel):
    """Validated representation of secrets.yaml."""

    model_config = ConfigDict(extra="ignore")

    llm_api_key: str

    @field_validator("llm_api_key")
    @classmethod
    def api_key_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("'llm_api_key' cannot be empty.")
        return v

    @classmethod
    def from_yaml(cls, path: Path) -> "SecretsConfig":
        """Load and validate secrets from a YAML file."""
        data = _load_yaml(path)
        try:
            return cls(**data)
        except ValidationError as exc:
            raise ConfigError(f"Secrets error in {path}:\n{exc}") from exc


# ---------------------------------------------------------------------------
# Runtime application config
# ---------------------------------------------------------------------------


class AppConfig(BaseModel):
    """Aggregates validated config models and runtime-resolved values."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    REQUIRED_FILES: ClassVar[list[str]] = [SECRETS_YAML, WORK_PREFERENCES_YAML, PLAIN_TEXT_RESUME_YAML]

    preferences: WorkPreferencesConfig
    secrets: SecretsConfig
    resume_object: Resume
    output_dir: Path

    @classmethod
    def from_data_folder(cls, data_folder: Path) -> "AppConfig":
        """Validate data folder, load configs, and return a fully initialised AppConfig."""
        if not data_folder.is_dir():
            raise FileNotFoundError(f"Data folder not found: {data_folder}")

        missing = [f for f in cls.REQUIRED_FILES if not (data_folder / f).exists()]
        if missing:
            raise FileNotFoundError(f"Missing files in data folder: {', '.join(missing)}")

        output_folder = data_folder / "output"
        output_folder.mkdir(exist_ok=True)

        resume_path = data_folder / PLAIN_TEXT_RESUME_YAML
        with open(resume_path, encoding="utf-8") as f:
            resume_object = Resume(f.read())

        return cls(
            preferences=WorkPreferencesConfig.from_yaml(data_folder / WORK_PREFERENCES_YAML),
            secrets=SecretsConfig.from_yaml(data_folder / SECRETS_YAML),
            resume_object=resume_object,
            output_dir=output_folder,
        )
