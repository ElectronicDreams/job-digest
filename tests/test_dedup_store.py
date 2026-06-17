from datetime import datetime, timezone

from jobdigest.core.dedup import make_dedup_key
from jobdigest.core.store import SeenJobsStore
from jobdigest.models import Job

_BUCKET = 7 * 86400


def _job(**kwargs) -> Job:
    defaults = dict(
        source="test",
        id="1",
        title="Senior Developer",
        company="Acme Corp",
        location="remote",
        is_remote=True,
        url="https://example.com/jobs/1",
    )
    return Job(**{**defaults, **kwargs})


# --- make_dedup_key ---


def test_key_uses_company_title_bucket():
    posted = datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc)
    key = make_dedup_key(_job(posted_date=posted))
    bucket = int(posted.timestamp()) // _BUCKET
    assert key == f"acme corp|senior developer|{bucket}"


def test_key_is_lowercase():
    posted = datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc)
    key = make_dedup_key(  # noqa: E501
        _job(title="SENIOR DEVELOPER", company="ACME CORP", posted_date=posted)
    )
    assert key == key.lower()


def test_key_no_posted_date_uses_today_bucket():
    key = make_dedup_key(_job(posted_date=None))
    today_bucket = int(datetime.now(timezone.utc).timestamp()) // _BUCKET
    assert key.endswith(f"|{today_bucket}")


def test_key_same_job_adjacent_7day_buckets_differ():
    # Two identical company+title but one week apart → different bucket → distinct keys
    week1 = datetime(2024, 3, 4, 0, 0, 0, tzinfo=timezone.utc)
    week2 = datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc)
    key1 = make_dedup_key(_job(posted_date=week1))
    key2 = make_dedup_key(_job(posted_date=week2))
    assert key1 != key2


def test_key_same_job_same_bucket_matches():
    # Two postings of the same job on different days within the same 7-day bucket
    day1 = datetime(2024, 3, 11, 0, 0, 0, tzinfo=timezone.utc)
    day2 = datetime(2024, 3, 13, 12, 0, 0, tzinfo=timezone.utc)
    bucket1 = int(day1.timestamp()) // _BUCKET
    bucket2 = int(day2.timestamp()) // _BUCKET
    # only assert equality if they land in the same bucket
    if bucket1 == bucket2:
        assert make_dedup_key(_job(posted_date=day1)) == make_dedup_key(  # noqa: E501
            _job(posted_date=day2)
        )


# --- SeenJobsStore ---


def test_fresh_key_is_new(tmp_path):
    store = SeenJobsStore(tmp_path / "seen.db")
    assert store.is_new("acme corp|senior developer|100") is True
    store.close()


def test_key_after_mark_seen_is_not_new(tmp_path):
    store = SeenJobsStore(tmp_path / "seen.db")
    key = "acme corp|senior developer|100"
    store.mark_seen(key)
    assert store.is_new(key) is False
    store.close()


def test_double_mark_seen_no_error(tmp_path):
    store = SeenJobsStore(tmp_path / "seen.db")
    key = "acme corp|senior developer|100"
    store.mark_seen(key)
    store.mark_seen(key)  # should not raise
    assert store.is_new(key) is False
    store.close()


def test_different_keys_independent(tmp_path):
    store = SeenJobsStore(tmp_path / "seen.db")
    store.mark_seen("key-a")
    assert store.is_new("key-b") is True
    store.close()


def test_store_persists_across_instances(tmp_path):
    db = tmp_path / "seen.db"
    store = SeenJobsStore(db)
    store.mark_seen("persistent-key")
    store.close()

    store2 = SeenJobsStore(db)
    assert store2.is_new("persistent-key") is False
    store2.close()
