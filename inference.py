import os
from client import LoanSharkClient

def run_inference(task_id="lse-easy"):
    client = LoanSharkClient()
    obs = client.reset(task_id)
    print(f"Task Started: {task_id}")
    
    done = False
    total_reward = 0
    
    while not done:
        # Placeholder for LLM logic
        # For now, just a naive strategy: pay minimum (action 1)
        action = 1 
        
        obs, reward, done = client.step(action)
        total_reward += reward
        print(f"Action: {action}, Reward: {reward}, Stress: {obs['stress_level']}")
        
    print(f"Episode Finished. Total Reward: {total_reward}")

if __name__ == "__main__":
    run_inference()
