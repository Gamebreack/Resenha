"""SQLite-backed cache with TTL support."""

import json
import sqlite3
from pathlib import Path


class Cache:
    """Simple SQLite cache for JSON-serializable data."""

    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._ensure_table()

    def _ensure_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                created_at INTEGER NOT NULL
            )
            """
        )
        self._conn.commit()

    def get(self, key: str, ttl_seconds: int) -> dict | None:
        import time

        row = self._conn.execute(
            "SELECT value, created_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
        if row is None:
            return None
        value_str, created_at = row
        now = int(time.time())
        if now - created_at > ttl_seconds:
            return None
        return json.loads(value_str)  # type: ignore[no-any-return]

    def set(self, key: str, value: dict) -> None:
        import time

        value_str = json.dumps(value)
        now = int(time.time())
        self._conn.execute(
            """
            INSERT INTO cache (key, value, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(key) DO UPDATE SET
                value = excluded.value,
                created_at = excluded.created_at
            """,
            (key, value_str, now),
        )
        self._conn.commit()
