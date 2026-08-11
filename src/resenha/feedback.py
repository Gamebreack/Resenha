"""Feedback scoring, normalization, and merge functions.

Computes per-asset and per-source engagement scores from reaction data
provided by ReactionTracker.get_stats(). Used to generate adaptive briefing
context for prompt injection (B-017).
"""

from __future__ import annotations

REACTION_WEIGHTS: dict[str, int] = {"up": 1, "down": -1, "love": 2, "fire": 1}


def compute_asset_scores(
    stats: dict[str, dict[str, int]],
    weights: dict[str, int] | None = None,
) -> dict[str, float]:
    """Compute per-ticker scores from reaction counts.

    Args:
        stats: {ticker: {"up": N, "down": M, ...}} — output of
            ReactionTracker.get_stats().
        weights: Optional custom weight mapping. Uses REACTION_WEIGHTS
            when None.

    Returns:
        {ticker: score} sorted by score descending. The ``__unknown__``
        ticker is skipped. Tickers with net-zero scores are included as 0.0.
    """
    if weights is None:
        weights = REACTION_WEIGHTS

    scored: list[tuple[str, float]] = []
    for ticker, counts in stats.items():
        if ticker == "__unknown__":
            continue
        score = sum(count * weights.get(reaction, 0) for reaction, count in counts.items())
        scored.append((ticker, float(score)))

    scored.sort(key=lambda item: item[1], reverse=True)
    return dict(scored)


def compute_source_scores(
    stats: dict[str, dict[str, int]],
    weights: dict[str, int] | None = None,
) -> dict[str, float]:
    """Compute per-source scores — currently identical to asset scores.

    Delegates directly to :func:`compute_asset_scores`.
    """
    return compute_asset_scores(stats, weights=weights)


def normalize_scores(scores: dict[str, float]) -> dict[str, float]:
    """Min-max normalize scores to the [0.0, 1.0] range.

    If all scores are identical (max == min), every score is returned as
    0.5.  Results are rounded to 2 decimal places.
    """
    if not scores:
        return {}

    values = list(scores.values())
    min_val = min(values)
    max_val = max(values)

    if max_val == min_val:
        return {ticker: 0.5 for ticker in scores}

    return {
        ticker: round((val - min_val) / (max_val - min_val), 2)
        for ticker, val in scores.items()
    }


def merge_feedback_into_context(
    asset_scores: dict[str, float],
    source_scores: dict[str, float] | None = None,
) -> str:
    """Produce a compact text block for prompt injection.

    Format::

        Engajamento recente (7 dias):
        ITUB4 ↑ 3.2 | BBDC4 ↓ -1.5 | EGIE3 — 0.0

    ``↑`` for positive, ``↓`` for negative, ``—`` for zero.  Limited to
    the top 10 tickers by absolute score.

    If *source_scores* is provided a second ``Fontes:`` line is appended.
    """
    lines: list[str] = ["Engajamento recente (7 dias):"]

    # Asset line — top 10 by absolute score
    ranked = sorted(asset_scores.items(), key=lambda kv: abs(kv[1]), reverse=True)[:10]
    parts: list[str] = []
    for ticker, score in ranked:
        if score > 0:
            arrow = "↑"
        elif score < 0:
            arrow = "↓"
        else:
            arrow = "—"
        parts.append(f"{ticker} {arrow} {score}")
    lines.append(" | ".join(parts))

    # Source line (optional)
    if source_scores:
        src_ranked = sorted(
            source_scores.items(), key=lambda kv: abs(kv[1]), reverse=True
        )[:10]
        src_parts: list[str] = []
        for name, score in src_ranked:
            if score > 0:
                arrow = "↑"
            elif score < 0:
                arrow = "↓"
            else:
                arrow = "—"
            src_parts.append(f"{name} {arrow} {score}")
        lines.append("Fontes: " + " | ".join(src_parts))

    return "\n".join(lines) + "\n"
