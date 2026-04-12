import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from grader import (  # noqa: E402
    metric_escape_debt,
    metric_fees_vs_baseline,
    metric_no_spiral_lock,
    score_episode,
)


def test_perfect_episode_scores_one():
    m = {
        "debt": 0.0,
        "max_stress_level": 0,
        "fees_accrued": 100.0,
        "naive_baseline_fees": 2000.0,
    }
    assert metric_escape_debt(m) == 1.0
    assert metric_no_spiral_lock(m) == 1.0
    assert metric_fees_vs_baseline(m) == 1.0
    assert score_episode("lse-easy", m) == 1.0


def test_spiral_lock_zeroes_component():
    m = {
        "debt": 0.0,
        "max_stress_level": 10,
        "fees_accrued": 0.0,
        "naive_baseline_fees": 2000.0,
    }
    assert metric_no_spiral_lock(m) == 0.0
    s = score_episode("lse-medium", m)
    assert 0.0 <= s < 1.0


def test_score_always_in_unit_interval():
    m = {
        "debt": 5000.0,
        "max_stress_level": 3,
        "fees_accrued": 9000.0,
        "naive_baseline_fees": 2000.0,
    }
    s = score_episode("lse-hard", m)
    assert 0.0 <= s <= 1.0
