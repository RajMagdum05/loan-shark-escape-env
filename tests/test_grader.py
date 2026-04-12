import pytest
from grader import _clamp, metric_escape_debt, score_episode

def test_clamp():
    assert _clamp(1.5) == 0.99
    assert _clamp(-0.5) == 0.01
    assert _clamp(0.5) == 0.5

def test_metric_escape_debt():
    assert metric_escape_debt({"debt": 0.0}) == 0.99
    assert metric_escape_debt({"debt": -100.0}) == 0.99
    assert metric_escape_debt({"debt": 500.0}) == 0.05

def test_score_episode():
    # Should calculate compound score correctly and clamp it
    metrics = {
        "debt": 0,
        "max_stress_level": 5,
        "fees_accrued": 500,
        "naive_baseline_fees": 1000
    }
    score = score_episode("lse-easy", metrics)
    assert 0.01 <= score <= 0.99
