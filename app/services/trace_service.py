from typing import Optional
from sqlalchemy.orm import Session, joinedload
from app.models import DetectionEvent, WatchlistRecord, Camera
from app.schemas import VehicleTraceResponse, TracePoint, WatchlistOut
from app.services.watchlist_service import normalize_plate

def get_vehicle_trace(db: Session, entity_identifier: str) -> VehicleTraceResponse:
    clean_id = normalize_plate(entity_identifier)
    
    events = (
        db.query(DetectionEvent)
        .options(joinedload(DetectionEvent.camera))
        .filter(DetectionEvent.entity_identifier == clean_id)
        .order_by(DetectionEvent.timestamp.asc())
        .all()
    )

    watchlist_record = (
        db.query(WatchlistRecord)
        .filter(WatchlistRecord.entity_identifier == clean_id)
        .first()
    )

    trail = []
    for ev in events:
        if ev.camera:
            trail.append(
                TracePoint(
                    camera_id=ev.camera_id,
                    camera_name=ev.camera.name,
                    zone=ev.camera.zone,
                    latitude=ev.camera.latitude,
                    longitude=ev.camera.longitude,
                    timestamp=ev.timestamp,
                    confidence=ev.confidence,
                    speed_kmh=ev.speed_kmh,
                    color=ev.color,
                    snapshot_url=ev.snapshot_url
                )
            )

    first_seen = events[0].timestamp if events else None
    last_seen = events[-1].timestamp if events else None

    wl_out = None
    if watchlist_record:
        wl_out = WatchlistOut.model_validate(watchlist_record)

    return VehicleTraceResponse(
        entity_identifier=clean_id,
        total_detections=len(events),
        first_seen=first_seen,
        last_seen=last_seen,
        is_watchlisted=watchlist_record is not None,
        watchlist_details=wl_out,
        trail=trail
    )
