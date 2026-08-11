"""Tests for resenha.memory.BriefingMemory."""

from resenha.memory import BriefingMemory


def test_save_and_get_last(tmp_path):
    """Saving two briefings for the same style returns the most recent."""
    db_path = tmp_path / "briefing_memory.db"
    memory = BriefingMemory(db_path)

    memory.save("pre-market", "first briefing")
    memory.save("pre-market", "second briefing")

    last = memory.get_last("pre-market")
    assert last == "second briefing"


def test_get_last_missing_style(tmp_path):
    """get_last returns None when no prior briefing exists for a style."""
    db_path = tmp_path / "briefing_memory.db"
    memory = BriefingMemory(db_path)

    assert memory.get_last("eod") is None


def test_prune_keeps_only_latest(tmp_path):
    """prune removes older rows, keeping only the latest for the style."""
    db_path = tmp_path / "briefing_memory.db"
    memory = BriefingMemory(db_path)

    memory.save("long-form", "oldest")
    memory.save("long-form", "middle")
    memory.save("long-form", "latest")

    memory.prune("long-form", keep=1)

    assert memory.get_last("long-form") == "latest"
    with memory._conn:
        row = memory._conn.execute(
            "SELECT COUNT(*) FROM past_briefings WHERE style = ?", ("long-form",)
        ).fetchone()
    assert row[0] == 1
