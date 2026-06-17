import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class SeenJobsStore:
    def __init__(self, db_path: Path) -> None:
        self._conn = sqlite3.connect(db_path)
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS seen_jobs (key TEXT PRIMARY KEY, seen_at TEXT)"
        )
        self._conn.commit()

    def is_new(self, key: str) -> bool:
        row = self._conn.execute(
            "SELECT 1 FROM seen_jobs WHERE key = ?", (key,)
        ).fetchone()
        return row is None

    def mark_seen(self, key: str) -> None:
        seen_at = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT OR IGNORE INTO seen_jobs (key, seen_at) VALUES (?, ?)",
            (key, seen_at),
        )
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
