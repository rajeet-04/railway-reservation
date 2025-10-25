"""FastAPI application factory."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger.info("Starting Railway Reservation API...")
    logger.info(f"Database URL: {settings.DATABASE_URL[:50]}...")
    
    # Startup tasks
    # TODO: Add database connection check
    # TODO: Preload routing graph for A* search
    
    yield
    
    # Shutdown tasks
    logger.info("Shutting down Railway Reservation API...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Railway Reservation API",
        description="Backend API for Railway Reservation System with route search and booking",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.DEBUG,
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "version": "0.1.0",
            "debug": settings.DEBUG,
        }
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "message": "Railway Reservation API",
            "version": "0.1.0",
            "docs": "/docs",
            "health": "/health",
        }
    
    # Register API v1 routers (simple stubs exist in app.api.v1)
    try:
        from app.api.v1 import auth, stations, trains, search, bookings, admin

        app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"]) 
        app.include_router(stations.router, prefix="/api/v1/stations", tags=["stations"]) 
        app.include_router(trains.router, prefix="/api/v1/trains", tags=["trains"]) 
        app.include_router(search.router, prefix="/api/v1/search", tags=["search"]) 
        app.include_router(bookings.router, prefix="/api/v1/bookings", tags=["bookings"]) 
        app.include_router(admin.router, prefix="/api/v1/admin", tags=["admin"]) 
    except Exception as exc:  # pragma: no cover - router import should usually succeed
        logger.warning(f"Could not register routers: {exc}")
    
    logger.info("FastAPI application created successfully")
    
    return app


# Create app instance
app = create_app()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
