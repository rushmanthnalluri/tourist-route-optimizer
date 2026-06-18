import sys
import os
import time
from backend.algorithms.co3_csp import TouristCSP
from backend.algorithms.co4_decision import MinimaxSolver, UtilityFunction
from backend.algorithms.co2_search import idastar
from backend.models.state import TouristProblem

print("Testing deep recursion in large algorithms")
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test Minimax with depth=20
try:
    uf = UtilityFunction()
    solver = MinimaxSolver(
        attractions=list(range(25)),
        utility_fn=uf,
        depth_limit=20,
        budget_inr=5000,
        max_time_min=3000,
    )
    # solver.solve() might take too long if it doesn't crash, let's just do a deep CSP
except Exception as e:
    print("Minimax error", repr(e))

# Test CSP with 25 variables
try:
    csp = TouristCSP(attraction_ids=list(range(25)), budget_inr=10000, max_time_min=6000)
    csp.solve()
    print("CSP solved successfully")
except RecursionError:
    print("RecursionError caught in CSP")
except Exception as e:
    print("CSP error", repr(e))

# Test IDA* with far goals
try:
    problem = TouristProblem(
        start_id=0,
        goal_ids=[15, 20, 24], # some goals
        must_visit=[15, 20, 24],
        budget_inr=6000,
        max_time_min=4000,
        start_hour=9.0,
    )
    idastar(problem, mode="distance")
    print("IDA* solved successfully")
except RecursionError:
    print("RecursionError caught in IDA*")
except Exception as e:
    print("IDA* error", repr(e))
