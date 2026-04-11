import pytest
from server.environment import LoanSharkEnvironment

def test_spiral_lock():
    """Verify that stress level 10 triggers spiral lock."""
    env = LoanSharkEnvironment()
    env.reset("lse-easy")
    # Action 4 (Do nothing) adds 2 stress per month
    # 0 -> 2 -> 4 -> 6 -> 8 -> 10 (5 steps)
    for _ in range(4):
        obs, reward, done = env.step(4)
        assert not done
        assert obs.stress_level < 10
    
    obs, reward, done = env.step(4)
    assert done
    assert obs.spiral_lock is True
    assert reward == -100.0

def test_win_condition_early_payoff():
    """Verify that paying off loans in full results in a win."""
    env = LoanSharkEnvironment()
    env.reset("lse-easy")
    # In easy scenario, cash allows full payoff in month 1
    obs, reward, done = env.step(0)
    assert done
    assert all(l.balance <= 1e-9 for l in obs.loans)
    assert reward > 100.0 # Clear bonus

def test_baseline_exists():
    """Verify that baseline is computed at reset."""
    env = LoanSharkEnvironment()
    obs = env.reset("lse-easy")
    assert obs.baseline_fees > 0
    assert env.state.baseline_fees == obs.baseline_fees

def test_medium_scenario_delayed_cu():
    """Verify that CU becomes available only at month 4 in medium scenario."""
    env = LoanSharkEnvironment()
    env.reset("lse-medium")
    
    # Month 1: CU should be False
    obs = env._get_observation()
    assert obs.escape_routes.credit_union_available is False
    
    # Fast forward to month 4
    for _ in range(3):
        env.state.stress_level = 0
        env.step(4)
    
    obs = env._get_observation()
    assert env.state.current_month == 4
    assert obs.escape_routes.credit_union_available is True

def test_medium_scenario_income_shock():
    """Verify that income shock applies correctly in month 8."""
    env = LoanSharkEnvironment()
    env.reset("lse-medium")
    
    for _ in range(6):
        env.state.stress_level = 0
        env.step(4)
    assert env.state.cash == 28000
    
    env.state.stress_level = 0
    env.step(4)
    assert env.state.current_month == 8
    assert env.state.cash == 27000

def test_hard_scenario_load():
    """Verify that the hard scenario loads with three loans."""
    env = LoanSharkEnvironment()
    obs = env.reset("lse-hard")
    assert len(obs.loans) == 3
    assert obs.months_remaining == 24
    assert obs.escape_routes.credit_union_available is False
