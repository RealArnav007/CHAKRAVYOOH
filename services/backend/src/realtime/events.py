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

class RealtimeEvent(BaseModel):
    event_type: str
    payload: dict[str, Any]
    timestamp: int
