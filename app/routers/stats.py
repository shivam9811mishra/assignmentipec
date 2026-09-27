from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone, timedelta
from app.database import get_db
from app.models import Camera, DetectionEvent, Alert, WatchlistRecord
from app.schemas import SystemStatsOut

router = APIRouter(prefix="/stats", tags=["System Stats"])

@router.get("", response_model=SystemStatsOut)
def get_system_stats(db: Session = Depends(get_db)):
    total_cameras = db.query(Camera).count()
    online_cameras = db.query(Camera).filter(Camera.status == "ONLINE").count()
    offline_cameras = db.query(Camera).filter(Camera.status == "OFFLINE").count()
    degraded_cameras = db.query(Camera).filter(Camera.status == "DEGRADED").count()

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    total_detections_today = db.query(DetectionEvent).filter(DetectionEvent.timestamp >= today_start).count()
    
    total_active_alerts = db.query(Alert).filter(Alert.status.in_(["PENDING", "ACKNOWLEDGED"])).count()
    total_watchlist = db.query(WatchlistRecord).filter(WatchlistRecord.is_active == True).count()

    return SystemStatsOut(
        total_cameras=total_cameras,
        online_cameras=online_cameras,
        offline_cameras=offline_cameras,
        degraded_cameras=degraded_cameras,
        total_detections_today=total_detections_today,
        total_active_alerts=total_active_alerts,
        total_watchlist_records=total_watchlist,
        avg_inference_latency_ms=14.2
    )
