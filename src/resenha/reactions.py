"""SQLite-backed reaction tracking for Discord briefing embeds."""

import sqlite3
from pathlib import Path


class ReactionTracker:
    """Tracks Discord reactions on briefing embeds in a SQLite table."""

    def __init__(self, db_path: str | Path) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                briefing_run_id TEXT NOT NULL,
                message_id INTEGER NOT NULL,
                embed_index INTEGER NOT NULL DEFAULT 0,
                asset_ticker TEXT NOT NULL DEFAULT '',
                reaction TEXT NOT NULL,
                user_id INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
        self._conn.commit()

    def track(
        self,
        briefing_run_id: str,
        message_id: int,
        embed_index: int,
        asset_ticker: str,
        reaction: str,
        user_id: int,
    ) -> None:
        """Insert a reaction event into the reactions table."""
        self._conn.execute(
            """
            INSERT INTO reactions (briefing_run_id, message_id, embed_index, asset_ticker, reaction, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (briefing_run_id, message_id, embed_index, asset_ticker, reaction, user_id),
        )
        self._conn.commit()

    def get_stats(self, days: int = 7) -> dict[str, dict[str, int]]:
        """Return reaction counts grouped by asset_ticker and reaction for the last N days.

        Returns:
            {ticker: {"up": N, "down": N, "love": N, "fire": N}}
        """
        cursor = self._conn.execute(
            """
            SELECT asset_ticker, reaction, COUNT(*)
            FROM reactions
            WHERE created_at >= datetime('now', ?)
            GROUP BY asset_ticker, reaction
            """,
            (f"-{days} days",),
        )

        stats: dict[str, dict[str, int]] = {}
        for ticker, reaction, count in cursor.fetchall():
            ticker = ticker if ticker else "__unknown__"
            if ticker not in stats:
                stats[ticker] = {}
            stats[ticker][reaction] = count

        return stats

    def get_source_stats(self, days: int = 7) -> dict[str, dict[str, int]]:
        """Return reaction counts grouped by source (asset_ticker) for the last N days.

        Currently sources are identical to tickers. Will be refined in B-016.
        """
        return self.get_stats(days=days)
