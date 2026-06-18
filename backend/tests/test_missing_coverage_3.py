import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.state import TouristState, TouristProblem, SearchNode
from backend.data.hyderabad_attractions import ATTRACTION_MAP
from backend.algorithms.co2_search import (
    visit_cost,
    expand,
    bfs,
    dfs,
    greedy,
    idastar,
    profile_all,
)
from backend.algorithms.co3_csp import TouristCSP, min_conflicts
from backend.algorithms.co4_decision import (
    MinimaxSolver,
    expected_utility,
    UtilityFunction,
)
from backend.algorithms.co5_probabilistic import BayesianNetwork

client = TestClient(app, raise_server_exceptions=False)

def test_visit_cost_invalid_attraction():
    assert visit_cost(999, "cost") == 0.0

def test_expand_invalid_attraction():
    state = TouristState(current_id=999, visited=frozenset([999]))
    node = SearchNode(state=state, parent=None, action=None, path_cost=0.0)
    problem = TouristProblem(start_id=0, goal_ids=[1])
    assert expand(node, problem, "distance") == []

def test_expand_invalid_neighbor_attr(monkeypatch):
    state = TouristState(current_id=0, visited=frozenset([0]))
    node = SearchNode(state=state, parent=None, action=None, path_cost=0.0)
    problem = TouristProblem(start_id=0, goal_ids=[1])

    original_map = dict(ATTRACTION_MAP)
    monkeypatch.setattr(
        "backend.algorithms.co2_search.ATTRACTION_MAP",
        {k: v for k, v in original_map.items() if k != 1},
    )
    expand(node, problem, "distance")

def test_search_node_less_than_comparison():
    state = TouristState(current_id=0, visited=frozenset([0]))
    node1 = SearchNode(
        state=state, parent=None, action=None, path_cost=10.0, heuristic=5.0
    )
    node2 = SearchNode(
        state=state, parent=None, action=None, path_cost=20.0, heuristic=5.0
    )
    assert node1 < node2
    assert not (node2 < node1)

def test_bfs_dfs_greedy_failure_cases():
    problem = TouristProblem(start_id=0, goal_ids=[1], budget_inr=1.0)

    res_bfs = bfs(problem, "distance")
    assert not res_bfs.success

    res_dfs = dfs(problem, "distance")
    assert not res_dfs.success

    res_greedy = greedy(problem, "distance")
    assert not res_greedy.success

def test_bfs_dfs_closed_trigger(monkeypatch):
    state = TouristState(current_id=2, visited=frozenset([0, 2]))
    child1 = SearchNode(state=state, parent=None, action=None, path_cost=10)
    child2 = SearchNode(state=state, parent=None, action=None, path_cost=20)

    calls_bfs = 0

    def mock_expand_bfs(*args, **kwargs):
        nonlocal calls_bfs
        if calls_bfs == 0:
            calls_bfs += 1
            return [child1, child2]
        return []

    monkeypatch.setattr("backend.algorithms.co2_search.expand", mock_expand_bfs)
    problem = TouristProblem(start_id=0, goal_ids=[3])
    bfs(problem, "distance")

    calls_dfs = 0

    def mock_expand_dfs(*args, **kwargs):
        nonlocal calls_dfs
        if calls_dfs == 0:
            calls_dfs += 1
            return [child1, child2]
        return []

    monkeypatch.setattr("backend.algorithms.co2_search.expand", mock_expand_dfs)
    dfs(problem, "distance")

def test_dfs_depth_limit():
    problem = TouristProblem(
        start_id=0, goal_ids=[1, 2, 3], budget_inr=5000.0, max_time_min=5000.0
    )
    res = dfs(problem, "distance", depth_limit=1)
    assert not res.success

def test_idastar_no_path_exceeding_bound():
    problem = TouristProblem(start_id=0, goal_ids=[1], budget_inr=1.0)
    res = idastar(problem, "distance")
    assert not res.success

def test_profile_all_gap_none():
    problem = TouristProblem(start_id=0, goal_ids=[1], budget_inr=1.0)
    res = profile_all(problem, "distance")
    assert res["BFS"]["optimality_gap_pct"] is None

def test_csp_initial_domain_invalid_attraction():
    scheduler = TouristCSP(attraction_ids=[999])
    assert "morning" in scheduler.domains[999]

def test_csp_all_constraints_satisfied_edge():
    scheduler = TouristCSP(attraction_ids=[0, 1, 2])
    assignment = {0: "morning", 1: "morning", 2: "morning"}
    assert not scheduler.all_constraints_satisfied(assignment)

    assignment_invalid = {999: "morning"}
    assert scheduler.all_constraints_satisfied(assignment_invalid)

def test_csp_mrv_and_degree_heuristics():
    scheduler = TouristCSP(attraction_ids=[0, 1, 2])
    scheduler.mrv({}, scheduler.domains)
    scheduler.degree_heuristic({}, scheduler.domains)
    with pytest.raises(ValueError):
        scheduler.mrv_with_degree(
            {0: "morning", 1: "afternoon", 2: "evening"}, scheduler.domains
        )

def test_csp_forward_check_pruning():
    scheduler = TouristCSP(attraction_ids=[0, 1, 2])
    domains = {0: ["morning"], 1: ["morning"], 2: ["morning", "afternoon"]}
    res = scheduler.forward_check(0, "morning", domains)
    assert "morning" not in res[2]

def test_csp_backtrack_forward_check_fail():
    scheduler = TouristCSP(attraction_ids=[0, 1, 2], must_morning=[0, 1, 2])
    res = scheduler.solve()
    assert not res["success"]

def test_csp_ac3_prune_and_fail(monkeypatch):
    scheduler = TouristCSP(attraction_ids=[0, 1])
    monkeypatch.setattr(scheduler, "ac3", lambda doms: (False, {}))
    res = scheduler.solve()
    assert not res["success"]
    assert res["failure_reason"] == "AC-3 preprocessing failed"

def test_csp_backtrack_fails_constraint_satisfied():
    scheduler = TouristCSP(attraction_ids=[0, 1])
    scheduler.all_constraints_satisfied = MagicMock(return_value=False)
    res = scheduler.backtrack({0: "morning", 1: "afternoon"}, scheduler.domains)
    assert res is None

def test_csp_backtrack_fails_no_solution():
    scheduler = TouristCSP(attraction_ids=[0, 5], budget_inr=10.0)
    res = scheduler.solve()
    assert not res["success"]

def test_csp_min_conflicts_time_exceeded():
    res = min_conflicts([0, 1], max_time_min=1.0)
    assert not res["success"]
    assert "Time exceeded" in res["failure_reason"]

def test_csp_min_conflicts_invalid_attraction_and_conflicts():
    res = min_conflicts([999], max_steps=5)
    assert not res["success"]
    res_conf = min_conflicts([0, 1, 2, 3, 4], max_steps=2)

def test_minimax_no_attractions():
    uf = UtilityFunction()
    solver = MinimaxSolver(attractions=[], utility_fn=uf)
    res = solver.solve()
    assert res["minimax_value"] == 0.0

def test_expected_utility_invalid_attraction():
    uf = UtilityFunction()
    res = expected_utility([999], uf)
    assert len(res["results"]) == 0

def test_bn_infer_satisfaction_zero_probability():
    bn = BayesianNetwork()
    bn.cpt_weather = {"sunny": 0.0, "rainy": 0.0}
    res = bn.infer_satisfaction({})
    assert res["P(satisfaction=good)"] == 0.5

def test_hmm_router_endpoint():
    res = client.post(
        "/api/probabilistic/hmm", json={"observations": ["gps_stationary"]}
    )
    assert res.status_code == 200
    assert "belief_states" in res.json()

def test_forward_check_empty_domain_trigger():
    scheduler = TouristCSP(attraction_ids=[0, 1])
    domains = {0: ["morning"], 1: []}
    res = scheduler.forward_check(0, "morning", domains)
    assert res is None

def test_csp_backtrack_recursive_fail_trigger():
    scheduler = TouristCSP(attraction_ids=[0, 1])
    scheduler.all_constraints_satisfied = lambda assignment: False
    res = scheduler.backtrack(
        {}, scheduler.domains, use_mrv=False, use_lcv=False, use_forward_checking=False
    )
    assert res is None
