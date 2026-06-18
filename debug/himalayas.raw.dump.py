import json
from typing import Any

from jobdigest.utils.http import get_json

data: Any = get_json("https://himalayas.app/jobs/api", params={"limit": 2})
print(json.dumps(data["jobs"][0], indent=2))
