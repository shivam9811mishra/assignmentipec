from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import WatchlistCreate, WatchlistUpdate, WatchlistOut
from app.services import watchlist_service

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])

@router.get("", response_model=List[WatchlistOut])
def list_watchlist(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    return watchlist_service.list_watchlist(
        db, skip=skip, limit=limit, category=category, is_active=is_active, search=search
    )

@router.post("", response_model=WatchlistOut, status_code=201)
def create_watchlist_record(
    record_in: WatchlistCreate,
    db: Session = Depends(get_db)
):
    try:
        return watchlist_service.create_watchlist_record(db, record_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{record_id}", response_model=WatchlistOut)
def get_watchlist_record(
    record_id: str,
    db: Session = Depends(get_db)
):
    record = watchlist_service.get_watchlist_record(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Watchlist record not found")
    return record

@router.put("/{record_id}", response_model=WatchlistOut)
def update_watchlist_record(
    record_id: str,
    record_in: WatchlistUpdate,
    db: Session = Depends(get_db)
):
    record = watchlist_service.update_watchlist_record(db, record_id, record_in)
    if not record:
        raise HTTPException(status_code=404, detail="Watchlist record not found")
    return record

@router.delete("/{record_id}")
def delete_watchlist_record(
    record_id: str,
    db: Session = Depends(get_db)
):
    success = watchlist_service.delete_watchlist_record(db, record_id)
    if not success:
        raise HTTPException(status_code=404, detail="Watchlist record not found")
    return {"status": "success", "message": f"Watchlist record {record_id} deleted"}
