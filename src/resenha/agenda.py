"""Google Calendar and Gmail agenda fetchers."""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


@dataclass
class CalendarEvent:
    """A calendar event summary."""

    summary: str
    start: datetime | date
    end: datetime | date
    location: str | None
    description: str | None


@dataclass
class EmailSummary:
    """A minimal Gmail message summary."""

    sender: str
    subject: str
    received_at: datetime | None


def _load_credentials(token_path: Path) -> Credentials:
    """Load OAuth credentials from the authorized-user JSON file."""
    return Credentials.from_authorized_user_file(str(token_path))  # type: ignore[no-any-return]


def _parse_event_time(time_value: dict) -> datetime | date:
    """Parse a Google Calendar event start/end time."""
    if "dateTime" in time_value:
        # Google returns ISO-8601 strings that may end with 'Z'.
        raw = time_value["dateTime"].replace("Z", "+00:00")
        return datetime.fromisoformat(raw)
    if "date" in time_value:
        return date.fromisoformat(time_value["date"])
    raise ValueError(f"Unknown event time format: {time_value!r}")


def _parse_email_date(date_header: str | None) -> datetime | None:
    """Parse an RFC 2822 Date header into an aware datetime."""
    if not date_header:
        return None
    try:
        return parsedate_to_datetime(date_header)
    except Exception:
        logger.warning("Failed to parse email date header: %s", date_header)
        return None


def fetch_calendar_events(token_path: Path, max_results: int = 20) -> list[CalendarEvent]:
    """Fetch upcoming events from the user's primary calendar for the next 7 days."""
    try:
        creds = _load_credentials(token_path)
        service = build("calendar", "v3", credentials=creds)

        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=7)).isoformat()

        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events: list[CalendarEvent] = []
        for item in events_result.get("items", []):
            events.append(
                CalendarEvent(
                    summary=item.get("summary", "(Sem título)"),
                    start=_parse_event_time(item.get("start", {})),
                    end=_parse_event_time(item.get("end", {})),
                    location=item.get("location"),
                    description=item.get("description"),
                )
            )
        return events
    except Exception:
        logger.warning("Failed to fetch calendar events", exc_info=True)
        return []


def fetch_relevant_emails(token_path: Path, max_results: int = 5) -> list[EmailSummary]:
    """Fetch recent unread Gmail messages from the last 24 hours."""
    try:
        creds = _load_credentials(token_path)
        service = build("gmail", "v1", credentials=creds)

        list_result = (
            service.users()
            .messages()
            .list(userId="me", q="is:unread newer_than:1d")
            .execute()
        )
        messages = list_result.get("messages", [])[:max_results]

        emails: list[EmailSummary] = []
        for msg in messages:
            detail = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                )
                .execute()
            )
            headers = {
                header["name"]: header["value"]
                for header in detail.get("payload", {}).get("headers", [])
            }
            emails.append(
                EmailSummary(
                    sender=headers.get("From", "Desconhecido"),
                    subject=headers.get("Subject", "(Sem assunto)"),
                    received_at=_parse_email_date(headers.get("Date")),
                )
            )
        return emails
    except Exception:
        logger.warning("Failed to fetch relevant emails", exc_info=True)
        return []
