import sys
import os
sys.setrecursionlimit(10000)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.routers.hybrid_router import router as hybrid_router
from backend.routers.probabilistic_router import router as prob_router
from backend.routers.decision_router import router as decision_router
from backend.routers.csp_router import router as csp_router
from backend.routers.search_router import router as search_router
from backend.data.hyderabad_attractions import (
    ATTRACTIONS,
    ATTRACTION_MAP,
    GRAPH,
    straight_line_distance,
)
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException, Request

app = FastAPI(
    title="Hyderabad Tourist Route Optimizer",
    description="AI-powered route planner using Search, CSP, Decision Theory & Probabilistic Reasoning",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = (
        "max-age=31536000; includeSubDomains"
    )
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error occurred.", "details": str(exc)},
    )

app.include_router(search_router)
app.include_router(csp_router)
app.include_router(decision_router)
app.include_router(prob_router)
app.include_router(hybrid_router)

@app.get("/api/attractions", tags=["Data"])
async def get_attractions():
    return [
        {
            "id": a.id,
            "name": a.name,
            "lat": a.lat,
            "lng": a.lng,
            "entry_cost": a.entry_cost,
            "duration_min": a.duration_min,
            "category": a.category,
            "rating": a.rating,
            "opening_time": a.opening_time,
            "closing_time": a.closing_time,
            "description": a.description,
            "crowd_probs": a.crowd_probs,
            "weather_sensitivity": a.weather_sensitivity,
        }
        for a in ATTRACTIONS
    ]

@app.get("/api/attractions/{attraction_id}", tags=["Data"])
async def get_attraction(attraction_id: int):
    a = ATTRACTION_MAP.get(attraction_id)
    if a is None:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "id": a.id,
        "name": a.name,
        "lat": a.lat,
        "lng": a.lng,
        "entry_cost": a.entry_cost,
        "duration_min": a.duration_min,
        "category": a.category,
        "rating": a.rating,
        "description": a.description,
        "crowd_probs": a.crowd_probs,
    }

@app.get("/api/graph", tags=["Data"])
async def get_graph():
    result = {}
    for node_id, neighbors in GRAPH.items():
        result[node_id] = [
            {"to": n[0], "road_km": n[1], "time_min": n[2], "cost_inr": n[3]}
            for n in neighbors
        ]
    return result

@app.get("/api/distance/{id1}/{id2}", tags=["Data"])
async def get_distance(id1: int, id2: int):
    if id1 not in ATTRACTION_MAP or id2 not in ATTRACTION_MAP:
        raise HTTPException(status_code=404, detail="Not found")
    return {
        "from": id1,
        "to": id2,
        "straight_line_km": round(straight_line_distance(id1, id2), 3),
    }

@app.get("/", tags=["Health"])
async def root():
    return {
        "status": "running",
        "message": "Hyderabad Tourist Route Optimizer API",
        "endpoints": [
            "/api/attractions",
            "/api/search/run",
            "/api/search/compare",
            "/api/csp/schedule",
            "/api/decision/utility",
            "/api/decision/minimax",
            "/api/decision/expected-utility",
            "/api/probabilistic/bayes-update",
            "/api/probabilistic/infer",
            "/api/probabilistic/hmm",
            "/api/hybrid/plan",
        ],
        "docs": "/docs",
    }
