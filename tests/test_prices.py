"""Tests for resenha.prices.fetch_price."""

from unittest.mock import MagicMock, patch

import pytest

from resenha.cache import Cache
from resenha.prices import fetch_price


@pytest.fixture
def fake_ticker_info():
    return {
        "regularMarketPrice": 30.5,
        "regularMarketChangePercent": 1.23,
        "regularMarketVolume": 12345678,
        "fiftyTwoWeekHigh": 35.0,
        "fiftyTwoWeekLow": 25.0,
    }


@patch("resenha.prices.yf.Ticker")
def test_fetch_price_returns_expected_keys(mock_ticker_cls, tmp_path, fake_ticker_info):
    mock_ticker = MagicMock()
    mock_ticker.info = fake_ticker_info
    mock_ticker_cls.return_value = mock_ticker

    cache = Cache(db_path=tmp_path / "cache.db")
    result = fetch_price("ITUB4", cache=cache)

    mock_ticker_cls.assert_called_once_with("ITUB4.SA")
    assert "price" in result
    assert "change_pct" in result
    assert "volume" in result
    assert "high_52w" in result
    assert "low_52w" in result
    assert result["price"] == 30.5
    assert result["change_pct"] == 1.23
    assert result["volume"] == 12345678
    assert result["high_52w"] == 35.0
    assert result["low_52w"] == 25.0


@patch("resenha.prices.yf.Ticker")
def test_fetch_price_uses_cache_on_second_call(mock_ticker_cls, tmp_path, fake_ticker_info):
    mock_ticker = MagicMock()
    mock_ticker.info = fake_ticker_info
    mock_ticker_cls.return_value = mock_ticker

    cache = Cache(db_path=tmp_path / "cache.db")
    result1 = fetch_price("ITUB4", cache=cache)
    assert result1["price"] == 30.5

    result2 = fetch_price("ITUB4", cache=cache)
    assert result2["price"] == 30.5

    # Should only call yfinance once because second call is cached
    mock_ticker_cls.assert_called_once_with("ITUB4.SA")


@patch("resenha.prices.yf.Ticker")
def test_fetch_price_cache_miss_after_ttl(mock_ticker_cls, tmp_path, fake_ticker_info):
    mock_ticker = MagicMock()
    mock_ticker.info = fake_ticker_info
    mock_ticker_cls.return_value = mock_ticker

    cache = Cache(db_path=tmp_path / "cache.db")
    result1 = fetch_price("ITUB4", cache=cache)
    assert result1["price"] == 30.5

    # Simulate cache expiration by modifying the timestamp manually
    import time
    conn = cache._conn
    one_hour_ago = int(time.time()) - 3601
    conn.execute("UPDATE cache SET created_at = ? WHERE key = ?", (one_hour_ago, "ITUB4.SA"))
    conn.commit()

    result2 = fetch_price("ITUB4", cache=cache)
    assert result2["price"] == 30.5

    # Should call yfinance twice because cache expired
    assert mock_ticker_cls.call_count == 2
    mock_ticker_cls.assert_any_call("ITUB4.SA")


@patch("resenha.prices.yf.Ticker")
def test_fetch_price_fallback_to_stale_cache(mock_ticker_cls, tmp_path, fake_ticker_info):
    mock_ticker = MagicMock()
    mock_ticker.info = fake_ticker_info
    mock_ticker_cls.return_value = mock_ticker

    cache = Cache(db_path=tmp_path / "cache.db")
    result1 = fetch_price("ITUB4", cache=cache)
    assert result1["price"] == 30.5

    # Expire cache and make yfinance fail
    import time
    conn = cache._conn
    one_hour_ago = int(time.time()) - 3601
    conn.execute("UPDATE cache SET created_at = ? WHERE key = ?", (one_hour_ago, "ITUB4.SA"))
    conn.commit()

    mock_ticker_cls.side_effect = Exception("network error")

    result2 = fetch_price("ITUB4", cache=cache)
    assert result2["price"] == 30.5


def test_fetch_price_raises_without_cache_and_network_fails():
    with patch("resenha.prices.yf.Ticker") as mock_ticker_cls:
        mock_ticker_cls.side_effect = Exception("network error")
        with pytest.raises(Exception):
            fetch_price("ITUB4")
