from jobdigest.adapters.himalayas import HimalayasSource
from jobdigest.config import load_config, load_profile
from jobdigest.core.gates import (
    _passes_eligibility_gate,
    _passes_metro_gate,
    _passes_title_gate,
)

config = load_config()
profile = load_profile()
if not profile:
    print("No profile loaded — skipping gates check")
    exit(0)
jobs = HimalayasSource(config).fetch()
for j in jobs[:5]:
    m = _passes_metro_gate(j, profile)
    e = _passes_eligibility_gate(j, config.exclusion_phrases)
    t = _passes_title_gate(j, profile)
    print(
        f"{j.title}: metro={m} elig={e} title={t} is_remote={j.is_remote}"
        f" loc={j.location}"
    )
