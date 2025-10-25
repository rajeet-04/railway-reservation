from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.database import get_supabase
from app.schemas.train import Train, TrainDetails, TrainStop

router = APIRouter()


@router.get("/", response_model=List[Train])
async def list_trains(limit: int = 100, offset: int = 0):
    """List trains"""
    supabase = get_supabase()
    
    result = supabase.table("trains").select("*").range(offset, offset + limit - 1).execute()
    
    return result.data


@router.get("/{number}", response_model=TrainDetails)
async def get_train(number: str):
    """Get train details with stops"""
    supabase = get_supabase()
    
    # Get train
    train_result = supabase.table("trains").select("*").eq("number", number).execute()
    
    if not train_result.data:
        raise HTTPException(status_code=404, detail="Train not found")
    
    train = train_result.data[0]
    
    # Get stops
    stops_result = supabase.table("train_stops").select(
        "*, stations(name)"
    ).eq("train_id", train["id"]).order("stop_sequence").execute()
    
    # Add station names to stops
    stops = []
    for stop in stops_result.data:
        stop_data = {**stop}
        if stop.get("stations"):
            stop_data["station_name"] = stop["stations"]["name"]
        stops.append(stop_data)
    
    train["stops"] = stops
    
    return train


@router.get("/{number}/route", response_model=List[TrainStop])
async def get_train_route(number: str):
    """Get train route (all stops)"""
    supabase = get_supabase()
    
    # Get train
    train_result = supabase.table("trains").select("id").eq("number", number).execute()
    
    if not train_result.data:
        raise HTTPException(status_code=404, detail="Train not found")
    
    train_id = train_result.data[0]["id"]
    
    # Get stops
    stops_result = supabase.table("train_stops").select(
        "*, stations(name)"
    ).eq("train_id", train_id).order("stop_sequence").execute()
    
    # Add station names
    stops = []
    for stop in stops_result.data:
        stop_data = {**stop}
        if stop.get("stations"):
            stop_data["station_name"] = stop["stations"]["name"]
        stops.append(stop_data)
    
    return stops
