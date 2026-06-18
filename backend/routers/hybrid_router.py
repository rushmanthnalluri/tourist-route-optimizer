from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from backend.algorithms.co6_hybrid import HybridTouristPlanner
from backend.data.memory_repository import MemoryAttractionRepository

repo = MemoryAttractionRepository()

router = APIRouter(prefix="/api/hybrid", tags=["CO6 Hybrid"])


class HybridRequest(BaseModel):
    start_id: int
    goal_ids: List[int] = Field(..., min_length=1, max_length=30)
    budget_inr: float = Field(2000.0, gt=0)
    max_time_min: float = Field(480.0, gt=0)
    start_hour: float = 9.0
    preferred_categories: Optional[List[str]] = None
    avoid_crowds: bool = False
    weather: str = "sunny"
    day_type: str = "weekday"
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


@router.post("/plan")
async def hybrid_plan(req: HybridRequest):
    planner = HybridTouristPlanner(
        start_id=req.start_id,
        goal_ids=req.goal_ids,
        budget_inr=req.budget_inr,
        max_time_min=req.max_time_min,
        start_hour=req.start_hour,
        preferred_categories=req.preferred_categories,
        avoid_crowds=req.avoid_crowds,
        weather=req.weather,
        day_type=req.day_type,
        cost_mode=req.cost_mode,
    )
    return planner.run()
