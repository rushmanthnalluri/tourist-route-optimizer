from backend.algorithms.co4_decision import (
    UtilityFunction,
    MinimaxSolver,
    expected_utility,
    multi_agent_negotiate,
)
from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
import sys
import os
from backend.data.memory_repository import MemoryAttractionRepository

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(prefix="/api/decision", tags=["CO4 Decision"])
repo = MemoryAttractionRepository()


def validate_attraction_ids(ids: List[int], field_name: str) -> List[int]:
    if len(ids) != len(set(ids)):
        raise ValueError(f"{field_name} must be unique")
    for aid in ids:
        if repo.get_attraction(aid) is None:
            raise ValueError(f"{field_name} contains unknown attraction_id {aid}")
    return ids


class UtilityRequest(BaseModel):
    path: List[int] = Field(..., min_length=1)
    total_cost: float = Field(..., ge=0)
    total_time_min: float = Field(..., ge=0)
    time_slot: str = "afternoon"
    preferred_categories: Optional[List[str]] = None
    budget_inr: float = Field(2000.0, gt=0)
    max_time_min: float = Field(480.0, gt=0)

    @field_validator("path")
    @classmethod
    def validate_path(cls, v: List[int]) -> List[int]:
        return validate_attraction_ids(v, "path")


class MinimaxRequest(BaseModel):
    attractions: List[int] = Field(..., min_length=1, max_length=30)
    depth_limit: int = Field(4, ge=1, le=8)
    budget_inr: float = Field(2000.0, gt=0)
    max_time_min: float = Field(480.0, gt=0)
    preferred_categories: Optional[List[str]] = None

    @field_validator("attractions")
    @classmethod
    def validate_attractions(cls, v: List[int]) -> List[int]:
        return validate_attraction_ids(v, "attractions")


class ExpectedUtilityRequest(BaseModel):
    attraction_ids: List[int] = Field(..., min_length=1, max_length=30)
    weather_prob_rain: float = Field(0.3, ge=0, le=1)
    preferred_categories: Optional[List[str]] = None
    budget_inr: float = Field(2000.0, gt=0)
    max_time_min: float = Field(480.0, gt=0)

    @field_validator("attraction_ids")
    @classmethod
    def validate_attraction_ids_field(cls, v: List[int]) -> List[int]:
        return validate_attraction_ids(v, "attraction_ids")


@router.post("/utility")
async def compute_utility(req: UtilityRequest):
    uf = UtilityFunction(
        preferred_categories=req.preferred_categories or [],
        budget_inr=req.budget_inr,
        max_time_min=req.max_time_min,
    )
    result = uf.evaluate(req.path, req.total_cost, req.total_time_min, req.time_slot)
    return result


@router.post("/minimax")
async def run_minimax(req: MinimaxRequest):
    uf = UtilityFunction(
        preferred_categories=req.preferred_categories or [],
        budget_inr=req.budget_inr,
        max_time_min=req.max_time_min,
    )
    solver = MinimaxSolver(
        attractions=req.attractions,
        utility_fn=uf,
        depth_limit=req.depth_limit,
        budget_inr=req.budget_inr,
        max_time_min=req.max_time_min,
    )
    return solver.solve()


@router.post("/expected-utility")
async def get_expected_utility(req: ExpectedUtilityRequest):
    uf = UtilityFunction(
        preferred_categories=req.preferred_categories,
        budget_inr=req.budget_inr,
        max_time_min=req.max_time_min,
    )
    return expected_utility(req.attraction_ids, uf, req.weather_prob_rain)


class NegotiateRequest(BaseModel):
    routes: List[Dict[str, Any]] = Field(..., min_length=1)


@router.post("/negotiate")
async def run_negotiate(req: NegotiateRequest):
    # Filter out routes with missing/None paths to prevent TypeErrors in algorithm
    valid_routes = [r for r in req.routes if r.get("path") and len(r["path"]) > 0]
    if not valid_routes:
        raise HTTPException(
            status_code=400,
            detail="No valid routes with paths provided for negotiation.",
        )
    return multi_agent_negotiate(valid_routes)
