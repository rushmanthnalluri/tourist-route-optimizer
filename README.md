# Hyderabad Tourist Route Optimizer.
AI-powered route planner — Search, CSP, Decision Theory, Probabilistic Reasoning

🚀 **Live Web App:** [https://rushmanthnalluri.github.io/tourist-route-optimizer/](https://rushmanthnalluri.github.io/tourist-route-optimizer/)
📡 **Live Backend API (Swagger UI):** [https://tourist-route-optimizer.onrender.com/docs](https://tourist-route-optimizer.onrender.com/docs)

---

## Project Structure

```
Tourist_Guide/
├── backend/
│   ├── main.py                        ← FastAPI app entry point
│   ├── requirements.txt
│   ├── data/
│   │   └── hyderabad_attractions.py   ← 25 attractions + graph (run standalone)
│   ├── models/
│   │   └── state.py                   ← CO1 dataclasses: State, Action, Problem, Node
│   ├── algorithms/
│   │   ├── co1_peas_agent.py          ← CO1: PEAS, environment types, KB, rules
│   │   ├── co2_search.py              ← CO2: BFS, DFS, UCS, A*, Greedy, IDA*
│   │   ├── co3_csp.py                 ← CO3: Backtracking, AC-3, MRV/LCV, Min-Conflicts
│   │   ├── co4_decision.py            ← CO4: Utility, Minimax, Alpha-Beta, EU
│   │   ├── co5_probabilistic.py       ← CO5: Bayes, BN, Var Elim, Sampling, HMM
│   │   └── co6_hybrid.py             ← CO6: Full hybrid pipeline + ethics
│   └── routers/
│       ├── search_router.py
│       ├── csp_router.py
│       ├── decision_router.py
│       ├── probabilistic_router.py
│       └── hybrid_router.py
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── App.jsx
        ├── utils/api.js
        ├── styles/index.css
        └── components/
            ├── MapView.jsx            ← Leaflet map with route overlay
            ├── AttractionSidebar.jsx  ← Pick start + goals
            ├── SearchPanel.jsx        ← CO2: run algorithms + compare + trace
            ├── CSPPanel.jsx           ← CO3: schedule + constraint trace
            ├── DecisionPanel.jsx      ← CO4: utility radar + minimax + EU
            ├── ProbabilisticPanel.jsx ← CO5: Bayes update + BN infer + HMM
            ├── HybridPanel.jsx        ← CO6: full pipeline + ethics
            └── TraceViewer.jsx        ← Step-by-step playback for any algorithm
```

---

## Setup & Run

### Backend (PyCharm or terminal)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Run individual algorithm files in PyCharm (no frontend needed)

Each algorithm file has a `if __name__ == "__main__":` block:

```bash
cd backend
python data/hyderabad_attractions.py   # view all 25 attractions & graph
python models/state.py                 # CO1 problem formulation demo
python algorithms/co1_peas_agent.py    # PEAS, environment types, rules
python algorithms/co2_search.py        # BFS/DFS/UCS/A*/Greedy/IDA* comparison
python algorithms/co3_csp.py           # CSP backtracking + min-conflicts
python algorithms/co4_decision.py      # Utility + minimax + alpha-beta + EU
python algorithms/co5_probabilistic.py # Bayes rule + BN + HMM
python algorithms/co6_hybrid.py        # Full hybrid pipeline
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:5173
```

---

## CO Coverage

| CO  | Module                  | Key Concepts |
|-----|-------------------------|-------------|
| CO1 | co1_peas_agent.py       | PEAS, environment types, graphs, rule sets, constraints, dataclasses |
| CO2 | co2_search.py           | BFS, DFS, UCS, A*, Greedy, IDA*, heuristics, closed/open sets, profiling |
| CO3 | co3_csp.py              | CSP, backtracking, AC-3, MRV, LCV, degree, min-conflicts, explainability |
| CO4 | co4_decision.py         | Utility functions, minimax, alpha-beta, expected utility, bounded rationality |
| CO5 | co5_probabilistic.py    | Bayes rule, Bayesian network, CPTs, variable elimination, sampling, HMM |
| CO6 | co6_hybrid.py           | Hybrid pipeline, explainable traces, ethics, bias, failure analysis |

---

## API Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/attractions` | GET | All 25 Hyderabad attractions |
| `/api/graph` | GET | Adjacency list |
| `/api/search/run` | POST | Run BFS/DFS/UCS/A*/Greedy/IDA* |
| `/api/search/compare` | POST | Empirical comparison of all algorithms |
| `/api/csp/schedule` | POST | CSP backtracking or min-conflicts |
| `/api/decision/utility` | POST | Compute utility score |
| `/api/decision/minimax` | POST | Minimax + alpha-beta |
| `/api/decision/expected-utility` | POST | EU under weather uncertainty |
| `/api/probabilistic/bayes-update` | POST | Bayes crowd estimation |
| `/api/probabilistic/infer` | POST | BN inference (exact/rejection/LW) |
| `/api/probabilistic/hmm` | POST | HMM sensor fusion |
| `/api/hybrid/plan` | POST | Full CO1–CO6 pipeline |
