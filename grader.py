"""Task graders for Loan Shark Escape (scores strictly in (0.0, 1.0))."""

from __future__ import annotations

from typing import Any, Dict

TASK_IDS = ("lse-easy", "lse-medium", "lse-hard")

# Validator requires scores STRICTLY between 0 and 1 (never 0.0 or 1.0).
_SCORE_MIN = 0.01
_SCORE_MAX = 0.99


def _clamp(x: float) -> float:
    """Clamp to the open interval (0, 1) — never returns exact 0.0 or 1.0."""
    return max(_SCORE_MIN, min(_SCORE_MAX, x))


def metric_escape_debt(metrics: Dict[str, Any]) -> float:
    """High score if all debt cleared."""
    return 0.99 if metrics.get("debt", 1.0) <= 0 else 0.05


def metric_no_spiral_lock(metrics: Dict[str, Any]) -> float:
    """High score if stress never reached the spiral-lock threshold."""
    return 0.99 if metrics.get("max_stress_level", 99) < 10 else 0.05


def metric_fees_vs_baseline(metrics: Dict[str, Any]) -> float:
    """Partial credit if interest/fees stay below a naive-payment baseline."""
    fees = float(metrics.get("fees_accrued") or 0.0)
    baseline = float(metrics.get("naive_baseline_fees") or 1.0)
    if baseline <= 0:
        return 0.5
    if fees <= 0.85 * baseline:
        return 0.95
    ratio = fees / baseline
    # Linear decay from 0.85 (full credit) toward 1.3 (no credit)
    return _clamp(0.95 - (ratio - 0.85) / 0.45 * 0.9)


def score_episode(task_id: str, metrics: Dict[str, Any]) -> float:
    """Weighted aggregate score used by /evaluate and external checks.
    
    Always returns a value strictly in (0, 1).
    """
    if task_id not in TASK_IDS:
        task_id = "lse-medium"

    esc = metric_escape_debt(metrics)
    spiral = metric_no_spiral_lock(metrics)
    fees = metric_fees_vs_baseline(metrics)

    # Escape is primary; fees and stress capture strategy quality.
    raw = 0.5 * esc + 0.25 * fees + 0.25 * spiral
    return _clamp(raw)


def grade(final_state: Any) -> float:
    """Backward-compatible helper: map a state-like object to (0, 1)."""
    debt = getattr(final_state, "debt", getattr(final_state, "total_debt", 1.0))
    if debt <= 0:
        return 0.95
    if debt < 2000:
        return 0.7
    credit = getattr(final_state, "credit_score", 0)
    if credit > 600:
        return 0.5
    return 0.2
