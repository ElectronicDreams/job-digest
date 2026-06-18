from jobdigest.adapters.himalayas import HimalayasSource
from jobdigest.config import load_config

config = load_config()
jobs = HimalayasSource(config).fetch()
print(f"Fetched {len(jobs)} jobs")
for j in jobs:
    print(f"  {j.title} @ {j.company} ({j.location})")
