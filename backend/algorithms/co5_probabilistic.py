from __future__ import annotations
from backend.data.hyderabad_attractions import ATTRACTION_MAP
import sys
import os
import random
from typing import Dict, List, Tuple, Any, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def bayes_rule(prior: float, likelihood: float, evidence_prob: float) -> float:
    if evidence_prob == 0:
        return 0.0
    return (likelihood * prior) / evidence_prob


def bayes_update_crowd(
    time_slot: str, day_type: str, weather: str, attraction_id: int
) -> Dict[str, Any]:
    attr = ATTRACTION_MAP.get(attraction_id)
    if attr is None:
        return {}

    base_crowd = attr.crowd_probs.get(time_slot, 0.5)

    day_factor = {"weekend": 1.4, "weekday": 1.0, "holiday": 1.6}.get(day_type, 1.0)

    weather_factor = 1.0
    if weather == "rain":
        weather_factor = 1.0 - attr.weather_sensitivity * 0.7
    elif weather == "cloudy":
        weather_factor = 1.0 - attr.weather_sensitivity * 0.2

    p_crowd_high = max(0.0, min(1.0, base_crowd * day_factor * weather_factor))
    p_crowd_low = 1.0 - p_crowd_high

    p_wait_given_high = 0.85
    p_wait_given_low = 0.15

    p_wait = p_wait_given_high * p_crowd_high + p_wait_given_low * p_crowd_low

    p_crowd_high_given_wait = bayes_rule(p_crowd_high, p_wait_given_high, p_wait)

    return {
        "attraction": attr.name,
        "time_slot": time_slot,
        "day_type": day_type,
        "weather": weather,
        "P(crowd=high)": round(p_crowd_high, 4),
        "P(crowd=low)": round(p_crowd_low, 4),
        "P(long_wait | crowd=high)": p_wait_given_high,
        "P(long_wait | crowd=low)": p_wait_given_low,
        "P(long_wait)": round(p_wait, 4),
        "P(crowd=high | long_wait)": round(p_crowd_high_given_wait, 4),
        "recommendation": "AVOID" if p_crowd_high > 0.7 else "VISIT_OK",
    }


class BayesianNetwork:
    def __init__(self):
        self.cpt_weather = {
            "sunny": 0.55,
            "cloudy": 0.30,
            "rain": 0.15,
        }

        self.cpt_time = {
            "morning": 0.35,
            "afternoon": 0.40,
            "evening": 0.25,
        }

        self.cpt_day = {
            "weekday": 0.71,
            "weekend": 0.29,
        }

        self.cpt_crowd: Dict[Tuple, Dict[str, float]] = {}
        self._init_crowd_cpt()

        self.cpt_wait = {
            "low": {"short": 0.80, "long": 0.20},
            "medium": {"short": 0.45, "long": 0.55},
            "high": {"short": 0.15, "long": 0.85},
        }

        self.cpt_satisfaction = {
            ("short", "sunny"): {"good": 0.90, "poor": 0.10},
            ("short", "cloudy"): {"good": 0.75, "poor": 0.25},
            ("short", "rain"): {"good": 0.50, "poor": 0.50},
            ("long", "sunny"): {"good": 0.55, "poor": 0.45},
            ("long", "cloudy"): {"good": 0.35, "poor": 0.65},
            ("long", "rain"): {"good": 0.20, "poor": 0.80},
        }

        self.trace: List[Dict[str, Any]] = []

    def _init_crowd_cpt(self):
        configs = [
            (
                ("sunny", "morning", "weekday"),
                {"low": 0.50, "medium": 0.35, "high": 0.15},
            ),
            (
                ("sunny", "morning", "weekend"),
                {"low": 0.30, "medium": 0.40, "high": 0.30},
            ),
            (
                ("sunny", "afternoon", "weekday"),
                {"low": 0.20, "medium": 0.45, "high": 0.35},
            ),
            (
                ("sunny", "afternoon", "weekend"),
                {"low": 0.10, "medium": 0.30, "high": 0.60},
            ),
            (
                ("sunny", "evening", "weekday"),
                {"low": 0.25, "medium": 0.40, "high": 0.35},
            ),
            (
                ("sunny", "evening", "weekend"),
                {"low": 0.15, "medium": 0.35, "high": 0.50},
            ),
            (
                ("cloudy", "morning", "weekday"),
                {"low": 0.55, "medium": 0.30, "high": 0.15},
            ),
            (
                ("cloudy", "morning", "weekend"),
                {"low": 0.40, "medium": 0.40, "high": 0.20},
            ),
            (
                ("cloudy", "afternoon", "weekday"),
                {"low": 0.30, "medium": 0.40, "high": 0.30},
            ),
            (
                ("cloudy", "afternoon", "weekend"),
                {"low": 0.20, "medium": 0.40, "high": 0.40},
            ),
            (
                ("cloudy", "evening", "weekday"),
                {"low": 0.35, "medium": 0.40, "high": 0.25},
            ),
            (
                ("cloudy", "evening", "weekend"),
                {"low": 0.25, "medium": 0.40, "high": 0.35},
            ),
            (
                ("rain", "morning", "weekday"),
                {"low": 0.70, "medium": 0.25, "high": 0.05},
            ),
            (
                ("rain", "morning", "weekend"),
                {"low": 0.60, "medium": 0.30, "high": 0.10},
            ),
            (
                ("rain", "afternoon", "weekday"),
                {"low": 0.55, "medium": 0.30, "high": 0.15},
            ),
            (
                ("rain", "afternoon", "weekend"),
                {"low": 0.45, "medium": 0.35, "high": 0.20},
            ),
            (
                ("rain", "evening", "weekday"),
                {"low": 0.65, "medium": 0.25, "high": 0.10},
            ),
            (
                ("rain", "evening", "weekend"),
                {"low": 0.55, "medium": 0.30, "high": 0.15},
            ),
        ]
        for key, dist in configs:
            self.cpt_crowd[key] = dist

    def _log(self, step: str, **kwargs):
        self.trace.append({"step": step, **kwargs})

    def infer_satisfaction(self, evidence: Dict[str, str]) -> Dict[str, Any]:
        self.trace = []
        self._log("START_INFERENCE", evidence=evidence)

        known_weather = evidence.get("weather")
        known_time = evidence.get("time_slot")
        known_day = evidence.get("day_type")
        known_crowd = evidence.get("crowd_level")
        known_wait = evidence.get("wait_time")

        weather_vals = (
            [known_weather] if known_weather else list(self.cpt_weather.keys())
        )
        time_vals = [known_time] if known_time else list(self.cpt_time.keys())
        day_vals = [known_day] if known_day else list(self.cpt_day.keys())
        crowd_vals = [known_crowd] if known_crowd else ["low", "medium", "high"]
        wait_vals = [known_wait] if known_wait else ["short", "long"]

        p_good = 0.0
        p_poor = 0.0

        for w in weather_vals:
            p_w = self.cpt_weather.get(w, 0.0)
            for t in time_vals:
                p_t = self.cpt_time.get(t, 0.0)
                for d in day_vals:
                    p_d = self.cpt_day.get(d, 0.0)
                    for c in crowd_vals:
                        p_c = self.cpt_crowd.get((w, t, d), {}).get(c, 0.0)
                        for wt in wait_vals:
                            p_wt = self.cpt_wait.get(c, {}).get(wt, 0.0)

                            p_joint = p_w * p_t * p_d * p_c * p_wt
                            sat_dist = self.cpt_satisfaction.get(
                                (wt, w), {"good": 0.5, "poor": 0.5}
                            )

                            p_good += p_joint * sat_dist["good"]
                            p_poor += p_joint * sat_dist["poor"]

                            self._log(
                                "FACTOR_MULTIPLY",
                                weather=w,
                                time=t,
                                day=d,
                                crowd=c,
                                wait=wt,
                                p_joint=round(p_joint, 6),
                                p_sat_good=round(sat_dist["good"], 3),
                            )

        total = p_good + p_poor
        if total == 0:
            return {
                "P(satisfaction=good)": 0.5,
                "P(satisfaction=poor)": 0.5,
                "trace": self.trace,
            }

        p_good_norm = p_good / total
        p_poor_norm = p_poor / total

        self._log("RESULT", p_good=round(p_good_norm, 4), p_poor=round(p_poor_norm, 4))

        return {
            "P(satisfaction=good)": round(p_good_norm, 4),
            "P(satisfaction=poor)": round(p_poor_norm, 4),
            "evidence": evidence,
            "trace": self.trace,
        }

    def infer_crowd_given_evidence(
        self,
        weather: Optional[str] = None,
        time_slot: Optional[str] = None,
        day_type: Optional[str] = None,
    ) -> Dict[str, float]:
        weather_vals = [weather] if weather else list(self.cpt_weather.keys())
        time_vals = [time_slot] if time_slot else list(self.cpt_time.keys())
        day_vals = [day_type] if day_type else list(self.cpt_day.keys())

        crowd_total = {"low": 0.0, "medium": 0.0, "high": 0.0}

        for w in weather_vals:
            p_w = self.cpt_weather[w]
            for t in time_vals:
                p_t = self.cpt_time[t]
                for d in day_vals:
                    p_d = self.cpt_day[d]
                    crowd_dist = self.cpt_crowd.get(
                        (w, t, d), {"low": 0.33, "medium": 0.34, "high": 0.33}
                    )
                    for c, p_c in crowd_dist.items():
                        crowd_total[c] += p_w * p_t * p_d * p_c

        total = sum(crowd_total.values())
        if total > 0:
            crowd_total = {k: round(v / total, 4) for k, v in crowd_total.items()}

        return crowd_total


def rejection_sampling(
    bn: BayesianNetwork,
    query: str,
    evidence: Dict[str, str],
    n_samples: int = 10000,
    seed: int = 42,
) -> Dict[str, Any]:
    random.seed(seed)
    counts: Dict[str, int] = {}
    accepted = 0
    rejected = 0

    for _ in range(n_samples):
        w = random.choices(
            list(bn.cpt_weather.keys()), weights=list(bn.cpt_weather.values())
        )[0]
        t = random.choices(
            list(bn.cpt_time.keys()), weights=list(bn.cpt_time.values())
        )[0]
        d = random.choices(list(bn.cpt_day.keys()), weights=list(bn.cpt_day.values()))[
            0
        ]
        crowd_dist = bn.cpt_crowd.get(
            (w, t, d), {"low": 0.33, "medium": 0.34, "high": 0.33}
        )
        c = random.choices(list(crowd_dist.keys()), weights=list(crowd_dist.values()))[
            0
        ]
        wait_dist = bn.cpt_wait[c]
        wt = random.choices(list(wait_dist.keys()), weights=list(wait_dist.values()))[0]
        sat_dist = bn.cpt_satisfaction.get((wt, w), {"good": 0.5, "poor": 0.5})
        sat = random.choices(list(sat_dist.keys()), weights=list(sat_dist.values()))[0]

        sample = {
            "weather": w,
            "time_slot": t,
            "day_type": d,
            "crowd_level": c,
            "wait_time": wt,
            "satisfaction": sat,
        }

        consistent = all(sample.get(k) == v for k, v in evidence.items())
        if not consistent:
            rejected += 1
            continue

        accepted += 1
        val = sample.get(query, "unknown")
        counts[val] = counts.get(val, 0) + 1

    total = sum(counts.values())
    probs = {k: round(v / total, 4) for k, v in counts.items()} if total > 0 else {}

    return {
        "query": query,
        "evidence": evidence,
        "probabilities": probs,
        "samples_accepted": accepted,
        "samples_rejected": rejected,
        "acceptance_rate": round(accepted / n_samples, 4),
        "n_samples": n_samples,
    }


def likelihood_weighting(
    bn: BayesianNetwork,
    query: str,
    evidence: Dict[str, str],
    n_samples: int = 5000,
    seed: int = 42,
) -> Dict[str, Any]:
    random.seed(seed)
    weighted_counts: Dict[str, float] = {}

    for _ in range(n_samples):
        weight = 1.0

        if "weather" in evidence:
            w = evidence["weather"]
            weight *= bn.cpt_weather.get(w, 0.01)
        else:
            w = random.choices(
                list(bn.cpt_weather.keys()), weights=list(bn.cpt_weather.values())
            )[0]

        if "time_slot" in evidence:
            t = evidence["time_slot"]
            weight *= bn.cpt_time.get(t, 0.01)
        else:
            t = random.choices(
                list(bn.cpt_time.keys()), weights=list(bn.cpt_time.values())
            )[0]

        if "day_type" in evidence:
            d = evidence["day_type"]
            weight *= bn.cpt_day.get(d, 0.01)
        else:
            d = random.choices(
                list(bn.cpt_day.keys()), weights=list(bn.cpt_day.values())
            )[0]

        crowd_dist = bn.cpt_crowd.get(
            (w, t, d), {"low": 0.33, "medium": 0.34, "high": 0.33}
        )
        if "crowd_level" in evidence:
            c = evidence["crowd_level"]
            weight *= crowd_dist.get(c, 0.01)
        else:
            c = random.choices(
                list(crowd_dist.keys()), weights=list(crowd_dist.values())
            )[0]

        wait_dist = bn.cpt_wait.get(c, {"short": 0.5, "long": 0.5})
        if "wait_time" in evidence:
            wt = evidence["wait_time"]
            weight *= wait_dist.get(wt, 0.01)
        else:
            wt = random.choices(
                list(wait_dist.keys()), weights=list(wait_dist.values())
            )[0]

        sat_dist = bn.cpt_satisfaction.get((wt, w), {"good": 0.5, "poor": 0.5})
        if "satisfaction" in evidence:
            sat = evidence["satisfaction"]
            weight *= sat_dist.get(sat, 0.01)
        else:
            sat = random.choices(
                list(sat_dist.keys()), weights=list(sat_dist.values())
            )[0]

        sample = {
            "weather": w,
            "time_slot": t,
            "day_type": d,
            "crowd_level": c,
            "wait_time": wt,
            "satisfaction": sat,
        }
        val = sample.get(query, "unknown")
        weighted_counts[val] = weighted_counts.get(val, 0.0) + weight

    total_w = sum(weighted_counts.values())
    probs = (
        {k: round(v / total_w, 4) for k, v in weighted_counts.items()}
        if total_w > 0
        else {}
    )

    return {
        "query": query,
        "evidence": evidence,
        "probabilities": probs,
        "n_samples": n_samples,
        "method": "likelihood_weighting",
    }


class TouristHMM:
    STATES = ["resting", "traveling", "visiting"]
    OBSERVATIONS = ["gps_stationary", "gps_moving", "ticket_scanned", "photo_taken"]

    def __init__(self):
        self.pi = {"resting": 0.6, "traveling": 0.3, "visiting": 0.1}

        self.A = {
            "resting": {"resting": 0.5, "traveling": 0.4, "visiting": 0.1},
            "traveling": {"resting": 0.1, "traveling": 0.3, "visiting": 0.6},
            "visiting": {"resting": 0.3, "traveling": 0.2, "visiting": 0.5},
        }

        self.B = {
            "resting": {
                "gps_stationary": 0.70,
                "gps_moving": 0.05,
                "ticket_scanned": 0.05,
                "photo_taken": 0.20,
            },
            "traveling": {
                "gps_stationary": 0.05,
                "gps_moving": 0.85,
                "ticket_scanned": 0.05,
                "photo_taken": 0.05,
            },
            "visiting": {
                "gps_stationary": 0.20,
                "gps_moving": 0.10,
                "ticket_scanned": 0.30,
                "photo_taken": 0.40,
            },
        }

    def forward(self, observations: List[str]) -> Tuple[List[Dict[str, float]], float]:
        if not observations:
            return [], 0.0
        T = len(observations)
        alpha: List[Dict[str, float]] = [{} for _ in range(T)]

        for s in self.STATES:
            alpha[0][s] = self.pi[s] * self.B[s].get(observations[0], 0.01)

        for t in range(1, T):
            for s in self.STATES:
                alpha[t][s] = sum(
                    alpha[t - 1][s_prev] * self.A[s_prev][s] for s_prev in self.STATES
                ) * self.B[s].get(observations[t], 0.01)

        p_obs = sum(alpha[T - 1].values())

        belief_sequence = []
        for t in range(T):
            total = sum(alpha[t].values())
            if total > 0:
                belief_sequence.append(
                    {s: round(alpha[t][s] / total, 4) for s in self.STATES}
                )
            else:
                belief_sequence.append({s: 1 / 3 for s in self.STATES})

        return belief_sequence, p_obs

    def viterbi(self, observations: List[str]) -> Tuple[List[str], float]:
        if not observations:
            return [], 0.0
        T = len(observations)
        delta: List[Dict[str, float]] = [{} for _ in range(T)]
        psi: List[Dict[str, Optional[str]]] = [{} for _ in range(T)]

        for s in self.STATES:
            delta[0][s] = self.pi[s] * self.B[s].get(observations[0], 0.01)
            psi[0][s] = None

        for t in range(1, T):
            for s in self.STATES:
                scores = {
                    s_prev: delta[t - 1][s_prev] * self.A[s_prev][s]
                    for s_prev in self.STATES
                }
                best_prev = max(scores, key=lambda k: scores[k])
                delta[t][s] = scores[best_prev] * self.B[s].get(observations[t], 0.01)
                psi[t][s] = best_prev

        best_last = max(self.STATES, key=lambda s: delta[T - 1][s])
        best_prob = delta[T - 1][best_last]

        path = [best_last]
        for t in range(T - 1, 0, -1):
            prev = psi[t][path[0]]
            assert prev is not None
            path.insert(0, prev)

        return path, best_prob

    def sensor_fusion(self, observations: List[str]) -> Dict[str, Any]:
        if not observations:
            return {
                "observations": [],
                "belief_states": [],
                "p_observation_sequence": 0.0,
                "viterbi_path": [],
                "viterbi_probability": 0.0,
                "current_belief": {},
                "most_likely_current_state": "unknown",
            }
        belief_seq, p_obs = self.forward(observations)
        viterbi_path, viterbi_prob = self.viterbi(observations)

        return {
            "observations": observations,
            "belief_states": belief_seq,
            "p_observation_sequence": round(p_obs, 8),
            "viterbi_path": viterbi_path,
            "viterbi_probability": round(viterbi_prob, 8),
            "current_belief": belief_seq[-1] if belief_seq else {},
            "most_likely_current_state": (
                viterbi_path[-1] if viterbi_path else "unknown"
            ),
        }


if __name__ == "__main__":
    print("=" * 65)
    print("CO5 — Probabilistic Reasoning (Hyderabad Tourist)")
    print("=" * 65)

    print("\n[1] BAYES' RULE — Crowd Estimation")
    print("-" * 50)
    result = bayes_update_crowd("afternoon", "weekend", "sunny", 0)
    for k, v in result.items():
        print(f"  {k:<40}: {v}")

    print("\n[2] BAYESIAN NETWORK — Variable Elimination")
    print("-" * 50)
    bn = BayesianNetwork()
    evidence = {"weather": "sunny", "time_slot": "afternoon", "day_type": "weekend"}
    inf_result = bn.infer_satisfaction(evidence)
    print(f"  Evidence: {evidence}")
    print(f"  P(satisfaction=good | evidence) = {inf_result['P(satisfaction=good)']}")
    print(f"  P(satisfaction=poor | evidence) = {inf_result['P(satisfaction=poor)']}")

    crowd = bn.infer_crowd_given_evidence("sunny", "afternoon", "weekend")
    print(f"\n  P(CrowdLevel | sunny, afternoon, weekend):")
    for level, prob in crowd.items():
        print(f"    {level}: {prob}")

    print("\n[3] REJECTION SAMPLING (n=10000)")
    print("-" * 50)
    rs = rejection_sampling(
        bn, "satisfaction", {"weather": "sunny", "time_slot": "afternoon"}
    )
    print(f"  Query: P(satisfaction | {rs['evidence']})")
    print(f"  Probabilities: {rs['probabilities']}")
    print(f"  Acceptance rate: {rs['acceptance_rate']}")

    print("\n[4] LIKELIHOOD WEIGHTING (n=5000)")
    print("-" * 50)
    lw = likelihood_weighting(
        bn, "satisfaction", {"weather": "sunny", "time_slot": "afternoon"}
    )
    print(f"  Probabilities: {lw['probabilities']}")

    print("\n[5] HMM — Tourist State Tracking")
    print("-" * 50)
    hmm = TouristHMM()
    obs_sequence = [
        "gps_stationary",
        "gps_moving",
        "ticket_scanned",
        "photo_taken",
        "photo_taken",
        "gps_moving",
        "gps_stationary",
    ]
    fusion = hmm.sensor_fusion(obs_sequence)
    print(f"  Observations: {obs_sequence}")
    print(f"  Viterbi path: {fusion['viterbi_path']}")
    print(f"  Current belief state: {fusion['current_belief']}")
    print(f"  Most likely state: {fusion['most_likely_current_state']}")
    print("\n  Belief sequence:")
    for i, (obs, belief) in enumerate(zip(obs_sequence, fusion["belief_states"])):
        belief_str = " | ".join(f"{k}:{v:.3f}" for k, v in belief.items())
        print(f"    t={i} obs={obs:<20} -> {belief_str}")
