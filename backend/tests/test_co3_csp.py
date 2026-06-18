
from backend.algorithms.co3_csp import TouristCSP, min_conflicts

def test_csp_backtracking_finds_schedule():
    csp = TouristCSP(
        attraction_ids=[0, 4], budget_inr=500, max_time_min=300, must_morning=[4]
    )
    result = csp.solve()

    assert result["success"] is True
    assert 0 in result["schedule"]
    assert 4 in result["schedule"]
    assert result["schedule"][4]["slot"] == "morning"

def test_csp_fails_over_budget():
    csp = TouristCSP(attraction_ids=[5], budget_inr=1000, max_time_min=600)
    result = csp.solve()
    assert result["success"] is False
    assert "Budget exceeded" in result["failure_reason"]

def test_csp_fails_over_time():
    csp = TouristCSP(attraction_ids=[5], budget_inr=2000, max_time_min=300)
    result = csp.solve()
    assert result["success"] is False
    assert "Time exceeded" in result["failure_reason"]

def test_min_conflicts_finds_schedule():
    res = min_conflicts([0, 4], budget_inr=500, max_time_min=300)
    assert res["success"] is True
    assert 0 in res["schedule"]
    assert 4 in res["schedule"]
