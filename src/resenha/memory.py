"""SQLite-backed persistence for generated briefing memory."""

import sqlite3
from pathlib import Path


class BriefingMemory:
    """Persist the most recently generated briefing per style."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._ensure_table()

    def _ensure_table(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS past_briefings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                style TEXT NOT NULL,
                briefing_text TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        self._conn.commit()

    def save(self, style: str, text: str) -> None:
        """Insert a new briefing row for the given style."""
        self._conn.execute(
            "INSERT INTO past_briefings (style, briefing_text) VALUES (?, ?)",
            (style, text),
        )
        self._conn.commit()

    def get_last(self, style: str) -> str | None:
        """Return the most recent briefing text for the style, or None."""
        row = self._conn.execute(
            "SELECT briefing_text FROM past_briefings WHERE style = ? ORDER BY id DESC LIMIT 1",
            (style,),
        ).fetchone()
        return row[0] if row else None

    def prune(self, style: str, keep: int = 1) -> None:
        """Delete older rows for the style, keeping only the latest `keep` rows."""
        self._conn.execute(
            """
            DELETE FROM past_briefings
            WHERE style = ? AND id NOT IN (
                SELECT id FROM past_briefings WHERE style = ? ORDER BY id DESC LIMIT ?
            )
            """,
            (style, style, keep),
        )
        self._conn.commit()
