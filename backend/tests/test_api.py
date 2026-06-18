from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_rate_limit_and_root():
    res = client.get("/")
    assert res.status_code == 200

def test_search_router_missing():
    res = client.post(
        "/api/search/run",
        json={
            "start_id": 1,
            "goal_ids": [2, 2],
            "budget_inr": 1000,
            "max_time_min": 1000,
        },
    )
    assert res.status_code == 422

    res = client.post(
        "/api/search/run",
        json={
            "start_id": 999,
            "goal_ids": [2],
            "budget_inr": 1000,
            "max_time_min": 1000,
        },
    )
    assert res.status_code == 422

    res = client.post(
        "/api/search/run",
        json={
            "start_id": 1,
            "goal_ids": [2],
            "budget_inr": 1000,
            "max_time_min": 1000,
            "algorithm": "all",
        },
    )
    assert res.status_code == 200

    res = client.post(
        "/api/search/compare",
        json={"start_id": 1, "goal_ids": [2], "budget_inr": 1000, "max_time_min": 1000},
    )
    assert res.status_code == 200

def test_csp_router_missing():
    res = client.post("/api/csp/schedule", json={"attraction_ids": [999]})
    assert res.status_code == 422
    res = client.post("/api/csp/schedule", json={"attraction_ids": [1, 1]})
    assert res.status_code == 422

    res = client.get("/api/csp/domains/1")
    assert res.status_code == 200

def test_decision_router_missing():
    res = client.post("/api/decision/utility", json={"path": [999, 1]})
    assert res.status_code == 422

    res = client.post("/api/decision/utility", json={"path": [1, 1]})
    assert res.status_code == 422

    res = client.post("/api/decision/minimax", json={"attractions": [1, 2]})
    assert res.status_code == 200
    res = client.post("/api/decision/expected-utility", json={"attraction_ids": [1, 2]})
    assert res.status_code == 200

def test_hybrid_router_missing():
    res = client.post("/api/hybrid/plan", json={"start_id": 1, "goal_ids": [2, 2]})
    assert res.status_code == 422
    res = client.post("/api/hybrid/plan", json={"start_id": 999, "goal_ids": [2]})
    assert res.status_code == 422
    res = client.post("/api/hybrid/plan", json={"start_id": 1, "goal_ids": [999]})
    assert res.status_code == 422

def test_probabilistic_router_missing():
    res = client.post("/api/probabilistic/bayes-update", json={"measurements": [999]})
    assert res.status_code == 422
