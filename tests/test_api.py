import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_onboard_and_list_camera():
    uid = str(uuid.uuid4())[:8]
    cam_id = f"CAM-TEST-{uid}"
    new_cam = {
        "id": cam_id,
        "name": "Test Checkpost Junction",
        "department": "Traffic Police Test",
        "latitude": 23.05,
        "longitude": 72.55,
        "camera_type": "ANPR",
        "protocol": "SIMULATED",
        "stream_url": "/assets/videos/feed1_junction.mp4",
        "zone": "Test Zone",
        "fps": 30
    }
    create_resp = client.post("/api/v1/cameras", json=new_cam)
    assert create_resp.status_code == 201
    assert create_resp.json()["id"] == cam_id

    list_resp = client.get("/api/v1/cameras")
    assert list_resp.status_code == 200
    cameras = list_resp.json()
    assert any(c["id"] == cam_id for c in cameras)

    update_resp = client.put(f"/api/v1/cameras/{cam_id}", json={"status": "DEGRADED"})
    assert update_resp.status_code == 200
    assert update_resp.json()["status"] == "DEGRADED"

    heartbeat_resp = client.post(f"/api/v1/cameras/{cam_id}/heartbeat", json={"status": "ONLINE", "fps": 28})
    assert heartbeat_resp.status_code == 200
    assert heartbeat_resp.json()["status"] == "ONLINE"

def test_watchlist_operations():
    uid = str(uuid.uuid4())[:8].upper()
    identifier = f"GJ01ZZ{uid}"
    new_record = {
        "entity_identifier": identifier,
        "category": "STOLEN_VEHICLE",
        "severity": "CRITICAL",
        "owner_or_suspect": "Test Owner",
        "description": "Test Stolen Car Case"
    }
    create_resp = client.post("/api/v1/watchlist", json=new_record)
    assert create_resp.status_code == 201
    assert create_resp.json()["entity_identifier"] == identifier

    list_resp = client.get(f"/api/v1/watchlist?search={identifier}")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

def test_event_ingestion_and_watchlist_alert():
    uid = str(uuid.uuid4())[:8].upper()
    cam_id = f"CAM-EV-{uid}"
    plate = f"GJ01WL{uid}"

    client.post("/api/v1/cameras", json={
        "id": cam_id,
        "name": f"Event Test Cam {uid}",
        "department": "Traffic Police",
        "latitude": 23.08,
        "longitude": 72.58,
        "camera_type": "ANPR",
        "protocol": "SIMULATED",
        "stream_url": "/assets/videos/feed1_junction.mp4",
        "zone": "Test Zone",
        "fps": 30
    })

    client.post("/api/v1/watchlist", json={
        "entity_identifier": plate,
        "category": "STOLEN_VEHICLE",
        "severity": "CRITICAL",
        "owner_or_suspect": "Suspect A",
        "description": "Stolen test vehicle"
    })

    event_payload = {
        "camera_id": cam_id,
        "event_type": "ANPR",
        "entity_identifier": plate,
        "entity_type": "SUV",
        "confidence": 0.96,
        "color": "White",
        "speed_kmh": 68.0,
        "bounding_box": {"x": 100, "y": 120, "width": 200, "height": 140}
    }
    resp = client.post("/api/v1/analytics/events", json=event_payload)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "success"
    assert data["alert_triggered"] is True
    assert data["alert"]["matched_entity"] == plate

    alerts_resp = client.get(f"/api/v1/alerts?camera_id={cam_id}")
    assert alerts_resp.status_code == 200
    alerts = alerts_resp.json()
    assert len(alerts) > 0

    alert_id = alerts[0]["id"]
    ack_resp = client.patch(f"/api/v1/alerts/{alert_id}/acknowledge", json={"acknowledged_by": "test_operator"})
    assert ack_resp.status_code == 200
    assert ack_resp.json()["status"] == "ACKNOWLEDGED"

    resolve_resp = client.patch(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"resolved_by": "test_officer", "resolution_notes": "Suspect apprehended"}
    )
    assert resolve_resp.status_code == 200
    assert resolve_resp.json()["status"] == "RESOLVED"

def test_vehicle_trajectory_trace():
    uid = str(uuid.uuid4())[:8].upper()
    cam_a = f"CAM-TRA-{uid}"
    cam_b = f"CAM-TRB-{uid}"
    plate = f"GJ01TR{uid}"

    client.post("/api/v1/cameras", json={
        "id": cam_a,
        "name": "Checkpoint A",
        "department": "Traffic Police",
        "latitude": 23.01,
        "longitude": 72.51,
        "stream_url": "/assets/videos/feed1_junction.mp4"
    })
    client.post("/api/v1/cameras", json={
        "id": cam_b,
        "name": "Checkpoint B",
        "department": "Traffic Police",
        "latitude": 23.09,
        "longitude": 72.59,
        "stream_url": "/assets/videos/feed1_junction.mp4"
    })

    client.post("/api/v1/analytics/events", json={
        "camera_id": cam_a,
        "entity_identifier": plate,
        "entity_type": "SEDAN",
        "confidence": 0.94
    })
    client.post("/api/v1/analytics/events", json={
        "camera_id": cam_b,
        "entity_identifier": plate,
        "entity_type": "SEDAN",
        "confidence": 0.97
    })

    trace_resp = client.get(f"/api/v1/analytics/trace/{plate}")
    assert trace_resp.status_code == 200
    data = trace_resp.json()
    assert data["entity_identifier"] == plate
    assert data["total_detections"] == 2
    assert len(data["trail"]) == 2

def test_system_stats():
    resp = client.get("/api/v1/stats")
    assert resp.status_code == 200
    stats = resp.json()
    assert "total_cameras" in stats
    assert "total_active_alerts" in stats
