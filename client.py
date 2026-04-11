import requests

class LoanSharkClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def reset(self, task_id):
        resp = requests.post(f"{self.base_url}/reset", json={"task_id": task_id})
        resp.raise_for_status()
        return resp.json()

    def step(self, action):
        resp = requests.post(f"{self.base_url}/step", json={"action": action})
        resp.raise_for_status()
        return resp.json()["observation"], resp.json()["reward"], resp.json()["done"]

    def state(self):
        resp = requests.get(f"{self.base_url}/state")
        resp.raise_for_status()
        return resp.json()

    def evaluate(self):
        resp = requests.post(f"{self.base_url}/evaluate")
        resp.raise_for_status()
        return resp.json()["score"]

if __name__ == "__main__":
    client = LoanSharkClient()
    print("Resetting to easy...")
    print(client.reset("lse-easy"))
