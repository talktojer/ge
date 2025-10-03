"""
Galactic Empire FastAPI Application
Main entry point for the backend API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import socketio
import asyncio
import logging

# Import API routers - lazy import to avoid startup issues
from .api import users, teams, ships, planets
from .websocket_server import sio

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Galactic Empire API",
    description="Backend API for the Galactic Empire space conquest game",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:13000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "Welcome to Galactic Empire API", "status": "online"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "galactic-empire-backend"}

# Include API routers - lazy import
def include_routers():
    from .api import game_engine, communications, wormholes, beacons, mines, spies, zippers, admin
    app.include_router(game_engine.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(teams.router, prefix="/api")
    app.include_router(ships.router, prefix="/api")
    app.include_router(planets.router, prefix="/api")
    app.include_router(communications.router)
    app.include_router(wormholes.router, prefix="/api")
    app.include_router(beacons.router, prefix="/api")
    app.include_router(mines.router, prefix="/api")
    app.include_router(spies.router, prefix="/api")
    app.include_router(zippers.router, prefix="/api")
    app.include_router(admin.router, prefix="/api")

# Include routers after app creation
include_routers()

@app.on_event("startup")
async def startup_event():
    """Initialize game engine on startup"""
    try:
        logger.info("Starting Galactic Empire backend...")
        
        # Import game engine here to avoid circular imports
        from .core.game_engine import game_engine
        
        # Initialize and start the game engine
        logger.info("Initializing game engine...")
        await game_engine.initialize()
        
        logger.info("Starting game engine...")
        await game_engine.start_game()
        
        logger.info("Galactic Empire backend started successfully!")
        
    except Exception as e:
        logger.error(f"Failed to start game engine: {e}")
        # Don't fail startup completely, but log the error
        logger.warning("Backend started without game engine - manual initialization required")

@app.on_event("shutdown")
async def shutdown_event():
    """Stop game engine on shutdown"""
    try:
        logger.info("Shutting down Galactic Empire backend...")
        
        # Import game engine here to avoid circular imports
        from .core.game_engine import game_engine
        
        # Stop the game engine
        if game_engine._initialized:
            logger.info("Stopping game engine...")
            await game_engine.stop_game()
            logger.info("Game engine stopped successfully")
        
        logger.info("Galactic Empire backend shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": "1.0.0",
        "status": "operational",
        "game": "Galactic Empire",
        "description": "Space conquest game backend"
    }

@app.get("/api/websocket/status")
async def websocket_status():
    """WebSocket server status endpoint"""
    from .websocket_server import get_connected_users
    connected_users = await get_connected_users()
    return {
        "websocket_enabled": True,
        "connected_users": len(connected_users),
        "users": connected_users
    }

# Create the combined ASGI app with Socket.IO
socket_app = socketio.ASGIApp(sio, other_asgi_app=app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
