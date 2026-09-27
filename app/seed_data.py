from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.models import Camera, WatchlistRecord

def utc_now():
    return datetime.now(timezone.utc)

DEFAULT_CAMERAS = [
    {
        "id": "CAM-001",
        "name": "SG Highway Junction",
        "department": "Traffic Police - Ahmedabad West",
        "latitude": 23.0305,
        "longitude": 72.5076,
        "camera_type": "ANPR",
        "protocol": "SIMULATED",
        "stream_url": "/assets/videos/feed1_junction.mp4",
        "status": "ONLINE",
        "zone": "Ahmedabad West",
        "fps": 25,
        "resolution": "1920x1080"
    },
    {
        "id": "CAM-002",
        "name": "Kalupur Station Checkpost",
        "department": "Railway Police - Kalupur",
        "latitude": 23.0270,
        "longitude": 72.5990,
        "camera_type": "ANPR",
        "protocol": "SIMULATED",
        "stream_url": "/assets/videos/feed2_station.mp4",
        "status": "ONLINE",
        "zone": "Ahmedabad Central",
        "fps": 25,
        "resolution": "1920x1080"
    },
    {
        "id": "CAM-003",
        "name": "Gandhinagar CH-0 Toll Plaza",
        "department": "Highway Police - Gandhinagar",
        "latitude": 23.2156,
        "longitude": 72.6369,
        "camera_type": "ANPR",
        "protocol": "SIMULATED",
        "stream_url": "/assets/videos/feed3_highway.mp4",
        "status": "ONLINE",
        "zone": "Gandhinagar Outer",
        "fps": 25,
        "resolution": "1920x1080"
    },
    {
        "id": "CAM-004",
        "name": "Airport Circle Junction",
        "department": "Traffic Police - East Division",
        "latitude": 23.0734,
        "longitude": 72.6266,
        "camera_type": "ANPR",
        "protocol": "SIMULATED",
        "stream_url": "/assets/videos/feed2_station.mp4",
        "status": "ONLINE",
        "zone": "Ahmedabad East",
        "fps": 25,
        "resolution": "1920x1080"
    },
    {
        "id": "CAM-005",
        "name": "S.P. Ring Road Smart Traffic Camera",
        "department": "Gujarat Police - Traffic Monitoring Cell",
        "latitude": 23.0850,
        "longitude": 72.6350,
        "camera_type": "ANPR",
        "protocol": "SIMULATED",
        "stream_url": "/assets/videos/feed1_junction.mp4",
        "status": "ONLINE",
        "zone": "Ahmedabad North-East",
        "fps": 25,
        "resolution": "1920x1080"
    },
    {
        "id": "CAM-006",
        "name": "Prahladnagar Cross Road",
        "department": "Traffic Police - Ahmedabad West",
        "latitude": 23.0125,
        "longitude": 72.5122,
        "camera_type": "ANPR",
        "protocol": "SIMULATED",
        "stream_url": "/assets/videos/feed1_junction.mp4",
        "status": "ONLINE",
        "zone": "Ahmedabad West",
        "fps": 25,
        "resolution": "1920x1080"
    }
]

DEFAULT_WATCHLIST = [
    {
        "entity_identifier": "GJ01XX0001",
        "category": "STOLEN_VEHICLE",
        "severity": "CRITICAL",
        "owner_or_suspect": "Pravin Solanki",
        "description": "White Fortuner SUV - Reported stolen under FIR #128/2026",
        "is_active": True
    },
    {
        "entity_identifier": "GJ05AB1234",
        "category": "WANTED_PERSON",
        "severity": "HIGH",
        "owner_or_suspect": "Vikram Rathore",
        "description": "Red Creta - Wanted for armed robbery in Surat",
        "is_active": True
    },
    {
        "entity_identifier": "GJ27CD9988",
        "category": "SUSPICIOUS_VEHICLE",
        "severity": "MEDIUM",
        "owner_or_suspect": "Unknown",
        "description": "Black Scorpio - Evaded checkpoint twice on NH-48",
        "is_active": True
    }
]

def seed_initial_data(db: Session):
    for cam_data in DEFAULT_CAMERAS:
        existing = db.query(Camera).filter(Camera.id == cam_data["id"]).first()
        if not existing:
            cam = Camera(
                id=cam_data["id"],
                name=cam_data["name"],
                department=cam_data["department"],
                latitude=cam_data["latitude"],
                longitude=cam_data["longitude"],
                camera_type=cam_data["camera_type"],
                protocol=cam_data["protocol"],
                stream_url=cam_data["stream_url"],
                status=cam_data["status"],
                zone=cam_data["zone"],
                fps=cam_data.get("fps", 25),
                resolution=cam_data.get("resolution", "1920x1080"),
                last_heartbeat=utc_now()
            )
            db.add(cam)

    for wl_data in DEFAULT_WATCHLIST:
        existing = db.query(WatchlistRecord).filter(WatchlistRecord.entity_identifier == wl_data["entity_identifier"]).first()
        if not existing:
            record = WatchlistRecord(
                entity_identifier=wl_data["entity_identifier"],
                category=wl_data["category"],
                severity=wl_data["severity"],
                owner_or_suspect=wl_data["owner_or_suspect"],
                description=wl_data["description"],
                is_active=wl_data["is_active"]
            )
            db.add(record)

    db.commit()
