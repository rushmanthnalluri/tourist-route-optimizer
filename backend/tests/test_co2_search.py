import math

from backend.models.state import TouristProblem
from backend.algorithms.co2_search import (
    heuristic,
    astar,
    bfs,
    dfs,
    ucs,
    greedy,
    idastar,
)
from backend.data.hyderabad_attractions import straight_line_distance

def test_a_star_optimal_path():
    problem = TouristProblem(
        start_id=0, goal_ids=[16], budget_inr=1000, max_time_min=600
    )
    result = astar(problem, mode="distance")
    assert result.success is True
    assert 16 in result.path
    assert len(result.path) >= 2
    assert result.path[-1] == 16

def test_heuristic_admissibility():
    problem = TouristProblem(
        start_id=0, goal_ids=[1, 16], budget_inr=1000, max_time_min=600
    )
    state = problem.initial_state()
    h = heuristic(state, problem, mode="distance")

    d1 = straight_line_distance(0, 1)
    d16 = straight_line_distance(0, 16)
    expected_h = max(d1, d16)

    assert math.isclose(h, expected_h, rel_tol=1e-5)

    result = astar(problem, mode="distance")
    if result.success:
        assert result.total_distance_km >= h

def test_bfs_completeness():
    problem = TouristProblem(
        start_id=0, goal_ids=[4], budget_inr=2000, max_time_min=1000
    )
    result = bfs(problem)
    assert result.success is True

def test_dfs_finds_path():
    problem = TouristProblem(
        start_id=0, goal_ids=[4], budget_inr=2000, max_time_min=1000
    )
    result = dfs(problem)
    assert result.success is True

def test_ucs_finds_optimal_cost():
    problem = TouristProblem(
        start_id=0, goal_ids=[4], budget_inr=2000, max_time_min=1000
    )
    result = ucs(problem, mode="cost")
    assert result.success is True

def test_greedy_fast_but_suboptimal():
    problem = TouristProblem(
        start_id=0, goal_ids=[1, 4], budget_inr=2000, max_time_min=1000
    )
    res_greedy = greedy(problem, mode="distance")
    res_astar = astar(problem, mode="distance")

    assert res_greedy.success is True
    assert res_astar.success is True

    assert res_greedy.total_distance_km >= res_astar.total_distance_km

def test_ida_star_finds_path():
    problem = TouristProblem(
        start_id=0, goal_ids=[16], budget_inr=1000, max_time_min=600
    )
    result = idastar(problem, mode="distance")
    assert result.success is True
    assert result.path[-1] == 16
