import re
import json
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import WatchlistRecord, AuditLog, generate_uuid
from app.schemas import WatchlistCreate, WatchlistUpdate

def normalize_plate(plate: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", plate).upper()

def list_watchlist(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None
) -> List[WatchlistRecord]:
    query = db.query(WatchlistRecord)
    if category:
        query = query.filter(WatchlistRecord.category == category.upper())
    if is_active is not None:
        query = query.filter(WatchlistRecord.is_active == is_active)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (WatchlistRecord.entity_identifier.ilike(search_pattern)) |
            (WatchlistRecord.description.ilike(search_pattern)) |
            (WatchlistRecord.owner_or_suspect.ilike(search_pattern))
        )
    return query.order_by(WatchlistRecord.created_at.desc()).offset(skip).limit(limit).all()

def get_watchlist_record(db: Session, record_id: str) -> Optional[WatchlistRecord]:
    return db.query(WatchlistRecord).filter(WatchlistRecord.id == record_id).first()

def get_by_identifier(db: Session, identifier: str) -> Optional[WatchlistRecord]:
    clean_id = normalize_plate(identifier)
    return db.query(WatchlistRecord).filter(
        WatchlistRecord.entity_identifier == clean_id,
        WatchlistRecord.is_active == True
    ).first()

def create_watchlist_record(db: Session, record_in: WatchlistCreate) -> WatchlistRecord:
    clean_id = normalize_plate(record_in.entity_identifier)
    existing = db.query(WatchlistRecord).filter(WatchlistRecord.entity_identifier == clean_id).first()
    if existing:
        raise ValueError(f"Watchlist record for {clean_id} already exists")

    record_id = generate_uuid()
    record = WatchlistRecord(
        id=record_id,
        entity_identifier=clean_id,
        category=record_in.category.upper(),
        severity=record_in.severity.upper(),
        owner_or_suspect=record_in.owner_or_suspect,
        description=record_in.description,
        notes=record_in.notes,
        is_active=record_in.is_active
    )
    db.add(record)
    audit = AuditLog(
        action="WATCHLIST_RECORD_CREATED",
        entity_type="WATCHLIST",
        entity_id=record_id,
        details=json.dumps({"identifier": clean_id, "category": record.category, "severity": record.severity})
    )
    db.add(audit)
    db.commit()
    db.refresh(record)
    return record

def update_watchlist_record(db: Session, record_id: str, record_in: WatchlistUpdate) -> Optional[WatchlistRecord]:
    record = get_watchlist_record(db, record_id)
    if not record:
        return None

    update_data = record_in.model_dump(exclude_unset=True)
    if "category" in update_data and update_data["category"]:
        update_data["category"] = update_data["category"].upper()
    if "severity" in update_data and update_data["severity"]:
        update_data["severity"] = update_data["severity"].upper()

    for key, value in update_data.items():
        setattr(record, key, value)

    audit = AuditLog(
        action="WATCHLIST_RECORD_UPDATED",
        entity_type="WATCHLIST",
        entity_id=record.id,
        details=json.dumps(update_data)
    )
    db.add(audit)
    db.commit()
    db.refresh(record)
    return record

def delete_watchlist_record(db: Session, record_id: str) -> bool:
    record = get_watchlist_record(db, record_id)
    if not record:
        return False
    db.delete(record)
    audit = AuditLog(
        action="WATCHLIST_RECORD_DELETED",
        entity_type="WATCHLIST",
        entity_id=record_id,
        details=json.dumps({"deleted_id": record_id})
    )
    db.add(audit)
    db.commit()
    return True
