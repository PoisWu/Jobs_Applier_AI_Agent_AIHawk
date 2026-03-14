"""Tests for the SQLite-backed JobStore."""

from pathlib import Path

import pytest

from src.job import Job
from src.libs.job_store import JobStore


@pytest.fixture
def store(tmp_path: Path) -> JobStore:
    """Create a fresh JobStore backed by a temp-directory SQLite file."""
    return JobStore(
        db_path=tmp_path / "test_jobs.db",
        assets_dir=tmp_path / "assets",
    )


@pytest.fixture
def sample_job() -> Job:
    return Job(
        role="Software Engineer",
        company="Acme Corp",
        location="San Francisco, CA",
        link="https://example.com/jobs/123",
        description="Build cool stuff.",
        salary_range="$120k–$160k",
        employment_type="full-time",
        experience_level="mid-level",
        required_skills=["Python", "Kubernetes", "PostgreSQL"],
        recruiter_email="recruiter@acme.com",
        source_type="html",
    )


class TestJobStoreCRUD:
    def test_save_and_get_by_url(self, store: JobStore, sample_job: Job) -> None:
        store.save(sample_job, raw_content="<html>test</html>", source_type="html")
        retrieved = store.get_by_url(sample_job.link)

        assert retrieved is not None
        assert retrieved.role == "Software Engineer"
        assert retrieved.company == "Acme Corp"
        assert retrieved.required_skills == ["Python", "Kubernetes", "PostgreSQL"]
        assert retrieved.salary_range == "$120k–$160k"
        assert retrieved.recruiter_email == "recruiter@acme.com"

    def test_get_by_url_returns_none_for_missing(self, store: JobStore) -> None:
        assert store.get_by_url("https://nonexistent.example.com") is None

    def test_save_upserts_on_same_link(self, store: JobStore, sample_job: Job) -> None:
        store.save(sample_job, raw_content="<html>v1</html>", source_type="html")
        sample_job.role = "Senior Software Engineer"
        store.save(sample_job, raw_content="<html>v2</html>", source_type="html")

        all_jobs = store.list_all()
        assert len(all_jobs) == 1
        assert all_jobs[0].role == "Senior Software Engineer"

    def test_list_all(self, store: JobStore, sample_job: Job) -> None:
        store.save(sample_job)
        second = sample_job.model_copy(update={"link": "https://example.com/jobs/456", "role": "PM"})
        store.save(second)
        assert len(store.list_all()) == 2

    def test_delete_by_url(self, store: JobStore, sample_job: Job) -> None:
        store.save(sample_job)
        store.delete_by_url(sample_job.link)
        assert store.get_by_url(sample_job.link) is None
        assert len(store.list_all()) == 0

    def test_delete_nonexistent_is_noop(self, store: JobStore) -> None:
        store.delete_by_url("https://nope.example.com")  # should not raise


class TestJobStoreAssets:
    def test_html_asset_saved(self, store: JobStore, sample_job: Job, tmp_path: Path) -> None:
        store.save(sample_job, raw_content="<html>body</html>", source_type="html")
        retrieved = store.get_by_url(sample_job.link)
        assert retrieved is not None
        assert retrieved.raw_content_path
        saved = Path(retrieved.raw_content_path)
        assert saved.exists()
        assert saved.read_text(encoding="utf-8") == "<html>body</html>"

    def test_pdf_asset_saved(self, store: JobStore, tmp_path: Path) -> None:
        pdf_bytes = b"%PDF-1.4 fake content"
        job = Job(link="local://test-pdf", source_type="pdf")
        store.save(job, raw_content=pdf_bytes, source_type="pdf")

        retrieved = store.get_by_url("local://test-pdf")
        assert retrieved is not None
        saved = Path(retrieved.raw_content_path)
        assert saved.exists()
        assert saved.read_bytes() == pdf_bytes

    def test_screenshot_asset_saved(self, store: JobStore, tmp_path: Path) -> None:
        fake_png = b"\x89PNG\r\n\x1a\nfake"
        job = Job(link="local://test-screenshot", source_type="screenshot")
        store.save(job, raw_content=fake_png, source_type="screenshot")

        retrieved = store.get_by_url("local://test-screenshot")
        assert retrieved is not None
        saved = Path(retrieved.raw_content_path)
        assert saved.exists()
        assert saved.suffix == ".png"


class TestJobStoreLocalLink:
    """Verify that URL-less jobs (screenshots, PDFs) can use local:// links."""

    def test_local_uuid_link(self, store: JobStore) -> None:
        job = Job(
            role="Designer",
            company="Startup Inc",
            link="local://550e8400-e29b-41d4-a716-446655440000",
            source_type="screenshot",
        )
        store.save(job, raw_content=b"\x89PNGfake", source_type="screenshot")
        retrieved = store.get_by_url(job.link)
        assert retrieved is not None
        assert retrieved.role == "Designer"

    def test_multiple_local_links_are_unique(self, store: JobStore) -> None:
        job1 = Job(link="local://aaa", source_type="pdf")
        job2 = Job(link="local://bbb", source_type="pdf")
        store.save(job1, raw_content=b"pdf1", source_type="pdf")
        store.save(job2, raw_content=b"pdf2", source_type="pdf")
        assert len(store.list_all()) == 2
