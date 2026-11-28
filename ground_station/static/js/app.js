/* COCKPIT Main Application Controller */

window.CockpitApp = {
  socket: null,
  activeView: "overview",
  viewTitles: {
    overview: "Operational Overview",
    telemetry: "Flight Telemetry (MPU6050)",
    camera: "Camera Feed",
    detection: "Object Detection (YOLO)",
    tracking: "Object Tracking",
    camouflage: "Camouflage Analysis",
    logs: "Mission Logs",
    settings: "System Settings",
  },

  toast(msg, kind = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;
    const el = document.createElement("div");
    el.className = `toast ${kind}`;
    el.textContent = msg;
    container.appendChild(el);
    setTimeout(() => el.remove(), 3500);
  },

  async api(url, options = {}) {
    try {
      const resp = await fetch(url, {
        headers: { "Content-Type": "application/json" },
        ...options,
      });
      const data = await resp.json().catch(() => ({ ok: false, error: "Invalid server response" }));
      return { status: resp.status, ...data };
    } catch (err) {
      return { ok: false, error: "Backend unreachable" };
    }
  },

  switchView(viewName) {
    this.activeView = viewName;
    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.classList.toggle("active", btn.dataset.view === viewName);
    });
    document.querySelectorAll(".view-section").forEach((sec) => {
      sec.classList.toggle("active", sec.id === `view-${viewName}`);
    });
    const heading = document.getElementById("activePageTitle");
    if (heading) heading.textContent = this.viewTitles[viewName] || "COCKPIT";

    document.getElementById("sidebar")?.classList.remove("open");

    if (viewName === "logs") this.loadMissionLogs();
    if (viewName === "settings") {
      this.loadSystemInfo();
      this.refreshSerialPorts();
    }
  },

  async refreshSerialPorts() {
    const sel = document.getElementById("camSerialPortSelect");
    if (!sel) return;
    const prev = sel.value;
    const res = await this.api("/api/serial/ports");
    if (!res.ok) return;
    const ports = res.ports || [];
    if (!ports.length) {
      sel.innerHTML = `<option value="">No COM ports detected</option>`;
      return;
    }
    sel.innerHTML = ports
      .map((p) => {
        const tag = p.is_cp210x ? " [USB-UART]" : "";
        return `<option value="${this.escapeHtml(p.device)}">${this.escapeHtml(p.device)} — ${this.escapeHtml(p.description)}${tag}</option>`;
      })
      .join("");
    if (prev && ports.some((p) => p.device === prev)) {
      sel.value = prev;
    } else {
      const usbPort = ports.find((p) => p.recommended || !p.description.toLowerCase().includes("bluetooth"));
      if (usbPort) sel.value = usbPort.device;
    }
  },

  appendOverviewEvent(ev) {
    const list = document.getElementById("ovEventList");
    if (!list) return;
    const row = document.createElement("div");
    row.className = "event-row";
    const lvlClass =
      ev.level === "ERROR" ? "text-critical" : ev.level === "WARNING" ? "text-warning" : "text-success";
    row.innerHTML = `<span class="text-muted">${ev.timestamp.split(" ")[1] || ev.timestamp}</span> <span class="${lvlClass}">[${ev.category}]</span> <span>${this.escapeHtml(ev.message)}</span>`;
    list.prepend(row);
    while (list.children.length > 60) {
      list.removeChild(list.lastChild);
    }
  },

  escapeHtml(str) {
    return String(str || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  },

  async refreshStatus() {
    const res = await this.api("/api/status");
    if (!res.ok) {
      document.getElementById("topSysStatus").textContent = "OFFLINE";
      document.getElementById("ovBackendStatus").textContent = "UNAVAILABLE";
      return;
    }
    document.getElementById("topSysStatus").textContent = "ONLINE";
    document.getElementById("ovBackendStatus").textContent = "ONLINE";

    const commMode = res.comm_mode || "USB_SERIAL";
    const ser = res.serial || {};
    if (commMode === "USB_SERIAL") {
      document.getElementById("ovUdpStatus").textContent = ser.connected ? `USB:${ser.port} @ ${ser.baudrate}` : "USB_SERIAL (DISCONNECTED)";
      document.getElementById("sidebarUdpLabel").textContent = ser.connected ? `USB ${ser.port} • ${ser.baudrate}` : "USB SERIAL (IDLE)";
    } else {
      document.getElementById("ovUdpStatus").textContent = res.udp_listening ? `UDP :${res.udp_port}` : "UDP STOPPED";
      document.getElementById("sidebarUdpLabel").textContent = `UDP 0.0.0.0:${res.udp_port}`;
    }

    if (window.CockpitTelemetry) window.CockpitTelemetry.applyState(res.telemetry, res.serial, commMode);
    if (window.CockpitCamera) window.CockpitCamera.applyStatus(res.camera, res.cam_serial);
    if (window.CockpitDetection) window.CockpitDetection.applyStatus(res.detection);
    if (window.CockpitTracking) window.CockpitTracking.applyStatus(res.tracking);
    if (window.CockpitCamouflage) window.CockpitCamouflage.applyStatus(res.camouflage);

    // Overview AI activity summary
    const det = res.detection || {};
    const trk = res.tracking || {};
    const camo = res.camouflage || {};
    const topAi = document.getElementById("topAiStatus");
    const dotAi = document.getElementById("dotAI");
    const ovAiStatus = document.getElementById("ovAiStatus");

    let activeMod = "NONE";
    if (det.running) activeMod = "YOLO DETECTION";
    else if (trk.running) activeMod = `TRACKING (${trk.tracker_mode})`;

    if (det.running || trk.running) {
      topAi.textContent = "ACTIVE";
      dotAi.className = "dot dot-success";
      ovAiStatus.textContent = "ACTIVE";
    } else if (det.model_loaded) {
      topAi.textContent = "READY";
      dotAi.className = "dot dot-warn";
      ovAiStatus.textContent = "MODEL READY";
    } else {
      topAi.textContent = "IDLE";
      dotAi.className = "dot dot-muted";
      ovAiStatus.textContent = det.model_status === "MODEL_NOT_FOUND" ? "NOT CONFIGURED" : "IDLE";
    }

    document.getElementById("ovAiModule").textContent = activeMod;
    document.getElementById("ovAiDetCount").textContent = det.running ? det.detection_count : 0;
    document.getElementById("ovAiTrackStatus").textContent = trk.running ? `ACTIVE (${trk.active_count})` : "INACTIVE";
    document.getElementById("ovAiCamoStatus").textContent = camo.active_mode || "BASELINE READY";
    const infMs = det.running ? det.inference_ms : trk.running ? trk.inference_ms : null;
    document.getElementById("ovAiLatency").textContent = infMs !== null ? `${infMs} ms` : "-- ms";
    document.getElementById("ovAiDevice").textContent = det.device || "CPU";
  },

  async loadMissionLogs() {
    const search = document.getElementById("logSearchInput")?.value || "";
    const category = document.getElementById("logCatSelect")?.value || "ALL";
    const dateFrom = document.getElementById("logDateFrom")?.value || "";
    const dateTo = document.getElementById("logDateTo")?.value || "";
    const params = new URLSearchParams({ search, category, date_from: dateFrom, date_to: dateTo, limit: "200" });
    const res = await this.api(`/api/logs?${params.toString()}`);
    const tbody = document.getElementById("logsTableBody");
    if (!tbody || !res.ok) return;

    if (!res.logs.length) {
      tbody.innerHTML = `<tr><td colspan="6" class="text-muted">No matching mission logs</td></tr>`;
      return;
    }
    tbody.innerHTML = res.logs
      .map(
        (r) => `<tr>
          <td>${r.id}</td>
          <td>${this.escapeHtml(r.timestamp)}</td>
          <td>${this.escapeHtml(r.category)}</td>
          <td>${this.escapeHtml(r.level)}</td>
          <td>${this.escapeHtml(r.message)}</td>
          <td>${r.image_ref ? `<a href="/api/captures/${encodeURIComponent(r.image_ref)}" target="_blank">${this.escapeHtml(r.image_ref)}</a>` : "--"}</td>
        </tr>`
      )
      .join("");
  },

  async loadInitialEvents() {
    const res = await this.api("/api/logs?limit=25");
    if (!res.ok) return;
    const list = document.getElementById("ovEventList");
    if (!list) return;
    list.innerHTML = "";
    res.logs.slice().reverse().forEach((ev) => this.appendOverviewEvent(ev));
  },

  async loadSystemInfo() {
    const res = await this.api("/api/system/info");
    if (!res.ok) return;
    const sys = res.system;
    const net = res.network;
    const ai = res.ai;
    const st = res.storage;

    document.getElementById("setLocalIp").textContent = sys.local_ip;
    if (document.getElementById("setCommMode")) {
      document.getElementById("setCommMode").value = res.comm_mode || "USB_SERIAL";
    }
    document.getElementById("setUdpPort").value = net.udp_port;
    document.getElementById("setTimeout").value = net.esp32_timeout_sec;
    document.getElementById("setHistorySize").value = net.history_size;

    document.getElementById("setGpuName").textContent = sys.gpu.gpu_device_name;
    document.getElementById("setCudaAvail").textContent = sys.gpu.cuda_available ? "YES (CUDA ACTIVE)" : "NO (CPU FALLBACK)";
    document.getElementById("setModelPath").value = ai.model_path;
    document.getElementById("setAiDevice").value = ai.device_pref;
    document.getElementById("setFrameSkip").value = ai.frame_skip;

    document.getElementById("setCapturesDir").textContent = st.captures_dir;
    document.getElementById("setDbPath").textContent = st.database_path;
    document.getElementById("setCpuPct").textContent = `${sys.cpu_percent}%`;
    document.getElementById("setMemPct").textContent = `${sys.memory_percent}% (${sys.memory_used_gb}/${sys.memory_total_gb} GB)`;

    if (res.camera) {
      const cam = res.camera;
      if (document.getElementById("setCamSource")) document.getElementById("setCamSource").value = cam.source_type || "esp32cam";
      if (document.getElementById("camSourceSelect")) document.getElementById("camSourceSelect").value = cam.source_type || "esp32cam";
      if (document.getElementById("setCamIp")) document.getElementById("setCamIp").value = cam.camera_ip || "";
      if (document.getElementById("setCamPort")) document.getElementById("setCamPort").value = cam.stream_port || 81;
      if (document.getElementById("setEsp32CamUrl")) document.getElementById("setEsp32CamUrl").value = cam.esp32_cam_url || "";
      if (document.getElementById("setCamTimeout")) document.getElementById("setCamTimeout").value = cam.connect_timeout || 4.0;
      if (document.getElementById("setCamAutoReconnect")) document.getElementById("setCamAutoReconnect").value = String(Boolean(cam.auto_reconnect));
    }
  },

  init() {
    if (window.lucide) window.lucide.createIcons();

    document.querySelectorAll(".nav-item").forEach((btn) => {
      btn.addEventListener("click", () => this.switchView(btn.dataset.view));
    });
    document.getElementById("topSettingsBtn")?.addEventListener("click", () => this.switchView("settings"));
    document.getElementById("mobileMenuBtn")?.addEventListener("click", () => {
      document.getElementById("sidebar")?.classList.toggle("open");
    });

    // Local clock
    setInterval(() => {
      const el = document.getElementById("localClock");
      if (el) el.textContent = new Date().toLocaleTimeString();
    }, 1000);

    // Logs controls
    document.getElementById("btnLogsRefresh")?.addEventListener("click", () => this.loadMissionLogs());
    document.getElementById("btnLogsClear")?.addEventListener("click", async () => {
      if (!confirm("Clear all mission log records from SQLite?")) return;
      const res = await this.api("/api/logs/clear", { method: "POST" });
      if (res.ok) {
        this.toast(`Cleared ${res.deleted} log records`, "success");
        this.loadMissionLogs();
      }
    });

    // Settings save
    document.getElementById("btnSaveSettings")?.addEventListener("click", async () => {
      const payload = {
        comm_mode: document.getElementById("setCommMode")?.value || "USB_SERIAL",
        udp_port: parseInt(document.getElementById("setUdpPort").value, 10),
        esp32_timeout_sec: parseFloat(document.getElementById("setTimeout").value),
        history_size: parseInt(document.getElementById("setHistorySize").value, 10),
        model_path: document.getElementById("setModelPath").value,
        ai_device: document.getElementById("setAiDevice").value,
        frame_skip: parseInt(document.getElementById("setFrameSkip").value, 10),
        camera_source: document.getElementById("setCamSource")?.value || "esp32cam",
        camera_ip: document.getElementById("setCamIp")?.value.trim(),
        stream_port: parseInt(document.getElementById("setCamPort")?.value || "81", 10),
        esp32_cam_url: document.getElementById("setEsp32CamUrl")?.value.trim(),
        connect_timeout: parseFloat(document.getElementById("setCamTimeout")?.value || "4.0"),
        auto_reconnect: document.getElementById("setCamAutoReconnect")?.value === "true",
      };
      const res = await this.api("/api/settings", { method: "POST", body: JSON.stringify(payload) });
      if (res.ok) {
        this.toast("Settings applied", "success");
        this.refreshStatus();
      } else {
        this.toast(res.error || "Failed to apply settings", "error");
      }
    });

    // Keep Camera IP / Port synced with Stream URL input when user edits IP or Port
    const syncCamUrl = () => {
      const ip = document.getElementById("setCamIp")?.value.trim();
      const port = document.getElementById("setCamPort")?.value.trim() || "81";
      const urlEl = document.getElementById("setEsp32CamUrl");
      if (ip && urlEl) {
        urlEl.value = `http://${ip}:${port}/stream`;
      }
    };
    document.getElementById("setCamIp")?.addEventListener("input", syncCamUrl);
    document.getElementById("setCamPort")?.addEventListener("input", syncCamUrl);

    // Test Camera Connection
    document.getElementById("btnTestCamConn")?.addEventListener("click", async () => {
      const badge = document.getElementById("setCamTestBadge");
      const resEl = document.getElementById("setCamTestResult");
      if (badge) { badge.textContent = "TESTING..."; badge.className = "badge badge-warning mono"; }
      const payload = {
        source_type: document.getElementById("setCamSource")?.value || "esp32cam",
        camera_ip: document.getElementById("setCamIp")?.value.trim(),
        stream_port: parseInt(document.getElementById("setCamPort")?.value || "81", 10),
        esp32_cam_url: document.getElementById("setEsp32CamUrl")?.value.trim(),
        connect_timeout: parseFloat(document.getElementById("setCamTimeout")?.value || "4.0"),
      };
      const res = await this.api("/api/camera/test", { method: "POST", body: JSON.stringify(payload) });
      if (badge) {
        badge.textContent = res.ok ? "REACHABLE" : "UNREACHABLE";
        badge.className = res.ok ? "badge badge-success mono" : "badge badge-critical mono";
      }
      if (resEl) {
        resEl.textContent = res.message || res.error || "--";
        resEl.className = res.ok ? "mono text-success" : "mono text-critical";
      }
      this.toast(res.message || res.error, res.ok ? "success" : "error");
    });

    // Section A: UDP Flight Controller Connect / Disconnect
    document.getElementById("btnUdpStart")?.addEventListener("click", async () => {
      const port = parseInt(document.getElementById("setUdpPort")?.value || "4210", 10);
      const res = await this.api("/api/telemetry/udp/start", {
        method: "POST",
        body: JSON.stringify({ port }),
      });
      this.toast(res.ok ? res.message : res.error, res.ok ? "success" : "error");
      this.refreshStatus();
    });

    document.getElementById("btnUdpStop")?.addEventListener("click", async () => {
      const res = await this.api("/api/telemetry/udp/stop", { method: "POST", body: JSON.stringify({}) });
      this.toast(res.message || "UDP stopped", "info");
      this.refreshStatus();
    });

    // Section B: ESP32-CAM USB Serial & Stream Controls
    document.getElementById("btnCamSerialRefresh")?.addEventListener("click", () => {
      this.refreshSerialPorts();
      this.toast("COM ports refreshed", "info");
    });

    document.getElementById("btnCamSerialConnect")?.addEventListener("click", async () => {
      const port = document.getElementById("camSerialPortSelect")?.value || "";
      const baudrate = parseInt(document.getElementById("camSerialBaudSelect")?.value || "115200", 10);
      if (!port) {
        this.toast("Select a COM port first", "error");
        return;
      }
      const res = await this.api("/api/camera/serial/connect", {
        method: "POST",
        body: JSON.stringify({ port, baudrate }),
      });
      this.toast(res.message || res.error, res.ok ? "success" : "error");
      this.refreshStatus();
    });

    document.getElementById("btnCamSerialDisconnect")?.addEventListener("click", async () => {
      const res = await this.api("/api/camera/serial/disconnect", { method: "POST" });
      this.toast(res.message || "ESP32-CAM USB disconnected", "info");
      this.refreshStatus();
    });

    document.getElementById("btnSetCamStart")?.addEventListener("click", () => {
      if (window.CockpitCamera) window.CockpitCamera.startStream();
    });
    document.getElementById("btnSetCamStop")?.addEventListener("click", () => {
      if (window.CockpitCamera) window.CockpitCamera.stopStream();
    });

    // WebSocket setup
    if (window.io) {
      this.socket = io();
      this.socket.on("connect", () => {
        const wsEl = document.getElementById("setWsStatus");
        if (wsEl) wsEl.textContent = "CONNECTED";
      });
      this.socket.on("disconnect", () => {
        const wsEl = document.getElementById("setWsStatus");
        if (wsEl) wsEl.textContent = "DISCONNECTED";
      });
      this.socket.on("telemetry_update", (state) => {
        if (window.CockpitTelemetry) window.CockpitTelemetry.applyState(state);
      });
      this.socket.on("detection_update", (det) => {
        if (window.CockpitDetection) window.CockpitDetection.applyStatus(det);
      });
      this.socket.on("tracking_update", (trk) => {
        if (window.CockpitTracking) window.CockpitTracking.applyStatus(trk);
      });
      this.socket.on("event_log", (ev) => this.appendOverviewEvent(ev));
    }

    this.loadInitialEvents();
    this.refreshStatus();
    setInterval(() => this.refreshStatus(), 2000);
  },
};

document.addEventListener("DOMContentLoaded", () => {
  window.CockpitApp.init();
});
