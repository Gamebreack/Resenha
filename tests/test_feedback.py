"""Tests for resenha.feedback — scoring, normalization, and merge functions."""

import pytest

from resenha.feedback import (
    REACTION_WEIGHTS,
    compute_asset_scores,
    compute_source_scores,
    merge_feedback_into_context,
    normalize_scores,
)


class TestComputeAssetScores:
    """Tests for compute_asset_scores()."""

    def test_basic_up_down(self):
        """up=2, down=1 → score=1.0."""
        stats = {"ITUB4": {"up": 2, "down": 1}}
        result = compute_asset_scores(stats)
        assert result == {"ITUB4": 1.0}

    def test_with_love_and_fire(self):
        """love and fire weighted correctly (love=2, fire=1)."""
        stats = {"PETR4": {"love": 1, "fire": 2}}
        result = compute_asset_scores(stats)
        # love=1*2 + fire=2*1 = 4.0
        assert result == {"PETR4": 4.0}

    def test_skips_unknown(self):
        """__unknown__ ticker is excluded from results."""
        stats = {"__unknown__": {"up": 5}, "ITUB4": {"up": 1}}
        result = compute_asset_scores(stats)
        assert "__unknown__" not in result
        assert "ITUB4" in result
        assert result["ITUB4"] == 1.0

    def test_sorted_descending(self):
        """Results are sorted by score descending."""
        stats = {"A": {"up": 5}, "B": {"up": 1}, "C": {"down": 3}}
        result = compute_asset_scores(stats)
        keys = list(result.keys())
        scores = list(result.values())
        assert keys == ["A", "B", "C"]
        assert scores == [5.0, 1.0, -3.0]

    def test_empty_stats_returns_empty(self):
        """Empty input returns empty dict."""
        result = compute_asset_scores({})
        assert result == {}

    def test_all_zero_net_included(self):
        """Tickers with all-zero or net-zero scores are included with 0.0."""
        stats = {"X": {"up": 1, "down": 1}}
        result = compute_asset_scores(stats)
        assert result == {"X": 0.0}


class TestCustomWeights:
    """Tests for custom weight overrides."""

    def test_custom_weights(self):
        """Passing a custom weight dict overrides REACTION_WEIGHTS."""
        stats = {"X": {"custom": 3}}
        custom_weights = {"custom": 10}
        result = compute_asset_scores(stats, weights=custom_weights)
        assert result == {"X": 30.0}


class TestComputeSourceScores:
    """Tests for compute_source_scores()."""

    def test_delegates_to_compute_asset_scores(self):
        """compute_source_scores is currently identical to compute_asset_scores."""
        stats = {"ITUB4": {"up": 2, "down": 1}}
        result = compute_source_scores(stats)
        assert result == {"ITUB4": 1.0}


class TestNormalizeScores:
    """Tests for normalize_scores()."""

    def test_range(self):
        """All values are normalized to [0.0, 1.0] range."""
        scores = {"A": 5.0, "B": 0.0, "C": -5.0}
        result = normalize_scores(scores)
        for value in result.values():
            assert 0.0 <= value <= 1.0
        assert result["A"] == 1.0
        assert result["C"] == 0.0

    def test_identical_scores(self):
        """When all scores are identical, returns all 0.5."""
        scores = {"A": 3.0, "B": 3.0}
        result = normalize_scores(scores)
        assert result == {"A": 0.5, "B": 0.5}

    def test_rounds_to_two_decimals(self):
        """Normalized values are rounded to 2 decimal places."""
        scores = {"A": 7.0, "B": 0.0}
        result = normalize_scores(scores)
        assert result["B"] == 0.0
        assert result["A"] == 1.0


class TestMergeFeedbackIntoContext:
    """Tests for merge_feedback_into_context()."""

    def test_format_basic(self):
        """Output contains tickers, arrow indicators, scores, and header."""
        scores = {"ITUB4": 3.2, "BBDC4": -1.5, "EGIE3": 0.0}
        output = merge_feedback_into_context(scores)
        assert "ITUB4" in output
        assert "BBDC4" in output
        assert "EGIE3" in output
        assert "3.2" in output
        assert "-1.5" in output
        assert "0.0" in output
        assert "↑" in output
        assert "↓" in output
        assert "—" in output
        assert "Engajamento recente" in output

    def test_source_scores_appended(self):
        """When source_scores provided, appends Fontes line."""
        asset = {"ITUB4": 3.0}
        sources = {"InfoMoney": 2.0}
        output = merge_feedback_into_context(asset, source_scores=sources)
        assert "Fontes" in output
        assert "InfoMoney" in output

    def test_top_10_limit(self):
        """Limits to top 10 tickers by absolute score."""
        scores = {f"T{i:03d}": float(i) for i in range(20)}
        output = merge_feedback_into_context(scores)
        # Only 10 tickers should appear (count the ↑/↓/— indicators)
        # Count pipes to determine number of tickers: N tickers = N-1 pipes
        asset_line = output.split("\n")[1]
        pipe_count = asset_line.count("|")
        # pipe_count = N-1, so N = pipe_count + 1
        ticker_count = pipe_count + 1
        assert ticker_count == 10
