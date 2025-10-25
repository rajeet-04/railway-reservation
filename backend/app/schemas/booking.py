from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class PassengerInfo(BaseModel):
    name: str
    age: int
    gender: str


class BookingCreate(BaseModel):
    train_run_id: int
    from_station_code: str
    to_station_code: str
    journey_date: date
    seat_class: str
    passengers: List[PassengerInfo]


class Booking(BaseModel):
    id: int
    booking_id: str  # PNR
    user_id: int
    train_run_id: int
    from_station_code: str
    to_station_code: str
    journey_date: date
    total_cents: int
    num_passengers: int
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class BookingDetails(Booking):
    train_number: Optional[str] = None
    train_name: Optional[str] = None
    passengers: List[PassengerInfo] = []
