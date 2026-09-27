import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Tuple, List
from sqlalchemy.orm import Session, joinedload
from app.config import settings
from app.models import DetectionEvent, Camera
from app.schemas import DetectionEventCreate
from app.services.watchlist_service import normalize_plate, get_by_identifier
from app.services.alert_service import create_alert

def utc_now():
    return datetime.now(timezone.utc)

def is_duplicate_event(
    db: Session,
    camera_id: str,
    entity_identifier: str,
    window_seconds: int = 15
) -> bool:
    cutoff = utc_now() - timedelta(seconds=window_seconds)
    recent = db.query(DetectionEvent).filter(
        DetectionEvent.camera_id == camera_id,
        DetectionEvent.entity_identifier == entity_identifier,
        DetectionEvent.timestamp >= cutoff
    ).first()
    return recent is not None

def process_detection_event(
    db: Session,
    event_in: DetectionEventCreate
) -> Tuple[DetectionEvent, Optional[dict]]:
    clean_identifier = normalize_plate(event_in.entity_identifier)
    
    camera = db.query(Camera).filter(Camera.id == event_in.camera_id).first()
    if not camera:
        raise ValueError(f"Camera with ID {event_in.camera_id} does not exist")

    camera.last_heartbeat = utc_now()
    camera.status = "ONLINE"

    duplicate = is_duplicate_event(
        db,
        camera_id=event_in.camera_id,
        entity_identifier=clean_identifier,
        window_seconds=settings.ANPR_DEDUP_WINDOW_SECONDS
    )

    bbox_str = json.dumps(event_in.bounding_box.model_dump()) if event_in.bounding_box else None
    meta_str = json.dumps(event_in.metadata_json) if event_in.metadata_json else None
    event_ts = event_in.timestamp if event_in.timestamp else utc_now()

    event = DetectionEvent(
        camera_id=event_in.camera_id,
        timestamp=event_ts,
        event_type=event_in.event_type.upper(),
        entity_identifier=clean_identifier,
        entity_type=event_in.entity_type.upper(),
        confidence=event_in.confidence,
        color=event_in.color or "Unknown",
        speed_kmh=event_in.speed_kmh,
        bounding_box=bbox_str,
        metadata_json=meta_str,
        snapshot_url=event_in.snapshot_url
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    alert_dict = None
    if not duplicate and event_in.confidence >= settings.MIN_ALERT_CONFIDENCE:
        watchlist_match = get_by_identifier(db, clean_identifier)
        if watchlist_match:
            alert = create_alert(
                db=db,
                camera_id=event.camera_id,
                watchlist_id=watchlist_match.id,
                detection_event_id=event.id,
                severity=watchlist_match.severity,
                matched_entity=watchlist_match.entity_identifier,
                matched_category=watchlist_match.category,
                confidence=event.confidence
            )
            alert_dict = {
                "id": alert.id,
                "camera_id": camera.id,
                "camera_name": camera.name,
                "camera_zone": camera.zone,
                "latitude": camera.latitude,
                "longitude": camera.longitude,
                "watchlist_id": watchlist_match.id,
                "detection_event_id": event.id,
                "severity": alert.severity,
                "status": alert.status,
                "matched_entity": alert.matched_entity,
                "matched_category": alert.matched_category,
                "description": watchlist_match.description,
                "confidence": alert.confidence,
                "triggered_at": alert.triggered_at.isoformat(),
                "snapshot_url": event.snapshot_url
            }

    return event, alert_dict

def list_recent_detections(
    db: Session,
    limit: int = 50,
    camera_id: Optional[str] = None,
    entity_identifier: Optional[str] = None
) -> List[DetectionEvent]:
    query = db.query(DetectionEvent).options(joinedload(DetectionEvent.camera))
    if camera_id:
        query = query.filter(DetectionEvent.camera_id == camera_id)
    if entity_identifier:
        clean = normalize_plate(entity_identifier)
        query = query.filter(DetectionEvent.entity_identifier == clean)
    return query.order_by(DetectionEvent.timestamp.desc()).limit(limit).all()
