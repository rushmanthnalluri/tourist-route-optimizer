from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app, raise_server_exceptions=False)

def test_chaos_empty_payload():
    for path in [
        "/api/search/run",
        "/api/csp/schedule",
        "/api/decision/utility",
        "/api/hybrid/plan",
    ]:
        response = client.post(path, json={})
        assert response.status_code == 422

def test_chaos_malformed_json():
    headers = {"Content-Type": "application/json"}
    for path in ["/api/search/run", "/api/csp/schedule", "/api/hybrid/plan"]:
        response = client.post(path, content=b"this is not valid json", headers=headers)
        assert response.status_code == 400 or response.status_code == 422

def test_chaos_extreme_goals_list():
    response = client.post(
        "/api/search/run",
        json={
            "start_id": 0,
            "goal_ids": list(range(1, 32)),
            "budget_inr": 2000.0,
            "max_time_min": 480.0,
        },
    )
    assert response.status_code == 422

def test_chaos_negative_numeric_inputs():
    response = client.post(
        "/api/search/run",
        json={
            "start_id": 0,
            "goal_ids": [1],
            "budget_inr": -50.0,
            "max_time_min": -10.0,
        },
    )
    assert response.status_code == 422

def test_chaos_huge_budget_time():
    response = client.post(
        "/api/search/run",
        json={
            "start_id": 0,
            "goal_ids": [1],
            "budget_inr": 9999999999.0,
            "max_time_min": 9999999999.0,
        },
    )
    assert response.status_code in [200, 422]

def test_chaos_invalid_id_boundaries():
    response = client.post(
        "/api/search/run",
        json={
            "start_id": -99999,
            "goal_ids": [1],
            "budget_inr": 2000.0,
            "max_time_min": 480.0,
        },
    )
    assert response.status_code == 422

def test_chaos_duplicate_goals():
    response = client.post(
        "/api/search/run",
        json={
            "start_id": 0,
            "goal_ids": [1, 1],
            "budget_inr": 2000.0,
            "max_time_min": 480.0,
        },
    )
    assert response.status_code == 422

def test_chaos_decision_extreme_values():
    response = client.post(
        "/api/decision/utility",
        json={
            "path": [0, 1],
            "total_cost": -100.0,
            "total_time_min": -50.0,
            "budget_inr": 100.0,
            "max_time_min": 200.0,
        },
    )
    assert response.status_code == 422

def test_chaos_non_existent_route():
    response = client.get("/api/not-a-real-endpoint")
    assert response.status_code == 404
