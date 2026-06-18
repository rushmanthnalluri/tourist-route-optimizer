import math

from backend.algorithms.co5_probabilistic import (
    bayes_rule,
    bayes_update_crowd,
    BayesianNetwork,
    rejection_sampling,
    likelihood_weighting,
    TouristHMM,
)

def test_bayes_rule():
    res = bayes_rule(prior=0.01, likelihood=0.8, evidence_prob=0.096)
    assert math.isclose(res, 0.083333333, rel_tol=1e-5)
    assert bayes_rule(0.1, 0.5, 0.0) == 0.0

def test_bayes_update_crowd():
    res = bayes_update_crowd("afternoon", "weekend", "sunny", 0)
    assert "P(crowd=high)" in res
    assert 0 <= res["P(crowd=high | long_wait)"] <= 1.0

    res_rain = bayes_update_crowd("morning", "weekday", "rain", 0)
    assert res_rain["P(crowd=high)"] < res["P(crowd=high)"]

    assert bayes_update_crowd("morning", "weekday", "rain", 9999) == {}

def test_bayesian_network_inference():
    bn = BayesianNetwork()
    evidence = {"weather": "sunny", "time_slot": "morning"}
    res = bn.infer_satisfaction(evidence)
    assert 0 <= res["P(satisfaction=good)"] <= 1.0

    res_all = bn.infer_satisfaction({})
    assert "P(satisfaction=good)" in res_all

def test_bayesian_network_infer_crowd():
    bn = BayesianNetwork()
    crowd = bn.infer_crowd_given_evidence("sunny", "afternoon", "weekend")
    assert "low" in crowd
    assert "high" in crowd
    assert math.isclose(sum(crowd.values()), 1.0, rel_tol=1e-5)

def test_rejection_sampling():
    bn = BayesianNetwork()
    res = rejection_sampling(bn, "satisfaction", {"weather": "sunny"}, n_samples=100)
    assert "probabilities" in res
    assert res["samples_accepted"] <= 100

def test_likelihood_weighting():
    bn = BayesianNetwork()
    res = likelihood_weighting(bn, "satisfaction", {"weather": "sunny"}, n_samples=100)
    assert "probabilities" in res

def test_hmm_forward_and_viterbi():
    hmm = TouristHMM()
    observations = ["gps_stationary", "gps_moving", "ticket_scanned"]

    belief, p_obs = hmm.forward(observations)
    assert len(belief) == 3
    assert p_obs > 0
    assert math.isclose(sum(belief[0].values()), 1.0, rel_tol=1e-3)

    path, prob = hmm.viterbi(observations)
    assert len(path) == 3
    assert prob > 0
    assert path[0] in hmm.STATES

    fusion = hmm.sensor_fusion(observations)
    assert fusion["most_likely_current_state"] == path[-1]

def test_hmm_zero_probability_edge_cases():
    hmm = TouristHMM()
    hmm.B["resting"]["impossible"] = 0.0
    hmm.B["traveling"]["impossible"] = 0.0
    hmm.B["visiting"]["impossible"] = 0.0

    belief, p_obs = hmm.forward(["impossible"])
    assert math.isclose(belief[0]["resting"], 1 / 3)
