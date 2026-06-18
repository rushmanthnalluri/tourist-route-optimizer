from __future__ import annotations
from backend.algorithms.co5_probabilistic import BayesianNetwork, TouristHMM, bayes_update_crowd
from backend.algorithms.co4_decision import (
    UtilityFunction,
    MinimaxSolver,
    expected_utility,
    policy_selection,
)
from backend.algorithms.co3_csp import TouristCSP, min_conflicts
from backend.algorithms.co2_search import astar, bfs, ucs
from backend.algorithms.co1_peas_agent import (
    TouristAgent,
)
from backend.models.state import TouristProblem, SearchResult
from backend.data.hyderabad_attractions import (
    ATTRACTION_MAP,
)
import sys
import os
import time
from typing import List, Dict, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class HybridTouristPlanner:
    def __init__(
        self,
        start_id: int,
        goal_ids: List[int],
        budget_inr: float = 2000.0,
        max_time_min: float = 480.0,
        start_hour: float = 9.0,
        preferred_categories: Optional[List[str]] = None,
        avoid_crowds: bool = False,
        weather: str = "sunny",
        day_type: str = "weekday",
        cost_mode: str = "distance",
    ):
        self.problem = TouristProblem(
            start_id=start_id,
            goal_ids=goal_ids,
            must_visit=goal_ids,
            budget_inr=budget_inr,
            max_time_min=max_time_min,
            start_hour=start_hour,
            preferred_categories=preferred_categories or [],
            avoid_crowds=avoid_crowds,
        )
        self.weather = weather
        self.day_type = day_type
        self.cost_mode = cost_mode
        self.preferred_categories = preferred_categories or []

        self.agent = TouristAgent(self.problem)
        self.bn = BayesianNetwork()
        self.hmm = TouristHMM()
        self.uf = UtilityFunction(
            preferred_categories=preferred_categories,
            budget_inr=budget_inr,
            max_time_min=max_time_min,
        )

        self.pipeline_trace: List[Dict[str, Any]] = []
        self.start_ns = time.perf_counter_ns()

    def _log(self, stage: str, **kwargs) -> None:
        elapsed = (time.perf_counter_ns() - self.start_ns) / 1e6
        self.pipeline_trace.append(
            {"stage": stage, "elapsed_ms": round(elapsed, 2), **kwargs}
        )

    def stage1_setup(self) -> Dict[str, Any]:
        init_state = self.problem.initial_state()
        perception = self.agent.perceive(init_state)
        rules_fired = self.agent.kb.fire_rules(init_state, self.problem)
        rule_advice = self.agent.kb.get_rule_advice(init_state, self.problem)

        result: Dict[str, Any] = {
            "peas": self.agent.get_peas(),
            "environment_type": self.agent.get_environment_type(),
            "initial_perception": perception,
            "rules_fired": rules_fired,
            "rule_advice": rule_advice,
            "problem": {
                "start_id": self.problem.start_id,
                "start_name": (
                    ATTRACTION_MAP[self.problem.start_id].name
                    if self.problem.start_id in ATTRACTION_MAP
                    else ""
                ),
                "goal_ids": self.problem.goal_ids,
                "goal_names": [
                    ATTRACTION_MAP[g].name
                    for g in self.problem.goal_ids
                    if g in ATTRACTION_MAP
                ],
                "budget_inr": self.problem.budget_inr,
                "max_time_min": self.problem.max_time_min,
            },
        }
        self._log(
            "CO1_SETUP",
            rules_fired=rules_fired,
            goal_names=result["problem"]["goal_names"],
            start_name=result["problem"]["start_name"],
        )
        return result

    def stage2_search(self) -> Dict[str, Any]:
        self._log("CO2_SEARCH_START", algorithm="A*", cost_mode=self.cost_mode)

        astar_result = astar(self.problem, self.cost_mode)
        bfs_result = bfs(self.problem, self.cost_mode)
        ucs_result = ucs(self.problem, self.cost_mode)

        candidate_paths = []
        for name, res in [
            ("A*", astar_result),
            ("BFS", bfs_result),
            ("UCS", ucs_result),
        ]:
            if res.success:
                candidate_paths.append(
                    {
                        "algorithm": name,
                        "path": res.path,
                        "path_names": [
                            ATTRACTION_MAP[p].name
                            for p in res.path
                            if p in ATTRACTION_MAP
                        ],
                        "total_cost": res.total_cost,
                        "total_time_min": res.total_time_min,
                        "total_distance_km": res.total_distance_km,
                        "nodes_expanded": res.nodes_expanded,
                        "runtime_ms": res.runtime_ms,
                        "trace": res.trace[:15],
                    }
                )

        profile_comparison = {}
        for name, res in [
            ("A*", astar_result),
            ("BFS", bfs_result),
            ("UCS", ucs_result),
        ]:
            profile_comparison[name] = {
                "success": res.success,
                "nodes_expanded": res.nodes_expanded,
                "total_distance_km": round(res.total_distance_km, 2),
                "runtime_ms": round(res.runtime_ms, 2),
                "optimality_gap_pct": None,
            }
        def get_metric_value(res: SearchResult, mode: str) -> float:
            if mode == "distance":
                return res.total_distance_km
            elif mode == "cost":
                return res.total_cost
            else:
                return res.total_time_min

        astar_metric = (
            get_metric_value(astar_result, self.cost_mode)
            if astar_result.success
            else None
        )
        for name in profile_comparison:
            d = profile_comparison[name]
            res = {"A*": astar_result, "BFS": bfs_result, "UCS": ucs_result}[name]
            if d["success"] and astar_metric and astar_metric > 0:
                metric_val = get_metric_value(res, self.cost_mode)
                gap = (metric_val - astar_metric) / astar_metric * 100
                d["optimality_gap_pct"] = round(gap, 1)

        result = {
            "candidate_paths": candidate_paths,
            "best_path": candidate_paths[0] if candidate_paths else None,
            "profile_comparison": profile_comparison,
            "astar_trace": astar_result.trace[:20],
        }
        self._log(
            "CO2_SEARCH_DONE",
            found=len(candidate_paths),
            best_algorithm=(
                candidate_paths[0]["algorithm"] if candidate_paths else "None"
            ),
        )
        return result

    def stage3_csp(self, paths: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._log("CO3_CSP_START")

        if not paths or paths[0] is None:
            return {
                "success": False,
                "schedules": [],
                "failure_reason": "No paths from search",
            }

        selected_path = paths[0]["path"]

        must_morning = [
            aid
            for aid in selected_path
            if aid in ATTRACTION_MAP and ATTRACTION_MAP[aid].category == "religious"
        ]

        csp = TouristCSP(
            attraction_ids=selected_path,
            budget_inr=self.problem.budget_inr,
            max_time_min=self.problem.max_time_min,
            preferred_categories=self.preferred_categories,
            must_morning=must_morning,
        )

        csp_result = csp.solve(
            use_mrv=True, use_lcv=True, use_forward_checking=True, use_ac3=True
        )

        mc_result = min_conflicts(
            selected_path, self.problem.budget_inr, self.problem.max_time_min
        )

        result = {
            "csp_result": csp_result,
            "min_conflicts_result": mc_result,
            "variables": selected_path,
            "variable_names": [
                ATTRACTION_MAP[a].name for a in selected_path if a in ATTRACTION_MAP
            ],
        }
        self._log(
            "CO3_CSP_DONE",
            success=csp_result["success"],
            backtracks=csp_result.get("backtracks", 0),
        )
        return result

    def stage4_probabilistic(self, paths: List[Dict[str, Any]]) -> Dict[str, Any]:
        self._log("CO5_PROB_START", weather=self.weather, day_type=self.day_type)

        time_slot = "morning" if self.problem.start_hour < 12 else "afternoon"

        bn_inference = self.bn.infer_satisfaction(
            {
                "weather": self.weather,
                "time_slot": time_slot,
                "day_type": self.day_type,
            }
        )

        crowd_inference = self.bn.infer_crowd_given_evidence(
            weather=self.weather,
            time_slot=time_slot,
            day_type=self.day_type,
        )

        seen_aids: set = set()
        attraction_assessments = []
        for path in paths[:2]:
            for aid in path.get("path", []):
                if aid in seen_aids or aid not in ATTRACTION_MAP:
                    continue
                seen_aids.add(aid)
                crowd_update = bayes_update_crowd(
                    time_slot, self.day_type, self.weather, aid
                )
                attraction_assessments.append(crowd_update)
                if len(attraction_assessments) >= 8:
                    break

        all_ids = list({aid for p in paths for aid in p.get("path", [])})
        eu_result = expected_utility(
            all_ids, self.uf, weather_prob_rain=0.3 if self.weather == "rain" else 0.1
        )

        obs_sequence = [
            "gps_stationary",
            "gps_moving",
            "ticket_scanned",
            "photo_taken",
            "gps_moving",
            "ticket_scanned",
        ]
        hmm_result = self.hmm.sensor_fusion(obs_sequence)

        result = {
            "satisfaction_inference": bn_inference,
            "crowd_inference": crowd_inference,
            "attraction_assessments": attraction_assessments,
            "expected_utility": eu_result,
            "hmm_tracking": hmm_result,
        }
        self._log(
            "CO5_PROB_DONE",
            p_satisfaction_good=bn_inference["P(satisfaction=good)"],
            crowd_levels=crowd_inference,
        )
        return result

    def stage4_decision(
        self, paths: List[Dict[str, Any]], prob_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        self._log("CO4_DECISION_START")

        if not paths:
            return {"success": False, "selected_route": None}

        scored_routes = []
        p_good = prob_result["satisfaction_inference"].get("P(satisfaction=good)", 0.5)
        time_slot = "morning" if self.problem.start_hour < 12 else "afternoon"

        for route in paths:
            u = self.uf.evaluate(
                route["path"],
                route["total_cost"],
                route["total_time_min"],
                time_slot,
            )
            eu_adjusted = u["utility"] * p_good

            route_summary = {k: v for k, v in route.items() if k != "trace"}
            scored_routes.append(
                {
                    **route_summary,
                    "utility": u["utility"],
                    "utility_components": u["components"],
                    "expected_utility_adjusted": round(eu_adjusted, 4),
                    "p_satisfaction_good": p_good,
                }
            )

        scored_routes.sort(key=lambda x: x["expected_utility_adjusted"], reverse=True)

        top_path = scored_routes[0]["path"]
        solver = MinimaxSolver(
            attractions=top_path,
            utility_fn=self.uf,
            depth_limit=4,
            budget_inr=self.problem.budget_inr,
            max_time_min=self.problem.max_time_min,
        )
        minimax_result = solver.solve()

        policy = policy_selection(scored_routes, self.uf, aspiration_level=0.35)

        result = {
            "scored_routes": scored_routes,
            "selected_route": scored_routes[0] if scored_routes else None,
            "minimax_result": minimax_result,
            "policy": policy,
        }
        self._log(
            "CO4_DECISION_DONE",
            selected_path=scored_routes[0]["path"] if scored_routes else [],
            utility=scored_routes[0]["utility"] if scored_routes else 0,
        )
        return result

    def stage6_ethics(
        self,
        search_result: Dict[str, Any],
        decision_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        ethics: Dict[str, Any] = {
            "bias_analysis": [
                {
                    "type": "Heuristic Bias",
                    "description": (
                        "Straight-line heuristic may underestimate actual road distances "
                        "in congested areas (e.g., Old City near Charminar). "
                        "This biases A* toward geographically close but traffic-heavy routes."
                    ),
                    "mitigation": "Use real-time traffic-weighted heuristic (e.g., from maps API).",
                    "severity": "medium",
                },
                {
                    "type": "Uncertainty Miscalibration",
                    "description": (
                        "Crowd CPTs are hand-crafted priors from historical patterns. "
                        "During festivals (Bonalu, Bathukamma, Eid), crowd levels spike "
                        "far beyond model predictions, causing overconfident low-crowd estimates."
                    ),
                    "mitigation": "Incorporate real-time crowd data and Bayesian updating from live sensors.",
                    "severity": "high",
                },
                {
                    "type": "Budget Fairness",
                    "description": (
                        "High-budget tourists see Ramoji Film City (Rs1500) as attractive; "
                        "the utility function may systematically favour premium venues, "
                        "creating a filter bubble that excludes culturally rich free sites."
                    ),
                    "mitigation": "Add diversity constraint: at least N free/low-cost attractions in every plan.",
                    "severity": "low",
                },
                {
                    "type": "Category Preference Amplification",
                    "description": (
                        "Preference score heavily rewards matching categories, causing "
                        "over-specialised itineraries (all-historical, all-nature) that miss "
                        "diverse Hyderabadi culture."
                    ),
                    "mitigation": "Add diversity bonus to utility for category spread.",
                    "severity": "low",
                },
            ],
            "failure_modes": [
                {
                    "scenario": "All goal attractions closed",
                    "detection": "A* returns failure; pipeline reports no candidate paths",
                    "recovery": "Relax goal set to closest open alternatives",
                },
                {
                    "scenario": "Budget exhausted mid-route",
                    "detection": "CSP forward-check prunes all remaining domains",
                    "recovery": "Backtrack to last affordable junction, replan",
                },
                {
                    "scenario": "Weather suddenly changes to rain",
                    "detection": "HMM observation anomaly: gps_stationary unexpectedly long",
                    "recovery": "Re-run Bayesian update, re-score routes, prefer indoor attractions",
                },
            ],
            "performance_summary": {
                "search_nodes_expanded": (search_result.get("best_path") or {}).get(
                    "nodes_expanded", 0
                ),
                "search_runtime_ms": (search_result.get("best_path") or {}).get(
                    "runtime_ms", 0
                ),
                "csp_available": True,
                "selected_utility": (decision_result.get("selected_route") or {}).get(
                    "utility", 0
                ),
            },
            "explainability": self._build_explanation(decision_result),
        }
        self._log(
            "CO6_ETHICS_COMPLETE",
            bias_types=[b["type"] for b in ethics["bias_analysis"]],
        )
        return ethics

    def _build_explanation(self, decision_result: Dict[str, Any]) -> List[str]:
        route = decision_result.get("selected_route")
        if not route:
            return ["No route selected — all constraints unsatisfiable."]

        path_names = route.get("path_names", [])
        comp = route.get("utility_components", {})
        eu = route.get("expected_utility_adjusted", 0)
        p_sat = route.get("p_satisfaction_good", 0)
        lines = [
            f"Selected route: {' -> '.join(path_names)}",
            f"Utility score: {route.get('utility', 0):.4f} (higher is better, max ~ 1.0)",
            f"Expected utility (weather-adjusted): {eu:.4f}",
            f"Bayesian satisfaction probability: {p_sat:.0%}",
            "",
            "Utility breakdown:",
            f"  * Rating score      {comp.get('rating_score', 0):.4f}  (avg attraction quality)",
            f"  * Cost efficiency   {comp.get('cost_efficiency', 0):.4f}  (value per rupee spent)",
            f"  * Time efficiency   {comp.get('time_efficiency', 0):.4f}  (attractions per hour)",
            f"  * Preference match  {comp.get('preference_score', 0):.4f}  (category alignment)",
            f"  * Crowd penalty    -{comp.get('crowd_penalty', 0):.4f}  (expected crowd level)",
        ]
        return lines

    def run(self) -> Dict[str, Any]:
        self.start_ns = time.perf_counter_ns()

        s1 = self.stage1_setup()

        s2 = self.stage2_search()
        paths = s2.get("candidate_paths", [])

        s4 = self.stage4_probabilistic(paths)

        s5 = self.stage4_decision(paths, s4)

        selected_route = s5.get("selected_route")
        s3 = self.stage3_csp([selected_route] if selected_route else [])

        s6 = self.stage6_ethics(s2, s5)

        total_ms = (time.perf_counter_ns() - self.start_ns) / 1e6

        return {
            "success": bool(paths),
            "total_runtime_ms": round(total_ms, 2),
            "co1_setup": s1,
            "co2_search": s2,
            "co3_csp": s3,
            "co5_probabilistic": s4,
            "co4_decision": s5,
            "co6_hybrid": s6,
            "pipeline_trace": self.pipeline_trace,
            "final_recommendation": {
                "route": s5.get("selected_route"),
                "schedule": s3.get("csp_result", {}).get("schedule", {}),
                "explanation": s6.get("explainability", []),
                "ethics_warnings": [
                    b["description"] for b in s6.get("bias_analysis", [])
                ],
            },
        }

if __name__ == "__main__":
    print("=" * 65)
    print("CO6 — Hybrid Intelligent Tourist Planner (Hyderabad)")
    print("=" * 65)

    planner = HybridTouristPlanner(
        start_id=0,
        goal_ids=[1, 9, 16],
        budget_inr=600,
        max_time_min=400,
        start_hour=9.0,
        preferred_categories=["historical", "religious"],
        avoid_crowds=True,
        weather="sunny",
        day_type="weekend",
        cost_mode="distance",
    )

    result = planner.run()

    print(f"\nTotal pipeline runtime: {result['total_runtime_ms']} ms")
    print(f"Success: {result['success']}")

    print("\n" + "=" * 65 + "\nPIPELINE TRACE")
    print("=" * 65)
    for entry in result["pipeline_trace"]:
        print(f"  [{entry['elapsed_ms']:7.2f}ms] {entry['stage']}")

    print("\n" + "=" * 65 + "\nFINAL RECOMMENDATION")
    print("=" * 65)
    rec = result["final_recommendation"]
    for line in rec.get("explanation", []):
        print(f"  {line}")

    if rec.get("schedule"):
        print("\n  SCHEDULE (CSP):")
        for aid, info in rec["schedule"].items():
            print(f"    [{info['slot']:<10}] {info['name']:<30} Rs{info['entry_cost']}")

    print("\n  ETHICS WARNINGS:")
    for w in rec.get("ethics_warnings", []):
        print(f"    [!] {w[:80]}...")

    print("\n" + "=" * 65 + "\nSEARCH PROFILE (All Algorithms)")
    print("=" * 65)
    profile = result["co2_search"].get("profile_comparison", {})
    print(
        f"  {'Algorithm':<10} {'Expanded':<10} {'Distance(km)':<14} {'Time(ms)':<10} {'Gap%'}"
    )
    print("  " + "-" * 55)
    for alg, data in profile.items():
        gap = (
            f"{data['optimality_gap_pct']:.1f}%"
            if data.get("optimality_gap_pct") is not None
            else "N/A"
        )
        print(
            f"  {alg:<10} {data['nodes_expanded']:<10} "
            f"{data['total_distance_km']:<14} {data['runtime_ms']:<10} {gap}"
        )
