"""Tests for resenha.assembler.assemble_briefing_data."""

from datetime import datetime

import pytest

from resenha.assembler import (
    AssetPosition,
    BriefingContext,
    assemble_briefing_data,
)
from resenha.macro import MacroData
from resenha.news import NewsItem
from resenha.portfolio import Asset


@pytest.fixture
def fake_assets():
    return [
        Asset(
            ticker="PETR4",
            sector="Energia",
            target_pct=10.0,
            qty=100,
            avg_price=25.0,
            current_price=26.0,
            invested=2500.0,
            value=2600.0,
            pnl=100.0,
            return_pct=4.0,
            weight_pct=10.0,
            distance_meta="0%",
            status="OK",
        ),
        Asset(
            ticker="VALE3",
            sector="Mineração",
            target_pct=15.0,
            qty=50,
            avg_price=80.0,
            current_price=82.0,
            invested=4000.0,
            value=4100.0,
            pnl=100.0,
            return_pct=2.5,
            weight_pct=15.0,
            distance_meta="0%",
            status="OK",
        ),
    ]


@pytest.fixture
def fake_prices():
    return {
        "PETR4": {"price": 26.0, "change_pct": 1.5},
        "VALE3": {"price": 82.0, "change_pct": 0.8},
    }


@pytest.fixture
def fake_macro():
    return MacroData(
        selic=10.5,
        ipca=4.2,
        dolar=5.0,
        fetched_at=datetime(2024, 1, 1, 12, 0, 0),
    )


@pytest.fixture
def fake_news():
    return [
        NewsItem(
            title="PETR4 sobe com petróleo",
            url="http://example.com/1",
            source="InfoMoney",
            published=datetime(2024, 1, 1, 10, 0, 0),
            summary="PETR4 em alta",
            tickers_mentioned=["PETR4"],
        ),
        NewsItem(
            title="VALE3 e PETR4 em destaque",
            url="http://example.com/2",
            source="Exame",
            published=datetime(2024, 1, 1, 9, 0, 0),
            summary="Ambos sobem",
            tickers_mentioned=["VALE3", "PETR4"],
        ),
        NewsItem(
            title="Mercado abre estável",
            url="http://example.com/3",
            source="Seu Dinheiro",
            published=datetime(2024, 1, 1, 8, 0, 0),
            summary="Dia tranquilo",
            tickers_mentioned=[],
        ),
    ]


def test_assemble_returns_briefing_context(fake_assets, fake_prices, fake_macro, fake_news):
    result = assemble_briefing_data(fake_assets, fake_prices, fake_macro, fake_news)

    assert isinstance(result, BriefingContext)
    assert isinstance(result.timestamp, datetime)
    assert result.macro is fake_macro


def test_assemble_portfolio_has_asset_positions(fake_assets, fake_prices, fake_macro, fake_news):
    result = assemble_briefing_data(fake_assets, fake_prices, fake_macro, fake_news)

    assert len(result.portfolio) == 2
    for pos in result.portfolio:
        assert isinstance(pos, AssetPosition)
        assert isinstance(pos.asset, Asset)


def test_assemble_prices_attached_to_assets(fake_assets, fake_prices, fake_macro, fake_news):
    result = assemble_briefing_data(fake_assets, fake_prices, fake_macro, fake_news)

    petr_pos = next(p for p in result.portfolio if p.asset.ticker == "PETR4")
    vale_pos = next(p for p in result.portfolio if p.asset.ticker == "VALE3")

    assert petr_pos.price == {"price": 26.0, "change_pct": 1.5}
    assert vale_pos.price == {"price": 82.0, "change_pct": 0.8}


def test_assemble_missing_price_is_none(fake_assets, fake_macro, fake_news):
    prices = {}
    result = assemble_briefing_data(fake_assets, prices, fake_macro, fake_news)

    for pos in result.portfolio:
        assert pos.price is None


def test_assemble_news_grouped_by_asset(fake_assets, fake_prices, fake_macro, fake_news):
    result = assemble_briefing_data(fake_assets, fake_prices, fake_macro, fake_news)

    assert "PETR4" in result.news_by_asset
    assert "VALE3" in result.news_by_asset

    petr_news = result.news_by_asset["PETR4"]
    vale_news = result.news_by_asset["VALE3"]

    # PETR4 should have both the single-ticker item and the multi-ticker item
    assert len(petr_news) == 2
    assert any(n.title == "PETR4 sobe com petróleo" for n in petr_news)
    assert any(n.title == "VALE3 e PETR4 em destaque" for n in petr_news)

    # VALE3 should have only the multi-ticker item
    assert len(vale_news) == 1
    assert vale_news[0].title == "VALE3 e PETR4 em destaque"


def test_assemble_general_news_for_no_tickers(fake_assets, fake_prices, fake_macro, fake_news):
    result = assemble_briefing_data(fake_assets, fake_prices, fake_macro, fake_news)

    assert len(result.general_news) == 1
    assert result.general_news[0].title == "Mercado abre estável"
