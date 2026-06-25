from jobdigest.adapters.adzuna import AdzunaSource
from jobdigest.adapters.himalayas import HimalayasSource
from jobdigest.adapters.jobicy import JobicySource
from jobdigest.adapters.remoteok import RemoteOkSource
from jobdigest.adapters.working_nomads import WorkingNomadsSource

SOURCES: list = [
    HimalayasSource,
    RemoteOkSource,
    JobicySource,
    AdzunaSource,
    WorkingNomadsSource,
]
