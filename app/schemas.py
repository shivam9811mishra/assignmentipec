from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class BoundingBox(BaseModel):
    x: float
    y: float
    width: float
    height: float

class CameraBase(BaseModel):
    name: str
    department: str = "Traffic Police"
    latitude: float
    longitude: float
    camera_type: str = "ANPR"
    protocol: str = "SIMULATED"
    stream_url: str
    status: str = "ONLINE"
    zone: str = "Ahmedabad West"
    storage_retention_days: int = 30
    fps: int = 25
    resolution: str = "1920x1080"

class CameraCreate(CameraBase):
    id: str

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    camera_type: Optional[str] = None
    protocol: Optional[str] = None
    stream_url: Optional[str] = None
    status: Optional[str] = None
    zone: Optional[str] = None
    storage_retention_days: Optional[int] = None
    fps: Optional[int] = None

class CameraHeartbeat(BaseModel):
    status: Optional[str] = "ONLINE"
    fps: Optional[int] = None

class CameraOut(CameraBase):
    id: str
    last_heartbeat: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DetectionEventCreate(BaseModel):
    camera_id: str
    timestamp: Optional[datetime] = None
    event_type: str = "ANPR"
    entity_identifier: str
    entity_type: str = "CAR"
    confidence: float = 0.90
    color: Optional[str] = "White"
    speed_kmh: Optional[float] = None
    bounding_box: Optional[BoundingBox] = None
    metadata_json: Optional[Dict[str, Any]] = None
    snapshot_url: Optional[str] = None

class DetectionEventOut(BaseModel):
    id: str
    camera_id: str
    timestamp: datetime
    event_type: str
    entity_identifier: str
    entity_type: str
    confidence: float
    color: Optional[str] = None
    speed_kmh: Optional[float] = None
    bounding_box: Optional[str] = None
    snapshot_url: Optional[str] = None
    camera_name: Optional[str] = None
    camera_zone: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class WatchlistCreate(BaseModel):
    entity_identifier: str
    category: str = "STOLEN_VEHICLE"
    severity: str = "CRITICAL"
    owner_or_suspect: Optional[str] = None
    description: str
    notes: Optional[str] = None
    is_active: bool = True

class WatchlistUpdate(BaseModel):
    category: Optional[str] = None
    severity: Optional[str] = None
    owner_or_suspect: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None

class WatchlistOut(BaseModel):
    id: str
    entity_identifier: str
    category: str
    severity: str
    owner_or_suspect: Optional[str] = None
    description: str
    notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class AlertAcknowledge(BaseModel):
    acknowledged_by: str = "operator_desk_1"

class AlertResolve(BaseModel):
    resolved_by: str = "duty_officer"
    resolution_notes: str

class AlertOut(BaseModel):
    id: str
    camera_id: str
    camera_name: Optional[str] = None
    camera_zone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    watchlist_id: str
    detection_event_id: str
    severity: str
    status: str
    matched_entity: str
    matched_category: str
    confidence: float
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    triggered_at: datetime
    snapshot_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class TracePoint(BaseModel):
    camera_id: str
    camera_name: str
    zone: str
    latitude: float
    longitude: float
    timestamp: datetime
    confidence: float
    speed_kmh: Optional[float] = None
    color: Optional[str] = None
    snapshot_url: Optional[str] = None

class VehicleTraceResponse(BaseModel):
    entity_identifier: str
    total_detections: int
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    is_watchlisted: bool = False
    watchlist_details: Optional[WatchlistOut] = None
    trail: List[TracePoint] = []

class SystemStatsOut(BaseModel):
    total_cameras: int
    online_cameras: int
    offline_cameras: int
    degraded_cameras: int
    total_detections_today: int
    total_active_alerts: int
    total_watchlist_records: int
    avg_inference_latency_ms: float = 14.2
