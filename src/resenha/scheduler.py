"""Asyncio-based scheduler that triggers briefings at configured BRT times."""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from datetime import datetime, timedelta, timezone
from typing import Any

from resenha.config import Settings

logger = logging.getLogger(__name__)

# BRT is UTC-3
BRT_OFFSET = timedelta(hours=3)


def _brt_now() -> datetime:
    """Return current BRT time as an aware datetime (UTC-3 offset)."""
    now_utc = datetime.now(timezone.utc)
    return now_utc - BRT_OFFSET


class ResenhaScheduler:
    """Checks time every 30 seconds and triggers the briefing pipeline on schedule.

    Schedule:
      Mon-Fri at settings.premarket_hour:00 BRT → "pre-market"
      Mon-Fri at settings.eod_hour:00 BRT     → "eod"
      Sat at 7:00 BRT                         → "long-form"
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._stop_event = asyncio.Event()
        self._last_run_style: str | None = None
        self._last_run_minute: int | None = None
        # _run_pipeline is set by start(); tests can mock it directly
        self._run_pipeline: Callable[[Settings, str], Coroutine[Any, Any, str]] | None = None

    async def start(self) -> None:
        """Start the scheduler loop. Runs until stop() is called."""
        # Lazy-import run_pipeline to avoid importing discord at module level
        from resenha.pipeline import run_pipeline

        self._run_pipeline = run_pipeline
        logger.info("Scheduler started")
        while not self._stop_event.is_set():
            try:
                await self._run_if_scheduled()
            except Exception:
                logger.exception("Scheduler loop error")
            # Check every 30 seconds, but check stop_event every second
            for _ in range(30):
                if self._stop_event.is_set():
                    break
                await asyncio.sleep(1)

    async def stop(self) -> None:
        """Signal the scheduler to stop."""
        self._stop_event.set()
        logger.info("Scheduler stop requested")

    async def _run_if_scheduled(self) -> None:
        """Check current BRT time and trigger pipeline if it matches a schedule slot."""
        brt = _brt_now()
        weekday = brt.weekday()  # 0=Monday, 6=Sunday
        hour = brt.hour
        minute = brt.minute

        style: str | None = None

        # Mon-Fri (0-4): pre-market and eod at configured hours
        if weekday < 5:
            if hour == self._settings.premarket_hour and minute == 0:
                style = "pre-market"
            elif hour == self._settings.eod_hour and minute == 0:
                style = "eod"
        # Sat (5): long-form at 7:00 BRT
        elif weekday == 5:
            if hour == 7 and minute == 0:
                style = "long-form"
        # Sun (6): no briefings

        if style is None:
            return

        # Duplicate prevention: skip if same style and same minute
        current_minute_key = weekday * 1440 + hour * 60 + minute
        if (
            self._last_run_style == style
            and self._last_run_minute == current_minute_key
        ):
            logger.debug("Skipping duplicate trigger for %s", style)
            return

        logger.info("Triggering %s briefing at %s", style, brt.strftime("%Y-%m-%d %H:%M BRT"))

        if self._run_pipeline is not None:
            self._last_run_style = style
            self._last_run_minute = current_minute_key
            await self._run_pipeline(self._settings, style)
