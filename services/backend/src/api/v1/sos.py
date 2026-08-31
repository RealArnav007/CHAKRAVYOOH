from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.dependencies import get_db_session
from src.security.rate_limiter import check_rate_limit
from src.sos.ingestion.pipeline import process_sos_ingestion
from src.sos.validation.validator import IngestRequest, IngestResponse

router = APIRouter()

@router.post("/ingest", response_model=IngestResponse)
async def ingest_sos(
    request: IngestRequest,
    x_gateway_id: str = Depends(check_rate_limit),
    x_app_version: str = Header(None, description="App version of the gateway"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Ingest a signed SOS packet from a Gateway node.
    Executes schema validation, Ed25519 signature verification, replay protection, deduplication, 
    X25519 decryption, AI scoring, persistence, correlation, and Realtime dashboard broadcasting.
    """
    return await process_sos_ingestion(db, request, gateway_id=x_gateway_id)

@router.get("/{sos_id}/status")
async def get_sos_status(sos_id: str, db: AsyncSession = Depends(get_db_session)):
    """Check the status of an ingested SOS packet."""
    from sqlalchemy import select

    from src.database.models import SOSReport
    
    stmt = select(SOSReport).where(SOSReport.sos_id == sos_id).limit(1)
    result = await db.execute(stmt)
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="SOS not found")
        
    return {
        "sos_id": report.sos_id,
        "delivery": "acknowledged",
        "incident_id": report.incident_id,
        "received_at": int(report.received_at.timestamp() * 1000) if report.received_at else None
    }
