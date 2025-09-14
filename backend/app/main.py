"""
Galactic Empire FastAPI Application
Main entry point for the backend API
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os

# Import API routers - lazy import to avoid startup issues
from .api import users, teams

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
    from .api import game_engine
    app.include_router(game_engine.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(teams.router, prefix="/api")

# Include routers after app creation
include_routers()

@app.get("/api/status")
async def api_status():
    """API status endpoint"""
    return {
        "api_version": "1.0.0",
        "status": "operational",
        "game": "Galactic Empire",
        "description": "Space conquest game backend"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
