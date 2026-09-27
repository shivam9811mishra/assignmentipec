from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import DetectionEventCreate, DetectionEventOut, VehicleTraceResponse
from app.services import analytics_service, trace_service
from app.websocket_manager import ws_manager

router = APIRouter(prefix="/analytics", tags=["Analytics"])

@router.post("/events", status_code=201)
async def ingest_detection_event(
    event_in: DetectionEventCreate,
    db: Session = Depends(get_db)
):
    try:
        event, alert_dict = analytics_service.process_detection_event(db, event_in)
        
        event_payload = {
            "id": event.id,
            "camera_id": event.camera_id,
            "camera_name": event.camera.name if event.camera else event.camera_id,
            "camera_zone": event.camera.zone if event.camera else "Unknown",
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "entity_identifier": event.entity_identifier,
            "entity_type": event.entity_type,
            "confidence": event.confidence,
            "color": event.color,
            "speed_kmh": event.speed_kmh,
            "bounding_box": event.bounding_box,
            "snapshot_url": event.snapshot_url
        }
        await ws_manager.broadcast_detection(event_payload)

        if alert_dict:
            await ws_manager.broadcast_alert(alert_dict)

        return {
            "status": "success",
            "event_id": event.id,
            "alert_triggered": alert_dict is not None,
            "alert": alert_dict
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/events")
def list_detections(
    limit: int = Query(50, ge=1, le=200),
    camera_id: Optional[str] = None,
    entity_identifier: Optional[str] = None,
    db: Session = Depends(get_db)
):
    events = analytics_service.list_recent_detections(
        db, limit=limit, camera_id=camera_id, entity_identifier=entity_identifier
    )
    result = []
    for ev in events:
        result.append({
            "id": ev.id,
            "camera_id": ev.camera_id,
            "camera_name": ev.camera.name if ev.camera else ev.camera_id,
            "camera_zone": ev.camera.zone if ev.camera else "Unknown",
            "timestamp": ev.timestamp,
            "event_type": ev.event_type,
            "entity_identifier": ev.entity_identifier,
            "entity_type": ev.entity_type,
            "confidence": ev.confidence,
            "color": ev.color,
            "speed_kmh": ev.speed_kmh,
            "bounding_box": ev.bounding_box,
            "snapshot_url": ev.snapshot_url
        })
    return result

@router.get("/trace/{entity_identifier}", response_model=VehicleTraceResponse)
def trace_vehicle(
    entity_identifier: str,
    db: Session = Depends(get_db)
):
    return trace_service.get_vehicle_trace(db, entity_identifier)
