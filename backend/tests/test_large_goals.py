from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_search_large_goals():
    # Charminar is 0, rest are 1 to 24
    goal_ids = list(range(1, 25))
    print(f"Running compare with {len(goal_ids)} goals...")
    res = client.post(
        "/api/search/compare",
        json={"start_id": 0, "goal_ids": goal_ids, "budget_inr": 10000, "max_time_min": 10000},
    )
    print("Status:", res.status_code)
    assert res.status_code == 400
    assert "Compare All is limited" in res.json()["detail"]

if __name__ == "__main__":
    test_search_large_goals()
