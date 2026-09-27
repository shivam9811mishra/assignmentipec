from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import AlertOut, AlertAcknowledge, AlertResolve
from app.services import alert_service
from app.websocket_manager import ws_manager

router = APIRouter(prefix="/alerts", tags=["Alerts"])

@router.get("", response_model=List[AlertOut])
def list_alerts(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    camera_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    alerts = alert_service.list_alerts(db, skip=skip, limit=limit, status=status, severity=severity, camera_id=camera_id)
    result = []
    for a in alerts:
        result.append({
            "id": a.id,
            "camera_id": a.camera_id,
            "camera_name": a.camera.name if a.camera else a.camera_id,
            "camera_zone": a.camera.zone if a.camera else "Unknown",
            "latitude": a.camera.latitude if a.camera else None,
            "longitude": a.camera.longitude if a.camera else None,
            "watchlist_id": a.watchlist_id,
            "detection_event_id": a.detection_event_id,
            "severity": a.severity,
            "status": a.status,
            "matched_entity": a.matched_entity,
            "matched_category": a.matched_category,
            "confidence": a.confidence,
            "acknowledged_by": a.acknowledged_by,
            "acknowledged_at": a.acknowledged_at,
            "resolution_notes": a.resolution_notes,
            "resolved_by": a.resolved_by,
            "resolved_at": a.resolved_at,
            "triggered_at": a.triggered_at,
            "snapshot_url": a.detection_event.snapshot_url if a.detection_event else None
        })
    return result

@router.get("/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: str,
    db: Session = Depends(get_db)
):
    a = alert_service.get_alert(db, alert_id)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    return {
        "id": a.id,
        "camera_id": a.camera_id,
        "camera_name": a.camera.name if a.camera else a.camera_id,
        "camera_zone": a.camera.zone if a.camera else "Unknown",
        "latitude": a.camera.latitude if a.camera else None,
        "longitude": a.camera.longitude if a.camera else None,
        "watchlist_id": a.watchlist_id,
        "detection_event_id": a.detection_event_id,
        "severity": a.severity,
        "status": a.status,
        "matched_entity": a.matched_entity,
        "matched_category": a.matched_category,
        "confidence": a.confidence,
        "acknowledged_by": a.acknowledged_by,
        "acknowledged_at": a.acknowledged_at,
        "resolution_notes": a.resolution_notes,
        "resolved_by": a.resolved_by,
        "resolved_at": a.resolved_at,
        "triggered_at": a.triggered_at,
        "snapshot_url": a.detection_event.snapshot_url if a.detection_event else None
    }

@router.patch("/{alert_id}/acknowledge", response_model=AlertOut)
async def acknowledge_alert(
    alert_id: str,
    payload: AlertAcknowledge,
    db: Session = Depends(get_db)
):
    a = alert_service.acknowledge_alert(db, alert_id, payload)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    out = {
        "id": a.id,
        "camera_id": a.camera_id,
        "camera_name": a.camera.name if a.camera else a.camera_id,
        "camera_zone": a.camera.zone if a.camera else "Unknown",
        "latitude": a.camera.latitude if a.camera else None,
        "longitude": a.camera.longitude if a.camera else None,
        "watchlist_id": a.watchlist_id,
        "detection_event_id": a.detection_event_id,
        "severity": a.severity,
        "status": a.status,
        "matched_entity": a.matched_entity,
        "matched_category": a.matched_category,
        "confidence": a.confidence,
        "acknowledged_by": a.acknowledged_by,
        "acknowledged_at": a.acknowledged_at,
        "resolution_notes": a.resolution_notes,
        "resolved_by": a.resolved_by,
        "resolved_at": a.resolved_at,
        "triggered_at": a.triggered_at,
        "snapshot_url": a.detection_event.snapshot_url if a.detection_event else None
    }
    await ws_manager.broadcast({
        "type": "ALERT_STATUS_UPDATE",
        "data": out
    })
    return out

@router.patch("/{alert_id}/resolve", response_model=AlertOut)
async def resolve_alert(
    alert_id: str,
    payload: AlertResolve,
    db: Session = Depends(get_db)
):
    a = alert_service.resolve_alert(db, alert_id, payload)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")

    out = {
        "id": a.id,
        "camera_id": a.camera_id,
        "camera_name": a.camera.name if a.camera else a.camera_id,
        "camera_zone": a.camera.zone if a.camera else "Unknown",
        "latitude": a.camera.latitude if a.camera else None,
        "longitude": a.camera.longitude if a.camera else None,
        "watchlist_id": a.watchlist_id,
        "detection_event_id": a.detection_event_id,
        "severity": a.severity,
        "status": a.status,
        "matched_entity": a.matched_entity,
        "matched_category": a.matched_category,
        "confidence": a.confidence,
        "acknowledged_by": a.acknowledged_by,
        "acknowledged_at": a.acknowledged_at,
        "resolution_notes": a.resolution_notes,
        "resolved_by": a.resolved_by,
        "resolved_at": a.resolved_at,
        "triggered_at": a.triggered_at,
        "snapshot_url": a.detection_event.snapshot_url if a.detection_event else None
    }
    await ws_manager.broadcast({
        "type": "ALERT_STATUS_UPDATE",
        "data": out
    })
    return out
