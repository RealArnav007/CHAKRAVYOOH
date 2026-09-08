import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Gateway-ID", "X-App-Version"],
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


# ── Frontend Static File Serving ──────────────────────────────────────────────
# Arnav's HTML portal lives in <repo_root>/frontend/.
# FastAPI serves it on the same port 8000 — zero CORS, single unified server.
# Path: Pukar/frontend/index.html  → served at http://localhost:8000/
#        Pukar/frontend/static/…   → served at http://localhost:8000/static/…
_THIS_FILE   = Path(__file__).resolve()         # .../services/backend/src/main.py
_REPO_ROOT   = _THIS_FILE.parent.parent.parent.parent  # .../Pukar/
_FRONTEND_DIR = _REPO_ROOT / "frontend"


@app.get("/portal", include_in_schema=False)
@app.get("/", include_in_schema=False)
async def serve_portal():
    """Serve Arnav's Command Center UI."""
    html_file = _FRONTEND_DIR / "index.html"
    if html_file.exists():
        return FileResponse(str(html_file), media_type="text/html")
    return {"error": "Frontend not built. Run: git checkout upstream/Frontend-A -- index.html static/ && mkdir -p frontend && mv index.html frontend/ && mv static frontend/"}


# Mount /static AFTER defining API routes so /api/v1 is never shadowed.
# This must come last — StaticFiles is a catch-all.
_static_dir = _FRONTEND_DIR / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
    logger.info("Frontend static assets mounted from %s", _static_dir)
else:
    logger.warning(
        "Frontend directory not found at %s. "
        "Populate with: git checkout upstream/Frontend-A -- index.html static/ "
        "&& mkdir -p frontend && mv index.html frontend/ && mv static frontend/",
        _FRONTEND_DIR
    )
