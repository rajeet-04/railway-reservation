from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date, time


class TrainBase(BaseModel):
    number: str
    name: str
    from_station_code: str
    to_station_code: str


class Train(TrainBase):
    id: int
    from_station_name: Optional[str] = None
    to_station_name: Optional[str] = None
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    distance_km: Optional[float] = None
    has_ac: bool = False
    has_sleeper: bool = False
    has_general: bool = False
    
    class Config:
        from_attributes = True


class TrainStop(BaseModel):
    id: int
    train_id: int
    station_code: str
    station_name: Optional[str] = None
    stop_sequence: int
    arrival_time: Optional[str] = None
    departure_time: Optional[str] = None
    day_offset: int = 0
    
    class Config:
        from_attributes = True


class TrainDetails(Train):
    stops: List[TrainStop] = []
