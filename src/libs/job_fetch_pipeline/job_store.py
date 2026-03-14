"""Persistent storage for parsed job postings backed by SQLite."""

import hashlib
import json
import shutil
from pathlib import Path

from loguru import logger
from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from src.job import Job

Base = declarative_base()

# Extension mapping keyed by source_type
_EXT_MAP: dict[str, str] = {
    "html": ".html",
    "pdf": ".pdf",
    "text": ".txt",
    "screenshot": ".png",
}


class JobRecord(Base):
    """SQLAlchemy model mapping to the ``jobs`` table."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Core fields (mirroring Job)
    role = Column(Text, default="")
    company = Column(Text, default="")
    location = Column(Text, default="")
    link = Column(String(2048), unique=True, nullable=False, index=True)
    apply_method = Column(Text, default="")
    description = Column(Text, default="")
    summarize_job_description = Column(Text, default="")
    recruiter_link = Column(Text, default="")
    resume_path = Column(Text, default="")
    cover_letter_path = Column(Text, default="")

    # New structured fields
    salary_range = Column(Text, default="")
    employment_type = Column(Text, default="")
    experience_level = Column(Text, default="")
    required_skills = Column(Text, default="[]")  # JSON-serialised list
    recruiter_email = Column(Text, default="")

    # Source / persistence metadata
    raw_content_path = Column(Text, default="")
    source_type = Column(String(32), default="")
    parsed_at = Column(DateTime, nullable=True)

    # ------------------------------------------------------------------

    def to_job(self) -> Job:
        """Convert a DB row back to a ``Job`` domain object."""
        return Job(
            role=self.role or "",
            company=self.company or "",
            location=self.location or "",
            link=self.link or "",
            apply_method=self.apply_method or "",
            description=self.description or "",
            summarize_job_description=self.summarize_job_description or "",
            recruiter_link=self.recruiter_link or "",
            resume_path=self.resume_path or "",
            cover_letter_path=self.cover_letter_path or "",
            salary_range=self.salary_range or "",
            employment_type=self.employment_type or "",
            experience_level=self.experience_level or "",
            required_skills=json.loads(self.required_skills) if self.required_skills else [],
            recruiter_email=self.recruiter_email or "",
            raw_content_path=self.raw_content_path or "",
            source_type=self.source_type or "",
            parsed_at=self.parsed_at,
        )

    @classmethod
    def from_job(cls, job: Job) -> "JobRecord":
        """Create a ``JobRecord`` from a ``Job`` domain object."""
        return cls(
            role=job.role,
            company=job.company,
            location=job.location,
            link=job.link,
            apply_method=job.apply_method,
            description=job.description,
            summarize_job_description=job.summarize_job_description,
            recruiter_link=job.recruiter_link,
            resume_path=job.resume_path,
            cover_letter_path=job.cover_letter_path,
            salary_range=job.salary_range,
            employment_type=job.employment_type,
            experience_level=job.experience_level,
            required_skills=json.dumps(job.required_skills),
            recruiter_email=job.recruiter_email,
            raw_content_path=job.raw_content_path,
            source_type=job.source_type,
            parsed_at=job.parsed_at,
        )


class JobStore:
    """CRUD interface over the SQLite ``jobs`` database.

    Args:
        db_path: Filesystem path for the SQLite database file.
                 Use ``\":memory:\"`` for an in-memory DB (useful for tests).
        assets_dir: Directory where raw source files are saved on disk.
    """

    def __init__(
        self,
        db_path: Path | str = Path("data_folder/jobs.db"),
        assets_dir: Path | str = Path("data_folder/jobs_assets"),
    ) -> None:
        self.assets_dir = Path(assets_dir)
        self.assets_dir.mkdir(parents=True, exist_ok=True)

        db_url = "sqlite:///:memory:" if str(db_path) == ":memory:" else f"sqlite:///{db_path}"
        self._engine = create_engine(db_url, echo=False)
        Base.metadata.create_all(self._engine)
        self._SessionFactory = sessionmaker(bind=self._engine)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    def get_by_url(self, url: str) -> Job | None:
        """Return a cached ``Job`` for *url*, or ``None`` if not found."""
        with self._session() as session:
            record = session.query(JobRecord).filter_by(link=url).first()
            if record:
                logger.debug(f"Cache hit for job URL: {url}")
                return record.to_job()
            return None

    def save(
        self,
        job: Job,
        raw_content: bytes | str | None = None,
        source_type: str = "",
    ) -> None:
        """Upsert a ``Job``.  Optionally persist the raw source file to disk.

        Args:
            job: The parsed job object to save.
            raw_content: The original content (HTML string, PDF bytes, image
                         bytes, etc.).  When provided the content is written
                         to ``assets_dir`` and the path stored on *job*.
            source_type: One of ``html``, ``pdf``, ``text``, ``screenshot``.
        """
        if raw_content is not None:
            saved_path = self._save_asset(raw_content, source_type, job.link)
            job.raw_content_path = str(saved_path)
            job.source_type = source_type

        with self._session() as session:
            existing = session.query(JobRecord).filter_by(link=job.link).first()
            if existing:
                # Update every column from the new job
                for col in JobRecord.__table__.columns:
                    if col.name == "id":
                        continue
                    value = getattr(JobRecord.from_job(job), col.name)
                    setattr(existing, col.name, value)
                logger.debug(f"Updated existing job record: {job.link}")
            else:
                session.add(JobRecord.from_job(job))
                logger.debug(f"Inserted new job record: {job.link}")
            session.commit()

    def list_all(self) -> list[Job]:
        """Return every stored ``Job``."""
        with self._session() as session:
            return [r.to_job() for r in session.query(JobRecord).all()]

    def delete_by_url(self, url: str) -> None:
        """Remove the record with the given *url* (``link``)."""
        with self._session() as session:
            record = session.query(JobRecord).filter_by(link=url).first()
            if record:
                session.delete(record)
                session.commit()
                logger.debug(f"Deleted job record: {url}")

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _session(self) -> Session:
        return self._SessionFactory()

    def _save_asset(self, raw_content: bytes | str, source_type: str, link: str) -> Path:
        """Write *raw_content* to ``assets_dir`` and return the saved path.

        The filename is derived from the MD5 hash of *link* to ensure
        deterministic, collision-free storage.
        """
        ext = _EXT_MAP.get(source_type, ".bin")
        name_hash = hashlib.md5(link.encode()).hexdigest()[:16]
        dest = self.assets_dir / f"{name_hash}{ext}"

        if isinstance(raw_content, str):
            dest.write_text(raw_content, encoding="utf-8")
        elif isinstance(raw_content, (bytes | bytearray)):
            dest.write_bytes(raw_content)
        elif isinstance(raw_content, Path):
            # If given a path, copy the file
            shutil.copy2(raw_content, dest)
        else:
            raise TypeError(f"Unsupported raw_content type: {type(raw_content)}")

        logger.debug(f"Saved raw content to: {dest}")
        return dest
