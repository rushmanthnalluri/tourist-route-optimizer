
from backend.algorithms.co6_hybrid import HybridTouristPlanner

def test_stage3_empty_paths():
    pipeline = HybridTouristPlanner(start_id=0, goal_ids=[1])
    res = pipeline.stage3_csp([])
    assert res["success"] is False

def test_stage4_probabilistic_cap():
    pipeline = HybridTouristPlanner(start_id=0, goal_ids=[1])
    path_data = [{"path": list(range(10))}]
    res = pipeline.stage4_probabilistic(path_data)
    assert len(res["attraction_assessments"]) == 8

def test_stage4_decision_empty_paths():
    pipeline = HybridTouristPlanner(start_id=0, goal_ids=[1])
    res = pipeline.stage4_decision([], {})
    assert res["success"] is False

def test_stage6_ethics_empty_route():
    pipeline = HybridTouristPlanner(start_id=0, goal_ids=[1])
    res = pipeline.stage6_ethics({}, {"selected_route": None})
    assert res["explainability"] == [
        "No route selected — all constraints unsatisfiable."
    ]
