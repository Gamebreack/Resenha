"""Tests for resenha.agenda Google Calendar/Gmail fetchers."""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from resenha.agenda import (
    CalendarEvent,
    EmailSummary,
    fetch_calendar_events,
    fetch_relevant_emails,
)


@pytest.fixture
def token_path(tmp_path):
    return tmp_path / "google_token.json"


def _mock_build(service_name, version, credentials=None):
    """Return a mock Google API service configured by the caller."""
    return MagicMock()


def test_fetch_calendar_events_returns_parsed_events(token_path):
    now = datetime(2026, 6, 19, 12, 0, 0, tzinfo=timezone.utc)
    future = now + timedelta(days=2)
    raw_events = {
        "items": [
            {
                "summary": "Reunião de alinhamento",
                "start": {"dateTime": future.isoformat()},
                "end": {"dateTime": (future + timedelta(hours=1)).isoformat()},
                "location": "Sala 101",
                "description": " discussão",
            },
            {
                "summary": "Dia inteiro",
                "start": {"date": "2026-06-25"},
                "end": {"date": "2026-06-26"},
                "location": None,
                "description": None,
            },
        ],
    }

    mock_service = MagicMock()
    mock_service.events().list().execute.return_value = raw_events

    with patch("resenha.agenda.Credentials") as mock_creds, patch(
        "resenha.agenda.build", return_value=mock_service
    ) as mock_build:
        mock_creds.from_authorized_user_file.return_value = MagicMock()

        with patch("resenha.agenda.datetime") as mock_datetime:
            mock_datetime.now.return_value = now
            mock_datetime.fromisoformat = datetime.fromisoformat
            mock_datetime.side_effect = lambda *args, **kw: datetime(*args, **kw)

            events = fetch_calendar_events(token_path)

    mock_creds.from_authorized_user_file.assert_called_once_with(str(token_path))
    mock_build.assert_called_once_with("calendar", "v3", credentials=mock_creds.from_authorized_user_file.return_value)
    call_kwargs = mock_service.events().list.call_args.kwargs
    assert call_kwargs["calendarId"] == "primary"
    assert call_kwargs["timeMin"] == now.isoformat()
    assert call_kwargs["timeMax"] == (now + timedelta(days=7)).isoformat()
    assert call_kwargs["maxResults"] == 20

    assert len(events) == 2
    assert events[0].summary == "Reunião de alinhamento"
    assert events[0].start == future
    assert events[0].location == "Sala 101"
    assert events[1].summary == "Dia inteiro"
    assert events[1].start == date(2026, 6, 25)


def test_fetch_relevant_emails_returns_parsed_summaries(token_path):
    raw_list = {"messages": [{"id": "msg1"}, {"id": "msg2"}]}
    details = {
        "msg1": {
            "payload": {
                "headers": [
                    {"name": "From", "value": "alice@example.com"},
                    {"name": "Subject", "value": "Orçamento"},
                    {"name": "Date", "value": "Fri, 19 Jun 2026 10:00:00 +0000"},
                ]
            }
        },
        "msg2": {
            "payload": {
                "headers": [
                    {"name": "From", "value": "bob@example.com"},
                    {"name": "Subject", "value": "Relatório"},
                    {"name": "Date", "value": "Fri, 19 Jun 2026 09:00:00 +0000"},
                ]
            }
        },
    }

    def _get_message(userId, id, format, metadataHeaders):
        return MagicMock(execute=MagicMock(return_value=details[id]))

    mock_service = MagicMock()
    mock_service.users().messages().list().execute.return_value = raw_list
    mock_service.users().messages().get.side_effect = _get_message

    with patch("resenha.agenda.Credentials") as mock_creds, patch(
        "resenha.agenda.build", return_value=mock_service
    ):
        mock_creds.from_authorized_user_file.return_value = MagicMock()
        emails = fetch_relevant_emails(token_path)

    assert len(emails) == 2
    assert emails[0] == EmailSummary(
        sender="alice@example.com",
        subject="Orçamento",
        received_at=datetime(2026, 6, 19, 10, 0, 0, tzinfo=timezone.utc),
    )
    assert emails[1] == EmailSummary(
        sender="bob@example.com",
        subject="Relatório",
        received_at=datetime(2026, 6, 19, 9, 0, 0, tzinfo=timezone.utc),
    )

    list_kwargs = mock_service.users().messages().list.call_args.kwargs
    assert list_kwargs["userId"] == "me"
    assert list_kwargs["q"] == "is:unread newer_than:1d"


def test_fetch_relevant_emails_respects_max_results(token_path):
    raw_list = {"messages": [{"id": f"msg{i}"} for i in range(10)]}

    def _get_message(userId, id, format, metadataHeaders):
        return MagicMock(
            execute=MagicMock(
                return_value={
                    "payload": {
                        "headers": [
                            {"name": "From", "value": f"sender{id}"},
                            {"name": "Subject", "value": f"subject{id}"},
                        ]
                    }
                }
            )
        )

    mock_service = MagicMock()
    mock_service.users().messages().list().execute.return_value = raw_list
    mock_service.users().messages().get.side_effect = _get_message

    with patch("resenha.agenda.Credentials") as mock_creds, patch(
        "resenha.agenda.build", return_value=mock_service
    ):
        mock_creds.from_authorized_user_file.return_value = MagicMock()
        emails = fetch_relevant_emails(token_path, max_results=3)

    assert len(emails) == 3


def test_fetch_calendar_events_graceful_failure(token_path):
    with patch("resenha.agenda.Credentials") as mock_creds, patch(
        "resenha.agenda.build", side_effect=Exception("Calendar API error")
    ):
        mock_creds.from_authorized_user_file.return_value = MagicMock()
        events = fetch_calendar_events(token_path)

    assert events == []


def test_fetch_relevant_emails_graceful_failure(token_path):
    with patch("resenha.agenda.Credentials") as mock_creds, patch(
        "resenha.agenda.build", side_effect=Exception("Gmail API error")
    ):
        mock_creds.from_authorized_user_file.return_value = MagicMock()
        emails = fetch_relevant_emails(token_path)

    assert emails == []
