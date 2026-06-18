from fastapi import APIRouter
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum

from backend.algorithms.co3_csp import TouristCSP, min_conflicts
from backend.data.memory_repository import MemoryAttractionRepository

repo = MemoryAttractionRepository()

router = APIRouter(prefix="/api/csp", tags=["CO3 CSP"])

class CSPAlgorithm(str, Enum):
    backtracking = "backtracking"
    min_conflicts = "min_conflicts"

class CSPRequest(BaseModel):
    attraction_ids: List[int] = Field(..., min_length=1, max_length=15)
    budget_inr: float = Field(2000.0, gt=0)
    max_time_min: float = Field(480.0, gt=0)
    preferred_categories: Optional[List[str]] = None
    must_morning: Optional[List[int]] = None
    use_mrv: bool = True
    use_lcv: bool = True
    use_forward_checking: bool = True
    use_ac3: bool = True
    algorithm: CSPAlgorithm = CSPAlgorithm.backtracking

    @field_validator("attraction_ids")
    @classmethod
    def validate_attraction_ids(cls, v: List[int]) -> List[int]:
        if len(v) != len(set(v)):
            raise ValueError("attraction_ids must be unique")
        for aid in v:
            if repo.get_attraction(aid) is None:
                raise ValueError(f"attraction_id {aid} does not exist")
        return v

@router.post("/schedule")
async def schedule(req: CSPRequest):
    if req.algorithm.value == "min_conflicts":
        result = min_conflicts(req.attraction_ids, req.budget_inr, req.max_time_min)
        return result

    csp = TouristCSP(
        attraction_ids=req.attraction_ids,
        budget_inr=req.budget_inr,
        max_time_min=req.max_time_min,
        preferred_categories=req.preferred_categories or [],
        must_morning=req.must_morning or [],
    )
    result = csp.solve(
        use_mrv=req.use_mrv,
        use_lcv=req.use_lcv,
        use_forward_checking=req.use_forward_checking,
        use_ac3=req.use_ac3,
    )
    return result

@router.get("/domains/{attraction_id}")
async def get_domains(attraction_id: int):
    csp = TouristCSP(attraction_ids=[attraction_id])
    return {
        "attraction_id": attraction_id,
        "domain": csp.domains.get(attraction_id, []),
    }
