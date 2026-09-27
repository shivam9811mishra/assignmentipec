# okDriver CCTV Video Analytics & Real-Time Alert Platform
## Complete Technical Architecture & Code Flow Documentation

---

## 1. Project Overview & Objective

The **okDriver CCTV Monitoring & Video Analytics Platform** is a centralized operational command prototype designed to ingest video streams, receive edge AI inference metadata, correlate license plates against an active watchlist, broadcast immediate alerts to operators without page reload, and visually reconstruct historical vehicle movement across checkpoints on a GIS map.

This platform directly aligns with the **Gujarat Police Innovation Hackathon 2026** problem statement regarding heterogeneous CCTV infrastructure, real-time alert dispatch, watchlist matching, and scalability toward **80,000 cameras**.

---

## 2. High-Level System Architecture

```
+---------------------------------------------------------------------------------------+
|                                FRONTEND CLIENT (Vanilla JS SPA)                       |
|  - index.html        : Clean dashboard UI (Navbar, Video Grid, Map, Alerts, Detections)|
|  - static/js/app.js  : Main coordinator and event binder                             |
|  - static/js/map.js  : Leaflet GIS map with custom camera pins & route polylines      |
|  - static/js/ws.js   : WebSocket client with synthesized Web Audio alert chime        |
|  - static/js/video.js: Canvas bounding box overlay engine over video feeds            |
+------------------------------------------+--------------------------------------------+
                                           | HTTP REST (/api/v1) & WebSocket (/ws/live)
                                           v
+---------------------------------------------------------------------------------------+
|                                BACKEND APPLICATION (FastAPI)                          |
|  app/main.py -> Routers -> Services -> Models -> SQLite / PostgreSQL                  |
+---------------------------------------------------------------------------------------+
        ^                                      ^                         |
        | Ingestion API                        | Database Session        | Real-Time Push
+-------+--------------------+     +-----------+-----------+   +---------v---------+
| AI TRAFFIC SIMULATOR       |     | okdriver_cctv.db      |   | WebSocket Hub     |
| (simulator/traffic_feeder) |     | - cameras             |   | (ConnectionManager|
| - ANPR detections          |     | - detection_events    |   | in websocket_mgr) |
| - Speed & coordinates      |     | - watchlist_records   |   +-------------------+
| - Target plate injection   |     | - alerts              |
+----------------------------+     | - audit_logs          |
                                   +-----------------------+
```

---

## 3. End-to-End Code Flow: From `main.py` to Frontend

This section traces execution from application startup down to individual request and event handling.

### Phase 1: Application Boot & Database Initialization
1. **Entrypoint (`app/main.py`)**:
   - `from app.database import engine, Base` is imported.
   - `Base.metadata.create_all(bind=engine)` executes at module load time. SQLAlchemy inspects all registered models (`Camera`, `DetectionEvent`, `WatchlistRecord`, `Alert`, `AuditLog`) and automatically creates any missing tables in `okdriver_cctv.db`.
   - `FastAPI(lifespan=lifespan)` is instantiated with CORS middleware configured for open development access.
   - The API routers are registered under `/api/v1`:
     - `cameras.router` (`/api/v1/cameras`)
     - `analytics.router` (`/api/v1/analytics`)
     - `watchlist.router` (`/api/v1/watchlist`)
     - `alerts.router` (`/api/v1/alerts`)
     - `stats.router` (`/api/v1/stats`)
     - `ws.router` (`/ws/live`)
   - Static files (`/static` and `/assets`) are mounted, and the root endpoint `GET /` serves `static/index.html`.

2. **Database Engine Setup (`app/database.py`)**:
   - Connects to the SQLite file using `check_same_thread=False` to safely handle asynchronous FastAPI workers.
   - Provides the `get_db()` generator dependency yielding isolated database sessions per request and guaranteeing clean closure in a `finally:` block.

---

### Phase 2: Operator Connects (Frontend Initialization)
When an operator navigates to `http://127.0.0.1:8000`:
1. `static/index.html` loads the DOM structure and imports `static/js/app.js` as an ES module.
2. `C4IApp.init()` executes:
   - **Map Init**: `map.init()` instantiates Leaflet on `#leafletMap`, sets view to Gujarat (`[23.08, 72.58]`), and adds OpenStreetMap tiles.
   - **Initial REST Fetch**: Calls `Promise.all` fetching:
     - `GET /api/v1/cameras` -> renders camera markers on map and video stream cards.
     - `GET /api/v1/stats` -> updates the top 4 metric counters.
     - `GET /api/v1/alerts?limit=15` -> populates the Active Alerts list.
     - `GET /api/v1/analytics/events?limit=20` -> populates the Recent Detections list.
   - **WebSocket Connection**: `realtimeHub.connect()` initiates `ws://127.0.0.1:8000/ws/live`.
   - FastAPI's `ws.py` accepts the socket and registers it inside `ws_manager.active_connections`. The top header status updates to **Live Connected**.

---

### Phase 3: Camera Onboarding Flow

```
[User clicks "Add Camera" in UI]
       |
       v
static/js/app.js (cameraForm submit event)
       |
       v HTTP POST JSON
app/routers/cameras.py (onboard_camera)
       |
       v
app/services/camera_service.py (create_camera)
       |--> Validate duplicate camera ID
       |--> Insert row into "cameras" table
       |--> Insert row into "audit_logs" table (action="CAMERA_ONBOARDED")
       |--> db.commit() & db.refresh()
       |
       v
app/websocket_manager.py (broadcast_camera_status)
       |--> Sends {"type": "CAMERA_STATUS_UPDATE", ...} to all connected WebSocket clients
       |
       v
Frontend WebSocket listener receives event:
       |--> Adds marker to Leaflet map
       |--> Updates total cameras counter
```

---

### Phase 4: AI Detection Ingestion & Real-Time Alert Correlation Flow

This is the central operational pipeline of the platform:

```
[Edge Camera / traffic_feeder.py]
       |
       v HTTP POST /api/v1/analytics/events
       | Payload: {camera_id, entity_identifier="GJ01XX0001", confidence=0.96, bounding_box, ...}
       |
app/routers/analytics.py (ingest_detection_event)
       |
       v
app/services/analytics_service.py (process_detection_event)
       |
       |-- 1. Normalize Plate:
       |      normalize_plate("GJ 01 XX 0001") -> "GJ01XX0001"
       |
       |-- 2. Update Camera Heartbeat:
       |      camera.last_heartbeat = utc_now(); camera.status = "ONLINE"
       |
       |-- 3. Deduplication Check:
       |      Queries detection_events in the last 15 seconds for this camera & plate.
       |      Prevents event floods and repeated alert storms.
       |
       |-- 4. Persist Detection:
       |      Inserts new DetectionEvent row into database.
       |
       |-- 5. Watchlist Correlation:
       |      Queries watchlist_records WHERE entity_identifier == "GJ01XX0001" AND is_active == True
       |
       |   [IF MATCH FOUND and confidence >= 0.75]:
       |      Calls app/services/alert_service.py (create_alert)
       |      Creates new Alert row with status="PENDING", severity=watchlist.severity
       |      Constructs alert_dict payload
       |
       v
app/websocket_manager.py
       |--> Broadcasts {"type": "NEW_DETECTION", data: detection_payload}
       |--> Broadcasts {"type": "NEW_ALERT", data: alert_payload} (if alert triggered)
       |
       v
[Frontend Browser Client]
       |
       |-- On NEW_DETECTION:
       |      - Prepends row to Recent Detections list
       |      - Increments Today's Detections counter
       |      - Draws green Canvas bounding box over video stream for 3 seconds
       |
       |-- On NEW_ALERT:
              - Synthesizes dual-frequency 880Hz -> 440Hz alert sound via Web Audio API
              - Prepends alert card to Active Alerts section with red left border
              - Increments Active Alerts counter
              - Turns camera pin red/pulsing on Leaflet map
```

---

### Phase 5: GIS Vehicle Trajectory & Route Reconstruction Flow

When an officer needs to reconstruct the chronological movement of a vehicle across multiple CCTV nodes (e.g., `GJ01XX0001`):

```
[Operator types "GJ01XX0001" into search box & clicks "Trace Vehicle"]
       |
       v
static/js/app.js (traceVehicle)
       |
       v HTTP GET /api/v1/analytics/trace/GJ01XX0001
app/routers/analytics.py (trace_vehicle)
       |
       v
app/services/trace_service.py (get_vehicle_trace)
       |
       |-- 1. Normalizes target plate string.
       |-- 2. Queries detection_events joined with cameras, sorted chronologically:
       |      SELECT * FROM detection_events WHERE entity_identifier = 'GJ01XX0001'
       |      ORDER BY timestamp ASC;
       |-- 3. Checks if entity exists in active watchlist_records.
       |-- 4. Assembles VehicleTraceResponse with trail coordinates:
       |      [
       |        {camera_id: "CAM-001", lat: 23.0305, lon: 72.5076, time: "10:02", speed: 58},
       |        {camera_id: "CAM-002", lat: 23.0270, lon: 72.5990, time: "10:18", speed: 42},
       |        {camera_id: "CAM-006", lat: 23.0734, lon: 72.6266, time: "10:35", speed: 65},
       |        {camera_id: "CAM-003", lat: 23.2156, lon: 72.6369, time: "10:52", speed: 78}
       |      ]
       |
       v Returns JSON to Frontend
static/js/map.js (renderVehicleTrace)
       |
       |-- 1. Clears existing route overlays.
       |-- 2. Renders numbered circular waypoint markers (1, 2, 3, 4) at each camera location.
       |-- 3. Draws connecting route polyline across all checkpoints.
       |-- 4. Calls map.fitBounds() to zoom and center smoothly on the vehicle's trajectory.
       |-- 5. Displays active trace summary bar with total checkpoint count.
```

---

### Phase 6: Alert Triage & Resolution Flow

```
[Operator clicks "Acknowledge" on Alert Card]
       |
       v HTTP PATCH /api/v1/alerts/{id}/acknowledge
app/services/alert_service.py:
       - alert.status = "ACKNOWLEDGED"
       - alert.acknowledged_at = utc_now()
       - Writes AuditLog (action="ALERT_ACKNOWLEDGED")
       - WebSocket broadcasts {"type": "ALERT_STATUS_UPDATE", status: "ACKNOWLEDGED"}
       - Card border turns amber

[Operator clicks "Resolve" & enters officer notes]
       |
       v HTTP PATCH /api/v1/alerts/{id}/resolve
app/services/alert_service.py:
       - alert.status = "RESOLVED"
       - alert.resolution_notes = "Vehicle intercepted by highway patrol"
       - Writes AuditLog (action="ALERT_RESOLVED")
       - WebSocket broadcasts {"type": "ALERT_STATUS_UPDATE", status: "RESOLVED"}
       - Camera pin turns back to green (online)
       - Active alert counter decrements
```

---

## 4. Database Schema & Data Models

All models inherit from SQLAlchemy's `Base` in `app/models.py`:

| Table Name | Key Columns | Purpose |
| :--- | :--- | :--- |
| `cameras` | `id` (PK), `name`, `department`, `latitude`, `longitude`, `camera_type`, `protocol`, `stream_url`, `status`, `last_heartbeat`, `zone`, `fps` | Registry of all physical and simulated camera assets with health metadata. |
| `detection_events` | `id` (PK), `camera_id` (FK), `timestamp`, `event_type`, `entity_identifier`, `entity_type`, `confidence`, `color`, `speed_kmh`, `bounding_box` | Time-series log of all vehicle and entity detections produced by computer vision inference. |
| `watchlist_records` | `id` (PK), `entity_identifier` (Unique), `category`, `severity`, `owner_or_suspect`, `description`, `notes`, `is_active` | Law enforcement register of flagged entities (Stolen, Wanted, Suspicious). |
| `alerts` | `id` (PK), `camera_id` (FK), `watchlist_id` (FK), `detection_event_id` (FK), `severity`, `status`, `matched_entity`, `acknowledged_by`, `resolution_notes` | Actionable security incidents generated when a detection matches an active watchlist record. |
| `audit_logs` | `id` (PK), `user_id`, `action`, `entity_type`, `entity_id`, `details`, `timestamp` | Immutable compliance and chain-of-custody audit log for forensic accountability. |

---

## 5. Frontend Modular Architecture

The client is built with native Vanilla ES Modules with zero heavy build tool requirements:

- **`static/index.html`**: Semantic layout containing the top navigation, statistics cards, live video matrix, Leaflet map container, alert triage column, and modal forms.
- **`static/css/style.css`**: Basic, clean CSS design with standard system fonts, neutral slate colors, standard cards, and clear status badges.
- **`static/js/api.js`**: Reusable async fetch wrapper handling all REST calls to `/api/v1/*`.
- **`static/js/websocket.js`**: `RealtimeHub` class managing the persistent WebSocket connection, automatic reconnect with exponential backoff, and synthesizing alert chimes using the browser's native Web Audio API oscillators.
- **`static/js/map.js`**: `C4IMap` class managing Leaflet markers, color-coded camera pins, popup cards, and vehicle trajectory polyline rendering.
- **`static/js/video_grid.js`**: `VideoGridManager` class that manages HTML5 video playback and renders lightweight bounding box rectangles on Canvas elements above the video whenever a detection event fires for that camera.
- **`static/js/app.js`**: `C4IApp` coordinator class initializing all modules, binding form submissions, and connecting WebSocket listeners to UI elements.

---

## 6. Video Integration & Simulation Engine

1. **Synthetic Video Feeds (`simulator/generate_sample_videos.py`)**:
   - Uses OpenCV to generate realistic MP4 video loops (`feed1_junction.mp4`, `feed2_station.mp4`, `feed3_highway.mp4`).
   - Draws multi-lane roads, moving vehicle blocks, camera watermarks, and live timestamps.
   - Saved to `static/assets/videos/` and served as standard HTTP video streams.

2. **AI Traffic Feeder (`simulator/traffic_feeder.py`)**:
   - Autonomous background service simulating live edge detections.
   - Randomly samples camera nodes and generates realistic ANPR payloads with speeds, confidence scores, and bounding boxes.
   - Periodically injects target watchlist vehicles (such as `GJ01XX0001` and `GJ05AB1234`), demonstrating instant alerts and real-time dashboard updates.

---

## 7. Scalability Roadmap to 80,000 Cameras

Addressing the production and distributed deployment requirements of the Gujarat Police Hackathon 2026:

### 1. Edge-First Metadata Extraction
Streaming 80,000 continuous 1080p video streams across WAN requires approximately **240 Gbps bandwidth**, which causes network saturation and extreme cloud egress costs.
- **Solution**: Run computer vision models (e.g. TensorRT YOLOv8 + LPRNet) directly at the edge on industrial mini-PCs or NVIDIA Jetson units located at each traffic junction.
- Only structured JSON metadata (<2 KB per detection) and small license plate thumbnail crops are transmitted upstream via secure MQTT/HTTPS.
- Full HD video streams remain buffered on local edge NVR storage (7-14 days) and are pulled to central operators on-demand only when a feed is actively selected for viewing.
- **Result**: Network bandwidth consumption is reduced by **greater than 98%**.

### 2. Regional Hub Aggregation
- Divide Gujarat into regional surveillance zones (Ahmedabad, Surat, Vadodara, Rajkot, Bhavnagar, Gandhinagar, Jamnagar, Junagadh).
- Each regional hub runs an edge aggregation cluster with Apache Kafka partitioned by `camera_zone` and `camera_id`, buffering and localizing high-throughput ingestion spikes.

### 3. Tiered Storage Model
- **Hot Tier (In-Memory)**: Redis cluster caching active watchlists and last-known camera heartbeat states (<1 ms lookup latency).
- **Warm Tier (Spatial-Temporal Analytics)**: TimescaleDB / ClickHouse hypertable partitioned monthly and indexed with GiST spatial indexes for sub-second trajectory tracing across millions of records.
- **Cold Tier (Archival)**: S3-compatible object storage (MinIO / AWS S3 Glacier) with automated lifecycle expiration for forensic video snapshots older than 30 days.

### 4. High Availability & Network Partition Tolerance
- Edge nodes retain a local SQLite / RocksDB buffer storing up to 72 hours of detections if WAN connectivity is lost.
- Upon reconnection, edge agents automatically replay buffered events with original timestamps, guaranteeing zero data loss.

---

## 8. How to Run the Platform

### Terminal 1: Backend Server
```powershell
cd D:\workspace\assignment
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2: AI Traffic Feeder
```powershell
cd D:\workspace\assignment
python simulator/traffic_feeder.py --interval 3.0
```

### Browser Access:
- **Operational Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger API Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Run Automated Test Suite**:
  ```powershell
  python -m pytest tests/test_api.py -v
  ```
