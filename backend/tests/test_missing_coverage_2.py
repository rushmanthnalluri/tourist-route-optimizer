from backend.algorithms.co2_search import (
    TouristProblem,
    astar,
    ucs,
    bfs,
    dfs,
    greedy,
    idastar,
    profile_all,
)
import pytest
from backend.data.hyderabad_attractions import Attraction, build_graph, get_attraction
from backend.data.attraction_models import AttractionModel
from backend.models.state import TouristState, SearchNode
from backend.data.memory_repository import MemoryAttractionRepository

def test_attraction_repr():
    a = Attraction(999, "Test", 0.0, 0.0, 0, 0, "Test", 5.0, 0, 24, "Desc")
    assert repr(a) == "Attraction(999: Test)"

def test_get_travel_time_zero_speed():
    with pytest.raises(ValueError, match="avg_speed_kmh must be strictly positive"):
        build_graph([], avg_speed_kmh=0.0)

def test_get_attraction():
    a = get_attraction(0)
    assert a.id == 0

def test_attraction_model_closing_time():
    with pytest.raises(ValueError, match="closing_time must be after opening_time"):
        AttractionModel(
            id=1,
            name="Test",
            lat=0.0,
            lng=0.0,
            entry_cost=0.0,
            duration_min=0,
            category="Test",
            rating=5.0,
            opening_time=10,
            closing_time=9,
            description="Desc",
        )

def test_state_repr():
    s = TouristState(0, frozenset([0]), 0.0, 0.0, 10.0)
    assert repr(s) == "State(at=0, visited=[0], time=0min, cost=Rs0)"

def test_search_node_lt():
    s1 = TouristState(0, frozenset([0]), 0.0, 0.0, 10.0)
    s2 = TouristState(1, frozenset([1]), 0.0, 0.0, 10.0)
    n1 = SearchNode(s1, None, None, 0.0, 1.0)
    n2 = SearchNode(s2, None, None, 0.0, 2.0)
    assert n1 < n2
    assert not n2 < n1

def test_memory_repo():
    repo = MemoryAttractionRepository()
    all_attr = repo.get_all_attractions()
    assert len(all_attr) > 0
    nbrs = repo.get_neighbors(0)
    assert isinstance(nbrs, list)
    all_nbrs = repo.get_graph()
    assert isinstance(all_nbrs, dict)

def test_co2_modes():
    p = TouristProblem(start_id=0, goal_ids=[1], budget_inr=5000, max_time_min=5000)
    assert astar(p, mode="cost").success
    assert astar(p, mode="time").success
    assert ucs(p, mode="cost").success
    assert ucs(p, mode="time").success
    assert greedy(p, mode="cost").success
    assert greedy(p, mode="time").success
    assert bfs(p, mode="cost").success
    assert dfs(p, mode="cost").success
    idastar(p, mode="cost")
    idastar(p, mode="time")
    prof = profile_all(p, mode="cost")
    assert "A*" in prof

def test_haversine_boundary():
    from backend.data.hyderabad_attractions import haversine

    assert haversine(0.0, 0.0, 0.0, 0.0) == 0.0

def test_csp_coverage():
    from backend.algorithms.co3_csp import TouristCSP, min_conflicts

    csp = TouristCSP([0, 1, 2], budget_inr=500, max_time_min=500, must_morning=[0])
    csp.solve(use_mrv=False, use_lcv=False, use_forward_checking=False, use_ac3=False)
    csp.solve(use_mrv=True, use_lcv=False, use_forward_checking=True, use_ac3=False)
    csp.solve(use_mrv=False, use_lcv=True, use_forward_checking=False, use_ac3=True)
    min_conflicts([0, 1, 2], budget_inr=10, max_time_min=10, max_steps=5)

def test_decision_prob_coverage():
    from backend.algorithms.co4_decision import (
        MinimaxSolver,
        expected_utility,
        GameNode,
        UtilityFunction,
    )

    uf = UtilityFunction()
    ms = MinimaxSolver([0, 1, 2], uf)
    ms.solve()
    repr(GameNode([0, 1, 2], [], [], is_max=True, depth=0))
    repr(GameNode([0, 1, 2], [], [], is_max=False, depth=0))
    expected_utility([0, 1, 2], uf)

    from backend.algorithms.co5_probabilistic import (
        BayesianNetwork,
        rejection_sampling,
        likelihood_weighting,
    )

    bn = BayesianNetwork()
    rejection_sampling(bn, "satisfaction", {"weather": "rainy"}, 10)
    likelihood_weighting(bn, "satisfaction", {"weather": "rainy"}, 10)
