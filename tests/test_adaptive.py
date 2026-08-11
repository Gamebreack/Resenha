"""Tests for resenha.adaptive — adaptive briefing context and feedback injection."""

from unittest.mock import MagicMock, patch

from resenha.adaptive import build_adaptive_context, inject_feedback


class TestBuildAdaptiveContext:
    """Tests for build_adaptive_context()."""

    def test_with_data(self):
        """When tracker has reaction data, output contains engagement header and ticker."""
        tracker = MagicMock()
        tracker.get_stats.return_value = {"ITUB4": {"up": 3, "down": 1}}

        result = build_adaptive_context(tracker, days=7)

        tracker.get_stats.assert_called_once_with(days=7)
        assert "Engajamento recente" in result
        assert "ITUB4" in result

    def test_empty_stats_returns_empty_string(self):
        """When tracker returns no stats, result is an empty string."""
        tracker = MagicMock()
        tracker.get_stats.return_value = {}

        result = build_adaptive_context(tracker)

        assert result == ""

    def test_default_days_is_seven(self):
        """Default look-back window is 7 days."""
        tracker = MagicMock()
        tracker.get_stats.return_value = {}

        build_adaptive_context(tracker)

        tracker.get_stats.assert_called_once_with(days=7)


class TestInjectFeedback:
    """Tests for inject_feedback()."""

    def test_inserts_before_headers(self):
        """Feedback is inserted as h3 section before the first ## h2 header."""
        prompt = "Some intro\n## ITUB4\nContent\n## BBDC4\nMore"
        feedback = "Engajamento recente (7 dias):\nITUB4 ↑ 2.0"

        result = inject_feedback(prompt, feedback)

        assert "### 📊 Engajamento" in result
        # The feedback h3 must appear before the first ## header
        h3_pos = result.index("### 📊 Engajamento")
        first_h2_pos = result.index("## ITUB4")
        assert h3_pos < first_h2_pos, "feedback section should come before first ## header"
        assert feedback in result

    def test_appends_when_no_headers(self):
        """When prompt has no ## headers, feedback is appended at the end."""
        prompt = "Just some text, no headers"
        feedback = "Feedback here"

        result = inject_feedback(prompt, feedback)

        assert result.endswith("### 📊 Engajamento\nFeedback here\n")
        assert result.startswith("Just some text, no headers")

    def test_empty_feedback_returns_unchanged(self):
        """Empty feedback text returns the prompt unchanged."""
        prompt = "## Something\nContent here"

        result = inject_feedback(prompt, "")

        assert result == prompt

    def test_prompt_starts_with_h2(self):
        """When prompt starts with ##, feedback is inserted before it."""
        prompt = "## ITUB4\nSome content"
        feedback = "Engajamento: ITUB4 ↑ 1.0"

        result = inject_feedback(prompt, feedback)

        assert result.startswith("### 📊 Engajamento")
        assert "## ITUB4" in result
        assert result.index("###") < result.index("## ITUB4")


class TestGenerateBriefingPassesFeedback:
    """Verify generate_briefing() calls inject_feedback with the correct arguments."""

    def test_passes_feedback_through_pipeline(self):
        """generate_briefing calls inject_feedback and then gemini.generate."""
        from resenha.assembler import BriefingContext
        from resenha.gemini import GeminiClient
        from resenha.summary import generate_briefing

        ctx = MagicMock(spec=BriefingContext)
        gemini = MagicMock(spec=GeminiClient)
        gemini.generate.return_value = "briefing output"

        with (
            patch("resenha.summary.build_briefing_prompt", return_value="mock prompt with ## header") as mock_build,
            patch("resenha.summary.inject_feedback", return_value="mock prompt with feedback") as mock_inject,
        ):
            result = generate_briefing(
                ctx, gemini, "pre-market", feedback_text="some feedback"
            )

            mock_build.assert_called_once_with(ctx, "pre-market", previous_briefing=None)
            mock_inject.assert_called_once_with(
                "mock prompt with ## header", "some feedback"
            )
            gemini.generate.assert_called_once_with(
                "mock prompt with feedback", max_tokens=4000
            )
            assert result == "briefing output"
