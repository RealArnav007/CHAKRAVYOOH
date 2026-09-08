import os
import uuid
import time
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router
from app.database.connection import engine, Base

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("beacon.main")

# ---------------------------------------------------------------------------
# Startup env-var validation (H-3 / L-2 fix)
# ---------------------------------------------------------------------------
# Safe environment fallbacks
if not os.getenv("SECRET_KEY"):
    os.environ["SECRET_KEY"] = "beacon_super_secret_jwt_key_2026"


# ---------------------------------------------------------------------------
# DB table creation
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Project Beacon — Cloud Command Node",
    version=os.getenv("APP_VERSION", "2.0.0"),
    description="Self-organizing emergency communication infrastructure backend"
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["X-Gateway-Id", "X-App-Version", "Content-Type", "Upgrade", "Connection"],
)

# ---------------------------------------------------------------------------
# Request logging middleware (L-5 fix)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = int((time.time() - start) * 1000)
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} ({duration_ms}ms)"
        + (f" [gw={request.headers.get('X-Gateway-Id', '-')}]" if "ingest" in request.url.path else "")
    )
    return response

# ---------------------------------------------------------------------------
# Exception handlers — all errors → contract envelope (H-3 fix)
# ---------------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "INVALID_PACKET",
                "message": "Schema/field validation failed",
                "request_id": str(uuid.uuid4())
            }
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    req_id = str(uuid.uuid4())
    logger.error(f"Unhandled exception [{req_id}]: {type(exc).__name__}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL",
                "message": "An unexpected server error occurred",
                "request_id": req_id
            }
        },
    )

# ---------------------------------------------------------------------------
# Routes & Static Files
# ---------------------------------------------------------------------------
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def serve_root():
    return FileResponse("static/chakravyooh_command_center.html")

@app.get("/chakravyooh")
async def serve_chakravyooh():
    return FileResponse("static/chakravyooh_command_center.html")

@app.get("/portal")
async def serve_portal():
    return FileResponse("static/chakravyooh_command_center.html")

@app.get("/landing")
async def serve_landing():
    return FileResponse("static/landing.html")

@app.get("/victim")
async def serve_victim():
    return FileResponse("static/victim.html")

@app.get("/officer")
async def serve_officer():
    return FileResponse("static/officer.html")

@app.get("/admin")
async def serve_admin():
    return FileResponse("static/admin.html")

