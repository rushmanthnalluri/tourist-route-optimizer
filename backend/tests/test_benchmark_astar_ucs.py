import random
from backend.data.hyderabad_attractions import ATTRACTIONS
from backend.algorithms.co2_search import TouristProblem, astar, ucs


def test_run_benchmark(iterations=20, max_goals=3):
    attraction_ids = [a.id for a in ATTRACTIONS]

    mismatches = 0
    valid_paths = 0

    print(f"Starting A* vs UCS Optimality Benchmark for {iterations} cases...")

    for i in range(iterations):
        start_id = random.choice(attraction_ids)
        num_goals = random.randint(1, max_goals)
        goals = random.sample([x for x in attraction_ids if x != start_id], num_goals)

        budget = random.randint(100, 2000)
        max_time = random.randint(60, 600)
        cost_mode = random.choice(["distance", "cost", "time"])

        problem = TouristProblem(
            start_id=start_id, goal_ids=goals, budget_inr=budget, max_time_min=max_time
        )

        astar_res = astar(problem, cost_mode)

        ucs_res = ucs(problem, cost_mode)

        if astar_res.success != ucs_res.success:
            print(
                f"Mismatch in success status! Case {i}: A*={astar_res.success}, UCS={ucs_res.success}"
            )
            print(
                f"Problem: start={start_id}, goals={goals}, budget={budget}, time={max_time}, mode={cost_mode}"
            )
            mismatches += 1
            continue

        if astar_res.success:
            valid_paths += 1
            if cost_mode == "distance":
                astar_cost = astar_res.total_distance_km
                ucs_cost = ucs_res.total_distance_km
            elif cost_mode == "time":
                astar_cost = astar_res.total_time_min
                ucs_cost = ucs_res.total_time_min
            else:
                astar_cost = astar_res.total_cost
                ucs_cost = ucs_res.total_cost

            if abs(astar_cost - ucs_cost) > 0.01:
                print(f"Mismatch in cost! Case {i}: A*={astar_cost}, UCS={ucs_cost}")
                print(f"A* Path: {astar_res.path}")
                print(f"UCS Path: {ucs_res.path}")
                mismatches += 1

    print("Benchmark completed.")
    print(f"Total cases: {iterations}")
    print(f"Valid paths found: {valid_paths}")
    print(f"Mismatches: {mismatches}")

    assert (
        mismatches == 0
    ), f"Benchmark failed: found {mismatches} mismatches between A* and UCS!"
    print("A* Optimality verified.")


if __name__ == "__main__":
    test_run_benchmark(1000, 4)
