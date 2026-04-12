import pytest
from server.environment import LoanSharkEnvironment
from server.models import LoanAction

def test_environment_initialization():
    env = LoanSharkEnvironment()
    obs = env.reset("lse-easy")
    assert obs.total_debt == 3000.0
    assert obs.income == 2500.0
    assert obs.month == 0
    assert not obs.is_done

def test_environment_step_pay():
    env = LoanSharkEnvironment()
    obs = env.reset("lse-easy")
    initial_debt = obs.total_debt
    
    # Take a step to pay
    obs = env.step(LoanAction(action_type="pay", amount=0))
    
    # Month increments
    assert obs.month == 1
    # Since we pay 80% of income (2000), debt should reduce
    # Then 5% interest is charged on the remaining
    assert obs.total_debt < initial_debt

def test_evaluation_bounds():
    env = LoanSharkEnvironment()
    env.reset("lse-easy")
    for _ in range(5):
        env.step(LoanAction(action_type="wait", amount=0))
    
    eval_res = env.evaluate()
    # Validator explicitly checks this condition
    assert 0.0 < eval_res["score"] < 1.0
