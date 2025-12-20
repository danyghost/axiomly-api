from pydantic import BaseModel, Field
from typing import List, Optional

class PredictRequest(BaseModel):
    location: str
    deal_type: str
    building_type: str = "1"
    object_type: str = "1"
    level: int = 1
    levels: int = 5
    rooms: int = Field(ge=0)  # Студия = 0
    area: float = Field(gt=0)
    kitchen_area: Optional[float] = None

class AnalogResponse(BaseModel):
    price: float
    price_formatted: str
    area: Optional[float]
    rooms: Optional[int]
    address: str
    url: str
    floor_info: str

class PredictResponse(BaseModel):
    success: bool
    price: float
    price_formatted: str
    ml_price: float
    ml_price_formatted: str
    is_rent: bool
    price_suffix: str
    region: str
    city: str
    area: float
    rooms: int
    analogs_count: int
    analogs: List[AnalogResponse]
    message: str
