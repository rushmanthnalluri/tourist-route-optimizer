from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app, raise_server_exceptions=False)


def test_get_attractions_200():
    response = client.get("/api/attractions")
    assert response.status_code == 200
    assert len(response.json()) > 0


def test_get_attraction_200():
    response = client.get("/api/attractions/0")
    assert response.status_code == 200
    assert response.json()["name"] == "Charminar"


def test_get_attraction_404():
    response = client.get("/api/attractions/999")
    assert response.status_code == 404


def test_get_graph_200():
    response = client.get("/api/graph")
    assert response.status_code == 200
    assert "0" in response.json()


def test_get_distance_200():
    response = client.get("/api/distance/0/1")
    assert response.status_code == 200
    assert "straight_line_km" in response.json()


def test_get_distance_404():
    response = client.get("/api/distance/0/999")
    assert response.status_code == 404


def test_search_200():
    response = client.post(
        "/api/search/run",
        json={
            "start_id": 0,
            "goal_ids": [1],
            "budget_inr": 2000.0,
            "max_time_min": 480.0,
        },
    )
    assert response.status_code == 200
    assert "path" in response.json()


def test_search_422_invalid_goal():
    response = client.post(
        "/api/search/run",
        json={
            "start_id": 0,
            "goal_ids": [999],
            "budget_inr": 2000.0,
            "max_time_min": 480.0,
        },
    )
    assert response.status_code == 422


def test_search_422_negative_budget():
    response = client.post(
        "/api/search/run",
        json={
            "start_id": 0,
            "goal_ids": [1],
            "budget_inr": -100.0,
            "max_time_min": 480.0,
        },
    )
    assert response.status_code == 422


def test_search_422_invalid_cost_mode():
    response = client.post(
        "/api/search/run",
        json={
            "start_id": 0,
            "goal_ids": [1],
            "cost_mode": "fastest",
        },
    )
    assert response.status_code == 422


def test_csp_200():
    response = client.post(
        "/api/csp/schedule",
        json={"attraction_ids": [0, 1], "budget_inr": 2000.0, "max_time_min": 480.0},
    )
    assert response.status_code == 200
    assert "schedule" in response.json()


def test_csp_422():
    response = client.post(
        "/api/csp/schedule",
        json={
            "attraction_ids": [],
            "budget_inr": 2000.0,
            "max_time_min": 480.0,
        },
    )
    assert response.status_code == 422


def test_decision_utility_200():
    response = client.post(
        "/api/decision/utility",
        json={
            "path": [0, 1],
            "total_cost": 50.0,
            "total_time_min": 120.0,
            "budget_inr": 2000.0,
            "max_time_min": 480.0,
        },
    )
    assert response.status_code == 200


def test_hybrid_200():
    response = client.post(
        "/api/hybrid/plan",
        json={
            "start_id": 0,
            "goal_ids": [1],
            "budget_inr": 2000.0,
            "max_time_min": 480.0,
        },
    )
    assert response.status_code == 200


def test_global_exception_500(monkeypatch):
    def mock_fail(*args, **kwargs):
        raise ValueError("Simulated unexpected crash")

    monkeypatch.setattr(
        "backend.algorithms.co6_hybrid.HybridTouristPlanner.run", mock_fail
    )

    response = client.post(
        "/api/hybrid/plan",
        json={
            "start_id": 0,
            "goal_ids": [1],
            "budget_inr": 2000.0,
            "max_time_min": 480.0,
        },
    )
    assert response.status_code == 500
    assert "Internal server error occurred." in response.text


def test_search_all_algorithms():
    for algo in ["bfs", "dfs", "ucs", "greedy", "idastar"]:
        res = client.post(
            "/api/search/run", json={"start_id": 0, "goal_ids": [1], "algorithm": algo}
        )
        assert res.status_code == 200


def test_csp_min_conflicts():
    res = client.post(
        "/api/csp/schedule",
        json={"attraction_ids": [0, 1], "algorithm": "min_conflicts"},
    )
    assert res.status_code == 200


def test_decision_minimax():
    res = client.post("/api/decision/minimax", json={"attractions": [0, 1]})
    assert res.status_code == 200


def test_decision_expected_utility():
    res = client.post("/api/decision/expected-utility", json={"attraction_ids": [0, 1]})
    assert res.status_code == 200


def test_decision_rejects_invalid_ids_and_ranges():
    res = client.post(
        "/api/decision/utility",
        json={"path": [999], "total_cost": 0, "total_time_min": 10},
    )
    assert res.status_code == 422

    res = client.post("/api/decision/minimax", json={"attractions": [0], "depth_limit": 99})
    assert res.status_code == 422

    res = client.post(
        "/api/decision/expected-utility",
        json={"attraction_ids": [0], "weather_prob_rain": 2},
    )
    assert res.status_code == 422


def test_prob_bayes():
    res = client.post("/api/probabilistic/bayes-update", json={"attraction_id": 0})
    assert res.status_code == 200


def test_probabilistic_rejects_invalid_inputs():
    res = client.post("/api/probabilistic/bayes-update", json={"attraction_id": 999})
    assert res.status_code == 422

    res = client.post(
        "/api/probabilistic/infer",
        json={"evidence": {"weather": "sunny"}, "method": "bogus"},
    )
    assert res.status_code == 422

    res = client.post(
        "/api/probabilistic/infer",
        json={"evidence": {"weather": "sunny"}, "method": "rejection", "n_samples": 50001},
    )
    assert res.status_code == 422


def test_prob_infer():
    for m in ["exact", "rejection", "likelihood_weighting"]:
        res = client.post(
            "/api/probabilistic/infer",
            json={"evidence": {"weather": "sunny"}, "method": m},
        )
        assert res.status_code == 200


def test_prob_infer_normalizes_legacy_weather_and_holiday():
    res = client.post(
        "/api/probabilistic/infer",
        json={"evidence": {"weather": "rainy", "day_type": "holiday"}, "method": "exact"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["P(satisfaction=good)"] != 0.5
    assert body["evidence"]["weather"] == "rain"
    assert body["evidence"]["day_type"] == "weekend"


def test_prob_crowd():
    res = client.get("/api/probabilistic/crowd?weather=sunny&time_slot=afternoon&day_type=weekday")
    assert res.status_code == 200


def test_search_all_large_goals():
    res = client.post(
        "/api/search/run",
        json={"start_id": 0, "goal_ids": list(range(1, 10)), "algorithm": "all"},
    )
    assert res.status_code == 400
    assert "Compare All is limited to 8 goals" in res.json()["detail"]


def test_hybrid_422_invalid_cost_mode():
    res = client.post(
        "/api/hybrid/plan",
        json={"start_id": 0, "goal_ids": [1], "cost_mode": "fastest"},
    )
    assert res.status_code == 422
