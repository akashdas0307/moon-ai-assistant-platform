from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from backend.config.settings import settings
import logging
from datetime import datetime
from backend.api.websocket.handlers import handle_websocket
from backend.database.db import init_db
from backend.api.routes.messages import router as messages_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Moon-AI-Assistant-Platform API",
    description="Backend API for Moon AI Assistant",
    version="0.1.0",
)

# Include Routers
app.include_router(messages_router, prefix="/api/v1")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint to verify backend is running."""
    return {
        "status": "healthy",
        "service": "moon-ai-backend",
        "version": "0.1.0",
        "timestamp": datetime.now().isoformat()
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await handle_websocket(websocket)


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info("Moon-AI Backend starting up...")
    logger.info(f"CORS origins: {settings.cors_origins}")

    # Initialize Database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info("Moon-AI Backend shutting down...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=settings.backend_port,
        reload=True,
    )
