import math

from backend.algorithms.co4_decision import (
    UtilityFunction,
    MinimaxSolver,
    expected_utility,
)


def test_utility_function_weights():
    uf = UtilityFunction(w_rating=1, w_cost=1, w_time=1, w_pref=1, w_crowd=1)
    assert math.isclose(uf.w_rating, 0.2)
    assert math.isclose(uf.w_cost, 0.2)
    assert math.isclose(uf.w_time, 0.2)
    assert math.isclose(uf.w_pref, 0.2)
    assert math.isclose(uf.w_crowd, 0.2)


def test_utility_function_evaluate():
    uf = UtilityFunction()
    res = uf.evaluate([0], total_cost=25, total_time_min=60)
    assert "utility" in res
    assert res["utility"] >= 0


def test_minimax_solver():
    uf = UtilityFunction()
    solver = MinimaxSolver(attractions=[0, 1], utility_fn=uf, depth_limit=2)
    result = solver.solve()
    assert result["minimax_value"] >= 0
    assert result["optimal_first_choice"] in ["Charminar", "Golconda Fort", "None"]


def test_expected_utility():
    uf = UtilityFunction()
    res = expected_utility([0], uf, weather_prob_rain=0.5)
    assert len(res["results"]) == 1
    item = res["results"][0]
    assert item["utility_rain"] <= item["expected_utility"] <= item["utility_sunny"]
