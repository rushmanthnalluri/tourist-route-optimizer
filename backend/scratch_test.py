import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from algorithms.co2_search import astar, dfs, bfs, ucs, idastar, TouristProblem

problem = TouristProblem(
    start_id=1,
    goal_ids=[2, 3, 5],
    must_visit=[2, 3, 5],
    budget_inr=20000.0,
    max_time_min=6000.0,
)

for algo in [idastar]:
    t0 = time.time()
    res = algo(problem, "distance")
    t1 = time.time()
    print(f"{algo.__name__} success: {res.success} {(t1-t0)*1000:.4f}ms, nodes: {res.nodes_expanded}")
    print(f"{algo.__name__} success: {res.success} {(t1-t0)*1000:.4f}ms, nodes: {res.nodes_expanded}")
    print(f"{algo.__name__} success: {res.success} {(t1-t0)*1000:.4f}ms, nodes: {res.nodes_expanded}")
