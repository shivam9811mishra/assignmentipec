import { api } from './api.js';
import { realtimeHub } from './websocket.js';
import { C4IMap } from './map.js';
import { VideoGridManager } from './video_grid.js';

class C4IApp {
  constructor() {
    this.map = new C4IMap('leafletMap');
    this.videoGrid = new VideoGridManager('videoTilesContainer');
    this.cameras = [];
  }

  async init() {
    this.map.init();
    this.setupEventListeners();
    this.setupWebSocketListeners();

    await this.loadInitialData();
    realtimeHub.connect();
    setInterval(() => this.refreshStats(), 15000);
  }

  async loadInitialData() {
    try {
      const [cameras, stats, alerts, detections] = await Promise.all([
        api.getCameras(),
        api.getSystemStats(),
        api.getAlerts({ limit: 15 }),
        api.getRecentDetections(20)
      ]);

      this.cameras = cameras;
      this.updateStatsDisplay(stats);
      this.map.updateCameraMarkers(this.cameras);
      this.videoGrid.renderStreams(this.cameras);
      this.renderAlerts(alerts);
      this.renderDetections(detections);
    } catch (err) {
      console.error('Initialization error:', err);
    }
  }

  async refreshStats() {
    try {
      const stats = await api.getSystemStats();
      this.updateStatsDisplay(stats);
    } catch (e) {}
  }

  updateStatsDisplay(stats) {
    document.getElementById('statTotalCameras').innerText = stats.total_cameras;
    document.getElementById('statOnlineCameras').innerText = stats.online_cameras;
    document.getElementById('statDegradedCameras').innerText = stats.degraded_cameras;
    document.getElementById('statOfflineCameras').innerText = stats.offline_cameras;
    document.getElementById('statActiveAlerts').innerText = stats.total_active_alerts;
    document.getElementById('statDetectionsToday').innerText = stats.total_detections_today;
  }

  renderAlerts(alerts) {
    const list = document.getElementById('alertsList');
    list.innerHTML = '';
    if (alerts.length === 0) {
      list.innerHTML = '<div style="font-size:12px; color:#64748b; padding:8px 0;">No active alerts.</div>';
      return;
    }
    alerts.forEach(alert => this.prependAlertItem(alert));
  }

  prependAlertItem(alert) {
    const list = document.getElementById('alertsList');
    const existingPlaceholder = list.querySelector('div[style*="No active alerts"]');
    if (existingPlaceholder) existingPlaceholder.remove();

    const existing = document.getElementById(`alertItem_${alert.id}`);
    if (existing) existing.remove();

    const item = document.createElement('div');
    item.className = `alert-item ${alert.status.toLowerCase()}`;
    item.id = `alertItem_${alert.id}`;

    const timeStr = new Date(alert.triggered_at).toLocaleTimeString();
    item.innerHTML = `
      <div class="alert-item-header">
        <span>${alert.matched_entity} (${alert.matched_category})</span>
        <span style="font-size:11px; font-weight:normal; color:#64748b;">${timeStr}</span>
      </div>
      <div class="alert-item-body">
        Camera: <strong>${alert.camera_name || alert.camera_id}</strong> (${alert.camera_zone || 'Zone'})<br/>
        Confidence: ${(alert.confidence * 100).toFixed(0)}% | Status: <strong>${alert.status}</strong>
      </div>
      <div class="alert-item-actions">
        <button class="btn btn-sm btn-trace" data-plate="${alert.matched_entity}">Trace</button>
        ${alert.status === 'PENDING' ? `
          <button class="btn btn-sm btn-ack" data-id="${alert.id}">Acknowledge</button>
        ` : ''}
        ${alert.status !== 'RESOLVED' ? `
          <button class="btn btn-sm btn-resolve" data-id="${alert.id}">Resolve</button>
        ` : ''}
      </div>
    `;

    item.querySelector('.btn-trace').addEventListener('click', () => {
      this.traceVehicle(alert.matched_entity);
    });

    const ackBtn = item.querySelector('.btn-ack');
    if (ackBtn) {
      ackBtn.addEventListener('click', async () => {
        await api.acknowledgeAlert(alert.id);
        this.refreshStats();
      });
    }

    const resBtn = item.querySelector('.btn-resolve');
    if (resBtn) {
      resBtn.addEventListener('click', async () => {
        const notes = prompt('Enter resolution notes:', 'Vehicle flagged and resolved');
        if (notes) {
          await api.resolveAlert(alert.id, notes);
          this.refreshStats();
        }
      });
    }

    list.prepend(item);
    this.map.setCameraAlertState(alert.camera_id, alert.status === 'PENDING');
    this.map.updateCameraMarkers(this.cameras);
  }

  renderDetections(detections) {
    const stream = document.getElementById('detectionsStream');
    stream.innerHTML = '';
    detections.forEach(det => this.prependDetectionItem(det));
  }

  prependDetectionItem(det) {
    const stream = document.getElementById('detectionsStream');
    const row = document.createElement('div');
    row.className = 'detection-item';

    const timeStr = new Date(det.timestamp).toLocaleTimeString();
    row.innerHTML = `
      <div>
        <span class="plate-badge">${det.entity_identifier}</span>
        <span style="color:#64748b; font-size:11px; margin-left:4px;">${det.entity_type}</span>
        <div style="font-size:11px; color:#64748b;">${det.camera_name || det.camera_id} (${timeStr})</div>
      </div>
      <div style="text-align:right;">
        <span style="font-weight:600; color:#16a34a;">${(det.confidence * 100).toFixed(0)}%</span>
        ${det.speed_kmh ? `<div style="color:#64748b;">${det.speed_kmh} km/h</div>` : ''}
      </div>
    `;

    row.addEventListener('click', () => {
      this.traceVehicle(det.entity_identifier);
    });

    stream.prepend(row);
    while (stream.children.length > 25) {
      stream.removeChild(stream.lastChild);
    }
  }

  async traceVehicle(plate) {
    if (!plate) return;
    const cleanPlate = plate.toUpperCase().trim();
    document.getElementById('traceSearchInput').value = cleanPlate;

    try {
      const traceData = await api.traceVehicle(cleanPlate);
      this.map.renderVehicleTrace(traceData);

      const banner = document.getElementById('traceActiveBanner');
      banner.style.display = 'flex';
      document.getElementById('tracePlateDisplay').innerText = traceData.entity_identifier;
      document.getElementById('traceCountDisplay').innerText = `(${traceData.total_detections} Checkpoints)`;
      document.getElementById('traceWatchlistBadge').style.display = traceData.is_watchlisted ? 'inline' : 'none';
    } catch (err) {
      alert(`No trace history found for ${cleanPlate}`);
    }
  }

  clearTrace() {
    this.map.clearVehicleTrace();
    document.getElementById('traceActiveBanner').style.display = 'none';
    document.getElementById('traceSearchInput').value = '';
    this.map.updateCameraMarkers(this.cameras);
  }

  setupEventListeners() {
    const searchBtn = document.getElementById('btnSearchTrace');
    const searchInput = document.getElementById('traceSearchInput');
    searchBtn.addEventListener('click', () => {
      this.traceVehicle(searchInput.value);
    });
    searchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') this.traceVehicle(searchInput.value);
    });

    document.getElementById('btnClearTrace').addEventListener('click', () => {
      this.clearTrace();
    });

    const btnAudio = document.getElementById('btnToggleAudio');
    btnAudio.addEventListener('click', () => {
      realtimeHub.soundEnabled = !realtimeHub.soundEnabled;
      btnAudio.innerText = realtimeHub.soundEnabled ? 'Sound: On' : 'Sound: Off';
    });

    this.setupModals();
  }

  setupModals() {
    const camModal = document.getElementById('cameraModal');
    document.getElementById('btnOpenCameras').addEventListener('click', async () => {
      camModal.classList.add('active');
      await this.loadCameraTable();
    });
    document.getElementById('btnCloseCameras').addEventListener('click', () => {
      camModal.classList.remove('active');
    });

    const wlModal = document.getElementById('watchlistModal');
    document.getElementById('btnOpenWatchlist').addEventListener('click', async () => {
      wlModal.classList.add('active');
      await this.loadWatchlistTable();
    });
    document.getElementById('btnCloseWatchlist').addEventListener('click', () => {
      wlModal.classList.remove('active');
    });

    document.getElementById('camProtocol').addEventListener('change', (e) => {
      const streamInput = document.getElementById('camStreamUrl');
      if (e.target.value === 'WEBCAM') {
        streamInput.value = 'webcam';
      } else if (e.target.value === 'HLS' && streamInput.value === 'webcam') {
        streamInput.value = 'https://test-streams.mux.dev/x36xhzz/x36xhzz.m3u8';
      } else if (e.target.value === 'SIMULATED' && streamInput.value === 'webcam') {
        streamInput.value = '/assets/videos/feed1_junction.mp4';
      }
    });

    document.getElementById('cameraForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        id: document.getElementById('camId').value.trim(),
        name: document.getElementById('camName').value.trim(),
        department: document.getElementById('camDept').value.trim(),
        latitude: parseFloat(document.getElementById('camLat').value),
        longitude: parseFloat(document.getElementById('camLon').value),
        camera_type: document.getElementById('camType').value,
        protocol: document.getElementById('camProtocol').value,
        stream_url: document.getElementById('camStreamUrl').value.trim(),
        zone: document.getElementById('camZone').value.trim(),
        status: 'ONLINE'
      };

      try {
        await api.onboardCamera(payload);
        alert(`Camera ${payload.id} added!`);
        document.getElementById('cameraForm').reset();
        await this.loadCameraTable();
        this.cameras = await api.getCameras();
        this.map.updateCameraMarkers(this.cameras);
        this.videoGrid.renderStreams(this.cameras);
        this.refreshStats();
      } catch (err) {
        alert(err.message);
      }
    });

    document.getElementById('watchlistForm').addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        entity_identifier: document.getElementById('wlIdentifier').value.trim(),
        category: document.getElementById('wlCategory').value,
        severity: document.getElementById('wlSeverity').value,
        owner_or_suspect: document.getElementById('wlOwner').value.trim(),
        description: document.getElementById('wlDesc').value.trim(),
        is_active: true
      };

      try {
        await api.createWatchlistRecord(payload);
        alert(`Target ${payload.entity_identifier} added to Watchlist!`);
        document.getElementById('watchlistForm').reset();
        await this.loadWatchlistTable();
        this.refreshStats();
      } catch (err) {
        alert(err.message);
      }
    });
  }

  async loadCameraTable() {
    const cameras = await api.getCameras();
    const tbody = document.getElementById('camerasTableBody');
    tbody.innerHTML = '';
    cameras.forEach(cam => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${cam.id}</strong></td>
        <td>${cam.name}</td>
        <td>${cam.zone}</td>
        <td><span style="color:${cam.status === 'ONLINE' ? '#16a34a' : '#dc2626'};">${cam.status}</span></td>
        <td>
          <button class="btn btn-sm btn-cam-toggle" data-id="${cam.id}">
            ${cam.status === 'ONLINE' ? 'Set Degraded' : 'Set Online'}
          </button>
        </td>
      `;

      tr.querySelector('.btn-cam-toggle').addEventListener('click', async () => {
        const newStatus = cam.status === 'ONLINE' ? 'DEGRADED' : 'ONLINE';
        await api.updateCamera(cam.id, { status: newStatus });
        await this.loadCameraTable();
        this.cameras = await api.getCameras();
        this.map.updateCameraMarkers(this.cameras);
        this.refreshStats();
      });

      tbody.appendChild(tr);
    });
  }

  async loadWatchlistTable() {
    const records = await api.getWatchlist();
    const tbody = document.getElementById('watchlistTableBody');
    tbody.innerHTML = '';
    records.forEach(rec => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${rec.entity_identifier}</strong></td>
        <td>${rec.category}</td>
        <td>${rec.severity}</td>
        <td>${rec.description}</td>
        <td>
          <button class="btn btn-sm btn-trace-item" data-plate="${rec.entity_identifier}">Trace</button>
        </td>
      `;

      tr.querySelector('.btn-trace-item').addEventListener('click', () => {
        document.getElementById('watchlistModal').classList.remove('active');
        this.traceVehicle(rec.entity_identifier);
      });

      tbody.appendChild(tr);
    });
  }

  setupWebSocketListeners() {
    realtimeHub.on('connectionChange', (status) => {
      const el = document.getElementById('systemWsStatus');
      const text = document.getElementById('systemWsText');
      if (status === 'online') {
        el.className = 'status-badge';
        text.innerText = 'Live Connected';
      } else {
        el.className = 'status-badge offline';
        text.innerText = 'Disconnected';
      }
    });

    realtimeHub.on('detection', (detection) => {
      this.prependDetectionItem(detection);
      this.videoGrid.showDetectionOverlay(detection);
      const detCount = document.getElementById('statDetectionsToday');
      detCount.innerText = parseInt(detCount.innerText || 0) + 1;
    });

    realtimeHub.on('alert', (alert) => {
      this.prependAlertItem(alert);
      const alertCount = document.getElementById('statActiveAlerts');
      alertCount.innerText = parseInt(alertCount.innerText || 0) + 1;
    });

    realtimeHub.on('cameraStatus', (data) => {
      const cam = this.cameras.find(c => c.id === data.camera_id);
      if (cam) {
        cam.status = data.status;
        this.map.updateCameraMarkers(this.cameras);
      }
    });

    realtimeHub.on('alertStatus', (alert) => {
      this.prependAlertItem(alert);
      this.refreshStats();
    });
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const app = new C4IApp();
  app.init();
});
