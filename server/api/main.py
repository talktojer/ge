"""
FastAPI application entry point.
Handles REST endpoints, WebSocket connections, middleware.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

logger = structlog.get_logger()

app = FastAPI(
    title="Galactic Empire API",
    version="1.0.0-scaffold",
    description="FastAPI backend for GE mobile MMO"
)

# CORS middleware for Unity client
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# TODO: Add auth middleware (JWT validation)
# TODO: Add rate limiting middleware
# TODO: Add structured logging middleware

@app.on_event("startup")
async def startup_event():
    """
    Initialize connections on startup.
    """
    logger.info("api_startup", message="Galactic Empire API starting")
    
    # Initialize database connection pool
    from database import init_db
    await init_db()
    logger.info("database_pool_initialized")
    
    # Redis connection is lazily initialized by WebSocket handler
    # TODO: Initialize Firebase Admin SDK
    # TODO: Start background tasks (health checks, metrics)

@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up connections on shutdown.
    """
    logger.info("api_shutdown", message="Galactic Empire API shutting down")
    
    # Close Redis connection used by WebSocket
    from api.routes.websocket import redis_client
    if redis_client:
        await redis_client.close()
        logger.info("api_redis_closed")
    
    # Close Postgres pool
    from database import close_db
    await close_db()
    
    # Close Redis connection used by commands
    from api.routes.commands import _redis_client
    if _redis_client:
        await _redis_client.close()
        logger.info("commands_redis_closed")

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "galactic-empire-api",
        "status": "healthy",
        "version": "1.0.0-scaffold"
    }

@app.get("/health")
async def health():
    """
    Detailed health check.
    TODO: Check Postgres connection
    TODO: Check Redis connection
    TODO: Check ge-sim connectivity
    """
    return {
        "api": "healthy",
        "database": "TODO",
        "redis": "TODO",
        "ge_sim": "TODO"
    }

# Include routers
from api.routes import auth, player, commands, websocket, sectors

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(player.router, prefix="/player", tags=["player"])
app.include_router(commands.router, prefix="/commands", tags=["commands"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])
app.include_router(sectors.router, prefix="/sectors", tags=["sectors"])

# TODO: Add trade router when implemented
# app.include_router(trade.router, prefix="/trade", tags=["trade"])
