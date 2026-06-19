import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.algorithms.co2_search import greedy, TouristProblem
from backend.data.hyderabad_attractions import ATTRACTIONS

# 24 goals
goals = [a.id for a in ATTRACTIONS][1:25]
prob = TouristProblem(
    start_id=0,
    goal_ids=goals,
    budget_inr=1000000,
    max_time_min=1000000,
)

res = greedy(prob)
max_depth = max([t.get('depth', 0) for t in res.trace]) if res.trace else 0
print(f"Greedy success: {res.success} {res.runtime_ms}ms")
print(f"Expanded: {res.nodes_expanded}, Generated: {res.nodes_generated}, Peak: {res.peak_frontier_size}, Max Depth: {max_depth}")
