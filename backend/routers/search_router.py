from fastapi import APIRouter, HTTPException
from typing import List
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from backend.models.state import TouristProblem
from backend.algorithms.co2_search import (
    astar,
    bfs,
    dfs,
    ucs,
    greedy,
    idastar,
    profile_all,
)
from backend.data.memory_repository import MemoryAttractionRepository
from backend.data.routing_service import routing_service

repo = MemoryAttractionRepository()

router = APIRouter(prefix="/api/search", tags=["CO2 Search"])


class SearchAlgorithm(str, Enum):
    astar = "astar"
    bfs = "bfs"
    dfs = "dfs"
    ucs = "ucs"
    greedy = "greedy"
    idastar = "idastar"
    all = "all"


class SearchRequest(BaseModel):
    start_id: int
    goal_ids: List[int] = Field(..., min_length=1, max_length=30)
    budget_inr: float = Field(2000.0, gt=0)
    max_time_min: float = Field(480.0, gt=0)
    start_hour: float = 9.0
    algorithm: SearchAlgorithm = SearchAlgorithm.astar
    cost_mode: str = "distance"

    @field_validator("goal_ids")
    @classmethod
    def validate_goal_ids(cls, v: List[int]) -> List[int]:
        if len(v) != len(set(v)):
            raise ValueError("goal_ids must be unique")
        for gid in v:
            if repo.get_attraction(gid) is None:
                raise ValueError(f"goal_id {gid} does not exist")
        return v

    @field_validator("start_id")
    @classmethod
    def validate_start_id(cls, v: int) -> int:
        if repo.get_attraction(v) is None:
            raise ValueError(f"start_id {v} does not exist")
        return v


def make_problem(req: SearchRequest) -> TouristProblem:
    return TouristProblem(
        start_id=req.start_id,
        goal_ids=req.goal_ids,
        must_visit=req.goal_ids,
        budget_inr=req.budget_inr,
        max_time_min=req.max_time_min,
        start_hour=req.start_hour,
    )


@router.post("/run")
async def run_search(req: SearchRequest):
    problem = make_problem(req)
    algo_map = {
        "astar": astar,
        "bfs": bfs,
        "dfs": dfs,
        "ucs": ucs,
        "greedy": greedy,
        "idastar": idastar,
    }
    if req.algorithm.value == "all":
        profile = profile_all(problem, req.cost_mode)
        return {"algorithm": "all", "profile": profile}

    algo_func = algo_map.get(req.algorithm.value)
    if not algo_func:
        raise HTTPException(status_code=400, detail="Unknown algorithm")
    # IDA* is memory-bounded but exponentially slow — cap it to avoid 60s timeouts
    if req.algorithm.value == "idastar" and len(req.goal_ids) > 4:
        raise HTTPException(
            status_code=400,
            detail="IDA* is limited to 4 goals to prevent server timeout. Use A* or Greedy for larger routes."
        )
    result = algo_func(problem, req.cost_mode)
    return {
        "algorithm": req.algorithm,
        "success": result.success,
        "path": result.path,
        "path_names": [],
        "total_cost": result.total_cost,
        "total_time_min": result.total_time_min,
        "total_distance_km": result.total_distance_km,
        "nodes_expanded": result.nodes_expanded,
        "nodes_generated": result.nodes_generated,
        "peak_frontier_size": result.peak_frontier_size,
        "runtime_ms": result.runtime_ms,
        "trace": result.trace[:1500],
        "failure_reason": result.failure_reason,
    }


@router.post("/compare")
async def compare_algorithms(req: SearchRequest):
    if len(req.goal_ids) > 6:
        raise HTTPException(
            status_code=400,
            detail="Compare All is limited to 6 goals to prevent server timeout. Please select fewer goals or run algorithms individually."
        )
    problem = make_problem(req)
    profile = profile_all(problem, req.cost_mode)
    return {"comparison": profile, "cost_mode": req.cost_mode}


@router.get("/live-traffic")
async def fetch_live_traffic():
    success = await routing_service.fetch_live_traffic()
    if not success:
        raise HTTPException(
            status_code=500, detail="Failed to fetch live traffic from OSRM"
        )
    return {"message": "Live traffic updated successfully"}
