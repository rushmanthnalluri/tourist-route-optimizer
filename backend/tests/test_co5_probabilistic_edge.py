
from backend.algorithms.co5_probabilistic import (
    bayes_update_crowd,
    likelihood_weighting,
    BayesianNetwork,
)

def test_bayes_update_cloudy():
    res = bayes_update_crowd("morning", "weekday", "cloudy", 0)
    assert res is not None

def test_bayes_update_invalid_attraction():
    res = bayes_update_crowd("morning", "weekday", "cloudy", 999)
    assert res == {}

def test_likelihood_weighting_no_evidence():
    bn = BayesianNetwork()
    res = likelihood_weighting(
        bn, query="satisfaction", evidence={}, n_samples=100, seed=42
    )
    assert "good" in res["probabilities"] or "poor" in res["probabilities"]

def test_likelihood_weighting_partial_evidence():
    bn = BayesianNetwork()
    res = likelihood_weighting(
        bn,
        query="satisfaction",
        evidence={"weather": "sunny", "crowd_level": "low"},
        n_samples=100,
        seed=42,
    )
    assert "good" in res["probabilities"] or "poor" in res["probabilities"]

def test_likelihood_weighting_full_evidence():
    bn = BayesianNetwork()
    evidence = {
        "weather": "sunny",
        "time_slot": "morning",
        "day_type": "weekday",
        "crowd_level": "low",
        "wait_time": "short",
        "satisfaction": "good",
    }
    res = likelihood_weighting(
        bn, query="satisfaction", evidence=evidence, n_samples=10, seed=42
    )
    assert res is not None
