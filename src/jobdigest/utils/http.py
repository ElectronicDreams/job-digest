import time

import requests


def get_json(
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    retries: int = 3,
) -> dict | list:
    """GET a URL and return the parsed JSON body.

    Retries on 5xx responses or network timeouts with exponential backoff.
    Raises RuntimeError when all retries are exhausted.
    4xx responses raise requests.HTTPError immediately (no retry).
    """
    session = requests.Session()
    delay = 1.0
    last_exc: Exception | None = None

    for attempt in range(retries):
        try:
            resp = session.get(url, params=params, headers=headers, timeout=10)
            if resp.status_code >= 500:
                last_exc = RuntimeError(f"HTTP {resp.status_code} from {url}")
                if attempt < retries - 1:
                    time.sleep(delay)
                    delay *= 2
                continue
            resp.raise_for_status()
            return resp.json()
        except (requests.Timeout, requests.ConnectionError) as exc:
            last_exc = exc
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2

    raise RuntimeError(
        f"All {retries} retries exhausted for {url}: {last_exc}"
    ) from last_exc
