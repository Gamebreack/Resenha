"""Tests for resenha.reactions.ReactionTracker."""

import sqlite3
from pathlib import Path

import pytest

from resenha.reactions import ReactionTracker


@pytest.fixture
def tracker(tmp_path):
    db_path = tmp_path / "test_reactions.db"
    return ReactionTracker(db_path=db_path)


class TestReactionTracker:
    """Tests for ReactionTracker SQLite wrapper."""

    def test_schema_created(self, tracker):
        """ReactionTracker creates the reactions table on init."""
        conn = tracker._conn
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reactions'")
        assert cursor.fetchone() is not None

        # Verify columns
        cursor = conn.execute("PRAGMA table_info(reactions)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        assert "id" in columns
        assert "briefing_run_id" in columns
        assert "message_id" in columns
        assert "embed_index" in columns
        assert "asset_ticker" in columns
        assert "reaction" in columns
        assert "user_id" in columns
        assert "created_at" in columns

    def test_track_inserts_row(self, tracker):
        """track() inserts a row into the reactions table."""
        tracker.track(
            briefing_run_id="run-123",
            message_id=456,
            embed_index=0,
            asset_ticker="ITUB4",
            reaction="up",
            user_id=789,
        )

        cursor = tracker._conn.execute(
            "SELECT briefing_run_id, message_id, embed_index, asset_ticker, reaction, user_id FROM reactions"
        )
        rows = cursor.fetchall()
        assert len(rows) == 1
        assert rows[0] == ("run-123", 456, 0, "ITUB4", "up", 789)

    def test_track_multiple_rows(self, tracker):
        """track() can insert multiple rows."""
        tracker.track("run-1", 100, 0, "ITUB4", "up", 1)
        tracker.track("run-1", 100, 0, "ITUB4", "down", 2)
        tracker.track("run-1", 101, 1, "BBDC4", "love", 1)

        cursor = tracker._conn.execute("SELECT COUNT(*) FROM reactions")
        assert cursor.fetchone()[0] == 3

    def test_get_stats_returns_counts(self, tracker):
        """get_stats() returns correct counts grouped by ticker and reaction."""
        # Insert known data
        entries = [
            ("run-1", 100, 0, "ITUB4", "up", 1),
            ("run-1", 100, 0, "ITUB4", "up", 2),
            ("run-1", 100, 0, "ITUB4", "down", 1),
            ("run-1", 101, 1, "BBDC4", "love", 1),
            ("run-1", 101, 1, "BBDC4", "fire", 1),
            ("run-1", 101, 1, "BBDC4", "fire", 2),
        ]
        for entry in entries:
            tracker.track(*entry)

        stats = tracker.get_stats(days=365)
        assert "ITUB4" in stats
        assert stats["ITUB4"]["up"] == 2
        assert stats["ITUB4"]["down"] == 1
        assert stats["ITUB4"].get("love", 0) == 0

        assert "BBDC4" in stats
        assert stats["BBDC4"]["love"] == 1
        assert stats["BBDC4"]["fire"] == 2

    def test_get_stats_respects_days_filter(self, tracker):
        """get_stats() filters rows older than N days."""
        # Insert a row with a backdated created_at
        conn = tracker._conn
        conn.execute(
            """INSERT INTO reactions (briefing_run_id, message_id, embed_index, asset_ticker, reaction, user_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now', '-30 days'))""",
            ("old-run", 1, 0, "OLD", "up", 1),
        )
        conn.execute(
            """INSERT INTO reactions (briefing_run_id, message_id, embed_index, asset_ticker, reaction, user_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, datetime('now', '-1 day'))""",
            ("recent-run", 2, 0, "NEW", "up", 1),
        )
        conn.commit()

        stats = tracker.get_stats(days=7)
        # OLD should be filtered out (>7 days)
        assert "OLD" not in stats
        # NEW should be present
        assert "NEW" in stats
        assert stats["NEW"]["up"] == 1

    def test_get_stats_empty_when_no_data(self, tracker):
        """get_stats() returns empty dict when no data exists."""
        stats = tracker.get_stats(days=7)
        assert stats == {}

    def test_get_source_stats_returns_by_source(self, tracker):
        """get_source_stats() groups by asset_ticker (source)."""
        tracker.track("run-1", 100, 0, "ITUB4", "up", 1)
        tracker.track("run-1", 100, 0, "ITUB4", "down", 1)
        tracker.track("run-1", 101, 1, "BBDC4", "love", 1)

        stats = tracker.get_source_stats(days=365)
        assert stats == tracker.get_stats(days=365)
