"""Adaptive briefing: injects engagement feedback into the briefing prompt.

Provides functions to build a feedback context string from reaction data
and inject it into the briefing prompt before the first h2 header.
"""

from __future__ import annotations

from resenha.feedback import (
    compute_asset_scores,
    merge_feedback_into_context,
    normalize_scores,
)
from resenha.reactions import ReactionTracker


def build_adaptive_context(tracker: ReactionTracker, days: int = 7) -> str:
    """Build a feedback context string from recent reaction data.

    Args:
        tracker: A ReactionTracker instance connected to the reactions DB.
        days: Look-back window in days (default 7).

    Returns:
        A feedback string suitable for prompt injection, or an empty
        string if no reaction data is available.
    """
    stats = tracker.get_stats(days=days)
    if not stats:
        return ""

    scores = compute_asset_scores(stats)
    normalized = normalize_scores(scores)
    return merge_feedback_into_context(normalized)


def inject_feedback(prompt: str, feedback_text: str) -> str:
    """Insert feedback text into the briefing prompt.

    The feedback is wrapped in a ``### 📊 Engajamento`` h3 section and
    placed before the first ``## `` h2 header.  If no h2 header is found,
    the feedback is appended at the end of the prompt.

    Args:
        prompt: The briefing prompt text.
        feedback_text: The feedback context string to inject.

    Returns:
        The modified prompt.  If *feedback_text* is empty, the original
        *prompt* is returned unchanged.
    """
    if not feedback_text:
        return prompt

    insertion = f"### 📊 Engajamento\n{feedback_text}\n"

    # Look for the first "## " at the start of a line
    idx = prompt.find("\n## ")
    if idx != -1:
        # Insert right before the h2 header (after the preceding newline)
        return prompt[: idx + 1] + insertion + prompt[idx + 1 :]

    # Edge case: prompt starts with "## "
    if prompt.startswith("## "):
        return insertion + prompt

    # No h2 header found — append at the end
    return prompt + "\n" + insertion
