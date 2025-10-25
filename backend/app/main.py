from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api import stations, trains, search, bookings, auth

app = FastAPI(
    title="Railway Reservation System API",
    description="Backend API for railway reservation system with Supabase",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Railway Reservation System API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(stations.router, prefix="/api/v1/stations", tags=["Stations"])
app.include_router(trains.router, prefix="/api/v1/trains", tags=["Trains"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["Bookings"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
