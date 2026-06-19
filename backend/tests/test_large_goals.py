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
    if res.status_code == 200:
        data = res.json()
        print("Comparison Results:")
        for alg, stats in data.get("comparison", {}).items():
            print(f"  {alg}: success={stats['success']}, runtime={stats['runtime_ms']}ms, failure_reason={stats.get('failure_reason')}")
    else:
        print("Error:", res.text)
    
    assert res.status_code == 200

if __name__ == "__main__":
    test_search_large_goals()
