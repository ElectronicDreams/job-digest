from jobdigest.adapters.himalayas import HimalayasSource
from jobdigest.config import load_config, load_profile
from jobdigest.core.gates import apply_gates

config = load_config()
profile = load_profile()
jobs = HimalayasSource(config).fetch()
print(f"Fetched: {len(jobs)}")
if not profile:
    print("No profile loaded — skipping gates check")
    exit(0)
gated = apply_gates(jobs, profile, config)
print(f"After gates: {len(gated)}")
if len(jobs) and not gated:
    print(
        "Title gate is filtering everything — check profile.json "
        "title_variants/seniority_terms/skills"
    )
