import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoint(endpoint, method="GET", payload=None):
    url = f"{BASE_URL}{endpoint}"
    print(f"Testing {method} {url}...")
    try:
        if method == "GET":
            response = requests.get(url)
        else:
            response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code != 200:
            print(f"Error Response: {response.text}")
        else:
            print("Success!")
    except Exception as e:
        print(f"Request failed: {e}")
    print("-" * 20)

if __name__ == "__main__":
    # Test simple GET endpoints
    test_endpoint("/api/attractions")
    test_endpoint("/api/graph")
    test_endpoint("/api/attractions/1")
    test_endpoint("/api/distance/1/2")
    
    # Test search run
    search_payload = {"start_id": 1, "goal_ids": [2, 3], "algorithm": "astar"}
    test_endpoint("/api/search/run", method="POST", payload=search_payload)
    test_endpoint("/api/search/compare", method="POST", payload=search_payload)

    # Test CSP schedule
    csp_payload = {"attraction_ids": [1, 2, 3], "algorithm": "backtracking"}
    test_endpoint("/api/csp/schedule", method="POST", payload=csp_payload)

    # Test Decision
    utility_payload = {"path": [1, 2, 3], "total_cost": 500, "total_time_min": 120}
    test_endpoint("/api/decision/utility", method="POST", payload=utility_payload)
    
    minimax_payload = {"attractions": [1, 2, 3]}
    test_endpoint("/api/decision/minimax", method="POST", payload=minimax_payload)
    
    eu_payload = {"attraction_ids": [1, 2, 3]}
    test_endpoint("/api/decision/expected-utility", method="POST", payload=eu_payload)

    # Test Probabilistic
    bayes_req = {"attraction_id": 1}
    test_endpoint("/api/probabilistic/bayes-update", method="POST", payload=bayes_req)
    
    infer_payload = {"evidence": {"weather": "sunny"}, "method": "exact"}
    test_endpoint("/api/probabilistic/infer", method="POST", payload=infer_payload)
    
    test_endpoint("/api/probabilistic/crowd", method="POST", payload={})
    
    hmm_payload = {"observations": ["low", "medium"]}
    test_endpoint("/api/probabilistic/hmm", method="POST", payload=hmm_payload)

    # Test hybrid plan
    hybrid_payload = {
        "start_id": 1,
        "goal_ids": [2, 3],
        "budget_inr": 5000,
        "max_time_min": 600,
        "weather": "sunny"
    }
    test_endpoint("/api/hybrid/plan", method="POST", payload=hybrid_payload)
