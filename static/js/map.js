export class C4IMap {
  constructor(containerId) {
    this.containerId = containerId;
    this.map = null;
    this.cameraMarkers = new Map();
    this.traceLayerGroup = null;
    this.activeAlertCameras = new Set();
  }

  init() {
    if (this.map) return;

    this.map = L.map(this.containerId, {
      zoomControl: true,
      attributionControl: false
    }).setView([23.08, 72.58], 11);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19
    }).addTo(this.map);

    this.traceLayerGroup = L.layerGroup().addTo(this.map);
  }

  updateCameraMarkers(cameras) {
    cameras.forEach(cam => {
      const isAlert = this.activeAlertCameras.has(cam.id);
      let bg = '#22c55e';
      if (isAlert) bg = '#ef4444';
      else if (cam.status === 'DEGRADED') bg = '#f59e0b';
      else if (cam.status === 'OFFLINE') bg = '#94a3b8';

      const icon = L.divIcon({
        className: 'basic-cam-icon',
        html: `<div style="background:${bg}; color:#fff; font-size:10px; font-weight:700; width:22px; height:22px; border-radius:50%; display:flex; align-items:center; justify-content:center; border:2px solid #fff; box-shadow:0 1px 3px rgba(0,0,0,0.3);" title="${cam.name}">${cam.id.replace('CAM-', '')}</div>`,
        iconSize: [22, 22],
        iconAnchor: [11, 11]
      });

      if (this.cameraMarkers.has(cam.id)) {
        const marker = this.cameraMarkers.get(cam.id);
        marker.setIcon(icon);
        marker.setLatLng([cam.latitude, cam.longitude]);
      } else {
        const marker = L.marker([cam.latitude, cam.longitude], { icon })
          .bindPopup(`
            <div style="font-size:12px; line-height:1.4;">
              <strong>${cam.name}</strong><br/>
              <span>ID: ${cam.id} | ${cam.zone}</span><br/>
              <span>Status: <strong>${cam.status}</strong> (${cam.fps} FPS)</span><br/>
              <span style="color:#64748b;">${cam.camera_type} (${cam.protocol})</span>
            </div>
          `);
        marker.addTo(this.map);
        this.cameraMarkers.set(cam.id, marker);
      }
    });
  }

  setCameraAlertState(cameraId, isAlert) {
    if (isAlert) {
      this.activeAlertCameras.add(cameraId);
    } else {
      this.activeAlertCameras.delete(cameraId);
    }
  }

  renderVehicleTrace(traceData) {
    this.clearVehicleTrace();
    if (!traceData.trail || traceData.trail.length === 0) return;

    const latlngs = [];
    traceData.trail.forEach((point, index) => {
      const latlng = [point.latitude, point.longitude];
      latlngs.push(latlng);

      const timeStr = new Date(point.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
      const waypointIcon = L.divIcon({
        className: 'basic-waypoint-icon',
        html: `
          <div style="background:#2563eb; color:#fff; font-weight:700; font-size:11px; border-radius:50%; width:22px; height:22px; display:flex; align-items:center; justify-content:center; border:2px solid #fff; box-shadow:0 1px 4px rgba(0,0,0,0.3);">
            ${index + 1}
          </div>
        `,
        iconSize: [22, 22],
        iconAnchor: [11, 11]
      });

      const marker = L.marker(latlng, { icon: waypointIcon }).bindPopup(`
        <div style="font-size:12px;">
          <strong>Stop ${index + 1}: ${point.camera_name}</strong><br/>
          <span>Time: ${timeStr}</span><br/>
          <span>Confidence: ${(point.confidence * 100).toFixed(0)}%</span>
          ${point.speed_kmh ? `<br/><span>Speed: ${point.speed_kmh} km/h</span>` : ''}
        </div>
      `);
      this.traceLayerGroup.addLayer(marker);
    });

    const routePolyline = L.polyline(latlngs, {
      color: '#2563eb',
      weight: 4,
      opacity: 0.8
    });
    this.traceLayerGroup.addLayer(routePolyline);

    if (latlngs.length > 1) {
      this.map.fitBounds(routePolyline.getBounds(), { padding: [40, 40] });
    } else {
      this.map.setView(latlngs[0], 14);
    }
  }

  clearVehicleTrace() {
    if (this.traceLayerGroup) {
      this.traceLayerGroup.clearLayers();
    }
  }
}
