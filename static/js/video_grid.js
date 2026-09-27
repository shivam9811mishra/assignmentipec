export class VideoGridManager {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.activeCameras = [];
    this.canvasOverlays = new Map();
  }

  renderStreams(cameras) {
    const prioritized = [...cameras].sort((a, b) => {
      const aIsWebcam = a.protocol === 'WEBCAM' || a.stream_url === 'webcam';
      const bIsWebcam = b.protocol === 'WEBCAM' || b.stream_url === 'webcam';
      if (aIsWebcam && !bIsWebcam) return -1;
      if (!aIsWebcam && bIsWebcam) return 1;
      return 0;
    });
    this.activeCameras = prioritized.slice(0, 4);
    this.container.innerHTML = '';
    this.canvasOverlays.clear();

    this.activeCameras.forEach(cam => {
      const box = document.createElement('div');
      box.className = 'video-box';
      box.id = `videoBox_${cam.id}`;

      box.innerHTML = `
        <video id="videoElement_${cam.id}" autoplay loop muted playsinline crossorigin="anonymous"></video>
        <canvas id="canvasOverlay_${cam.id}" class="video-canvas"></canvas>
        <div class="video-caption">${cam.id} - ${cam.name}</div>
      `;

      this.container.appendChild(box);

      const video = box.querySelector('video');
      const url = cam.stream_url;

      if (url === 'webcam' || cam.protocol === 'WEBCAM' || url.startsWith('webcam')) {
        if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
          navigator.mediaDevices.getUserMedia({ video: true, audio: false })
            .then(stream => {
              video.srcObject = stream;
              video.play().catch(() => {});
            })
            .catch(err => {
              console.warn('Real webcam feed unavailable, falling back:', err);
              video.src = '/assets/videos/feed1_junction.mp4';
              video.play().catch(() => {});
            });
        }
      } else if (url.includes('.m3u8')) {
        if (window.Hls && window.Hls.isSupported()) {
          const hls = new window.Hls();
          hls.loadSource(url);
          hls.attachMedia(video);
          hls.on(window.Hls.Events.MANIFEST_PARSED, () => video.play().catch(() => {}));
        } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
          video.src = url;
          video.play().catch(() => {});
        }
      } else {
        video.src = url;
        video.play().catch(() => {});
      }

      const canvas = box.querySelector('canvas');
      const resizeCanvas = () => {
        canvas.width = box.clientWidth || 320;
        canvas.height = box.clientHeight || 180;
      };
      setTimeout(resizeCanvas, 150);
      window.addEventListener('resize', resizeCanvas);

      this.canvasOverlays.set(cam.id, {
        canvas,
        ctx: canvas.getContext('2d'),
        activeDetections: []
      });
    });
  }

  showDetectionOverlay(detection) {
    const entry = this.canvasOverlays.get(detection.camera_id);
    if (!entry) return;

    const { canvas, ctx, activeDetections } = entry;
    const now = Date.now();

    let bbox = { x: 120, y: 100, width: 220, height: 160 };
    if (detection.bounding_box) {
      try {
        const parsed = typeof detection.bounding_box === 'string' ? JSON.parse(detection.bounding_box) : detection.bounding_box;
        if (parsed.x !== undefined) bbox = parsed;
      } catch (e) {}
    }

    const scaleX = canvas.width / 640;
    const scaleY = canvas.height / 360;

    activeDetections.push({
      x: bbox.x * scaleX,
      y: bbox.y * scaleY,
      width: bbox.width * scaleX,
      height: bbox.height * scaleY,
      plate: detection.entity_identifier,
      entityType: detection.entity_type,
      confidence: detection.confidence,
      expiresAt: now + 3000
    });

    this.drawOverlays(detection.camera_id);
  }

  drawOverlays(cameraId) {
    const entry = this.canvasOverlays.get(cameraId);
    if (!entry) return;

    const { canvas, ctx } = entry;
    const now = Date.now();

    entry.activeDetections = entry.activeDetections.filter(d => d.expiresAt > now);
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    entry.activeDetections.forEach(det => {
      ctx.strokeStyle = '#22c55e';
      ctx.lineWidth = 2;
      ctx.strokeRect(det.x, det.y, det.width, det.height);

      ctx.fillStyle = '#22c55e';
      const label = `${det.plate} (${(det.confidence * 100).toFixed(0)}%)`;
      ctx.font = 'bold 11px sans-serif';
      const textWidth = ctx.measureText(label).width;
      ctx.fillRect(det.x, Math.max(0, det.y - 16), textWidth + 6, 16);

      ctx.fillStyle = '#ffffff';
      ctx.fillText(label, det.x + 3, Math.max(12, det.y - 4));
    });

    if (entry.activeDetections.length > 0) {
      requestAnimationFrame(() => this.drawOverlays(cameraId));
    }
  }
}
