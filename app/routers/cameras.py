from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import CameraCreate, CameraUpdate, CameraOut, CameraHeartbeat
from app.services import camera_service
from app.websocket_manager import ws_manager

router = APIRouter(prefix="/cameras", tags=["Cameras"])

@router.get("", response_model=List[CameraOut])
def list_cameras(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    zone: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return camera_service.list_cameras(db, skip=skip, limit=limit, zone=zone, status=status, search=search)

@router.post("", response_model=CameraOut, status_code=201)
async def onboard_camera(
    camera_in: CameraCreate,
    db: Session = Depends(get_db)
):
    try:
        cam = camera_service.create_camera(db, camera_in)
        await ws_manager.broadcast_camera_status(
            camera_id=cam.id,
            status=cam.status,
            last_heartbeat=cam.last_heartbeat.isoformat()
        )
        return cam
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{camera_id}", response_model=CameraOut)
def get_camera(
    camera_id: str,
    db: Session = Depends(get_db)
):
    cam = camera_service.get_camera(db, camera_id)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    return cam

@router.put("/{camera_id}", response_model=CameraOut)
async def update_camera(
    camera_id: str,
    camera_in: CameraUpdate,
    db: Session = Depends(get_db)
):
    cam = camera_service.update_camera(db, camera_id, camera_in)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    await ws_manager.broadcast_camera_status(
        camera_id=cam.id,
        status=cam.status,
        last_heartbeat=cam.last_heartbeat.isoformat()
    )
    return cam

@router.delete("/{camera_id}")
def delete_camera(
    camera_id: str,
    db: Session = Depends(get_db)
):
    success = camera_service.delete_camera(db, camera_id)
    if not success:
        raise HTTPException(status_code=404, detail="Camera not found")
    return {"status": "success", "message": f"Camera {camera_id} deleted"}

@router.post("/{camera_id}/heartbeat", response_model=CameraOut)
async def camera_heartbeat(
    camera_id: str,
    payload: CameraHeartbeat,
    db: Session = Depends(get_db)
):
    cam = camera_service.record_heartbeat(db, camera_id, status=payload.status, fps=payload.fps)
    if not cam:
        raise HTTPException(status_code=404, detail="Camera not found")
    await ws_manager.broadcast_camera_status(
        camera_id=cam.id,
        status=cam.status,
        last_heartbeat=cam.last_heartbeat.isoformat()
    )
    return cam
