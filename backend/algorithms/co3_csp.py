from __future__ import annotations
from backend.data.hyderabad_attractions import ATTRACTION_MAP
import sys
import os
import random
import time
from typing import List, Dict, Tuple, Optional, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TIME_SLOTS = ["morning", "afternoon", "evening"]

SLOT_HOURS: Dict[str, Tuple[int, int]] = {
    "morning": (9, 12),
    "afternoon": (12, 17),
    "evening": (17, 21),
}

SLOT_START: Dict[str, float] = {"morning": 9.0, "afternoon": 12.0, "evening": 17.0}

class TouristCSP:
    def __init__(
        self,
        attraction_ids: List[int],
        budget_inr: float = 2000.0,
        max_time_min: float = 480.0,
        preferred_categories: Optional[List[str]] = None,
        must_morning: Optional[List[int]] = None,
        must_avoid_slots: Optional[Dict[int, List[str]]] = None,
    ):
        self.variables: List[int] = attraction_ids
        self.budget = budget_inr
        self.max_time = max_time_min
        self.preferred_categories = preferred_categories or []
        self.must_morning = must_morning or []
        self.must_avoid_slots = must_avoid_slots or {}

        self.domains: Dict[int, List[str]] = {}
        for aid in self.variables:
            self.domains[aid] = self._initial_domain(aid)

        self.trace: List[Dict[str, Any]] = []
        self.backtracks = 0
        self.constraint_checks = 0

    def _initial_domain(self, aid: int) -> List[str]:
        attr = ATTRACTION_MAP.get(aid)
        if attr is None:
            return list(TIME_SLOTS)
        valid = []
        for slot, (start, end) in SLOT_HOURS.items():
            open_overlap = min(attr.closing_time, end) - max(attr.opening_time, start)
            if open_overlap >= 0.5:
                valid.append(slot)
        avoid = self.must_avoid_slots.get(aid, [])
        valid = [s for s in valid if s not in avoid]
        if aid in self.must_morning:
            valid = [s for s in valid if s == "morning"] or valid
        return valid if valid else list(TIME_SLOTS)

    def _log(self, step: str, **kwargs) -> None:
        self.trace.append({"step": step, **kwargs})

    def is_consistent(
        self, aid: int, slot: str, assignment: Dict[int, str]
    ) -> Tuple[bool, str]:
        self.constraint_checks += 1
        attr = ATTRACTION_MAP.get(aid)
        if attr is None:
            return False, "Unknown attraction"

        slot_start, slot_end = SLOT_HOURS[slot]
        open_overlap = min(attr.closing_time, slot_end) - max(
            attr.opening_time, slot_start
        )
        if open_overlap < 0.5:
            return False, f"OPENING_HOURS: {attr.name} is not open enough during {slot}"

        slot_count = sum(
            1
            for assigned_id, assigned_slot in assignment.items()
            if assigned_slot == slot and assigned_id != aid
        )
        if slot_count >= 2:
            return False, f"SLOT_FULL: {slot} already has 2 attractions"

        current_cost = sum(
            ATTRACTION_MAP[i].entry_cost for i in assignment if i in ATTRACTION_MAP
        )
        if current_cost + attr.entry_cost > self.budget:
            return (
                False,
                f"BUDGET: adding Rs{attr.entry_cost} exceeds Rs{self.budget} budget",
            )

        current_time = sum(
            ATTRACTION_MAP[i].duration_min for i in assignment if i in ATTRACTION_MAP
        )
        if current_time + attr.duration_min > self.max_time:
            return (
                False,
                f"TIME: adding {attr.duration_min}min exceeds {self.max_time}min limit",
            )

        slot_limits = {"morning": 180, "afternoon": 300, "evening": 240}
        limit = slot_limits.get(slot)
        if limit is not None:
            if attr.duration_min > limit:
                return (
                    False,
                    f"SLOT_DURATION: {attr.name} duration {attr.duration_min}min exceeds {slot} limit of {limit}min",
                )

            slot_total_duration = sum(
                ATTRACTION_MAP[i].duration_min
                for i, s in assignment.items()
                if s == slot and i != aid and i in ATTRACTION_MAP
            )
            if slot_total_duration + attr.duration_min > limit:
                return (
                    False,
                    f"SLOT_DURATION: total duration in {slot} exceeds limit of {limit}min",
                )

        return True, "OK"

    def all_constraints_satisfied(self, assignment: Dict[int, str]) -> bool:
        slot_counts: Dict[str, int] = {}
        slot_durations: Dict[str, float] = {}
        slot_limits = {"morning": 180, "afternoon": 300, "evening": 240}
        total_cost = 0.0
        total_time = 0.0

        for aid, slot in assignment.items():
            slot_counts[slot] = slot_counts.get(slot, 0) + 1
            if slot_counts[slot] > 2:
                return False

            attr = ATTRACTION_MAP.get(aid)
            if attr is None:
                continue

            limit = slot_limits.get(slot, 9999)
            if attr.duration_min > limit:
                return False

            slot_durations[slot] = slot_durations.get(slot, 0.0) + attr.duration_min
            if slot_durations[slot] > limit:
                return False

            total_cost += attr.entry_cost
            total_time += attr.duration_min

        return total_cost <= self.budget and total_time <= self.max_time

    def mrv(self, assignment: Dict[int, str], domains: Dict[int, List[str]]) -> int:
        unassigned = [v for v in self.variables if v not in assignment]
        return min(unassigned, key=lambda v: len(domains.get(v, TIME_SLOTS)))

    def degree_heuristic(
        self, assignment: Dict[int, str], domains: Dict[int, List[str]]
    ) -> int:
        unassigned = [v for v in self.variables if v not in assignment]
        if not unassigned:
            raise ValueError("No unassigned variables")

        def degree(v: int) -> int:
            deg = 0
            dom_v = set(domains.get(v, TIME_SLOTS))
            for u in unassigned:
                if u != v:
                    dom_u = set(domains.get(u, TIME_SLOTS))
                    if dom_v.intersection(dom_u):
                        deg += 1
            return deg

        return max(unassigned, key=degree)

    def mrv_with_degree(
        self, assignment: Dict[int, str], domains: Dict[int, List[str]]
    ) -> int:
        unassigned = [v for v in self.variables if v not in assignment]
        if not unassigned:
            raise ValueError("No unassigned variables")
        min_remaining = min(len(domains.get(v, TIME_SLOTS)) for v in unassigned)
        mrv_tied = [
            v for v in unassigned if len(domains.get(v, TIME_SLOTS)) == min_remaining
        ]

        def degree(v: int) -> int:
            deg = 0
            dom_v = set(domains.get(v, TIME_SLOTS))
            for u in unassigned:
                if u != v:
                    dom_u = set(domains.get(u, TIME_SLOTS))
                    if dom_v.intersection(dom_u):
                        deg += 1
            return deg

        return max(mrv_tied, key=degree)

    def lcv(
        self, var: int, assignment: Dict[int, str], domains: Dict[int, List[str]]
    ) -> List[str]:
        def count_conflicts(slot: str) -> int:
            assigned_count = sum(1 for s in assignment.values() if s == slot)
            if assigned_count + 1 >= 2:
                conflicts = 0
                for other in self.variables:
                    if other == var or other in assignment:
                        continue
                    if slot in domains.get(other, list(TIME_SLOTS)):
                        conflicts += 1
                return conflicts
            return 0

        available = domains.get(var, list(TIME_SLOTS))
        return sorted(available, key=count_conflicts)

    def forward_check(
        self, var: int, slot: str, domains: Dict[int, List[str]]
    ) -> Optional[Dict[int, List[str]]]:
        new_domains = {k: list(v) for k, v in domains.items()}
        new_domains[var] = [slot]

        assigned_to_slot = sum(
            1 for d in new_domains.values() if len(d) == 1 and d[0] == slot
        )

        if assigned_to_slot >= 2:
            for other in self.variables:
                if (
                    other != var
                    and len(new_domains.get(other, [])) > 1
                    and slot in new_domains.get(other, [])
                ):
                    new_domains[other].remove(slot)

        if any(len(v) == 0 for v in new_domains.values()):
            return None

        for s in TIME_SLOTS:
            forced = sum(1 for d in new_domains.values() if len(d) == 1 and d[0] == s)
            if forced > 2:
                return None

        return new_domains

    def ac3(self, domains: Dict[int, List[str]]) -> Tuple[bool, Dict[int, List[str]]]:
        new_domains = {k: list(v) for k, v in domains.items()}

        queue = []
        for xi in self.variables:
            for xj in self.variables:
                if xi != xj:
                    queue.append((xi, xj))

        iterations = 0
        max_iter = len(queue) * 20

        def revise(xi: int, xj: int) -> bool:
            revised = False
            di = list(new_domains.get(xi, []))
            dj = list(new_domains.get(xj, []))

            for val_i in di:
                has_consistent = False
                for val_j in dj:
                    forced_to_val_i = sum(
                        1
                        for v in self.variables
                        if v != xi
                        and v != xj
                        and len(new_domains.get(v, [])) == 1
                        and new_domains[v][0] == val_i
                    )
                    if val_i != val_j:
                        forced_to_val_j = sum(
                            1
                            for v in self.variables
                            if v != xi
                            and v != xj
                            and len(new_domains.get(v, [])) == 1
                            and new_domains[v][0] == val_j
                        )
                        consistent = forced_to_val_i < 2 and forced_to_val_j < 2
                    else:
                        consistent = forced_to_val_i == 0

                    if consistent:
                        has_consistent = True
                        break

                if not has_consistent:
                    new_domains[xi].remove(val_i)
                    revised = True
            return revised

        while queue and iterations < max_iter:
            xi, xj = queue.pop(0)
            iterations += 1

            if revise(xi, xj):
                if len(new_domains[xi]) == 0:
                    return False, new_domains
                for xk in self.variables:
                    if xk != xi and xk != xj:
                        queue.append((xk, xi))

        return True, new_domains

    def backtrack(
        self,
        assignment: Dict[int, str],
        domains: Dict[int, List[str]],
        use_mrv: bool = True,
        use_lcv: bool = True,
        use_forward_checking: bool = True,
    ) -> Optional[Dict[int, str]]:
        if len(assignment) == len(self.variables):
            if self.all_constraints_satisfied(assignment):
                self._log("SOLUTION_FOUND", assignment=dict(assignment))
                return assignment
            return None

        if use_mrv:
            var = self.mrv_with_degree(assignment, domains)
        else:
            unassigned = [v for v in self.variables if v not in assignment]
            var = unassigned[0]

        if use_lcv:
            values = self.lcv(var, assignment, domains)
        else:
            values = domains.get(var, list(TIME_SLOTS))

        attr_name = ATTRACTION_MAP[var].name if var in ATTRACTION_MAP else str(var)
        self._log(
            "TRY_VARIABLE",
            var=var,
            name=attr_name,
            domain_size=len(values),
            values=values,
        )

        for slot in values:
            ok, reason = self.is_consistent(var, slot, assignment)
            if not ok:
                self._log("CONSTRAINT_FAIL", var=var, slot=slot, reason=reason)
                continue

            assignment[var] = slot
            self._log(
                "ASSIGN",
                var=var,
                name=attr_name,
                slot=slot,
                assignment_size=len(assignment),
            )

            new_domains: Optional[Dict[int, List[str]]] = domains
            if use_forward_checking:
                new_domains = self.forward_check(var, slot, domains)
                if new_domains is None:
                    del assignment[var]
                    self.backtracks += 1
                    self._log("BACKTRACK", var=var, reason="Forward check failed")
                    continue

            assert new_domains is not None
            result = self.backtrack(
                assignment, new_domains, use_mrv, use_lcv, use_forward_checking
            )
            if result is not None:
                return result

            del assignment[var]
            self.backtracks += 1
            self._log(
                "BACKTRACK", var=var, slot=slot, reason="No solution found in subtree"
            )

        return None

    def solve(
        self,
        use_mrv: bool = True,
        use_lcv: bool = True,
        use_forward_checking: bool = True,
        use_ac3: bool = True,
    ) -> Dict[str, Any]:
        start = time.perf_counter_ns()
        self.trace = []
        self.backtracks = 0
        self.constraint_checks = 0

        domains = {k: list(v) for k, v in self.domains.items()}

        total_cost = sum(
            ATTRACTION_MAP[i].entry_cost for i in self.variables if i in ATTRACTION_MAP
        )
        total_duration = sum(
            ATTRACTION_MAP[i].duration_min
            for i in self.variables
            if i in ATTRACTION_MAP
        )

        if total_cost > self.budget:
            self.trace.append({"step": "INIT", "assignment": {}})
            self.trace.append(
                {
                    "step": "CONSTRAINT_FAIL",
                    "reason": f"Budget exceeded: requires Rs{total_cost} > Rs{self.budget}",
                }
            )
            return {
                "success": False,
                "schedule": {},
                "trace": self.trace,
                "backtracks": 0,
                "constraint_checks": 0,
                "runtime_ms": 0.0,
                "failure_reason": f"Budget exceeded: requires Rs{total_cost} > Rs{self.budget}",
            }

        if total_duration > self.max_time:
            self.trace.append({"step": "INIT", "assignment": {}})
            self.trace.append(
                {
                    "step": "CONSTRAINT_FAIL",
                    "reason": f"Time exceeded: requires {total_duration}min > {self.max_time}min limit",
                }
            )
            return {
                "success": False,
                "schedule": {},
                "trace": self.trace,
                "backtracks": 0,
                "constraint_checks": 0,
                "runtime_ms": 0.0,
                "failure_reason": f"Time exceeded: requires {total_duration}min > {self.max_time}min limit",
            }

        if use_ac3:
            consistent, domains = self.ac3(domains)
            if not consistent:
                return {
                    "success": False,
                    "schedule": {},
                    "trace": self.trace,
                    "backtracks": self.backtracks,
                    "constraint_checks": self.constraint_checks,
                    "failure_reason": "AC-3 preprocessing failed",
                }
            self._log("AC3_COMPLETE", domains_after={k: v for k, v in domains.items()})

        assignment = self.backtrack({}, domains, use_mrv, use_lcv, use_forward_checking)

        runtime_ms = (time.perf_counter_ns() - start) / 1e6

        if assignment is None:
            return {
                "success": False,
                "schedule": {},
                "trace": self.trace,
                "backtracks": self.backtracks,
                "constraint_checks": self.constraint_checks,
                "runtime_ms": round(runtime_ms, 3),
                "failure_reason": "No valid schedule found",
            }

        schedule = {}
        total_cost = 0.0
        total_time = 0.0
        for aid, slot in assignment.items():
            attr = ATTRACTION_MAP.get(aid)
            if attr:
                total_cost += attr.entry_cost
                total_time += attr.duration_min
                schedule[aid] = {
                    "name": attr.name,
                    "slot": slot,
                    "entry_cost": attr.entry_cost,
                    "duration_min": attr.duration_min,
                    "category": attr.category,
                    "rating": attr.rating,
                }

        return {
            "success": True,
            "schedule": schedule,
            "total_cost": round(total_cost, 2),
            "total_time_min": round(total_time, 2),
            "trace": self.trace,
            "backtracks": self.backtracks,
            "constraint_checks": self.constraint_checks,
            "runtime_ms": round(runtime_ms, 3),
        }

def min_conflicts(
    attraction_ids: List[int],
    budget_inr: float = 2000.0,
    max_time_min: float = 480.0,
    max_steps: int = 1000,
    seed: int = 42,
) -> Dict[str, Any]:
    start_time = time.perf_counter_ns()
    random.seed(seed)

    total_cost_check = sum(
        ATTRACTION_MAP[i].entry_cost for i in attraction_ids if i in ATTRACTION_MAP
    )
    total_time_check = sum(
        ATTRACTION_MAP[i].duration_min for i in attraction_ids if i in ATTRACTION_MAP
    )
    if total_cost_check > budget_inr:
        trace = [
            {"step": "INIT", "assignment": {}},
            {
                "step": "CONSTRAINT_FAIL",
                "reason": f"Budget exceeded: requires Rs{total_cost_check} > Rs{budget_inr}",
            },
        ]
        return {
            "algorithm": "min_conflicts",
            "success": False,
            "schedule": {},
            "total_cost": total_cost_check,
            "total_time_min": total_time_check,
            "runtime_ms": 0.0,
            "final_conflicts": 1,
            "steps_taken": 0,
            "trace": trace,
            "failure_reason": f"Budget exceeded: requires Rs{total_cost_check} > Rs{budget_inr}",
        }
    if total_time_check > max_time_min:
        trace = [
            {"step": "INIT", "assignment": {}},
            {
                "step": "CONSTRAINT_FAIL",
                "reason": f"Time exceeded: requires {total_time_check}min > {max_time_min}min limit",
            },
        ]
        return {
            "algorithm": "min_conflicts",
            "success": False,
            "schedule": {},
            "total_cost": total_cost_check,
            "total_time_min": total_time_check,
            "runtime_ms": 0.0,
            "final_conflicts": 1,
            "steps_taken": 0,
            "trace": trace,
            "failure_reason": f"Time exceeded: requires {total_time_check}min > {max_time_min}min limit",
        }

    trace = []

    def count_conflicts_for(aid: int, slot: str, assignment: Dict[int, str]) -> int:
        conflicts = 0
        attr = ATTRACTION_MAP.get(aid)
        if attr is None:
            return 999

        slot_count = sum(
            1
            for other_id, other_slot in assignment.items()
            if other_id != aid and other_slot == slot
        )
        if slot_count >= 2:
            conflicts += slot_count - 1

        s_start, s_end = SLOT_HOURS[slot]
        open_overlap = min(attr.closing_time, s_end) - max(attr.opening_time, s_start)
        if open_overlap < 0.5:
            conflicts += 2

        slot_limits = {"morning": 180, "afternoon": 300, "evening": 240}
        limit = slot_limits.get(slot, 9999)
        if attr.duration_min > limit:
            conflicts += 2
        slot_total_duration = sum(
            ATTRACTION_MAP[i].duration_min
            for i, s in assignment.items()
            if s == slot and i != aid and i in ATTRACTION_MAP
        )
        if slot_total_duration + attr.duration_min > limit:
            conflicts += 2

        return conflicts

    def total_conflicts(assignment: Dict[int, str]) -> int:
        return sum(
            count_conflicts_for(aid, slot, assignment)
            for aid, slot in assignment.items()
        )

    assignment: Dict[int, str] = {
        aid: random.choice(TIME_SLOTS) for aid in attraction_ids
    }
    trace.append(
        {
            "step": "INIT",
            "assignment": dict(assignment),
            "conflicts": total_conflicts(assignment),
        }
    )

    for step in range(max_steps):
        conflicts = total_conflicts(assignment)
        if conflicts == 0:
            break

        conflicted = [
            aid
            for aid in attraction_ids
            if count_conflicts_for(aid, assignment[aid], assignment) > 0
        ]

        var = random.choice(conflicted)
        best_slot = min(
            TIME_SLOTS, key=lambda s: count_conflicts_for(var, s, assignment)
        )
        old_slot = assignment[var]
        assignment[var] = best_slot

        trace.append(
            {
                "step": step,
                "action": "REASSIGN",
                "var": var,
                "name": ATTRACTION_MAP[var].name if var in ATTRACTION_MAP else str(var),
                "old_slot": old_slot,
                "slot": best_slot,
                "conflicts_after": total_conflicts(assignment),
            }
        )

    final_conflicts = total_conflicts(assignment)
    success = final_conflicts == 0

    schedule = {}
    total_cost = 0.0
    total_time = 0.0
    for aid, slot in assignment.items():
        attr = ATTRACTION_MAP.get(aid)
        if attr:
            total_cost += attr.entry_cost
            total_time += attr.duration_min
            schedule[aid] = {
                "name": attr.name,
                "slot": slot,
                "entry_cost": attr.entry_cost,
                "duration_min": attr.duration_min,
                "category": attr.category,
                "rating": attr.rating,
            }

    runtime_ms = (time.perf_counter_ns() - start_time) / 1e6

    return {
        "algorithm": "min_conflicts",
        "success": success,
        "schedule": schedule,
        "total_cost": round(total_cost, 2),
        "total_time_min": round(total_time, 2),
        "runtime_ms": round(runtime_ms, 3),
        "final_conflicts": final_conflicts,
        "steps_taken": len(trace) - 1,
        "trace": trace,
        "failure_reason": (
            f"Failed with {final_conflicts} conflicts" if not success else None
        ),
    }

if __name__ == "__main__":
    print("=" * 65)
    print("CO3 — CSP Tourist Schedule Planner (Hyderabad)")
    print("=" * 65)

    selected = [0, 1, 3, 4, 9, 16]
    names = [ATTRACTION_MAP[i].name for i in selected]
    print(f"\nAttractions to schedule: {names}")

    csp = TouristCSP(
        attraction_ids=selected,
        budget_inr=500,
        max_time_min=420,
        preferred_categories=["historical", "religious"],
        must_morning=[4],
    )

    print("\n--- Initial Domains ---")
    for aid in selected:
        print(f"  {ATTRACTION_MAP[aid].name:<30} : {csp.domains[aid]}")

    print("\n--- Solving with Backtracking + MRV + LCV + Forward Checking + AC-3 ---")
    result = csp.solve(
        use_mrv=True, use_lcv=True, use_forward_checking=True, use_ac3=True
    )

    if result["success"]:
        print(f"\n[OK] SOLUTION FOUND!")
        print(f"   Total cost    : Rs{result['total_cost']}")
        print(f"   Total time    : {result['total_time_min']} min")
        print(f"   Backtracks    : {result['backtracks']}")
        print(f"   Constraint chk: {result['constraint_checks']}")
        print(f"   Runtime       : {result['runtime_ms']} ms\n")
        for aid, info in result["schedule"].items():
            print(
                f"   [{info['slot']:<10}] {info['name']:<30} Rs{info['entry_cost']} | {info['duration_min']}min"
            )
    else:
        print(f"[FAIL] FAILED: {result['failure_reason']}")

    print("\n--- Trace (first 10 steps) ---")
    for entry in result["trace"][:10]:
        print(f"  {entry}")

    print("\n" + "=" * 65)
    print("Min-Conflicts Local Search")
    print("=" * 65)
    mc = min_conflicts(selected, budget_inr=500, max_time_min=420)
    print(
        f"Success: {mc['success']}, Conflicts: {mc['final_conflicts']}, Steps: {mc['steps_taken']}"
    )
    for aid, info in mc["schedule"].items():
        print(f"  [{info['slot']:<10}] {info['name']}")
