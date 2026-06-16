from datetime import datetime, timezone

from jobdigest.models import Job, Profile


def test_job_required_fields():
    job = Job(
        source="test",
        id="123",
        title="Senior Developer",
        company="Acme",
        location="Toronto, ON",
        is_remote=False,
        url="https://example.com/job/123",
    )
    assert job.source == "test"
    assert job.salary is None
    assert job.employment_type is None
    assert job.posted_date is None
    assert job.description is None


def test_job_all_optional_fields():
    posted = datetime(2024, 1, 15, tzinfo=timezone.utc)
    job = Job(
        source="himalayas",
        id="abc",
        title="Frontend Engineer",
        company="Startup",
        location="Remote",
        is_remote=True,
        url="https://himalayas.app/job/abc",
        salary={"min": 80_000, "max": 120_000, "currency": "CAD"},
        employment_type="permanent",
        posted_date=posted,
        description="We are looking for a frontend engineer.",
    )
    assert job.salary == {"min": 80_000, "max": 120_000, "currency": "CAD"}
    assert job.posted_date == posted
    assert job.is_remote is True


def test_profile_empty_defaults():
    profile = Profile()
    assert profile.title_variants == []
    assert profile.skills == []
    assert profile.salary_floor is None
    assert profile.location == ""
    assert profile.employment_types == []


def test_profile_all_fields():
    profile = Profile(
        title_variants=["Senior Frontend Developer", "Frontend Engineer"],
        skills=["Angular", "TypeScript"],
        seniority_terms=["senior", "lead"],
        experience_terms=["5+ years"],
        location="Toronto, ON, Canada",
        acceptable_locations=["Toronto", "Remote"],
        work_types=["remote", "hybrid"],
        work_authorization="Authorized to work in Canada",
        salary_floor={"amount": 100_000, "currency": "CAD"},
        employment_types=["permanent", "contract"],
    )
    assert profile.location == "Toronto, ON, Canada"
    assert len(profile.skills) == 2
    assert profile.salary_floor == {"amount": 100_000, "currency": "CAD"}


def test_profile_lists_are_independent():
    """Each Profile instance must get its own list, not a shared default."""
    a = Profile()
    b = Profile()
    a.skills.append("Python")
    assert b.skills == []
