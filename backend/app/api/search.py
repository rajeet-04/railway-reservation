from fastapi import APIRouter, HTTPException
from typing import List
from datetime import date
from app.database import get_supabase
from app.schemas.train import Train

router = APIRouter()


@router.get("/", response_model=List[Train])
async def search_trains(
    from_station: str,
    to_station: str,
    journey_date: date,
    limit: int = 20
):
    """Search for trains between stations"""
    supabase = get_supabase()
    
    # Find direct trains
    result = supabase.table("trains").select("*").eq(
        "from_station_code", from_station
    ).eq("to_station_code", to_station).limit(limit).execute()
    
    trains = result.data
    
    # If no direct trains, search for trains that pass through both stations
    if not trains:
        # Get all trains passing through from_station
        from_trains = supabase.table("train_stops").select(
            "train_id, stop_sequence"
        ).eq("station_code", from_station).execute()
        
        from_train_map = {t["train_id"]: t["stop_sequence"] for t in from_trains.data}
        
        # Get all trains passing through to_station
        to_trains = supabase.table("train_stops").select(
            "train_id, stop_sequence"
        ).eq("station_code", to_station).execute()
        
        # Find common trains where from_station comes before to_station
        valid_train_ids = []
        for t in to_trains.data:
            train_id = t["train_id"]
            if train_id in from_train_map and from_train_map[train_id] < t["stop_sequence"]:
                valid_train_ids.append(train_id)
        
        if valid_train_ids:
            # Get train details
            trains_result = supabase.table("trains").select("*").in_(
                "id", valid_train_ids[:limit]
            ).execute()
            trains = trains_result.data
    
    return trains


@router.get("/direct", response_model=List[Train])
async def search_direct_trains(from_station: str, to_station: str):
    """Search for direct trains only"""
    supabase = get_supabase()
    
    result = supabase.table("trains").select("*").eq(
        "from_station_code", from_station
    ).eq("to_station_code", to_station).execute()
    
    return result.data
