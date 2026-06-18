from pydantic import BaseModel, field_validator, ValidationInfo

class AttractionModel(BaseModel):
    id: int
    name: str
    lat: float
    lng: float
    entry_cost: float
    duration_min: int
    category: str
    rating: float
    opening_time: int
    closing_time: int
    description: str

    @field_validator("closing_time")
    @classmethod
    def validate_closing_time(cls, v: int, info: ValidationInfo) -> int:
        if "opening_time" in info.data and v <= info.data["opening_time"]:
            raise ValueError("closing_time must be after opening_time")
        return v
