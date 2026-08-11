"""Tests for resenha.cache.Cache."""

import time

import pytest

from resenha.cache import Cache


@pytest.fixture
def cache(tmp_path):
    return Cache(db_path=tmp_path / "test_cache.db")


def test_cache_set_and_get(cache):
    data = {"price": 30.5, "change_pct": 1.2}
    cache.set("ITUB4.SA", data)
    result = cache.get("ITUB4.SA", ttl_seconds=3600)
    assert result == data


def test_cache_get_missing_returns_none(cache):
    result = cache.get("MISSING", ttl_seconds=3600)
    assert result is None


def test_cache_ttl_expiration(cache):
    data = {"price": 30.5}
    cache.set("ITUB4.SA", data)
    # Simulate time passing by backdating the row
    conn = cache._conn
    two_hours_ago = int(time.time()) - 7200
    conn.execute("UPDATE cache SET created_at = ? WHERE key = ?", (two_hours_ago, "ITUB4.SA"))
    conn.commit()
    result = cache.get("ITUB4.SA", ttl_seconds=3600)
    assert result is None


def test_cache_overwrite(cache):
    cache.set("ITUB4.SA", {"price": 30.0})
    cache.set("ITUB4.SA", {"price": 31.0})
    result = cache.get("ITUB4.SA", ttl_seconds=3600)
    assert result == {"price": 31.0}
