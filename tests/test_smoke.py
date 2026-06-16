from jobdigest.models import Job, Profile


def test_smoke():
    assert Job is not None
    assert Profile is not None
