class RealtimeHub {
  constructor() {
    this.ws = null;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 30;
    this.listeners = {
      detection: [],
      alert: [],
      cameraStatus: [],
      alertStatus: [],
      connectionChange: []
    };
    this.audioContext = null;
    this.soundEnabled = true;
  }

  initAudio() {
    if (!this.audioContext) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (AudioCtx) {
        this.audioContext = new AudioCtx();
      }
    }
  }

  playAlertSound() {
    if (!this.soundEnabled) return;
    try {
      this.initAudio();
      if (!this.audioContext) return;
      if (this.audioContext.state === 'suspended') {
        this.audioContext.resume();
      }

      const osc1 = this.audioContext.createOscillator();
      const gain1 = this.audioContext.createGain();
      osc1.type = 'sawtooth';
      osc1.frequency.setValueAtTime(880, this.audioContext.currentTime);
      osc1.frequency.exponentialRampToValueAtTime(440, this.audioContext.currentTime + 0.15);
      gain1.gain.setValueAtTime(0.2, this.audioContext.currentTime);
      gain1.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.25);
      osc1.connect(gain1);
      gain1.connect(this.audioContext.destination);
      osc1.start();
      osc1.stop(this.audioContext.currentTime + 0.25);

      const osc2 = this.audioContext.createOscillator();
      const gain2 = this.audioContext.createGain();
      osc2.type = 'sawtooth';
      osc2.frequency.setValueAtTime(880, this.audioContext.currentTime + 0.25);
      osc2.frequency.exponentialRampToValueAtTime(440, this.audioContext.currentTime + 0.4);
      gain2.gain.setValueAtTime(0.25, this.audioContext.currentTime + 0.25);
      gain2.gain.exponentialRampToValueAtTime(0.01, this.audioContext.currentTime + 0.5);
      osc2.connect(gain2);
      gain2.connect(this.audioContext.destination);
      osc2.start(this.audioContext.currentTime + 0.25);
      osc2.stop(this.audioContext.currentTime + 0.5);
    } catch (e) {
      console.warn('Audio playback error:', e);
    }
  }

  connect() {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws/live`;

    this.notifyConnection('connecting');
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      this.notifyConnection('online');
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'NEW_DETECTION') {
          this.listeners.detection.forEach(cb => cb(msg.data));
        } else if (msg.type === 'NEW_ALERT') {
          this.playAlertSound();
          this.listeners.alert.forEach(cb => cb(msg.data));
        } else if (msg.type === 'CAMERA_STATUS_UPDATE') {
          this.listeners.cameraStatus.forEach(cb => cb(msg.data));
        } else if (msg.type === 'ALERT_STATUS_UPDATE') {
          this.listeners.alertStatus.forEach(cb => cb(msg.data));
        }
      } catch (err) {
        console.error('Error handling WebSocket message:', err);
      }
    };

    this.ws.onclose = () => {
      this.notifyConnection('offline');
      this.scheduleReconnect();
    };

    this.ws.onerror = () => {
      this.notifyConnection('offline');
      if (this.ws) this.ws.close();
    };
  }

  scheduleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const timeout = Math.min(1000 * Math.pow(1.5, this.reconnectAttempts), 10000);
      setTimeout(() => this.connect(), timeout);
    }
  }

  notifyConnection(status) {
    this.listeners.connectionChange.forEach(cb => cb(status));
  }

  on(event, callback) {
    if (this.listeners[event]) {
      this.listeners[event].push(callback);
    }
  }
}

export const realtimeHub = new RealtimeHub();
