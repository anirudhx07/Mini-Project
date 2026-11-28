/* COCKPIT ESP32-CAM & Webcam Feed Controller */

window.CockpitCamera = {
  streaming: false,
  activeStreamUrl: "",

  applyStatus(cam, camSerial = null) {
    if (!cam) return;
    const running = Boolean(cam.running);
    const status = cam.status || "DISCONNECTED";
    const isStreaming = status === "STREAMING" || status === "CONNECTED";

    // Independent CAM USB indicator (never affects Wi-Fi STREAMING status)
    if (camSerial) {
      const usbConn = Boolean(camSerial.connected);
      const topUsb = document.getElementById("topCamUsbStatus");
      const dotUsb = document.getElementById("dotCamUsb");
      if (topUsb && dotUsb) {
        topUsb.textContent = usbConn ? `CONNECTED (${camSerial.port})` : "DISCONNECTED";
        dotUsb.className = usbConn ? "dot dot-success" : "dot dot-muted";
      }
      const usbBadge = document.getElementById("camSerialConnBadge");
      if (usbBadge) {
        usbBadge.textContent = usbConn ? `CONNECTED (${camSerial.port})` : "DISCONNECTED";
        usbBadge.className = usbConn ? "badge badge-success mono" : "badge badge-muted mono";
      }
      const lastLn = document.getElementById("camSerialLastLine");
      if (lastLn) lastLn.textContent = camSerial.last_line || camSerial.last_error || "--";
    }

    // Settings Wi-Fi stream status badge
    const setStreamBadge = document.getElementById("setCamStreamBadge");
    if (setStreamBadge) {
      setStreamBadge.textContent = status;
      setStreamBadge.className = isStreaming ? "badge badge-success mono" : "badge badge-muted mono";
    }

    // Top navigation bar Camera pill
    const topCam = document.getElementById("topCamStatus");
    const dotCam = document.getElementById("dotCamera");
    if (topCam && dotCam) {
      topCam.textContent = status;
      if (status === "STREAMING" || status === "CONNECTED") {
        dotCam.className = "dot dot-success";
      } else if (status === "CONNECTING" || status === "RECONNECTING") {
        dotCam.className = "dot dot-warn";
      } else if (status === "ERROR" || status === "UNAVAILABLE") {
        dotCam.className = "dot dot-critical";
      } else {
        dotCam.className = "dot dot-muted";
      }
    }

    // Overview card
    const ovStatus = document.getElementById("ovCamStatus");
    const ovFps = document.getElementById("ovCamFps");
    if (ovStatus) ovStatus.textContent = status;
    if (ovFps) ovFps.textContent = `${cam.actual_fps || 0} FPS`;

    // Camera Feed toolbar badges & info panel
    const stateBadge = document.getElementById("camStateBadge");
    if (stateBadge) {
      stateBadge.textContent = status;
      stateBadge.className =
        isStreaming
          ? "badge badge-success mono"
          : status === "CONNECTING" || status === "RECONNECTING"
          ? "badge badge-warning mono"
          : status === "ERROR" || status === "UNAVAILABLE"
          ? "badge badge-critical mono"
          : "badge badge-muted mono";
    }

    const resBadge = document.getElementById("camResBadge");
    if (resBadge) resBadge.textContent = cam.resolution || "Unknown";

    const latBadge = document.getElementById("camLatencyBadge");
    if (latBadge) latBadge.textContent = cam.latency_ms != null ? `${cam.latency_ms} ms` : "-- ms";

    const metaEl = document.getElementById("camFeedMeta");
    if (metaEl) metaEl.textContent = `${cam.actual_fps || 0} FPS`;

    const stageTitle = document.getElementById("camStageTitle");
    if (stageTitle) stageTitle.textContent = cam.camera_name || cam.source_label || "ESP32-CAM OV2640";

    const errNotice = document.getElementById("camErrorNotice");
    if (errNotice) {
      if (cam.error) {
        errNotice.textContent = cam.error;
        errNotice.classList.remove("hidden");
      } else {
        errNotice.textContent = "";
        errNotice.classList.add("hidden");
      }
    }

    // Camera Information Panel
    const setText = (id, val) => {
      const el = document.getElementById(id);
      if (el) el.textContent = val;
    };
    setText("camInfoName", cam.camera_name || "ESP32-CAM OV2640");
    setText("camInfoIp", cam.source_type === "esp32cam" ? (cam.camera_ip || "--") : "Local USB");
    setText("camInfoConn", status);
    setText("camInfoStream", status === "STREAMING" ? "ACTIVE" : status === "RECONNECTING" ? "RECOVERING" : "INACTIVE");
    setText("camInfoRes", cam.resolution || "Unknown");
    setText("camInfoUrl", cam.source_type === "esp32cam" ? (cam.esp32_cam_url || "--") : `Webcam #${cam.camera_index}`);
    setText("camInfoLastConn", cam.last_connected_at || "--");

    // Placeholder text
    const phText = document.getElementById("camPlaceholderText");
    if (phText) {
      if (status === "CONNECTING") {
        phText.textContent = `Connecting to ${cam.camera_name}...`;
      } else if (status === "RECONNECTING") {
        phText.textContent = `Connection lost — Reconnecting to ${cam.camera_ip || "camera"}...`;
      } else if (cam.error) {
        phText.textContent = cam.error;
      } else {
        phText.textContent = `${cam.camera_name || "Camera"} disconnected — Click "Start Stream" to connect`;
      }
    }

    const ovImg = document.getElementById("ovCamImg");
    const ovPh = document.getElementById("ovCamPlaceholder");
    const liveImg = document.getElementById("camLiveImg");
    const livePh = document.getElementById("camLivePlaceholder");

    if (running && (status === "STREAMING" || status === "CONNECTED") && !this.streaming) {
      const streamUrl = `/api/camera/stream?t=${Date.now()}`;
      this.activeStreamUrl = streamUrl;
      ovImg.src = streamUrl;
      liveImg.src = streamUrl;
      ovImg.classList.remove("hidden");
      liveImg.classList.remove("hidden");
      ovPh.classList.add("hidden");
      livePh.classList.add("hidden");
      this.streaming = true;
    } else if ((!running || status === "RECONNECTING" || status === "DISCONNECTED" || status === "ERROR") && this.streaming) {
      ovImg.removeAttribute("src");
      liveImg.removeAttribute("src");
      ovImg.classList.add("hidden");
      liveImg.classList.add("hidden");
      ovPh.classList.remove("hidden");
      livePh.classList.remove("hidden");
      this.streaming = false;
    }
  },

  async startStream() {
    const sourceType = document.getElementById("camSourceSelect")?.value || "esp32cam";
    const payload = {
      source_type: sourceType,
      esp32_cam_url: document.getElementById("setEsp32CamUrl")?.value || undefined,
      camera_ip: document.getElementById("setCamIp")?.value || undefined,
      stream_port: document.getElementById("setCamPort")?.value ? parseInt(document.getElementById("setCamPort").value, 10) : undefined,
      auto_reconnect: document.getElementById("setCamAutoReconnect")?.value === "true",
      connect_timeout: document.getElementById("setCamTimeout")?.value ? parseFloat(document.getElementById("setCamTimeout").value) : undefined,
    };
    const res = await window.CockpitApp.api("/api/camera/start", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    if (res.ok) {
      this.streaming = false;
      this.applyStatus(res.camera);
      window.CockpitApp.toast(res.message, "success");
    } else {
      this.applyStatus(res.camera);
      window.CockpitApp.toast(res.message || res.error || "Camera start failed", "error");
    }
  },

  async stopStream() {
    const res = await window.CockpitApp.api("/api/camera/stop", { method: "POST" });
    if (res.ok) {
      this.applyStatus(res.camera);
      window.CockpitApp.toast("Camera stream stopped", "info");
    }
  },

  init() {
    document.getElementById("btnCamStart")?.addEventListener("click", () => this.startStream());
    document.getElementById("btnCamStop")?.addEventListener("click", () => this.stopStream());

    document.getElementById("btnCamRefresh")?.addEventListener("click", async () => {
      await this.stopStream();
      await this.startStream();
    });

    document.getElementById("btnCamCapture")?.addEventListener("click", async () => {
      const res = await window.CockpitApp.api("/api/camera/capture", { method: "POST" });
      if (res.ok) {
        const box = document.getElementById("camSnapshotBox");
        box.innerHTML = `<img src="${res.url}?t=${Date.now()}" alt="Snapshot" />`;
        window.CockpitApp.toast(`Snapshot saved: ${res.filename}`, "success");
      } else {
        window.CockpitApp.toast(res.error || "Snapshot capture failed", "error");
      }
    });

    // Fullscreen API support (Esc exits automatically)
    const videoContainer = document.getElementById("camVideoContainer");
    document.getElementById("btnCamFullscreen")?.addEventListener("click", async () => {
      if (!videoContainer) return;
      try {
        if (!document.fullscreenElement) {
          await videoContainer.requestFullscreen();
        } else {
          await document.exitFullscreen();
        }
      } catch (err) {
        window.CockpitApp.toast("Fullscreen not permitted by browser", "error");
      }
    });

    document.getElementById("btnCamExitFullscreen")?.addEventListener("click", async () => {
      if (document.fullscreenElement) {
        await document.exitFullscreen();
      }
    });
  },
};

document.addEventListener("DOMContentLoaded", () => {
  window.CockpitCamera.init();
});
