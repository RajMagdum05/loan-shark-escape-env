import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server.app import app  # noqa: E402


@pytest.fixture
def client():
    return TestClient(app)


def test_root_and_health(client):
    assert client.get("/").status_code == 200
    assert client.get("/health").json().get("status") == "healthy"


def test_reset_empty_body_defaults_easy(client):
    r = client.post("/reset", content=b"")
    assert r.status_code == 200
    body = r.json()
    assert body["task_id"] == "lse-easy"
    assert body["total_debt"] == 3000.0


def test_reset_with_task(client):
    r = client.post("/reset", json={"task_id": "lse-hard"})
    assert r.status_code == 200
    assert r.json()["task_id"] == "lse-hard"
    assert r.json()["total_debt"] == 8000.0


def test_state_after_reset(client):
    client.post("/reset", json={"task_id": "lse-medium"})
    s = client.get("/state").json()
    assert s["debt"] == 5000.0
    assert s["is_done"] is False


def test_hard_task_no_refinance_in_actions(client, no_random_shocks):
    r = client.post("/reset", json={"task_id": "lse-hard"})
    assert "refinance" not in r.json()["available_actions"]


def test_easy_includes_refinance(client, no_random_shocks):
    r = client.post("/reset", json={"task_id": "lse-easy"})
    assert "refinance" in r.json()["available_actions"]


def test_step_pay_and_evaluate_in_range(client, no_random_shocks):
    client.post("/reset", json={"task_id": "lse-easy"})
    for _ in range(25):
        st = client.get("/state").json()
        if st.get("is_done"):
            break
        client.post("/step", json={"action_type": "pay", "amount": 0.0})
    ev = client.post("/evaluate").json()
    assert "score" in ev
    assert "reward" in ev
    assert 0.0 <= float(ev["score"]) <= 1.0
    assert 0.0 <= float(ev["reward"]) <= 1.0


def test_refinance_blocked_on_hard(client, no_random_shocks):
    client.post("/reset", json={"task_id": "lse-hard"})
    # Force high score path still cannot refinance (action ignored for debt relief)
    r = client.post("/step", json={"action_type": "refinance", "amount": 0.0})
    assert r.status_code == 200
    assert "unavailable" in r.json()["message"].lower() or "refinance" in r.json()[
        "message"
    ].lower()
