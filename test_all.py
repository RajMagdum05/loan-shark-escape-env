from server.environment import LoanSharkEnvironment

def run_test(name, func):
    print(f"Running {name}...")
    try:
        func()
        print(f"SUCCESS: {name}")
    except Exception as e:
        print(f"FAILED: {name}: {e}")
        import traceback
        traceback.print_exc()

def test_spiral_lock():
    env = LoanSharkEnvironment()
    env.reset("lse-easy")
    for _ in range(4):
        obs, reward, done = env.step(4)
        assert not done
    obs, reward, done = env.step(4)
    assert done
    assert obs.spiral_lock is True

def test_medium_shock():
    env = LoanSharkEnvironment()
    env.reset("lse-medium")
    env.state.stress_level = 0
    print(f"Start Cash: {env.state.cash}")
    for i in range(1, 7):
        env.state.stress_level = 0 # Reset to prevent spiral
        env.step(4)
        print(f"Step {i} Month {env.state.current_month} Cash: {env.state.cash}")
    assert env.state.cash == 28000
    env.state.stress_level = 0
    env.step(4)
    print(f"Step 7 Month {env.state.current_month} Cash: {env.state.cash}")
    assert env.state.current_month == 8
    assert env.state.cash == 27000

def test_hard_load():
    env = LoanSharkEnvironment()
    obs = env.reset("lse-hard")
    assert len(obs.loans) == 3

if __name__ == "__main__":
    run_test("test_spiral_lock", test_spiral_lock)
    run_test("test_medium_shock", test_medium_shock)
    run_test("test_hard_load", test_hard_load)
