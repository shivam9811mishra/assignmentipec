import json
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from app.models import Alert, AuditLog, Camera
from app.schemas import AlertAcknowledge, AlertResolve

def utc_now():
    return datetime.now(timezone.utc)

def create_alert(
    db: Session,
    camera_id: str,
    watchlist_id: str,
    detection_event_id: str,
    severity: str,
    matched_entity: str,
    matched_category: str,
    confidence: float
) -> Alert:
    alert = Alert(
        camera_id=camera_id,
        watchlist_id=watchlist_id,
        detection_event_id=detection_event_id,
        severity=severity.upper(),
        status="PENDING",
        matched_entity=matched_entity,
        matched_category=matched_category,
        confidence=confidence,
        triggered_at=utc_now()
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert

def list_alerts(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    camera_id: Optional[str] = None
) -> List[Alert]:
    query = db.query(Alert).options(joinedload(Alert.camera), joinedload(Alert.detection_event))
    if status:
        query = query.filter(Alert.status == status.upper())
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    if camera_id:
        query = query.filter(Alert.camera_id == camera_id)
    return query.order_by(Alert.triggered_at.desc()).offset(skip).limit(limit).all()

def get_alert(db: Session, alert_id: str) -> Optional[Alert]:
    return db.query(Alert).options(joinedload(Alert.camera), joinedload(Alert.detection_event)).filter(Alert.id == alert_id).first()

def acknowledge_alert(db: Session, alert_id: str, payload: AlertAcknowledge) -> Optional[Alert]:
    alert = get_alert(db, alert_id)
    if not alert:
        return None
    alert.status = "ACKNOWLEDGED"
    alert.acknowledged_by = payload.acknowledged_by
    alert.acknowledged_at = utc_now()
    
    audit = AuditLog(
        action="ALERT_ACKNOWLEDGED",
        entity_type="ALERT",
        entity_id=alert.id,
        details=json.dumps({"acknowledged_by": payload.acknowledged_by, "matched_entity": alert.matched_entity})
    )
    db.add(audit)
    db.commit()
    db.refresh(alert)
    return alert

def resolve_alert(db: Session, alert_id: str, payload: AlertResolve) -> Optional[Alert]:
    alert = get_alert(db, alert_id)
    if not alert:
        return None
    alert.status = "RESOLVED"
    alert.resolved_by = payload.resolved_by
    alert.resolution_notes = payload.resolution_notes
    alert.resolved_at = utc_now()

    audit = AuditLog(
        action="ALERT_RESOLVED",
        entity_type="ALERT",
        entity_id=alert.id,
        details=json.dumps({"resolved_by": payload.resolved_by, "notes": payload.resolution_notes})
    )
    db.add(audit)
    db.commit()
    db.refresh(alert)
    return alert
