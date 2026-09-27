# okDriver CCTV Monitoring & Video Analytics Platform

An integrated Command, Control, Communications, and Intelligence (C4I) surveillance prototype engineered for real-time video monitoring, edge AI metadata ingestion, watchlist correlation, and GIS vehicle trajectory reconstruction.

Aligned with the **Gujarat Police Innovation Hackathon 2026** problem statement and technical evaluation criteria.

---

## Architecture Overview

```
+-----------------------------------------------------------------------------------------+
|                                OPERATOR C4I DASHBOARD (Web)                              |
|  +--------------------+  +----------------------+  +------------------+  +------------+ |
|  | Multi-Stream Matrix|  | GIS Live & Trajectory|  | Watchlist Alerts |  | Telemetry  | |
|  +--------------------+  +----------------------+  +------------------+  +------------+ |
+--------------------------------------------+--------------------------------------------+
                                             | WebSocket (/ws/live) & REST (/api/v1)
                                             v
+-----------------------------------------------------------------------------------------+
|                                BACKEND API GATEWAY (FastAPI)                            |
|  +--------------------+  +----------------------+  +------------------+  +------------+ |
|  | Camera Registry    |  | AI Ingestion Service |  | Watchlist Matcher|  | Trace Eng. | |
|  +--------------------+  +----------------------+  +------------------+  +------------+ |
+--------------------------------------------+--------------------------------------------+
                                             |
                  +--------------------------+--------------------------+
                  v                                                     v
      +-----------------------+                             +-----------------------+
      |  Database (SQLAlchemy)|                             | WebSocket Hub         |
      |  - cameras            |                             | - Real-time alerts    |
      |  - detection_events   |                             | - Live ANPR stream    |
      |  - watchlist_records  |                             | - Heartbeat updates   |
      |  - alerts & audit     |                             +-----------------------+
      +-----------------------+
                  ^
                  | Ingestion API (/api/v1/analytics/events)
+-----------------+-------------------+
|  AI TRAFFIC SIMULATOR / EDGE AGENT  |
|  - Autonomous ANPR generator        |
|  - Watchlist target injection       |
|  - Dynamic bounding box coordinates |
+-------------------------------------+
```

---

## Core System Modules

### 1. Camera Registry & Health Monitoring
- Support for manual and programmatic onboarding (`POST /api/v1/cameras`).
- Records ID, name, department, geographic coordinates, protocol (RTSP, HLS, WebRTC, ONVIF, SIMULATED), stream URL, FPS, and zone.
- Continuous heartbeat monitoring with health state transitions (`ONLINE`, `DEGRADED`, `OFFLINE`).
- Full administrative audit trail for create, update, and delete actions.

### 2. Live Video Integration & Dynamic Annotation
- Multi-camera matrix supporting flexible grid layouts (`1x1`, `1x2`, `2x2`).
- Integrated CCTV video streams with timecode synchronization.
- Real-time Canvas overlay engine rendering dynamic bounding boxes and license plate tags directly over video streams when detections occur.

### 3. AI Ingestion & Watchlist Alert Engine
- High-throughput endpoint (`POST /api/v1/analytics/events`) validating incoming ANPR and object detection payloads.
- Plate normalization removing whitespace, hyphens, and casing irregularities.
- Configurable deduplication window (default 15 seconds) suppressing redundant hits at the same camera node.
- Instant exact and fuzzy correlation against active stolen, wanted, and blacklisted vehicle registers.
- Immediate WebSocket push with synthesized dual-tone audio chime and operator triage workflow (`PENDING` -> `ACKNOWLEDGED` -> `RESOLVED`).

### 4. GIS & Vehicle Trajectory Reconstruction
- Interactive Leaflet map centered on Gujarat smart city junctions with dark cartographic styling.
- Dynamic camera pins reflecting operational status and active alert states with visual pulses.
- **Vehicle Tracing**: Search any plate (e.g., `GJ01XX0001`) to reconstruct the vehicle's chronological journey across checkpoints, rendering numbered waypoint markers, route polylines, and inspection telemetry.

---

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2, WebSockets.
- **Frontend**: Vanilla ES Modules, Modern CSS with glassmorphism tokens, Leaflet GIS, HTML5 Canvas.
- **Database**: SQLite (local development) / PostgreSQL & TimescaleDB ready (RDS compatible).
- **Video & Vision Simulation**: OpenCV synthetic CCTV generator, Python autonomous traffic feeder.
- **Packaging**: Docker, Docker Compose.

---

## Project Structure

```
├── app/
│   ├── config.py              # Application settings and environment variables
│   ├── database.py            # Database engine and session dependency
│   ├── models.py              # SQLAlchemy models (Camera, Event, Watchlist, Alert, Audit)
│   ├── schemas.py             # Pydantic validation schemas
│   ├── websocket_manager.py   # Connection hub and broadcasting
│   ├── seed_data.py           # Preloaded Gujarat Police cameras & sample watchlists
│   ├── main.py                # FastAPI app initialization, routes, static mount
│   ├── services/
│   │   ├── camera_service.py
│   │   ├── analytics_service.py
│   │   ├── watchlist_service.py
│   │   ├── alert_service.py
│   │   └── trace_service.py
│   └── routers/
│       ├── cameras.py
│       ├── analytics.py
│       ├── watchlist.py
│       ├── alerts.py
│       ├── stats.py
│       └── ws.py
├── static/
│   ├── index.html             # Operational C4I Command Center interface
│   ├── css/
│   │   └── style.css          # Dark command center design system
│   ├── js/
│   │   ├── api.js             # REST client
│   │   ├── websocket.js       # WebSocket client & audio alert synthesizer
│   │   ├── map.js             # Leaflet GIS & vehicle trajectory renderer
│   │   ├── video_grid.js      # Video player & canvas bounding box engine
│   │   └── app.js             # UI coordinator
│   └── assets/
│       └── videos/            # Synthetic CCTV video loops
├── simulator/
│   ├── generate_sample_videos.py # CCTV stream generator
│   └── traffic_feeder.py      # Autonomous AI detection event generator
├── tests/
│   └── test_api.py            # Automated API verification test suite
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Getting Started

### Prerequisites
- Python 3.10 or higher
- pip

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone <repo-url>
cd assignment
python -m pip install -r requirements.txt
```

### 2. Generate Video Feeds (First Run)
Generate the synthetic CCTV feeds:
```bash
python simulator/generate_sample_videos.py
```

### 3. Launch the Server
Start the FastAPI server:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser to:
- **C4I Dashboard**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive OpenAPI Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 4. Start the AI Traffic Simulator (Separate Terminal)
In a second terminal, run the traffic feeder to push live detections and trigger watchlist alerts:
```bash
python simulator/traffic_feeder.py --interval 3.0
```

---

## Docker Deployment

To run the complete platform inside a container:
```bash
docker compose up --build
```
The platform will be available at `http://localhost:8000`.

---

## API Reference Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/v1/cameras` | List cameras with zone/status/search filters |
| `POST` | `/api/v1/cameras` | Onboard a new camera node |
| `PUT` | `/api/v1/cameras/{id}` | Update camera configuration or status |
| `POST` | `/api/v1/cameras/{id}/heartbeat` | Record camera heartbeat |
| `POST` | `/api/v1/analytics/events` | Ingest AI detection event (triggers alerts if matched) |
| `GET` | `/api/v1/analytics/events` | Retrieve recent detection events |
| `GET` | `/api/v1/analytics/trace/{plate}` | Reconstruct chronological vehicle trajectory across cameras |
| `GET` | `/api/v1/watchlist` | List watchlist records |
| `POST` | `/api/v1/watchlist` | Add a new target to the watchlist |
| `GET` | `/api/v1/alerts` | List real-time alerts |
| `PATCH` | `/api/v1/alerts/{id}/acknowledge` | Mark alert as acknowledged |
| `PATCH` | `/api/v1/alerts/{id}/resolve` | Resolve alert with operational notes |
| `GET` | `/api/v1/stats` | Telemetry metrics (camera health, alerts, detections) |
| `WS` | `/ws/live` | WebSocket stream for live events, alerts, and heartbeats |

---

## Scalability Roadmap: Path to 80,000 Cameras

Addressing the scalability requirements of the Gujarat Police Hackathon 2026:

### 1. Edge-First Metadata Extraction
Backhauling 80,000 uncompressed 1080p video streams requires ~240 Gbps of bandwidth, which is technically and economically impractical. 
- Edge devices (NVIDIA Jetson / x86 industrial PCs) run lightweight inference (YOLOv8 + OCR) locally.
- Only structured JSON metadata (<2 KB per event) and compressed cropped license plate thumbnails are transmitted upstream via MQTT/HTTPS.
- Full HD video streams remain buffered on edge storage (7-14 days) and are pulled to the central VMS on-demand only when requested by an operator.
- **Bandwidth Reduction**: >98% compared to continuous centralized video ingestion.

### 2. Tiered Regional Aggregation
- **Regional Hubs**: 8 regional zones (e.g., Ahmedabad, Surat, Vadodara, Rajkot, Bhavnagar, Gandhinagar, Jamnagar, Junagadh) each managing ~10,000 cameras.
- **Partitioned Kafka Clusters**: Event streams partitioned by `camera_zone` and `camera_id` ensuring linear horizontal throughput.

### 3. Tiered Storage Architecture
- **Hot Tier (In-Memory)**: Redis cluster storing active watchlists and last-known camera heartbeat states (<1 ms latency).
- **Warm Tier (Spatial-Temporal Analytics)**: TimescaleDB / ClickHouse hypertable partitioned by month and zone, with GiST spatial indexes on camera coordinates for sub-second trajectory tracing across millions of records.
- **Cold Tier (Archive)**: S3-compatible object storage (AWS S3 / MinIO) with automated lifecycle policies moving video clips to Glacier after 30 days.

### 4. High Availability & Disaster Recovery
- Multi-AZ Kubernetes deployment with active-active API replicas behind AWS Application Load Balancers.
- Edge local store-and-forward buffering up to 72 hours of events locally during network outages, seamlessly resynchronizing on reconnection.

---

## Automated Testing

Run the test suite:
```bash
python -m pytest tests/test_api.py -v
```
All 8 test suites validate camera onboarding, watchlist management, event ingestion, deduplication, alert lifecycle transitions, vehicle tracing, and operational telemetry.

---

## 3 to 5 Minute Demo Walkthrough Guide

1. **System Overview (0:00 - 0:45)**:
   - Point out the C4I dark dashboard layout, telemetry bar showing 6 preloaded cameras across Ahmedabad, Gandhinagar, Surat, and Vadodara.
   - Show the connection badge indicating active WebSocket synchronization.
2. **Live Feed & Canvas Overlays (0:45 - 1:30)**:
   - Highlight the 2x2 video matrix playing simulated CCTV junctions (SG Highway, Kalupur Station, Gandhinagar Checkpost).
   - Switch layout between 1x1, 1x2, and 2x2.
3. **AI Event Ingestion & Real-Time Alert (1:30 - 2:30)**:
   - Run `python simulator/traffic_feeder.py` in the terminal.
   - Observe incoming events in the live detection stream.
   - When a watchlist target (e.g., `GJ01XX0001` or `GJ05AB1234`) is detected:
     - The alert sounds with an audio chime.
     - The critical alert card appears at the top of the Alert Triage HUD.
     - The camera marker pulses red on the map.
     - Click **Acknowledge**, then **Resolve** with notes.
4. **GIS Vehicle Movement Tracing (2:30 - 3:30)**:
   - Enter `GJ01XX0001` in the GIS search box and click **Trace Route** (or click "Trace Route" on the alert card).
   - Watch the interactive map plot the numbered checkpoints (Stop 1: SG Highway -> Stop 2: Kalupur Station -> Stop 3: Airport Circle -> Stop 4: Gandhinagar RTO) with the directional cyan route polyline.
5. **Camera Registry & Watchlist Modals (3:30 - 4:15)**:
   - Open **Camera Registry**, onboard a new camera or toggle health between Online and Degraded.
   - Open **Watchlist**, add a new suspicious vehicle.
6. **Architecture & 80,000 Camera Roadmap (4:15 - 5:00)**:
   - Summarize edge-first metadata extraction, regional Kafka partitioning, and TimescaleDB spatial indexing.
