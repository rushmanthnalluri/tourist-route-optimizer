
from backend.algorithms.co3_csp import TouristCSP, min_conflicts

def test_csp_empty_domain():
    csp = TouristCSP(attraction_ids=[], budget_inr=1000, max_time_min=600)
    res = csp.solve()
    assert res["success"] is True

def test_csp_impossible_budget():
    csp = TouristCSP(attraction_ids=[0, 5], budget_inr=100, max_time_min=600)
    res = csp.solve()
    assert res["success"] is False
    assert "Budget exceeded" in res["failure_reason"]

def test_csp_impossible_time():
    csp = TouristCSP(attraction_ids=[0, 5], budget_inr=5000, max_time_min=100)
    res = csp.solve()
    assert res["success"] is False
    assert "Time exceeded" in res["failure_reason"]

def test_csp_must_morning_conflict():
    csp = TouristCSP(
        attraction_ids=[0, 5], budget_inr=5000, max_time_min=800, must_morning=[0, 5]
    )
    res = csp.solve()
    assert res["success"] is False

def test_min_conflicts_failure():
    res = min_conflicts([0, 5], budget_inr=10, max_time_min=600, max_steps=10)
    assert res["success"] is False

def test_csp_all_variables():
    csp = TouristCSP(attraction_ids=[0, 1, 2], budget_inr=1000, max_time_min=600)
    res = csp.solve()
    assert res["success"] is True

def test_is_consistent_edge_cases():
    csp = TouristCSP(attraction_ids=[0, 1, 2], budget_inr=1000, max_time_min=600)
    valid, reason = csp.is_consistent(999, "morning", {})
    assert not valid and "Unknown attraction" in reason

    valid, reason = csp.is_consistent(2, "morning", {0: "morning", 1: "morning"})
    assert not valid and "SLOT_FULL" in reason

    csp_budget = TouristCSP(attraction_ids=[0, 5], budget_inr=1000, max_time_min=600)
    valid, reason = csp_budget.is_consistent(5, "morning", {0: "morning"})
    assert not valid and "BUDGET" in reason

    csp_time = TouristCSP(attraction_ids=[0, 5], budget_inr=5000, max_time_min=400)
    valid, reason = csp_time.is_consistent(5, "morning", {0: "morning"})
    assert not valid and "TIME" in reason

    valid, reason = csp.is_consistent(0, "evening", {})
    assert not valid and "OPENING_HOURS" in reason
