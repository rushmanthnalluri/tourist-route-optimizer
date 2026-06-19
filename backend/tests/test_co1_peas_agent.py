from backend.models.state import TouristState, TouristProblem
from backend.algorithms.co1_peas_agent import (
    TouristAgent,
    TOURIST_AGENT_PEAS,
    TOURIST_ENV,
)


def test_agent_perception():
    problem = TouristProblem(start_id=0, goal_ids=[1])
    agent = TouristAgent(problem)
    state = problem.initial_state()

    perc = agent.perceive(state)
    assert perc["location"] == 0
    assert "budget_remaining" in perc
    assert isinstance(perc["active_rules"], list)


def test_kb_rules_firing():
    problem = TouristProblem(start_id=0, goal_ids=[1], budget_inr=100)
    agent = TouristAgent(problem)

    state = TouristState(
        current_id=0, visited=frozenset([0]), time_elapsed_min=10, cost_spent=90, day_hour=14.0
    )
    fired = agent.kb.fire_rules(state, problem)
    assert "BUDGET_CRITICAL" in fired

    advice = agent.kb.get_rule_advice(state, problem)
    assert any("Budget" in a for a in advice)


def test_peas_and_env_describe():
    desc_peas = TOURIST_AGENT_PEAS.describe()
    assert "Performance Measures" in desc_peas

    desc_env = TOURIST_ENV.describe()
    assert "Observability" in desc_env


def test_kb_descriptions():
    problem = TouristProblem(start_id=0, goal_ids=[1])
    agent = TouristAgent(problem)

    g_desc = agent.kb.describe_graph()
    assert "Nodes:" in g_desc

    c_desc = agent.kb.describe_constraints()
    assert "BUDGET" in c_desc


def test_agent_log():
    problem = TouristProblem(start_id=0, goal_ids=[1])
    agent = TouristAgent(problem)
    agent.log("TEST", {"key": "value"})
    assert len(agent.trace) == 1
    assert agent.trace[0]["step"] == "TEST"


def test_kb_exception_handling():
    problem = TouristProblem(start_id=0, goal_ids=[1])
    agent = TouristAgent(problem)

    bad_state = TouristState(current_id=0, visited=frozenset(), time_elapsed_min=0, cost_spent=0, day_hour=0.0)
    fired = agent.kb.fire_rules(bad_state, problem)
    assert isinstance(fired, list)

    advice = agent.kb.get_rule_advice(bad_state, problem)
    assert isinstance(advice, list)



def test_closing_soon_rule():
    problem = TouristProblem(start_id=0, goal_ids=[0])
    agent = TouristAgent(problem)
    state = TouristState(
        current_id=1, visited=frozenset([1]), time_elapsed_min=10, cost_spent=0, day_hour=16.5
    )
    fired = agent.kb.fire_rules(state, problem)
    assert "CLOSING_SOON" in fired
