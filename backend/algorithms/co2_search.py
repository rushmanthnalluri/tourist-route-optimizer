from __future__ import annotations
from backend.models.state import (
    TouristState,
    Action,
    SearchNode,
    TouristProblem,
    SearchResult,
)
import sys
import os
import time
import heapq
from collections import deque
from typing import List, Dict, Tuple, Optional, Any, Set
from backend.data.hyderabad_attractions import (
    ATTRACTION_MAP,
    get_neighbors,
    straight_line_distance,
)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SEARCH_TIMEOUT_SEC = float(os.getenv("SEARCH_TIMEOUT_SEC", 60.0))

# Hard cap on trace entries per algorithm run.
# Prevents 100MB+ JSON responses when many goals are selected.
MAX_TRACE_ENTRIES = 2000

def trace_append(trace: List[Dict], entry: Dict) -> None:
    """Append to trace only if under the cap. Silently drops when full."""
    if len(trace) < MAX_TRACE_ENTRIES:
        trace.append(entry)

COST_MODES = ("distance", "cost", "time")



def edge_cost(nbr: Tuple[int, float, float, float], mode: str) -> float:
    _, road_km, time_min, cost_inr = nbr
    if mode == "distance":
        return road_km
    elif mode == "cost":
        return cost_inr
    else:
        return time_min


def visit_cost(attr_id: int, mode: str) -> float:
    attr = ATTRACTION_MAP.get(attr_id)
    if attr is None:
        return 0.0
    if mode == "cost":
        return attr.entry_cost
    elif mode == "time":
        return attr.duration_min
    return 0.0


def heuristic(state: TouristState, problem: TouristProblem, mode: str) -> float:
    unvisited_goals = [g for g in problem.goal_ids if g not in state.visited]
    if not unvisited_goals:
        return 0.0

    max_dist = max(straight_line_distance(state.current_id, g) for g in unvisited_goals)

    if mode == "distance":
        return max_dist
    elif mode == "cost":
        return max(0.0, max_dist * 12.0 - 0.5)
    else:
        return (max_dist / 20.0) * 60.0

def greedy_heuristic(state: TouristState, problem: TouristProblem, mode: str) -> float:
    unvisited_goals = [g for g in problem.goal_ids if g not in state.visited]
    if not unvisited_goals:
        return 0.0
    
    min_dist = min(straight_line_distance(state.current_id, g) for g in unvisited_goals)
    
    # Strongly prefer states that have visited MORE goals
    penalty = len(unvisited_goals) * 10000.0

    if mode == "distance":
        return penalty + min_dist
    elif mode == "cost":
        return penalty + max(0.0, min_dist * 12.0 - 0.5)
    else:
        return penalty + (min_dist / 20.0) * 60.0


def expand(node: SearchNode, problem: TouristProblem, mode: str) -> List[SearchNode]:
    successors: List[SearchNode] = []
    state = node.state
    attr = ATTRACTION_MAP.get(state.current_id)
    if attr is None:
        return successors

    for nbr_id, road_km, time_min, cost_inr in get_neighbors(state.current_id):
        if nbr_id in state.visited:
            continue

        nbr_attr = ATTRACTION_MAP.get(nbr_id)
        if nbr_attr is None:
            continue

        arrival_hour = state.day_hour + time_min / 60.0
        wait_time_min = 0.0
        
        h = arrival_hour % 24
        if not nbr_attr.is_open(int(h)):
            if h < nbr_attr.opening_time:
                wait_hours = nbr_attr.opening_time - h
            else:
                wait_hours = (24.0 - h) + nbr_attr.opening_time
            wait_time_min = wait_hours * 60.0
            arrival_hour += wait_hours

        total_cost = cost_inr + nbr_attr.entry_cost
        if not problem.is_budget_ok(state, total_cost):
            continue

        total_time = time_min + wait_time_min + nbr_attr.duration_min
        if not problem.is_time_ok(state, total_time):
            continue

        new_visited = set(state.visited)
        if nbr_id in problem.goal_ids or nbr_id in problem.must_visit:
            new_visited.add(nbr_id)

        new_state = TouristState(
            current_id=nbr_id,
            visited=frozenset(new_visited),
            time_elapsed_min=state.time_elapsed_min + total_time,
            cost_spent=state.cost_spent + total_cost,
            day_hour=arrival_hour + nbr_attr.duration_min / 60.0,
        )

        action = Action(
            from_id=state.current_id,
            to_id=nbr_id,
            travel_km=road_km,
            travel_time_min=time_min + wait_time_min,
            travel_cost=cost_inr,
        )

        def get_edge_cost(mode: str) -> float:
            if mode == "distance":
                return road_km
            elif mode == "cost":
                return cost_inr
            else:
                return time_min + wait_time_min

        step_g = get_edge_cost(mode) + visit_cost(nbr_id, mode)
        new_g = node.path_cost + step_g
        h = heuristic(new_state, problem, mode)

        child = SearchNode(
            state=new_state,
            parent=node,
            action=action,
            path_cost=new_g,
            depth=node.depth + 1,
            heuristic=h,
        )
        successors.append(child)

    return successors


def make_trace_entry(
    step: int,
    algorithm: str,
    action: str,
    node_id: int,
    g: float,
    h: float,
    frontier_size: int,
    extra: Optional[Dict] = None,
) -> Dict[str, Any]:
    attr = ATTRACTION_MAP.get(node_id)
    entry: Dict[str, Any] = {
        "step": step,
        "algorithm": algorithm,
        "action": action,
        "node_id": node_id,
        "node_name": attr.name if attr else str(node_id),
        "g": round(g, 3),
        "h": round(h, 3),
        "f": round(g + h, 3),
        "frontier_size": frontier_size,
    }
    if extra:
        entry.update(extra)
    return entry


def build_result(
    algorithm: str,
    goal_node: Optional[SearchNode],
    nodes_expanded: int,
    nodes_generated: int,
    peak_frontier: int,
    start_ns: int,
    trace: List[Dict],
    mode: str,
) -> SearchResult:
    runtime_ms = (time.perf_counter_ns() - start_ns) / 1e6

    if goal_node is None:
        if runtime_ms >= 5000:
            failure_reason = f"Search timed out after {SEARCH_TIMEOUT_SEC} seconds to prevent server overload."
        else:
            failure_reason = "No path found within constraints"
        return SearchResult(
            algorithm=algorithm,
            path=[],
            actions=[],
            total_cost=0,
            total_time_min=0,
            total_distance_km=0,
            nodes_expanded=nodes_expanded,
            nodes_generated=nodes_generated,
            peak_frontier_size=peak_frontier,
            runtime_ms=runtime_ms,
            trace=trace,
            success=False,
            failure_reason=failure_reason,
        )

    path = goal_node.extract_path()
    actions = goal_node.extract_actions()
    total_dist = sum(a.travel_km for a in actions)
    total_time = goal_node.state.time_elapsed_min
    total_cost = goal_node.state.cost_spent

    return SearchResult(
        algorithm=algorithm,
        path=path,
        actions=actions,
        total_cost=total_cost,
        total_time_min=total_time,
        total_distance_km=total_dist,
        nodes_expanded=nodes_expanded,
        nodes_generated=nodes_generated,
        peak_frontier_size=peak_frontier,
        runtime_ms=runtime_ms,
        trace=trace,
        success=True,
    )


def bfs(problem: TouristProblem, mode: str = "distance") -> SearchResult:
    start_ns = time.perf_counter_ns()
    trace: List[Dict] = []
    root = SearchNode(
        state=problem.initial_state(),
        parent=None,
        action=None,
        path_cost=0,
        heuristic=heuristic(problem.initial_state(), problem, mode),
    )
    frontier: deque = deque([root])
    closed: Set[TouristState] = set([root.state])
    nodes_expanded = 0
    nodes_generated = 1
    peak_frontier = 1
    step = 0

    trace_append(trace, 
        make_trace_entry(
            step, "BFS", "INIT", root.state.current_id, 0, root.heuristic, 1
        )
    )

    while frontier:
        peak_frontier = max(peak_frontier, len(frontier))
        node = frontier.popleft()
        step += 1
        
        if (time.perf_counter_ns() - start_ns) / 1e9 > SEARCH_TIMEOUT_SEC:
            return build_result("BFS", None, nodes_expanded, nodes_generated, peak_frontier, start_ns, trace, mode)

        nodes_expanded += 1

        trace_append(trace, 
            make_trace_entry(
                step,
                "BFS",
                "EXPAND",
                node.state.current_id,
                node.path_cost,
                node.heuristic,
                len(frontier),
                {"depth": node.depth, "visited": list(node.state.visited)},
            )
        )

        if problem.goal_test(node.state):
            return build_result(
                "BFS",
                node,
                nodes_expanded,
                nodes_generated,
                peak_frontier,
                start_ns,
                trace,
                mode,
            )

        for child in expand(node, problem, mode):
            if child.state not in closed:
                closed.add(child.state)
                frontier.append(child)
                nodes_generated += 1
                trace_append(trace, 
                    make_trace_entry(
                        step,
                        "BFS",
                        "GENERATE",
                        child.state.current_id,
                        child.path_cost,
                        child.heuristic,
                        len(frontier),
                    )
                )

    return build_result(
        "BFS",
        None,
        nodes_expanded,
        nodes_generated,
        peak_frontier,
        start_ns,
        trace,
        mode,
    )


def dfs(
    problem: TouristProblem, mode: str = "distance", depth_limit: int = None
) -> SearchResult:
    # Scale depth limit by number of goals: each goal may need ~4 hops to reach.
    # Cap at 30 to prevent combinatorial explosion — with 30 depth, worst case is
    # still manageable. 60s timeout acts as the final backstop.
    if depth_limit is None:
        depth_limit = min(30, max(15, len(problem.goal_ids) * 5))

    start_ns = time.perf_counter_ns()
    trace: List[Dict] = []
    root = SearchNode(
        state=problem.initial_state(),
        parent=None,
        action=None,
        path_cost=0,
        heuristic=heuristic(problem.initial_state(), problem, mode),
    )
    frontier: List[SearchNode] = [root]
    closed: Set[TouristState] = set()
    nodes_expanded = 0
    nodes_generated = 1
    peak_frontier = 1
    step = 0

    trace_append(trace, 
        make_trace_entry(
            step, "DFS", "INIT", root.state.current_id, 0, root.heuristic, 1
        )
    )

    while frontier:
        peak_frontier = max(peak_frontier, len(frontier))
        node = frontier.pop()
        step += 1

        if node.state in closed:
            continue

        if (time.perf_counter_ns() - start_ns) / 1e9 > SEARCH_TIMEOUT_SEC:
            return build_result("DFS", None, nodes_expanded, nodes_generated, peak_frontier, start_ns, trace, mode)

        if node.depth > depth_limit:
            trace_append(trace, 
                make_trace_entry(
                    step,
                    "DFS",
                    "DEPTH_LIMIT",
                    node.state.current_id,
                    node.path_cost,
                    node.heuristic,
                    len(frontier),
                )
            )
            continue

        closed.add(node.state)
        nodes_expanded += 1

        trace_append(trace, 
            make_trace_entry(
                step,
                "DFS",
                "EXPAND",
                node.state.current_id,
                node.path_cost,
                node.heuristic,
                len(frontier),
                {"depth": node.depth, "visited": list(node.state.visited)},
            )
        )

        if problem.goal_test(node.state):
            return build_result(
                "DFS",
                node,
                nodes_expanded,
                nodes_generated,
                peak_frontier,
                start_ns,
                trace,
                mode,
            )

        for child in reversed(expand(node, problem, mode)):
            if child.state not in closed:
                frontier.append(child)
                nodes_generated += 1

    return build_result(
        "DFS",
        None,
        nodes_expanded,
        nodes_generated,
        peak_frontier,
        start_ns,
        trace,
        mode,
    )


def ucs(problem: TouristProblem, mode: str = "cost") -> SearchResult:
    start_ns = time.perf_counter_ns()
    trace: List[Dict] = []
    init_state = problem.initial_state()
    root = SearchNode(state=init_state, parent=None, action=None, path_cost=0)

    counter = 0
    heap: List[Tuple[float, int, SearchNode]] = [(0.0, counter, root)]
    closed: Dict[TouristState, float] = {}
    nodes_expanded = 0
    nodes_generated = 1
    peak_frontier = 1
    step = 0

    trace_append(trace, make_trace_entry(step, "UCS", "INIT", root.state.current_id, 0, 0, 1))

    while heap:
        peak_frontier = max(peak_frontier, len(heap))
        g, _, node = heapq.heappop(heap)
        step += 1

        if node.state in closed and closed[node.state] < g:
            continue

        if (time.perf_counter_ns() - start_ns) / 1e9 > SEARCH_TIMEOUT_SEC:
            return build_result("UCS", None, nodes_expanded, nodes_generated, peak_frontier, start_ns, trace, mode)


        closed[node.state] = g
        nodes_expanded += 1

        trace_append(trace, 
            make_trace_entry(
                step,
                "UCS",
                "EXPAND",
                node.state.current_id,
                node.path_cost,
                0,
                len(heap),
                {
                    "depth": node.depth,
                    "visited": list(node.state.visited),
                    "g": round(g, 2),
                },
            )
        )

        if problem.goal_test(node.state):
            return build_result(
                "UCS",
                node,
                nodes_expanded,
                nodes_generated,
                peak_frontier,
                start_ns,
                trace,
                mode,
            )

        for child in expand(node, problem, mode):
            if child.state not in closed or closed[child.state] > child.path_cost:
                counter += 1
                heapq.heappush(heap, (child.path_cost, counter, child))
                nodes_generated += 1
                trace_append(trace, 
                    make_trace_entry(
                        step,
                        "UCS",
                        "GENERATE",
                        child.state.current_id,
                        child.path_cost,
                        0,
                        len(heap),
                    )
                )

    return build_result(
        "UCS",
        None,
        nodes_expanded,
        nodes_generated,
        peak_frontier,
        start_ns,
        trace,
        mode,
    )


def greedy(problem: TouristProblem, mode: str = "distance") -> SearchResult:
    start_ns = time.perf_counter_ns()
    trace: List[Dict] = []
    init_state = problem.initial_state()
    h0 = greedy_heuristic(init_state, problem, mode)
    root = SearchNode(
        state=init_state, parent=None, action=None, path_cost=0, heuristic=h0
    )

    counter = 0
    heap: List[Tuple[float, int, SearchNode]] = [(h0, counter, root)]
    closed: Set[TouristState] = set()
    nodes_expanded = 0
    nodes_generated = 1
    peak_frontier = 1
    step = 0

    trace_append(trace, 
        make_trace_entry(step, "Greedy", "INIT", root.state.current_id, 0, h0, 1)
    )

    while heap:
        peak_frontier = max(peak_frontier, len(heap))
        h_val, _, node = heapq.heappop(heap)
        step += 1

        if node.state in closed:
            continue

        if (time.perf_counter_ns() - start_ns) / 1e9 > SEARCH_TIMEOUT_SEC:
            return build_result("Greedy", None, nodes_expanded, nodes_generated, peak_frontier, start_ns, trace, mode)

        closed.add(node.state)
        nodes_expanded += 1

        trace_append(trace, 
            make_trace_entry(
                step,
                "Greedy",
                "EXPAND",
                node.state.current_id,
                node.path_cost,
                node.heuristic,
                len(heap),
                {"depth": node.depth, "visited": list(node.state.visited)},
            )
        )

        if problem.goal_test(node.state):
            return build_result(
                "Greedy",
                node,
                nodes_expanded,
                nodes_generated,
                peak_frontier,
                start_ns,
                trace,
                mode,
            )

        for child in expand(node, problem, mode):
            if child.state not in closed:
                child.heuristic = greedy_heuristic(child.state, problem, mode)
                counter += 1
                heapq.heappush(heap, (child.heuristic, counter, child))
                nodes_generated += 1

    return build_result(
        "Greedy",
        None,
        nodes_expanded,
        nodes_generated,
        peak_frontier,
        start_ns,
        trace,
        mode,
    )


def astar(problem: TouristProblem, mode: str = "distance") -> SearchResult:
    start_ns = time.perf_counter_ns()
    trace: List[Dict] = []
    init_state = problem.initial_state()
    h0 = heuristic(init_state, problem, mode)
    root = SearchNode(
        state=init_state, parent=None, action=None, path_cost=0, heuristic=h0, depth=0
    )

    counter = 0
    heap: List[Tuple[float, float, int, SearchNode]] = [(root.f, 0.0, counter, root)]
    closed: Dict[TouristState, float] = {}
    nodes_expanded = 0
    nodes_generated = 1
    peak_frontier = 1
    step = 0

    trace_append(trace, make_trace_entry(step, "A*", "INIT", root.state.current_id, 0, h0, 1))

    while heap:
        peak_frontier = max(peak_frontier, len(heap))
        f_val, g_val, _, node = heapq.heappop(heap)
        step += 1

        if node.state in closed:
            continue

        if (time.perf_counter_ns() - start_ns) / 1e9 > SEARCH_TIMEOUT_SEC:
            return build_result("A*", None, nodes_expanded, nodes_generated, peak_frontier, start_ns, trace, mode)

        closed[node.state] = node.path_cost
        nodes_expanded += 1

        trace_append(trace, 
            make_trace_entry(
                step,
                "A*",
                "EXPAND",
                node.state.current_id,
                node.path_cost,
                node.heuristic,
                len(heap),
                {
                    "f": round(node.f, 3),
                    "depth": node.depth,
                    "visited": list(node.state.visited),
                    "heuristic_note": f"h={node.heuristic:.2f} (admissible: SL-dist to nearest goal)",
                },
            )
        )

        if problem.goal_test(node.state):
            return build_result(
                "A*",
                node,
                nodes_expanded,
                nodes_generated,
                peak_frontier,
                start_ns,
                trace,
                mode,
            )

        for child in expand(node, problem, mode):
            if child.state not in closed:
                counter += 1
                heapq.heappush(heap, (child.f, child.path_cost, counter, child))
                nodes_generated += 1
                trace_append(trace, 
                    make_trace_entry(
                        step,
                        "A*",
                        "GENERATE",
                        child.state.current_id,
                        child.path_cost,
                        child.heuristic,
                        len(heap),
                        {"f": round(child.f, 3)},
                    )
                )

    return build_result(
        "A*",
        None,
        nodes_expanded,
        nodes_generated,
        peak_frontier,
        start_ns,
        trace,
        mode,
    )


def _ida_search(
    node: SearchNode,
    bound: float,
    problem: TouristProblem,
    mode: str,
    trace: List[Dict],
    counts: Dict[str, int],
    iteration_closed: dict,
) -> Tuple[Optional[SearchNode], float]:
    f = node.f
    if f > bound:
        return None, f
    if problem.goal_test(node.state):
        return node, bound

    if (time.perf_counter_ns() - counts["start_ns"]) / 1e9 > SEARCH_TIMEOUT_SEC:
        return None, float("inf")

    if node.state in iteration_closed and iteration_closed[node.state] <= node.path_cost:
        return None, float("inf")
    iteration_closed[node.state] = node.path_cost

    minimum = float("inf")
    counts["expanded"] += 1
    trace_append(trace, 
        make_trace_entry(
            counts["step"],
            "IDA*",
            "EXPAND",
            node.state.current_id,
            node.path_cost,
            node.heuristic,
            0,
            {"bound": round(bound, 2), "f": round(f, 2)},
        )
    )
    counts["step"] += 1

    children = expand(node, problem, mode)
    children.sort(key=lambda c: c.f)
    for child in children:
        counts["generated"] += 1
        result, t = _ida_search(child, bound, problem, mode, trace, counts, iteration_closed)
        if result is not None:
            return result, bound
        minimum = min(minimum, t)

    return None, minimum


def idastar(
    problem: TouristProblem, mode: str = "distance", max_iterations: int = 2000
) -> SearchResult:
    start_ns = time.perf_counter_ns()
    trace: List[Dict] = []
    init_state = problem.initial_state()
    h0 = heuristic(init_state, problem, mode)
    root = SearchNode(
        state=init_state, parent=None, action=None, path_cost=0, heuristic=h0
    )

    bound = h0
    counts = {"expanded": 0, "generated": 1, "step": 0, "start_ns": start_ns}


    trace_append(trace, 
        make_trace_entry(
            0,
            "IDA*",
            "INIT",
            root.state.current_id,
            0,
            h0,
            0,
            {"initial_bound": round(bound, 2)},
        )
    )

    for iteration in range(max_iterations):
        trace_append(trace, 
            {
                "step": counts["step"],
                "algorithm": "IDA*",
                "action": "NEW_ITERATION",
                "iteration": iteration,
                "bound": round(bound, 2),
            }
        )
        iteration_closed = {}
        result, new_bound = _ida_search(root, bound, problem, mode, trace, counts, iteration_closed)
        if result is not None:
            return build_result(
                "IDA*",
                result,
                counts["expanded"],
                counts["generated"],
                0,
                start_ns,
                trace,
                mode,
            )
        if new_bound == float("inf"):
            break

        # Avoid float precision "small-step" problem by enforcing a minimum bound step
        eps = 0.25
        if mode == "cost":
            eps = 25.0
        elif mode == "time":
            eps = 10.0
        bound = max(new_bound, bound + eps)

    return build_result(
        "IDA*", None, counts["expanded"], counts["generated"], 0, start_ns, trace, mode
    )


def profile_all(problem: TouristProblem, mode: str = "distance") -> Dict[str, Any]:
    algorithms = [
        ("BFS", lambda: bfs(problem, mode)),
        ("DFS", lambda: dfs(problem, mode)),
        ("UCS", lambda: ucs(problem, mode)),
        ("Greedy", lambda: greedy(problem, mode)),
        ("A*", lambda: astar(problem, mode)),
    ]
    results: Dict[str, Any] = {}
    best_metric = float("inf")

    def get_metric(r: SearchResult) -> float:
        if mode == "distance": return r.total_distance_km
        if mode == "time": return r.total_time_min
        return r.total_cost

    for name, fn in algorithms:
        r = fn()
        metric_val = get_metric(r)
        results[name] = {
            "success": r.success,
            "path": r.path,
            "path_length": len(r.path),
            "total_cost": round(r.total_cost, 2),
            "total_time_min": round(r.total_time_min, 2),
            "total_distance_km": round(r.total_distance_km, 2),
            "metric_val": metric_val,
            "nodes_expanded": r.nodes_expanded,
            "nodes_generated": r.nodes_generated,
            "runtime_ms": round(r.runtime_ms, 3),
            "failure_reason": r.failure_reason,
        }
        if r.success and metric_val < best_metric:
            best_metric = metric_val

    for name in results:
        m = results[name]["metric_val"]
        if results[name]["success"] and best_metric > 0:
            gap = (m - best_metric) / best_metric * 100
            results[name]["optimality_gap_pct"] = round(gap, 1)
        elif results[name]["success"] and best_metric == 0:
            results[name]["optimality_gap_pct"] = 0.0
        else:
            results[name]["optimality_gap_pct"] = None

    return results


if __name__ == "__main__":
    print("=" * 65)
    print("CO2 — SEARCH ALGORITHMS — Tourist Route Finder (Hyderabad)")
    print("=" * 65)

    problem = TouristProblem(
        start_id=0,
        goal_ids=[1, 16, 4],
        must_visit=[1, 16, 4],
        budget_inr=600,
        max_time_min=400,
        start_hour=9.0,
    )
    print(f"\nProblem: {problem}")
    print(f"Start: {ATTRACTION_MAP[0].name}")
    print(f"Goals: {[ATTRACTION_MAP[g].name for g in problem.goal_ids]}\n")

    print("Running A* (distance mode)...")
    result = astar(problem, mode="distance")
    print(result.summary())
    if result.success:
        path_names = [ATTRACTION_MAP[p].name for p in result.path]
        print(f"  Path names: {' -> '.join(path_names)}")

    print("\n" + "=" * 65)
    print("EMPIRICAL COMPARISON — All Algorithms")
    print("=" * 65)
    profile = profile_all(problem, mode="distance")
    print(
        f"\n{'Algorithm':<10} {'Success':<8} {'Expanded':<10} {'Cost(km)':<10} {'Time(ms)':<10} {'Gap%'}"
    )
    print("-" * 60)
    for alg, data in profile.items():
        gap = (
            f"{data['optimality_gap_pct']:.1f}%"
            if data["optimality_gap_pct"] is not None
            else "N/A"
        )
        print(
            f"{alg:<10} {str(data['success']):<8} {data['nodes_expanded']:<10} "
            f"{data['total_distance_km']:<10} {data['runtime_ms']:<10} {gap}"
        )

    print("\n" + "=" * 65)
    print("A* TRACE (first 10 steps)")
    print("=" * 65)
    result2 = astar(problem, mode="distance")
    for entry in result2.trace[:10]:
        print(
            f"  Step {entry['step']:3d} | {entry['action']:<10} | "
            f"Node: {entry.get('node_name', ''):<25} | "
            f"g={entry['g']:.2f} h={entry['h']:.2f} f={entry['f']:.2f}"
        )
