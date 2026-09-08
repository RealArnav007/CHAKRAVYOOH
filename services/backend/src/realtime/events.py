from enum import Enum
from typing import Any

from pydantic import BaseModel


class RealtimeEventType(str, Enum):
    NEW_SOS = "NEW_SOS"
    INCIDENT_CREATED = "INCIDENT_CREATED"
    REPORT_ADDED = "REPORT_ADDED"
    INCIDENT_UPDATED = "INCIDENT_UPDATED"
    SEVERITY_CHANGED = "SEVERITY_CHANGED"
    ZONE_UPDATED = "ZONE_UPDATED"
    DISPATCH_UPDATED = "DISPATCH_UPDATED"
    
    # Chakravyooh Cyclone Intelligence Events
    CYCLONE_DETECTED = "CYCLONE_DETECTED"
    CYCLONE_CLASSIFIED = "CYCLONE_CLASSIFIED"
    CYCLONE_PREDICTION_UPDATED = "CYCLONE_PREDICTION_UPDATED"
    CYCLONE_RISK_UPDATED = "CYCLONE_RISK_UPDATED"
    RISK_ZONE_ELEVATED = "RISK_ZONE_ELEVATED"
    PUKAR_ALERT_CREATED = "PUKAR_ALERT_CREATED"

class RealtimeEvent(BaseModel):
    event_type: str
    payload: dict[str, Any]
    timestamp: int
