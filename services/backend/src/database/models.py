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
    
    priority_score = Column(Integer, nullable=True)
    ai_category = Column(String(50), nullable=True)
    ai_reasoning = Column(JSON, nullable=True)
    
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
