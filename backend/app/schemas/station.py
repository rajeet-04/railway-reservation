from pydantic import BaseModel
from typing import Optional


class StationBase(BaseModel):
    code: str
    name: str
    state: Optional[str] = None
    zone: Optional[str] = None
    address: Optional[str] = None


class Station(StationBase):
    id: int
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    class Config:
        from_attributes = True


class StationSearch(BaseModel):
    query: str
    limit: int = 10
