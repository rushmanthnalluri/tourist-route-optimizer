from backend.algorithms.co4_decision import (
    UtilityFunction,
    expected_utility,
    MinimaxSolver,
    policy_selection,
    GameNode,
)


def test_expected_utility():
    uf = UtilityFunction()
    res = expected_utility([0], uf, weather_prob_rain=0.5)
    item = res["results"][0]
    assert item["utility_rain"] <= item["expected_utility"] <= item["utility_sunny"]


def test_utility_empty_path():
    uf = UtilityFunction()
    u = uf.evaluate([], 0, 0)
    assert u["utility"] == 0.0


def test_utility_zero_cost():
    uf = UtilityFunction()
    u = uf.evaluate([0], 0, 60)
    assert u["components"]["cost_efficiency"] == 1.0


def test_utility_preferred_categories():
    uf = UtilityFunction(preferred_categories=["historical", "heritage"])
    u = uf.evaluate([0], 50, 60)
    assert "preference_score" in u["components"]


def test_expected_utility_empty_path():
    uf = UtilityFunction()
    res = expected_utility([], uf, weather_prob_rain=0.5)
    assert len(res["results"]) == 0


def test_satisficing_policy_best_available():
    uf = UtilityFunction()
    res = policy_selection(
        [{"path": [0], "total_cost": 10, "total_time_min": 10}],
        uf,
        aspiration_level=0.99,
    )
    assert res["policy"] == "best_available"
    assert "accepted_route" in res


def test_satisficing_policy_no_routes():
    uf = UtilityFunction()
    res = policy_selection([], uf, aspiration_level=0.5)
    assert res["policy"] == "no_routes"


def test_minimax_empty():
    uf = UtilityFunction()
    solver = MinimaxSolver([0], uf, depth_limit=1)
    node = GameNode(
        attractions=[], collected=[], nature_disrupted=[], depth=0, is_max=True
    )
    val = solver.minimax(node, float("-inf"), float("inf"))
    assert val >= 0
