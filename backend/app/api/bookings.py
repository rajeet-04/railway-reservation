from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.database import get_supabase
from app.schemas.booking import BookingCreate, Booking, BookingDetails
from app.api.auth import get_current_user
import random
import string

router = APIRouter()


def generate_pnr() -> str:
    """Generate PNR-like booking ID"""
    return ''.join(random.choices(string.digits, k=10))


@router.post("/", response_model=Booking)
async def create_booking(
    booking: BookingCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new booking"""
    supabase = get_supabase()
    
    # Calculate total price (simplified - in real app, get from seats)
    total_cents = len(booking.passengers) * 50000  # ₹500 per passenger
    
    # Create booking
    booking_data = {
        "booking_id": generate_pnr(),
        "user_id": current_user["id"],
        "train_run_id": booking.train_run_id,
        "from_station_code": booking.from_station_code,
        "to_station_code": booking.to_station_code,
        "journey_date": booking.journey_date.isoformat(),
        "total_cents": total_cents,
        "num_passengers": len(booking.passengers),
        "status": "CONFIRMED"
    }
    
    result = supabase.table("bookings").insert(booking_data).execute()
    
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create booking")
    
    booking_record = result.data[0]
    
    # Add passengers
    for passenger in booking.passengers:
        passenger_data = {
            "booking_id": booking_record["id"],
            "passenger_name": passenger.name,
            "passenger_age": passenger.age,
            "passenger_gender": passenger.gender,
            "price_cents": total_cents // len(booking.passengers)
        }
        supabase.table("booking_seats").insert(passenger_data).execute()
    
    return booking_record


@router.get("/", response_model=List[Booking])
async def list_bookings(current_user: dict = Depends(get_current_user)):
    """List user's bookings"""
    supabase = get_supabase()
    
    result = supabase.table("bookings").select("*").eq(
        "user_id", current_user["id"]
    ).order("created_at", desc=True).execute()
    
    return result.data


@router.get("/{booking_id}", response_model=BookingDetails)
async def get_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get booking details"""
    supabase = get_supabase()
    
    # Get booking
    result = supabase.table("bookings").select("*").eq(
        "booking_id", booking_id
    ).eq("user_id", current_user["id"]).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking = result.data[0]
    
    # Get passengers
    passengers_result = supabase.table("booking_seats").select("*").eq(
        "booking_id", booking["id"]
    ).execute()
    
    booking["passengers"] = [
        {
            "name": p["passenger_name"],
            "age": p["passenger_age"],
            "gender": p["passenger_gender"]
        }
        for p in passengers_result.data
    ]
    
    return booking


@router.post("/{booking_id}/cancel", response_model=Booking)
async def cancel_booking(
    booking_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a booking"""
    supabase = get_supabase()
    
    # Get booking
    result = supabase.table("bookings").select("*").eq(
        "booking_id", booking_id
    ).eq("user_id", current_user["id"]).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    booking = result.data[0]
    
    if booking["status"] == "CANCELLED":
        raise HTTPException(status_code=400, detail="Booking already cancelled")
    
    # Update status
    update_result = supabase.table("bookings").update(
        {"status": "CANCELLED"}
    ).eq("id", booking["id"]).execute()
    
    return update_result.data[0]
