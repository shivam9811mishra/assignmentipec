const API_BASE = '/api/v1';

export const api = {
  async getCameras(params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/cameras?${query}`);
    return res.json();
  },

  async onboardCamera(cameraData) {
    const res = await fetch(`${API_BASE}/cameras`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cameraData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to onboard camera');
    }
    return res.json();
  },

  async updateCamera(cameraId, cameraData) {
    const res = await fetch(`${API_BASE}/cameras/${cameraId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cameraData)
    });
    return res.json();
  },

  async deleteCamera(cameraId) {
    const res = await fetch(`${API_BASE}/cameras/${cameraId}`, {
      method: 'DELETE'
    });
    return res.json();
  },

  async getWatchlist(params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/watchlist?${query}`);
    return res.json();
  },

  async createWatchlistRecord(recordData) {
    const res = await fetch(`${API_BASE}/watchlist`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(recordData)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create watchlist record');
    }
    return res.json();
  },

  async getAlerts(params = {}) {
    const query = new URLSearchParams(params).toString();
    const res = await fetch(`${API_BASE}/alerts?${query}`);
    return res.json();
  },

  async acknowledgeAlert(alertId, acknowledgedBy = 'operator_desk_1') {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/acknowledge`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ acknowledged_by: acknowledgedBy })
    });
    return res.json();
  },

  async resolveAlert(alertId, resolutionNotes, resolvedBy = 'duty_officer') {
    const res = await fetch(`${API_BASE}/alerts/${alertId}/resolve`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resolution_notes: resolutionNotes, resolved_by: resolvedBy })
    });
    return res.json();
  },

  async getRecentDetections(limit = 30) {
    const res = await fetch(`${API_BASE}/analytics/events?limit=${limit}`);
    return res.json();
  },

  async traceVehicle(entityIdentifier) {
    const res = await fetch(`${API_BASE}/analytics/trace/${encodeURIComponent(entityIdentifier)}`);
    if (!res.ok) {
      throw new Error('Vehicle trace query failed');
    }
    return res.json();
  },

  async getSystemStats() {
    const res = await fetch(`${API_BASE}/stats`);
    return res.json();
  }
};
