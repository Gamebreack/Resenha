"""Tests for resenha.prompts.build_briefing_prompt."""

from datetime import date, datetime, timezone

from resenha.agenda import CalendarEvent, EmailSummary
from resenha.assembler import AgendaData, AssetPosition, BriefingContext
from resenha.macro import MacroData
from resenha.news import NewsItem
from resenha.portfolio import Asset
from resenha.prompts import build_briefing_prompt


def _make_context(agenda=None):
    assets = [
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
    ]
    portfolio = [AssetPosition(asset=assets[0], price={"price": 26.0})]
    macro = MacroData(selic=10.5, ipca=4.2, dolar=5.0, fetched_at=datetime.now())
    news_by_asset = {
        "PETR4": [
            NewsItem(
                title="PETR4 sobe",
                url="http://example.com/1",
                source="InfoMoney",
                published=datetime.now(),
                summary="Alta",
                tickers_mentioned=["PETR4"],
            ),
        ],
    }
    general_news = [
        NewsItem(
            title="Mercado estável",
            url="http://example.com/2",
            source="Seu Dinheiro",
            published=datetime.now(),
            summary="Dia tranquilo",
            tickers_mentioned=[],
        ),
    ]
    return BriefingContext(
        portfolio=portfolio,
        macro=macro,
        news_by_asset=news_by_asset,
        general_news=general_news,
        agenda=agenda,
        timestamp=datetime.now(),
    )


def test_prompt_contains_tickers_and_macro():
    ctx = _make_context()
    prompt = build_briefing_prompt(ctx, "pre-market")
    assert "PETR4" in prompt
    assert "SELIC" in prompt
    assert "10.5" in prompt


def test_prompt_contains_voice_instruction():
    ctx = _make_context()
    prompt = build_briefing_prompt(ctx, "pre-market")
    assert any(word in prompt.lower() for word in ["relaxed", "informal", "brasileiro"])
    assert "notícias gerais (Brasil, mundo, tecnologia)" in prompt


def test_prompt_includes_previous_briefing():
    ctx = _make_context()
    previous = "Resumo anterior do briefing."
    prompt = build_briefing_prompt(ctx, "pre-market", previous_briefing=previous)
    assert "## Resumo Anterior" in prompt
    assert previous in prompt


def test_prompt_includes_avoid_repetition_instruction():
    ctx = _make_context()
    previous = "Resumo anterior do briefing."
    prompt = build_briefing_prompt(ctx, "pre-market", previous_briefing=previous)
    assert "evite repetir" in prompt.lower()
    assert "novo ou mudou" in prompt.lower()


def test_prompt_contains_agenda_section():
    agenda = AgendaData(
        events=[
            CalendarEvent(
                summary="Reunião",
                start=datetime(2026, 6, 20, 14, 0, tzinfo=timezone.utc),
                end=datetime(2026, 6, 20, 15, 0, tzinfo=timezone.utc),
                location="Sala 1",
                description=None,
            ),
        ],
        emails=[
            EmailSummary(
                sender="alice@example.com",
                subject="Orçamento",
                received_at=datetime(2026, 6, 19, 10, 0, tzinfo=timezone.utc),
            ),
        ],
    )
    ctx = _make_context(agenda=agenda)
    prompt = build_briefing_prompt(ctx, "pre-market")
    assert "## Agenda da Semana" in prompt
    assert "20/06/2026 14:00" in prompt
    assert "Reunião" in prompt
    assert "Sala 1" in prompt
    assert "alice@example.com" in prompt
    assert "Orçamento" in prompt


def test_prompt_agenda_all_day_event():
    agenda = AgendaData(
        events=[
            CalendarEvent(
                summary="Feriado",
                start=date(2026, 6, 25),
                end=date(2026, 6, 26),
                location=None,
                description=None,
            ),
        ],
        emails=[],
    )
    ctx = _make_context(agenda=agenda)
    prompt = build_briefing_prompt(ctx, "pre-market")
    assert "25/06/2026" in prompt
    assert "Feriado" in prompt


def test_prompt_agenda_fallback_when_empty():
    ctx = _make_context(agenda=AgendaData(events=[], emails=[]))
    prompt = build_briefing_prompt(ctx, "pre-market")
    assert "## Agenda da Semana" in prompt
    assert "Nada relevante por enquanto." in prompt


def test_prompt_agenda_fallback_when_missing():
    ctx = _make_context(agenda=None)
    prompt = build_briefing_prompt(ctx, "pre-market")
    assert "## Agenda da Semana" in prompt
    assert "Nada relevante por enquanto." in prompt
