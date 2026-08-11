"""Tests for resenha.macro.fetch_macro."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from resenha.cache import Cache
from resenha.macro import MacroData, fetch_macro


@pytest.fixture
def fake_bcb_response():
    def _make_response(valor):
        mock = MagicMock()
        mock.json.return_value = [{"data": "14/05/2026", "valor": valor}]
        mock.raise_for_status.return_value = None
        return mock
    return _make_response


@patch("resenha.macro.requests.get")
def test_fetch_macro_returns_macro_data(mock_get, tmp_path, fake_bcb_response):
    mock_get.side_effect = [
        fake_bcb_response("10,75"),   # SELIC series 432
        fake_bcb_response("4,50"),    # IPCA series 433
        fake_bcb_response("5,1234"),  # Dólar series 1
    ]

    cache = Cache(db_path=tmp_path / "macro_cache.db")
    result = fetch_macro(cache=cache)

    assert isinstance(result, MacroData)
    assert result.selic == 10.75
    assert result.ipca == 4.50
    assert result.dolar == 5.1234
    assert isinstance(result.fetched_at, datetime)

    # Assert correct endpoints were called
    calls = mock_get.call_args_list
    assert "bcdata.sgs.432" in calls[0][0][0]  # SELIC
    assert "bcdata.sgs.433" in calls[1][0][0]  # IPCA
    assert "bcdata.sgs.1" in calls[2][0][0]    # Dólar


@patch("resenha.macro.requests.get")
def test_fetch_macro_uses_cache_on_second_call(mock_get, tmp_path, fake_bcb_response):
    mock_get.side_effect = [
        fake_bcb_response("10,75"),
        fake_bcb_response("4,50"),
        fake_bcb_response("5,1234"),
    ]

    cache = Cache(db_path=tmp_path / "macro_cache.db")
    result1 = fetch_macro(cache=cache)
    assert result1.selic == 10.75

    # Second call should use cache; no additional HTTP requests
    result2 = fetch_macro(cache=cache)
    assert result2.selic == 10.75

    assert mock_get.call_count == 3


@patch("resenha.macro.requests.get")
def test_fetch_macro_cache_miss_after_ttl(mock_get, tmp_path, fake_bcb_response):
    mock_get.side_effect = [
        fake_bcb_response("10,75"),
        fake_bcb_response("4,50"),
        fake_bcb_response("5,1234"),
        fake_bcb_response("11,00"),
        fake_bcb_response("4,60"),
        fake_bcb_response("5,2000"),
    ]

    cache = Cache(db_path=tmp_path / "macro_cache.db")
    result1 = fetch_macro(cache=cache)
    assert result1.selic == 10.75

    # Expire cache by backdating the row
    import time
    conn = cache._conn
    one_hour_ago = int(time.time()) - 3601
    conn.execute("UPDATE cache SET created_at = ? WHERE key = ?", (one_hour_ago, "macro"))
    conn.commit()

    result2 = fetch_macro(cache=cache)
    assert result2.selic == 11.00

    assert mock_get.call_count == 6


@patch("resenha.macro.requests.get")
def test_fetch_macro_returns_stale_cache_on_failure(mock_get, tmp_path, fake_bcb_response):
    mock_get.side_effect = [
        fake_bcb_response("10,75"),
        fake_bcb_response("4,50"),
        fake_bcb_response("5,1234"),
    ]

    cache = Cache(db_path=tmp_path / "macro_cache.db")
    result1 = fetch_macro(cache=cache)
    assert result1.selic == 10.75

    # Expire cache
    import time
    conn = cache._conn
    one_hour_ago = int(time.time()) - 3601
    conn.execute("UPDATE cache SET created_at = ? WHERE key = ?", (one_hour_ago, "macro"))
    conn.commit()

    # Now API calls fail
    mock_get.side_effect = Exception("API down")

    result2 = fetch_macro(cache=cache)
    assert result2 is not None
    assert result2.selic == 10.75


@patch("resenha.macro.requests.get")
def test_fetch_macro_returns_none_and_logs_warning_when_all_fail(mock_get, tmp_path, caplog):
    mock_get.side_effect = Exception("API down")

    cache = Cache(db_path=tmp_path / "macro_cache.db")

    import logging
    with caplog.at_level(logging.WARNING):
        result = fetch_macro(cache=cache)

    assert result is None
    assert "API" in caplog.text or "macro" in caplog.text or "warning" in caplog.text.lower()
