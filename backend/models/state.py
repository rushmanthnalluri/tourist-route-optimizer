from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

@dataclass
class TouristState:
    current_id: int
    visited: frozenset[int]
    time_elapsed_min: float = 0.0
    cost_spent: float = 0.0
    day_hour: float = 9.0

    def __hash__(self) -> int:
        return hash((self.current_id, self.visited))

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TouristState):
            return False
        return self.current_id == other.current_id and self.visited == other.visited

    def __repr__(self) -> str:
        return (
            f"State(at={self.current_id}, visited={list(self.visited)}, "
            f"time={self.time_elapsed_min:.0f}min, cost=Rs{self.cost_spent:.0f})"
        )

    def time_slot(self) -> str:
        h = self.day_hour % 24
        if 6 <= h < 12:
            return "morning"
        elif 12 <= h < 17:
            return "afternoon"
        else:
            return "evening"

@dataclass
class Action:
    from_id: int
    to_id: int
    travel_km: float
    travel_time_min: float
    travel_cost: float

    def __repr__(self) -> str:
        return f"Action({self.from_id} -> {self.to_id}, {self.travel_km:.1f}km, {self.travel_time_min:.0f}min, Rs{self.travel_cost:.0f})"

@dataclass
class SearchNode:
    state: TouristState
    parent: Optional[SearchNode]
    action: Optional[Action]
    path_cost: float
    depth: int = 0
    heuristic: float = 0.0

    @property
    def f(self) -> float:
        return self.path_cost + self.heuristic

    def __lt__(self, other: SearchNode) -> bool:
        if self.f == other.f:
            return self.depth < other.depth
        return self.f < other.f

    def extract_path(self) -> List[int]:
        path: List[int] = []
        node: Optional[SearchNode] = self
        while node is not None:
            path.append(node.state.current_id)
            node = node.parent
        return list(reversed(path))

    def extract_actions(self) -> List[Action]:
        actions: List[Action] = []
        node: Optional[SearchNode] = self
        while node is not None and node.action is not None:
            actions.append(node.action)
            node = node.parent
        return list(reversed(actions))

@dataclass
class TouristProblem:
    start_id: int
    goal_ids: List[int]
    must_visit: List[int] = field(default_factory=list)
    budget_inr: float = 2000.0
    max_time_min: float = 480.0
    start_hour: float = 9.0
    preferred_categories: List[str] = field(default_factory=list)
    avoid_crowds: bool = False

    def initial_state(self) -> TouristState:
        from backend.data.hyderabad_attractions import ATTRACTION_MAP
        attr = ATTRACTION_MAP.get(self.start_id)
        entry_cost = attr.entry_cost if attr else 0.0
        duration = attr.duration_min if attr else 0.0
        return TouristState(
            current_id=self.start_id,
            visited=frozenset([self.start_id]),
            time_elapsed_min=duration,
            cost_spent=entry_cost,
            day_hour=self.start_hour + duration / 60.0,
        )

    def goal_test(self, state: TouristState) -> bool:
        targets = self.goal_ids if self.goal_ids else self.must_visit
        return all(g in state.visited for g in targets)

    def is_budget_ok(self, state: TouristState, extra_cost: float = 0) -> bool:
        return state.cost_spent + extra_cost <= self.budget_inr

    def is_time_ok(self, state: TouristState, extra_min: float = 0) -> bool:
        return state.time_elapsed_min + extra_min <= self.max_time_min

    def __repr__(self) -> str:
        return (
            f"TouristProblem(start={self.start_id}, goals={self.goal_ids}, "
            f"budget=Rs{self.budget_inr}, time={self.max_time_min}min)"
        )

@dataclass
class SearchResult:
    algorithm: str
    path: List[int]
    actions: List[Action]
    total_cost: float
    total_time_min: float
    total_distance_km: float
    nodes_expanded: int
    nodes_generated: int
    peak_frontier_size: int
    runtime_ms: float
    trace: List[Dict[str, Any]]
    success: bool
    failure_reason: str = ""

    def summary(self) -> str:
        status = (
            "[OK] SUCCESS" if self.success else f"[FAIL] FAILED ({self.failure_reason})"
        )
        return (
            f"\n{'='*60}\n"
            f"Algorithm  : {self.algorithm}\n"
            f"Status     : {status}\n"
            f"Path       : {' -> '.join(str(p) for p in self.path)}\n"
            f"Distance   : {self.total_distance_km:.2f} km\n"
            f"Time       : {self.total_time_min:.0f} min\n"
            f"Cost       : Rs{self.total_cost:.0f}\n"
            f"Expanded   : {self.nodes_expanded} nodes\n"
            f"Generated  : {self.nodes_generated} nodes\n"
            f"Peak front : {self.peak_frontier_size}\n"
            f"Runtime    : {self.runtime_ms:.2f} ms\n"
            f"{'='*60}"
        )

if __name__ == "__main__":
    print("CO1 — State / Problem Formulation Demo")
    print("=" * 50)

    prob = TouristProblem(
        start_id=0,
        goal_ids=[1, 9, 16],
        must_visit=[1, 9, 16],
        budget_inr=500,
        max_time_min=300,
        start_hour=9.0,
    )
    print(f"Problem: {prob}")

    s0 = prob.initial_state()
    print(f"Initial state: {s0}")
    print(f"Time slot: {s0.time_slot()}")
    print(f"Goal reached at start? {prob.goal_test(s0)}")

    action = Action(
        from_id=0, to_id=16, travel_km=0.1, travel_time_min=3, travel_cost=30
    )
    s1 = TouristState(
        current_id=16,
        visited=frozenset([0, 16]),
        time_elapsed_min=3 + 30,
        cost_spent=30,
        day_hour=9.55,
    )
    print(f"After action {action}: {s1}")
    print(f"State hash: {hash(s1)}")

    node = SearchNode(state=s0, parent=None, action=None, path_cost=0)
    child = SearchNode(
        state=s1, parent=node, action=action, path_cost=33, depth=1, heuristic=5.0
    )
    print(
        f"\nSearch node f(n)={child.f:.1f} (g={child.path_cost}, h={child.heuristic})"
    )
    print(f"Path: {child.extract_path()}")
