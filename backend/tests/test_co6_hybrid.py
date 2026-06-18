
from backend.algorithms.co6_hybrid import HybridTouristPlanner

def test_hybrid_planner_success():
    planner = HybridTouristPlanner(
        start_id=0, goal_ids=[1], budget_inr=1000, max_time_min=600
    )
    result = planner.run()
    assert "success" in result
    assert result["success"] is True
    assert "final_recommendation" in result
