from server.environment import LoanSharkEnvironment

def debug_medium():
    env = LoanSharkEnvironment()
    env.reset("lse-medium")
    print(f"Initial: Month={env.state.current_month}, Cash={env.state.cash}, Stress={env.state.stress_level}, Done={env.state.episode_done}")
    
    for i in range(1, 10):
        # Reset stress to prevent spiral lock
        env.state.stress_level = 0
        obs, reward, done = env.step(4)
        print(f"Step {i}: Month={env.state.current_month}, Cash={env.state.cash}, Stress={env.state.stress_level}, Done={done}, Reward={reward}")

if __name__ == "__main__":
    debug_medium()
