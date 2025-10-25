from fastapi import APIRouter, HTTPException
from typing import List, Optional
from app.database import get_supabase
from app.schemas.station import Station, StationSearch

router = APIRouter()


@router.get("/", response_model=List[Station])
async def list_stations(q: Optional[str] = None, limit: int = 100):
    """List stations with optional search"""
    supabase = get_supabase()
    
    query = supabase.table("stations").select("*")
    
    if q:
        query = query.or_(f"name.ilike.%{q}%,code.ilike.%{q}%")
    
    query = query.limit(limit)
    result = query.execute()
    
    return result.data


@router.get("/autocomplete", response_model=List[Station])
async def autocomplete_stations(q: str, limit: int = 10):
    """Autocomplete station search"""
    supabase = get_supabase()
    
    result = supabase.table("stations").select("*").or_(
        f"name.ilike.%{q}%,code.ilike.%{q}%"
    ).limit(limit).execute()
    
    return result.data


@router.get("/{code}", response_model=Station)
async def get_station(code: str):
    """Get station by code"""
    supabase = get_supabase()
    
    result = supabase.table("stations").select("*").eq("code", code).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Station not found")
    
    return result.data[0]
