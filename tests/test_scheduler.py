"""Tests for resenha.scheduler.ResenhaScheduler."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from resenha.config import Settings


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "mock-token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GEMINI_API_KEY", "mock-api-key")
    monkeypatch.setenv("GOOGLE_SHEET_ID", "mock-sheet-id")
    return Settings()


class TestResenhaScheduler:
    """Tests for ResenhaScheduler time-based triggering logic."""

    @pytest.mark.asyncio
    async def test_scheduler_triggers_premarket(self, mock_settings):
        """Scheduler triggers pre-market at configured hour (default 7:00 BRT = 10:00 UTC)."""
        from resenha.scheduler import ResenhaScheduler

        scheduler = ResenhaScheduler(mock_settings)
        scheduler._run_pipeline = AsyncMock()

        # Mock BRT time: Monday 7:00 BRT = Monday 10:00 UTC
        monday_10utc = datetime(2026, 5, 11, 10, 0, 0, tzinfo=timezone.utc)
        with patch("resenha.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = monday_10utc
            mock_dt.timezone = timezone
            mock_dt.timedelta = timedelta

            await scheduler._run_if_scheduled()

        scheduler._run_pipeline.assert_called_once_with(mock_settings, "pre-market")

    @pytest.mark.asyncio
    async def test_scheduler_triggers_eod(self, mock_settings):
        """Scheduler triggers EOD at configured hour (default 19:00 BRT = 22:00 UTC)."""
        from resenha.scheduler import ResenhaScheduler

        scheduler = ResenhaScheduler(mock_settings)
        scheduler._run_pipeline = AsyncMock()

        # Friday 19:00 BRT = Friday 22:00 UTC
        friday_22utc = datetime(2026, 5, 15, 22, 0, 0, tzinfo=timezone.utc)
        with patch("resenha.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = friday_22utc
            mock_dt.timezone = timezone
            mock_dt.timedelta = timedelta

            await scheduler._run_if_scheduled()

        scheduler._run_pipeline.assert_called_once_with(mock_settings, "eod")

    @pytest.mark.asyncio
    async def test_scheduler_triggers_longform_on_saturday(self, mock_settings):
        """Scheduler triggers long-form on Saturday at 7:00 BRT."""
        from resenha.scheduler import ResenhaScheduler

        scheduler = ResenhaScheduler(mock_settings)
        scheduler._run_pipeline = AsyncMock()

        # Saturday 7:00 BRT = Saturday 10:00 UTC
        saturday_10utc = datetime(2026, 5, 16, 10, 0, 0, tzinfo=timezone.utc)
        with patch("resenha.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = saturday_10utc
            mock_dt.timezone = timezone
            mock_dt.timedelta = timedelta

            await scheduler._run_if_scheduled()

        scheduler._run_pipeline.assert_called_once_with(mock_settings, "long-form")

    @pytest.mark.asyncio
    async def test_scheduler_skips_duplicate_same_minute(self, mock_settings):
        """Second call within the same minute for the same style is skipped."""
        from resenha.scheduler import ResenhaScheduler

        scheduler = ResenhaScheduler(mock_settings)
        scheduler._run_pipeline = AsyncMock()

        # Monday 7:00 BRT = Monday 10:00 UTC
        monday_10utc = datetime(2026, 5, 11, 10, 0, 0, tzinfo=timezone.utc)
        with patch("resenha.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = monday_10utc
            mock_dt.timezone = timezone
            mock_dt.timedelta = timedelta

            # First call triggers
            await scheduler._run_if_scheduled()
            assert scheduler._run_pipeline.call_count == 1

            # Second call within same minute skips
            await scheduler._run_if_scheduled()
            assert scheduler._run_pipeline.call_count == 1

    @pytest.mark.asyncio
    async def test_scheduler_no_trigger_on_sunday(self, mock_settings):
        """Sunday at 7:00 BRT should not trigger any briefing."""
        from resenha.scheduler import ResenhaScheduler

        scheduler = ResenhaScheduler(mock_settings)
        scheduler._run_pipeline = AsyncMock()

        # Sunday 7:00 BRT = Sunday 10:00 UTC
        sunday_10utc = datetime(2026, 5, 17, 10, 0, 0, tzinfo=timezone.utc)
        with patch("resenha.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = sunday_10utc
            mock_dt.timezone = timezone
            mock_dt.timedelta = timedelta

            await scheduler._run_if_scheduled()

        scheduler._run_pipeline.assert_not_called()

    @pytest.mark.asyncio
    async def test_scheduler_no_trigger_outside_schedule(self, mock_settings):
        """Random time on a weekday (e.g., 15:00 BRT) should not trigger."""
        from resenha.scheduler import ResenhaScheduler

        scheduler = ResenhaScheduler(mock_settings)
        scheduler._run_pipeline = AsyncMock()

        # Monday 15:00 BRT = Monday 18:00 UTC
        monday_18utc = datetime(2026, 5, 11, 18, 0, 0, tzinfo=timezone.utc)
        with patch("resenha.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = monday_18utc
            mock_dt.timezone = timezone
            mock_dt.timedelta = timedelta

            await scheduler._run_if_scheduled()

        scheduler._run_pipeline.assert_not_called()

    @pytest.mark.asyncio
    async def test_scheduler_respects_custom_hours(self, monkeypatch, mock_settings):
        """Scheduler uses settings.premarket_hour and settings.eod_hour."""
        monkeypatch.setenv("DISCORD_BOT_TOKEN", "mock-token")
        monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
        monkeypatch.setenv("GEMINI_API_KEY", "mock-api-key")
        monkeypatch.setenv("GOOGLE_SHEET_ID", "mock-sheet-id")
        monkeypatch.setenv("PREMARKET_HOUR", "8")
        monkeypatch.setenv("EOD_HOUR", "20")
        settings = Settings()

        from resenha.scheduler import ResenhaScheduler

        scheduler = ResenhaScheduler(settings)
        scheduler._run_pipeline = AsyncMock()

        # Monday 8:00 BRT = Monday 11:00 UTC → should trigger pre-market
        monday_11utc = datetime(2026, 5, 11, 11, 0, 0, tzinfo=timezone.utc)
        with patch("resenha.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = monday_11utc
            mock_dt.timezone = timezone
            mock_dt.timedelta = timedelta

            await scheduler._run_if_scheduled()

        scheduler._run_pipeline.assert_called_once_with(settings, "pre-market")
