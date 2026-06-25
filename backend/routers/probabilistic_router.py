from backend.algorithms.co5_probabilistic import (
    BayesianNetwork,
    TouristHMM,
    bayes_update_crowd,
    rejection_sampling,
    likelihood_weighting,
)
from backend.data.weather_service import weather_service
from backend.data.live_crowd_service import live_crowd_service
from backend.data.memory_repository import MemoryAttractionRepository
from fastapi import APIRouter
from typing import Optional, Dict, List
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

router = APIRouter(prefix="/api/probabilistic", tags=["CO5 Probabilistic"])
repo = MemoryAttractionRepository()

_bn = BayesianNetwork()
_hmm = TouristHMM()


class InferenceMethod(str, Enum):
    exact = "exact"
    rejection = "rejection"
    likelihood_weighting = "likelihood_weighting"


class BayesRequest(BaseModel):
    attraction_id: int
    time_slot: str = "afternoon"
    day_type: str = "weekday"
    weather: str = "sunny"

    @field_validator("attraction_id")
    @classmethod
    def validate_attraction_id(cls, v: int) -> int:
        if repo.get_attraction(v) is None:
            raise ValueError(f"attraction_id {v} does not exist")
        return v


class InferenceRequest(BaseModel):
    evidence: Dict[str, str]
    query: str = "satisfaction"
    n_samples: int = Field(5000, ge=1, le=50000)
    method: InferenceMethod = InferenceMethod.exact


class HMMRequest(BaseModel):
    observations: List[str] = Field(default_factory=list, max_length=100)


@router.post("/bayes-update")
async def bayes_update(req: BayesRequest):
    return bayes_update_crowd(
        req.time_slot, req.day_type, req.weather, req.attraction_id
    )


@router.post("/infer")
async def infer(req: InferenceRequest):
    if req.method == InferenceMethod.exact:
        return _bn.infer_satisfaction(req.evidence)
    elif req.method == InferenceMethod.rejection:
        return rejection_sampling(_bn, req.query, req.evidence, req.n_samples)
    else:
        return likelihood_weighting(_bn, req.query, req.evidence, req.n_samples)


@router.get("/crowd")
async def infer_crowd(
    weather: Optional[str] = None,
    time_slot: Optional[str] = None,
    day_type: Optional[str] = None,
):
    return _bn.infer_crowd_given_evidence(weather, time_slot, day_type)


@router.post("/hmm")
async def hmm_track(req: HMMRequest):
    return _hmm.sensor_fusion(req.observations)



@router.get("/live-weather")
async def get_live_weather():
    condition, prob_rain = await weather_service.get_live_weather()
    return {"weather": condition, "prob_rain": prob_rain}


@router.get("/live-crowds")
async def get_live_crowds():
    return await live_crowd_service.update_live_crowds()
