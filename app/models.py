import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class Camera(Base):
    __tablename__ = "cameras"

    id = Column(String(64), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    department = Column(String(128), nullable=False, default="Traffic Police")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    camera_type = Column(String(64), default="ANPR")
    protocol = Column(String(32), default="SIMULATED")
    stream_url = Column(String(512), nullable=False)
    status = Column(String(32), default="ONLINE")
    last_heartbeat = Column(DateTime, default=utc_now)
    zone = Column(String(128), default="Ahmedabad West")
    storage_retention_days = Column(Integer, default=30)
    fps = Column(Integer, default=25)
    resolution = Column(String(32), default="1920x1080")
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    detections = relationship("DetectionEvent", back_populates="camera", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="camera")

class DetectionEvent(Base):
    __tablename__ = "detection_events"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    camera_id = Column(String(64), ForeignKey("cameras.id"), nullable=False, index=True)
    timestamp = Column(DateTime, default=utc_now, index=True)
    event_type = Column(String(64), default="ANPR")
    entity_identifier = Column(String(64), index=True, nullable=False)
    entity_type = Column(String(64), default="CAR")
    confidence = Column(Float, default=0.90)
    color = Column(String(32), default="Unknown")
    speed_kmh = Column(Float, nullable=True)
    bounding_box = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)
    snapshot_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=utc_now)

    camera = relationship("Camera", back_populates="detections")
    alert = relationship("Alert", back_populates="detection_event", uselist=False)

class WatchlistRecord(Base):
    __tablename__ = "watchlist_records"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    entity_identifier = Column(String(64), unique=True, index=True, nullable=False)
    category = Column(String(64), default="STOLEN_VEHICLE")
    severity = Column(String(32), default="CRITICAL")
    owner_or_suspect = Column(String(128), nullable=True)
    description = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)

    alerts = relationship("Alert", back_populates="watchlist_record")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    camera_id = Column(String(64), ForeignKey("cameras.id"), nullable=False, index=True)
    watchlist_id = Column(String(64), ForeignKey("watchlist_records.id"), nullable=False, index=True)
    detection_event_id = Column(String(64), ForeignKey("detection_events.id"), nullable=False, unique=True)
    severity = Column(String(32), default="CRITICAL")
    status = Column(String(32), default="PENDING")
    matched_entity = Column(String(64), nullable=False)
    matched_category = Column(String(64), nullable=False)
    confidence = Column(Float, default=0.95)
    acknowledged_by = Column(String(64), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(64), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    triggered_at = Column(DateTime, default=utc_now, index=True)

    camera = relationship("Camera", back_populates="alerts")
    watchlist_record = relationship("WatchlistRecord", back_populates="alerts")
    detection_event = relationship("DetectionEvent", back_populates="alert")

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(64), default="system_operator")
    action = Column(String(64), nullable=False)
    entity_type = Column(String(64), nullable=False)
    entity_id = Column(String(64), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), default="127.0.0.1")
    timestamp = Column(DateTime, default=utc_now, index=True)
