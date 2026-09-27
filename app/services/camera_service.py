import json
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Camera, AuditLog
from app.schemas import CameraCreate, CameraUpdate

def utc_now():
    return datetime.now(timezone.utc)

def list_cameras(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    zone: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
) -> List[Camera]:
    query = db.query(Camera)
    if zone:
        query = query.filter(Camera.zone == zone)
    if status:
        query = query.filter(Camera.status == status.upper())
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (Camera.name.ilike(search_pattern)) | 
            (Camera.id.ilike(search_pattern)) | 
            (Camera.department.ilike(search_pattern))
        )
    return query.offset(skip).limit(limit).all()

def get_camera(db: Session, camera_id: str) -> Optional[Camera]:
    return db.query(Camera).filter(Camera.id == camera_id).first()

def create_camera(db: Session, camera_in: CameraCreate) -> Camera:
    existing = get_camera(db, camera_in.id)
    if existing:
        raise ValueError(f"Camera with ID {camera_in.id} already exists")

    camera = Camera(
        id=camera_in.id,
        name=camera_in.name,
        department=camera_in.department,
        latitude=camera_in.latitude,
        longitude=camera_in.longitude,
        camera_type=camera_in.camera_type,
        protocol=camera_in.protocol,
        stream_url=camera_in.stream_url,
        status=camera_in.status.upper(),
        zone=camera_in.zone,
        storage_retention_days=camera_in.storage_retention_days,
        fps=camera_in.fps,
        resolution=camera_in.resolution,
        last_heartbeat=utc_now()
    )
    db.add(camera)

    audit = AuditLog(
        action="CAMERA_ONBOARDED",
        entity_type="CAMERA",
        entity_id=camera.id,
        details=json.dumps({"name": camera.name, "zone": camera.zone, "stream_url": camera.stream_url})
    )
    db.add(audit)
    db.commit()
    db.refresh(camera)
    return camera

def update_camera(db: Session, camera_id: str, camera_in: CameraUpdate) -> Optional[Camera]:
    camera = get_camera(db, camera_id)
    if not camera:
        return None

    update_data = camera_in.model_dump(exclude_unset=True)
    if "status" in update_data and update_data["status"]:
        update_data["status"] = update_data["status"].upper()

    for key, value in update_data.items():
        setattr(camera, key, value)

    camera.updated_at = utc_now()
    audit = AuditLog(
        action="CAMERA_UPDATED",
        entity_type="CAMERA",
        entity_id=camera.id,
        details=json.dumps(update_data)
    )
    db.add(audit)
    db.commit()
    db.refresh(camera)
    return camera

def delete_camera(db: Session, camera_id: str) -> bool:
    camera = get_camera(db, camera_id)
    if not camera:
        return False
    db.delete(camera)
    audit = AuditLog(
        action="CAMERA_DELETED",
        entity_type="CAMERA",
        entity_id=camera_id,
        details=json.dumps({"deleted_id": camera_id})
    )
    db.add(audit)
    db.commit()
    return True

def record_heartbeat(db: Session, camera_id: str, status: str = "ONLINE", fps: Optional[int] = None) -> Optional[Camera]:
    camera = get_camera(db, camera_id)
    if not camera:
        return None
    camera.last_heartbeat = utc_now()
    camera.status = status.upper()
    if fps is not None:
        camera.fps = fps
    db.commit()
    db.refresh(camera)
    return camera
