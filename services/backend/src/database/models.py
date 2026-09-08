import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from .session import Base


def generate_uuid():
    return str(uuid.uuid4())


def utc_now():
    return datetime.now(timezone.utc)


class RoleEnum(str, enum.Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    COMMANDER = "COMMANDER"
    RESPONDER = "RESPONDER"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"


class IncidentStatus(str, enum.Enum):
    NEW = "NEW"
    DISPATCHED = "DISPATCHED"
    RESOLVED = "RESOLVED"


class IncidentPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ZoneStatus(str, enum.Enum):
    NORMAL = "NORMAL"
    EMERGING = "EMERGING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"
    EXTREME = "EXTREME"


class DispatchStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    DISPATCHED = "DISPATCHED"
    EN_ROUTE = "EN_ROUTE"
    ON_SCENE = "ON_SCENE"
    RESOLVED = "RESOLVED"


class User(Base):
    __tablename__ = "users"

    user_id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=True) 
    role = Column(String(50), default=RoleEnum.VIEWER.value)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    last_activity = Column(DateTime(timezone=True), default=utc_now)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True)


class Role(Base):
    __tablename__ = "roles"

    name = Column(String(50), primary_key=True)
    description = Column(String(255))


class Permission(Base):
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_name = Column(String(50), ForeignKey("roles.name"))
    action = Column(String(100), nullable=False)


class DeviceKey(Base):
    __tablename__ = "device_keys"

    origin_key_id = Column(String(64), primary_key=True)
    origin_id = Column(String(64), nullable=False, index=True)
    ed25519_public_key = Column(String(128), nullable=False)
    x25519_public_key = Column(String(128), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    status = Column(String(50), default="ACTIVE")


class SOSReport(Base):
    __tablename__ = "sos_reports"

    sos_id = Column(String(36), primary_key=True, default=generate_uuid)
    msg_id = Column(String(64), unique=True, index=True, nullable=False)
    origin_id = Column(String(64), nullable=False)
    origin_key_id = Column(String(64), ForeignKey("device_keys.origin_key_id"), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    nonce = Column(String(64), nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    acc = Column(Float, nullable=False)
    trigger_type = Column(String(50), nullable=False)
    request_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    regex_score = Column(Integer, nullable=False)
    local_model_score = Column(Integer, nullable=False)
    confidence = Column(Float, nullable=False)
    payload_enc = Column(Text, nullable=False)
    payload_decrypted = Column(Text, nullable=True)
    
    priority_score = Column(Float, nullable=True)
    ai_category = Column(String(50), nullable=True)
    ai_reasoning = Column(JSON, nullable=True)
    # ScoreResult v2.0.0 ML intelligence columns
    escalation_signal = Column(Float, nullable=True)          # zone surge multiplier 0.0-1.0
    false_alarm_likelihood = Column(Float, nullable=True)     # drill/false-alarm probability
    needs_human_review = Column(Boolean, default=False, nullable=True)   # commander review badge
    injection_suspected = Column(Boolean, default=False, nullable=True)  # prompt injection flag
    ai_correlation_id = Column(String(64), nullable=True)     # trace ID for observability

    incident_id = Column(String(36), ForeignKey("incidents.incident_id"), nullable=True)
    gateway_id = Column(String(64), nullable=True)
    received_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("ix_sos_reports_location_time", "lat", "lon", "created_at"),
    )



class Incident(Base):
    __tablename__ = "incidents"

    incident_id = Column(String(36), primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True)
    status = Column(String(50), default=IncidentStatus.NEW.value)
    priority_level = Column(String(50), default=IncidentPriority.MEDIUM.value)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    radius_m = Column(Float, default=100.0)
    zone_id = Column(String(36), ForeignKey("zones.zone_id"), nullable=True)
    report_count = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    reports = relationship("SOSReport", backref="incident")
    dispatches = relationship("Dispatch", backref="incident")
    
    __table_args__ = (
        Index("ix_incidents_location_time", "lat", "lon", "created_at"),
        Index("ix_incidents_status", "status"),
    )


class Zone(Base):
    __tablename__ = "zones"

    zone_id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=True)
    status = Column(String(50), default=ZoneStatus.NORMAL.value)
    center_lat = Column(Float, nullable=False)
    center_lon = Column(Float, nullable=False)
    radius_m = Column(Float, default=1000.0)
    report_count = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    
    incidents = relationship("Incident", backref="zone")


class Resource(Base):
    __tablename__ = "resources"

    resource_id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)
    status = Column(String(50), default="AVAILABLE")


class Dispatch(Base):
    __tablename__ = "dispatches"

    dispatch_id = Column(String(36), primary_key=True, default=generate_uuid)
    incident_id = Column(String(36), ForeignKey("incidents.incident_id"), nullable=False)
    unit_name = Column(String(100), nullable=False)
    responder_id = Column(String(36), ForeignKey("users.user_id"), nullable=True)
    status = Column(String(50), default=DispatchStatus.DISPATCHED.value)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    event_id = Column(String(36), primary_key=True, default=generate_uuid)
    action = Column(String(100), nullable=False)
    actor_id = Column(String(36), nullable=True)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=utc_now)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.user_id"), nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)


class Device(Base):
    __tablename__ = "devices"
    device_id = Column(String(64), primary_key=True)
    owner_id = Column(String(36), nullable=True)


class IncidentReport(Base):
    __tablename__ = "incident_reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(36), ForeignKey("incidents.incident_id"))
    report_id = Column(String(36), ForeignKey("sos_reports.sos_id"))


# ═══════════════════════════════════════════════════════════════════════════════
# PROJECT Chakravyooh: Cyclone Intelligence & Resilient Warning Models
# ═══════════════════════════════════════════════════════════════════════════════

class CycloneIntelligenceRecord(Base):
    """
    Append-only log of every incoming CycloneIntelligence frame from Rishabh's AI pipeline.
    Preserves audit history of predictions and trajectories over time.
    """
    __tablename__ = "cyclone_intelligence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cyclone_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    model_version = Column(String(64), default="Chakravyooh-brain-0.1")
    raw_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        UniqueConstraint("cyclone_id", "timestamp", name="uq_cyclone_intel_id_ts"),
    )


class CycloneLatest(Base):
    """
    Materialized latest state pointer per active cyclone for rapid dashboard reads.
    """
    __tablename__ = "cyclone_latest"

    cyclone_id = Column(String(64), primary_key=True)
    name = Column(String(100), nullable=True)
    stage = Column(String(100), nullable=True)
    intensity_level = Column(String(50), nullable=True)
    confidence = Column(Float, nullable=True)
    current_lat = Column(Float, nullable=True)
    current_lon = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    raw_json = Column(JSON, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)


class CycloneZoneRisk(Base):
    """
    Geospatial risk assessment snapshot mapping predicted cyclone hazard to existing Pukar zones.
    """
    __tablename__ = "cyclone_zone_risk"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cyclone_id = Column(String(64), nullable=False, index=True)
    zone_id = Column(String(36), ForeignKey("zones.zone_id"), nullable=False, index=True)
    zone_name = Column(String(100), nullable=True)
    risk_level = Column(String(50), nullable=False)  # NORMAL, EMERGING, HIGH, CRITICAL, EXTREME
    risk_score = Column(Float, nullable=False)       # 0.0 - 1.0 normalized
    distance_km = Column(Float, nullable=False)      # Min distance to predicted path
    eta_hours = Column(Float, nullable=True)         # Landfall / impact ETA
    computed_at = Column(DateTime(timezone=True), default=utc_now)

    __table_args__ = (
        Index("ix_zone_risk_cyc_zone", "cyclone_id", "zone_id"),
    )


class Alert(Base):
    """
    Actionable warnings generated by the Risk Engine for Chakravyooh realtime and offline mesh delivery.
    Supports versioning (§21), lifecycle state transitions (§20), and Ed25519 authority signing (§22).
    """
    __tablename__ = "alerts"

    alert_id = Column(String(36), primary_key=True, default=generate_uuid)
    type = Column(String(50), default="CYCLONE_WARNING")  # CYCLONE_WARNING, CYCLONE_WATCH, SYSTEM_ALERT
    cyclone_id = Column(String(64), nullable=True, index=True)
    stage = Column(String(100), nullable=True)
    message = Column(Text, nullable=False)
    zone_ids = Column(JSON, nullable=False)               # list[str] of affected zone IDs
    priority = Column(String(50), default="EXTREME")      # EXTREME, HIGH, MODERATE, LOW

    # Alert Lifecycle (Master PRD §20) — ACTIVE → UPDATED → SUPERSEDED → EXPIRED → REVOKED
    status = Column(String(50), default="ACTIVE")

    # Alert Versioning (Master PRD §21)
    version = Column(Integer, default=1, nullable=False)
    supersedes = Column(String(36), nullable=True)        # alert_id of the previous version
    issued_at = Column(DateTime(timezone=True), default=utc_now)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now)
    valid_until = Column(DateTime(timezone=True), nullable=True)  # EXPIRED when past this timestamp
    ttl_s = Column(Integer, default=86400)                # Time to live in seconds (fallback)

    # Cryptographic Verification (Master PRD §22) — Ed25519 authority signature
    signature = Column(Text, nullable=True)               # Hex-encoded Ed25519 signature
    authority_key_id = Column(String(64), nullable=True)  # Key ID of the signing authority


