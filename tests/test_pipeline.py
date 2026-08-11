"""Tests for resenha.pipeline.run_pipeline."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "mock-token")
    monkeypatch.setenv("DISCORD_CHANNEL_ID", "123456789")
    monkeypatch.setenv("GEMINI_API_KEY", "mock-api-key")
    monkeypatch.setenv("GOOGLE_SHEET_ID", "mock-sheet-id")

    from resenha.config import Settings

    return Settings()


@pytest.fixture
def mock_asset():
    from resenha.portfolio import Asset

    return Asset(
        ticker="ITUB4",
        sector="Financeiro",
        target_pct=10.0,
        qty=100,
        avg_price=30.0,
        current_price=32.0,
        invested=3000.0,
        value=3200.0,
        pnl=200.0,
        return_pct=6.67,
        weight_pct=10.0,
        distance_meta="0%",
        status="OK",
    )


@pytest.fixture
def fake_macro():
    from datetime import datetime
    from resenha.macro import MacroData

    return MacroData(selic=10.5, ipca=4.2, dolar=5.0, fetched_at=datetime.now())


@pytest.fixture
def fake_context(fake_macro):
    from datetime import datetime
    from resenha.assembler import BriefingContext

    return BriefingContext(
        portfolio=[],
        macro=fake_macro,
        news_by_asset={},
        general_news=[],
        timestamp=datetime.now(),
    )


class TestRunPipeline:
    """Tests for run_pipeline orchestration."""

    @pytest.mark.asyncio
    async def test_run_pipeline_calls_all_steps(
        self, mock_settings, mock_asset, fake_macro, fake_context
    ):
        """run_pipeline calls all steps in correct order and returns briefing text."""
        fake_briefing_text = "**Resenha diária**\n\nTudo tranquilo."
        fake_embed = MagicMock()

        with (
            patch("resenha.pipeline.read_portfolio", return_value=[mock_asset]),
            patch("resenha.pipeline.fetch_price", return_value={"price": 32.0, "change_pct": 1.5}),
            patch("resenha.pipeline.fetch_macro", return_value=fake_macro),
            patch("resenha.pipeline.fetch_calendar_events", return_value=[]),
            patch("resenha.pipeline.fetch_relevant_emails", return_value=[]),
            patch("resenha.pipeline.fetch_news", return_value=[]),
            patch("resenha.pipeline.fetch_general_news", return_value=[]),
            patch("resenha.pipeline.assemble_briefing_data", return_value=fake_context),
            patch("resenha.pipeline.build_adaptive_context", return_value=""),
            patch("resenha.pipeline.generate_briefing", return_value=fake_briefing_text),
            patch("resenha.pipeline.generate_embeds", return_value=[fake_embed]),
            patch("resenha.pipeline.run_bot", new_callable=AsyncMock),
            patch("resenha.pipeline.ReactionTracker"),
            patch("resenha.pipeline.GeminiClient") as mock_gemini_cls,
            patch("resenha.pipeline.Cache"),
        ):
            mock_gemini_instance = MagicMock()
            mock_gemini_cls.return_value = mock_gemini_instance

            from resenha.pipeline import run_pipeline

            result = await run_pipeline(mock_settings, "pre-market")

            assert result == fake_briefing_text

    @pytest.mark.asyncio
    async def test_run_pipeline_partial_failure_price_fetcher(
        self, mock_settings, mock_asset, fake_macro, fake_context
    ):
        """When price fetching fails, pipeline continues and returns text."""
        fake_briefing_text = "Briefing parcial."

        with (
            patch("resenha.pipeline.read_portfolio", return_value=[mock_asset]),
            patch("resenha.pipeline.fetch_price", side_effect=Exception("Yahoo down")),
            patch("resenha.pipeline.fetch_macro", return_value=fake_macro),
            patch("resenha.pipeline.fetch_calendar_events", return_value=[]),
            patch("resenha.pipeline.fetch_relevant_emails", return_value=[]),
            patch("resenha.pipeline.fetch_news", return_value=[]),
            patch("resenha.pipeline.fetch_general_news", return_value=[]),
            patch("resenha.pipeline.assemble_briefing_data", return_value=fake_context),
            patch("resenha.pipeline.build_adaptive_context", return_value=""),
            patch("resenha.pipeline.generate_briefing", return_value=fake_briefing_text),
            patch("resenha.pipeline.generate_embeds", return_value=[]),
            patch("resenha.pipeline.run_bot", new_callable=AsyncMock),
            patch("resenha.pipeline.ReactionTracker"),
            patch("resenha.pipeline.GeminiClient"),
            patch("resenha.pipeline.Cache"),
        ):
            from resenha.pipeline import run_pipeline

            result = await run_pipeline(mock_settings, "pre-market")

            assert result == fake_briefing_text

    @pytest.mark.asyncio
    async def test_run_pipeline_partial_failure_news_fetcher(
        self, mock_settings, mock_asset, fake_macro, fake_context
    ):
        """When news fetching fails, pipeline continues and returns text."""
        fake_briefing_text = "Briefing sem notícias."

        with (
            patch("resenha.pipeline.read_portfolio", return_value=[mock_asset]),
            patch("resenha.pipeline.fetch_price", return_value={"price": 32.0}),
            patch("resenha.pipeline.fetch_macro", return_value=fake_macro),
            patch("resenha.pipeline.fetch_calendar_events", return_value=[]),
            patch("resenha.pipeline.fetch_relevant_emails", return_value=[]),
            patch("resenha.pipeline.fetch_news", side_effect=Exception("RSS down")),
            patch("resenha.pipeline.fetch_general_news", return_value=[]),
            patch("resenha.pipeline.assemble_briefing_data", return_value=fake_context),
            patch("resenha.pipeline.build_adaptive_context", return_value=""),
            patch("resenha.pipeline.generate_briefing", return_value=fake_briefing_text),
            patch("resenha.pipeline.generate_embeds", return_value=[]),
            patch("resenha.pipeline.run_bot", new_callable=AsyncMock),
            patch("resenha.pipeline.ReactionTracker"),
            patch("resenha.pipeline.GeminiClient"),
            patch("resenha.pipeline.Cache"),
        ):
            from resenha.pipeline import run_pipeline

            result = await run_pipeline(mock_settings, "pre-market")

            assert result == fake_briefing_text

    @pytest.mark.asyncio
    async def test_run_pipeline_fallback_tickers_when_portfolio_fails(
        self, mock_settings, fake_macro, fake_context
    ):
        """When read_portfolio fails, pipeline uses hardcoded fallback ticker list."""
        with (
            patch("resenha.pipeline.read_portfolio", side_effect=Exception("Auth error")),
            patch("resenha.pipeline.fetch_price", return_value={"price": 30.0}) as mock_price,
            patch("resenha.pipeline.fetch_macro", return_value=fake_macro),
            patch("resenha.pipeline.fetch_calendar_events", return_value=[]),
            patch("resenha.pipeline.fetch_relevant_emails", return_value=[]),
            patch("resenha.pipeline.fetch_news", return_value=[]),
            patch("resenha.pipeline.fetch_general_news", return_value=[]),
            patch("resenha.pipeline.assemble_briefing_data", return_value=fake_context),
            patch("resenha.pipeline.build_adaptive_context", return_value=""),
            patch("resenha.pipeline.generate_briefing", return_value="ok"),
            patch("resenha.pipeline.generate_embeds", return_value=[]),
            patch("resenha.pipeline.run_bot", new_callable=AsyncMock),
            patch("resenha.pipeline.ReactionTracker"),
            patch("resenha.pipeline.GeminiClient"),
            patch("resenha.pipeline.Cache"),
        ):
            from resenha.pipeline import run_pipeline

            result = await run_pipeline(mock_settings, "pre-market")

            assert result == "ok"
            # Should have called fetch_price for each fallback ticker (11 tickers)
            assert mock_price.call_count == 11

    @pytest.mark.asyncio
    async def test_run_pipeline_saves_briefing_memory(
        self, mock_settings, mock_asset, fake_macro, fake_context
    ):
        """Pipeline saves the generated briefing text to BriefingMemory."""
        fake_briefing_text = "**Resenha diária**\n\nTudo tranquilo."

        with (
            patch("resenha.pipeline.read_portfolio", return_value=[mock_asset]),
            patch("resenha.pipeline.fetch_price", return_value={"price": 32.0}),
            patch("resenha.pipeline.fetch_macro", return_value=fake_macro),
            patch("resenha.pipeline.fetch_calendar_events", return_value=[]),
            patch("resenha.pipeline.fetch_relevant_emails", return_value=[]),
            patch("resenha.pipeline.fetch_news", return_value=[]),
            patch("resenha.pipeline.fetch_general_news", return_value=[]),
            patch("resenha.pipeline.assemble_briefing_data", return_value=fake_context),
            patch("resenha.pipeline.build_adaptive_context", return_value=""),
            patch("resenha.pipeline.generate_briefing", return_value=fake_briefing_text),
            patch("resenha.pipeline.generate_embeds", return_value=[]),
            patch("resenha.pipeline.run_bot", new_callable=AsyncMock),
            patch("resenha.pipeline.ReactionTracker"),
            patch("resenha.pipeline.GeminiClient"),
            patch("resenha.pipeline.Cache"),
            patch("resenha.pipeline.BriefingMemory") as mock_memory_cls,
        ):
            mock_memory_instance = MagicMock()
            mock_memory_cls.return_value = mock_memory_instance

            from resenha.pipeline import run_pipeline

            await run_pipeline(mock_settings, "pre-market")

            mock_memory_instance.save.assert_called_once_with("pre-market", fake_briefing_text)

    @pytest.mark.asyncio
    async def test_run_pipeline_passes_previous_briefing_to_generate(
        self, mock_settings, mock_asset, fake_macro, fake_context
    ):
        """Pipeline passes the previous briefing from memory to generate_briefing."""
        fake_briefing_text = "Novo briefing."
        previous_briefing = "Briefing anterior."
        fake_embed = MagicMock()

        with (
            patch("resenha.pipeline.read_portfolio", return_value=[mock_asset]),
            patch("resenha.pipeline.fetch_price", return_value={"price": 32.0}),
            patch("resenha.pipeline.fetch_macro", return_value=fake_macro),
            patch("resenha.pipeline.fetch_calendar_events", return_value=[]),
            patch("resenha.pipeline.fetch_relevant_emails", return_value=[]),
            patch("resenha.pipeline.fetch_news", return_value=[]),
            patch("resenha.pipeline.fetch_general_news", return_value=[]),
            patch("resenha.pipeline.assemble_briefing_data", return_value=fake_context),
            patch("resenha.pipeline.build_adaptive_context", return_value=""),
            patch("resenha.pipeline.generate_briefing", return_value=fake_briefing_text) as mock_gen,
            patch("resenha.pipeline.generate_embeds", return_value=[fake_embed]),
            patch("resenha.pipeline.run_bot", new_callable=AsyncMock),
            patch("resenha.pipeline.ReactionTracker"),
            patch("resenha.pipeline.GeminiClient") as mock_gemini_cls,
            patch("resenha.pipeline.Cache"),
            patch("resenha.pipeline.BriefingMemory") as mock_memory_cls,
        ):
            mock_memory_instance = MagicMock()
            mock_memory_instance.get_last.return_value = previous_briefing
            mock_memory_cls.return_value = mock_memory_instance
            mock_gemini_instance = MagicMock()
            mock_gemini_cls.return_value = mock_gemini_instance

            from resenha.pipeline import run_pipeline

            await run_pipeline(mock_settings, "eod")

            mock_memory_instance.get_last.assert_called_once_with("eod")
            mock_gen.assert_called_once_with(
                fake_context, mock_gemini_instance, "eod", feedback_text="", previous_briefing=previous_briefing
            )

    @pytest.mark.asyncio
    async def test_run_pipeline_calls_agenda_fetchers(
        self, mock_settings, mock_asset, fake_macro, fake_context
    ):
        """Pipeline fetches calendar events and emails before assembling context."""
        fake_briefing_text = "Briefing com agenda."
        fake_event = {"summary": "Reunião"}
        fake_email = {"sender": "alice@example.com", "subject": "Orçamento"}

        with (
            patch("resenha.pipeline.read_portfolio", return_value=[mock_asset]),
            patch("resenha.pipeline.fetch_price", return_value={"price": 32.0}),
            patch("resenha.pipeline.fetch_macro", return_value=fake_macro),
            patch("resenha.pipeline.fetch_calendar_events", return_value=[fake_event]) as mock_calendar,
            patch("resenha.pipeline.fetch_relevant_emails", return_value=[fake_email]) as mock_email,
            patch("resenha.pipeline.fetch_news", return_value=[]),
            patch("resenha.pipeline.fetch_general_news", return_value=[]),
            patch("resenha.pipeline.assemble_briefing_data", return_value=fake_context) as mock_assemble,
            patch("resenha.pipeline.build_adaptive_context", return_value=""),
            patch("resenha.pipeline.generate_briefing", return_value=fake_briefing_text),
            patch("resenha.pipeline.generate_embeds", return_value=[]),
            patch("resenha.pipeline.run_bot", new_callable=AsyncMock),
            patch("resenha.pipeline.ReactionTracker"),
            patch("resenha.pipeline.GeminiClient"),
            patch("resenha.pipeline.Cache"),
        ):
            from resenha.pipeline import run_pipeline

            await run_pipeline(mock_settings, "pre-market")

            mock_calendar.assert_called_once()
            mock_email.assert_called_once()
            mock_assemble.assert_called_once()
            passed_agenda = mock_assemble.call_args.kwargs["agenda"]
            assert passed_agenda.events == [fake_event]
            assert passed_agenda.emails == [fake_email]
