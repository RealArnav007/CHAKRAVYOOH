import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.router import api_router
from src.config import get_settings
from src.database.session import init_db

# Setup basic logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("pukar.backend")

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for the FastAPI application.
    Executes database schema creation on startup.
    """
    logger.info("Initializing Database...")
    await init_db()
    logger.info("Database initialized successfully.")
    
    # Check keys configured
    if settings.ENVIRONMENT.lower() != "production":
        logger.info("Running in DEVELOPMENT mode.")
    
    yield
    
    logger.info("Shutting down Pukar backend...")

app = FastAPI(
    title="Pukar Command Backend",
    description="Offline-first emergency communication mesh command node.",
    version="4.0.0",
    lifespan=lifespan
)

# CORS configuration for Web Command Center
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/health", tags=["Observability"])
async def health_check():
    """
    Ping endpoint used by Render / Load Balancers to prevent cold starts.
    """
    return {"status": "ok", "environment": settings.ENVIRONMENT}

@app.get("/ready", tags=["Observability"])
async def readiness_check():
    """
    Readiness probe for K8s / advanced deployments.
    """
    return {"status": "ready"}
