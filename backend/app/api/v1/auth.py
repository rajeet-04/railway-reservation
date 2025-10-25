from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.post("/register")
async def register(payload: dict):
    """Stub register endpoint."""
    # In real implementation: validate, hash password, save user
    if not payload.get("email"):
        raise HTTPException(status_code=400, detail="email required")
    return {"message": "registered", "email": payload.get("email")}


@router.post("/login")
async def login(payload: dict):
    """Stub login endpoint returning a fake token."""
    if not payload.get("email"):
        raise HTTPException(status_code=400, detail="email required")
    return {"access_token": "fake-token", "token_type": "bearer"}
