"""Tests for resenha.config.Settings."""

from pathlib import Path

import pytest


def test_settings_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings loads all fields from environment variables."""
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "mock-token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GEMINI_API_KEY", "mock-api-key")
    monkeypatch.setenv("GOOGLE_SHEET_ID", "mock-sheet-id")
    monkeypatch.setenv("GOOGLE_SHEET_TAB", "TestTab")
    monkeypatch.setenv("CACHE_DB_PATH", "/tmp/test.db")
    monkeypatch.setenv("PREMARKET_HOUR", "8")
    monkeypatch.setenv("EOD_HOUR", "20")

    from resenha.config import Settings

    settings = Settings()

    assert settings.discord_bot_token == "mock-token"
    assert settings.discord_channel_id == 123456789
    assert settings.gemini_api_key == "mock-api-key"
    assert settings.google_sheet_id == "mock-sheet-id"
    assert settings.google_sheet_tab == "TestTab"
    assert settings.cache_db_path == Path("/tmp/test.db")
    assert settings.premarket_hour == 8
    assert settings.eod_hour == 20


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    """Settings uses defaults when optional env vars are absent."""
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "mock-token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GEMINI_API_KEY", "mock-api-key")
    monkeypatch.setenv("GOOGLE_SHEET_ID", "mock-sheet-id")
    monkeypatch.delenv("GOOGLE_SHEET_TAB", raising=False)
    monkeypatch.delenv("CACHE_DB_PATH", raising=False)
    monkeypatch.delenv("PREMARKET_HOUR", raising=False)
    monkeypatch.delenv("EOD_HOUR", raising=False)

    from resenha.config import Settings

    settings = Settings()

    assert settings.google_sheet_tab == "Consolidado"
    assert settings.cache_db_path == Path("data/resenha.db")
    assert settings.premarket_hour == 7
    assert settings.eod_hour == 19
