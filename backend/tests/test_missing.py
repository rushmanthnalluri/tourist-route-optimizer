from backend.models.state import (
    TouristState,
    Action,
    SearchNode,
    TouristProblem,
    SearchResult,
)
from backend.data.repository import AbstractAttractionRepository


def test_repository_abc():
    class DummyRepo(AbstractAttractionRepository):
        def get_all_attractions(self):
            super().get_all_attractions()

        def get_attraction(self, attraction_id):
            super().get_attraction(attraction_id)

        def get_neighbors(self, attraction_id):
            super().get_neighbors(attraction_id)

        def get_graph(self):
            super().get_graph()

    d = DummyRepo()
    d.get_all_attractions()
    d.get_attraction(1)
    d.get_neighbors(1)
    d.get_graph()


def test_state_missing():
    s = TouristState(
        current_id=1,
        visited=frozenset([1]),
        time_elapsed_min=10,
        cost_spent=10,
        day_hour=13.0,
    )
    assert s.time_slot() == "afternoon"
    s2 = TouristState(
        current_id=1,
        visited=frozenset([1]),
        time_elapsed_min=10,
        cost_spent=10,
        day_hour=18.0,
    )
    assert s2.time_slot() == "evening"
    s3 = TouristState(
        current_id=1,
        visited=frozenset([1]),
        time_elapsed_min=10,
        cost_spent=10,
        day_hour=8.0,
    )
    assert s3.time_slot() == "morning"

    assert s != "Not a state"

    a = Action(from_id=1, to_id=2, travel_km=1.0, travel_time_min=10, travel_cost=50)
    assert "Action(" in repr(a)

    sn1 = SearchNode(
        state=s, parent=None, action=None, path_cost=10, depth=1, heuristic=5
    )
    sn2 = SearchNode(
        state=s, parent=None, action=None, path_cost=10, depth=2, heuristic=5
    )
    assert sn1 < sn2

    from backend.algorithms.co2_search import profile_all

    tp = TouristProblem(start_id=1, goal_ids=[2])
    assert "TouristProblem(" in repr(tp)

    tp2 = TouristProblem(start_id=0, goal_ids=[1], budget_inr=5000, max_time_min=1000)
    res = profile_all(tp2, mode="distance")
    assert "BFS" in res

    sr1 = SearchResult("Alg", [1], [], 10, 10, 1.0, 1, 1, 1, 1.0, [], True, "")
    assert "[OK] SUCCESS" in sr1.summary()
    sr2 = SearchResult("Alg", [], [], 0, 0, 0, 0, 0, 0, 0, [], False, "Fail")
    assert "[FAIL] FAILED" in sr2.summary()
