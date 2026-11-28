/* COCKPIT Flight Telemetry & Bounded Real-Time Charting */

window.CockpitTelemetry = {
  maxPoints: 60,
  charts: {},
  lastSerialStatus: null,

  makeChart(canvasId, datasets) {
    const ctx = document.getElementById(canvasId);
    if (!ctx || !window.Chart) return null;
    return new Chart(ctx, {
      type: "line",
      data: {
        labels: [],
        datasets: datasets.map((ds) => ({
          label: ds.label,
          data: [],
          borderColor: ds.color,
          borderWidth: 1.8,
          pointRadius: 0,
          tension: 0.2,
        })),
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        scales: {
          x: { display: false },
          y: {
            grid: { color: "rgba(37, 50, 72, 0.55)" },
            ticks: { color: "#8795AA", font: { family: "JetBrains Mono", size: 10 } },
          },
        },
        plugins: {
          legend: {
            labels: { color: "#E7EDF7", boxWidth: 12, font: { size: 11 } },
          },
        },
      },
    });
  },

  pushPoint(chart, label, values) {
    if (!chart) return;
    chart.data.labels.push(label);
    values.forEach((v, idx) => chart.data.datasets[idx].data.push(v));
    if (chart.data.labels.length > this.maxPoints) {
      chart.data.labels.shift();
      chart.data.datasets.forEach((ds) => ds.data.shift());
    }
    chart.update("none");
  },

  clearCharts() {
    Object.values(this.charts).forEach((c) => {
      if (!c) return;
      c.data.labels = [];
      c.data.datasets.forEach((ds) => (ds.data = []));
      c.update("none");
    });
  },

  applyState(state, serialStatus = null, commMode = null) {
    if (!state) return;
    const status = state.status || "WAITING_FOR_DATA";
    const isDemo = Boolean(state.demo_mode);
    const mode = commMode || state.comm_mode || "USB_SERIAL";
    const activeSerial = serialStatus || state.serial || this.lastSerialStatus;
    if (serialStatus || state.serial) {
      this.lastSerialStatus = serialStatus || state.serial;
    }

    // Demo Mode indicators
    document.getElementById("demoBanner")?.classList.toggle("hidden", !isDemo);
    const modeLabel = document.getElementById("sidebarModeLabel");
    const modeDot = document.getElementById("sidebarModeDot");
    const demoBtnLabel = document.getElementById("btnDemoLabel");
    if (modeLabel) modeLabel.textContent = isDemo ? "DEMO MODE (SIMULATED)" : "REAL HARDWARE MODE";
    if (modeDot) modeDot.className = isDemo ? "dot dot-warn" : "dot dot-success";
    if (demoBtnLabel) demoBtnLabel.textContent = isDemo ? "Disable Demo Mode" : "Enable Demo Mode";

    // Topbar ESP32 WIFI + MPU6050 pills
    const topEsp = document.getElementById("topEsp32Status");
    const dotEsp = document.getElementById("dotEsp32");
    const topMpu = document.getElementById("topMpuStatus");
    const dotMpu = document.getElementById("dotMpu");

    const usbConnected = Boolean(activeSerial?.connected);
    if (topEsp && dotEsp) {
      if (isDemo) {
        topEsp.textContent = "DEMO";
        dotEsp.className = "dot dot-warn";
      } else if (mode === "UDP_WIFI") {
        if (status === "CONNECTED") {
          topEsp.textContent = "CONNECTED";
          dotEsp.className = "dot dot-success";
        } else if (status === "DISCONNECTED") {
          topEsp.textContent = "DISCONNECTED";
          dotEsp.className = "dot dot-critical";
        } else {
          topEsp.textContent = "WAITING";
          dotEsp.className = "dot dot-warn";
        }
      } else {
        topEsp.textContent = usbConnected ? `USB (${activeSerial.port})` : "DISCONNECTED";
        dotEsp.className = usbConnected ? "dot dot-success" : "dot dot-critical";
      }
    }

    if (topMpu && dotMpu) {
      if (status === "CONNECTED") {
        topMpu.textContent = "CONNECTED";
        dotMpu.className = "dot dot-success";
      } else if (status === "DISCONNECTED") {
        topMpu.textContent = "DISCONNECTED";
        dotMpu.className = "dot dot-critical";
      } else if (status === "SENSOR_ERROR") {
        topMpu.textContent = "SENSOR_ERROR";
        dotMpu.className = "dot dot-critical";
      } else if (status === "INVALID_PACKET") {
        topMpu.textContent = "BAD_PACKET";
        dotMpu.className = "dot dot-critical";
      } else {
        topMpu.textContent = "WAITING";
        dotMpu.className = "dot dot-warn";
      }
    }

    // Section A: Flight Controller Panel updates
    const fcBadge = document.getElementById("setFcConnBadge");
    if (fcBadge) {
      fcBadge.textContent = status;
      fcBadge.className =
        status === "CONNECTED"
          ? "badge badge-success mono"
          : status === "DISCONNECTED" || status === "INVALID_PACKET"
          ? "badge badge-critical mono"
          : "badge badge-warning mono";
    }
    const fcIpEl = document.getElementById("setFcEsp32Ip");
    if (fcIpEl) fcIpEl.textContent = state.source_ip || "--";
    const fcLastEl = document.getElementById("setFcLastPkt");
    if (fcLastEl) fcLastEl.textContent = state.last_packet_ts || "--";

    // Overview & Telemetry page metadata
    document.getElementById("ovEspStatus").textContent = status;
    document.getElementById("ovMpuStatus").textContent = state.mpu6050_status || "WAITING";
    document.getElementById("ovRateBadge").textContent = `${(state.rate_hz || 0).toFixed(1)} Hz`;
    document.getElementById("ovPacketCounter").textContent = `PKTS: ${state.packet_count || 0}`;
    document.getElementById("ovOrientSource").textContent = isDemo ? "SIMULATED" : (status === "CONNECTED" ? "ESP32 LIVE" : "NO DATA");

    document.getElementById("telStatusBadge").textContent = status;
    document.getElementById("telSourceIp").textContent = state.source_ip || "--";
    document.getElementById("telRateHz").textContent = `${(state.rate_hz || 0).toFixed(1)} Hz`;
    document.getElementById("telValidCount").textContent = state.packet_count || 0;
    document.getElementById("telInvalidCount").textContent = state.invalid_count || 0;

    const d = state.data;
    if (!d) {
      ["ovPitch", "ovRoll", "ovYawRate"].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.textContent = id === "ovYawRate" ? "--.-°/s" : "--.-°";
      });
      ["ovAx", "ovAy", "ovAz", "ovGx", "ovGy", "ovGz"].forEach((id) => {
        const el = document.getElementById(id);
        if (el) el.textContent = "--.--";
      });
      return;
    }

    document.getElementById("ovPitch").textContent = `${d.pitch.toFixed(1)}°`;
    document.getElementById("ovRoll").textContent = `${d.roll.toFixed(1)}°`;
    document.getElementById("ovYawRate").textContent = `${d.yaw_rate.toFixed(1)}°/s`;

    document.getElementById("ovAx").textContent = d.ax.toFixed(2);
    document.getElementById("ovAy").textContent = d.ay.toFixed(2);
    document.getElementById("ovAz").textContent = d.az.toFixed(2);
    document.getElementById("ovGx").textContent = d.gx.toFixed(2);
    document.getElementById("ovGy").textContent = d.gy.toFixed(2);
    document.getElementById("ovGz").textContent = d.gz.toFixed(2);

    // Artificial Horizon update
    const disc = document.getElementById("horizonDisc");
    if (disc) {
      const pitchShift = Math.max(-25, Math.min(25, d.pitch * 0.8));
      disc.style.transform = `rotate(${-d.roll}deg) translateY(${pitchShift}px)`;
    }

    // Push to scrolling charts
    if (status === "CONNECTED") {
      this.pushPoint(this.charts.ovOrient, d.timestamp, [d.pitch, d.roll]);
      this.pushPoint(this.charts.telAttitude, d.timestamp, [d.pitch, d.roll]);
      this.pushPoint(this.charts.telAccel, d.timestamp, [d.ax, d.ay, d.az]);
      this.pushPoint(this.charts.telGyro, d.timestamp, [d.gx, d.gy, d.gz]);
    }
  },

  async toggleDemoMode() {
    const res = await window.CockpitApp.api("/api/telemetry");
    const currentlyDemo = Boolean(res.telemetry?.demo_mode);
    const toggled = await window.CockpitApp.api("/api/telemetry/demo", {
      method: "POST",
      body: JSON.stringify({ enabled: !currentlyDemo }),
    });
    if (toggled.ok) {
      this.clearCharts();
      window.CockpitApp.toast(
        toggled.demo_mode ? "DEMO MODE enabled (simulated packets)" : "Switched to REAL HARDWARE MODE",
        "info"
      );
      window.CockpitApp.refreshStatus();
    }
  },

  init() {
    this.charts.ovOrient = this.makeChart("chartOvOrientation", [
      { label: "Pitch (°)", color: "#36A7FF" },
      { label: "Roll (°)", color: "#25D69A" },
    ]);
    this.charts.telAttitude = this.makeChart("chartTelAttitude", [
      { label: "Pitch (°)", color: "#36A7FF" },
      { label: "Roll (°)", color: "#25D69A" },
    ]);
    this.charts.telAccel = this.makeChart("chartTelAccel", [
      { label: "Ax", color: "#36A7FF" },
      { label: "Ay", color: "#25D69A" },
      { label: "Az", color: "#FFB84D" },
    ]);
    this.charts.telGyro = this.makeChart("chartTelGyro", [
      { label: "Gx", color: "#36A7FF" },
      { label: "Gy", color: "#25D69A" },
      { label: "Gz", color: "#FF5268" },
    ]);

    document.getElementById("btnCalibrateZero")?.addEventListener("click", async () => {
      const res = await window.CockpitApp.api("/api/telemetry/calibrate", {
        method: "POST",
        body: JSON.stringify({ action: "zero" }),
      });
      window.CockpitApp.toast(res.ok ? res.message : res.error, res.ok ? "success" : "error");
    });

    document.getElementById("btnCalibrateReset")?.addEventListener("click", async () => {
      const res = await window.CockpitApp.api("/api/telemetry/calibrate", {
        method: "POST",
        body: JSON.stringify({ action: "reset" }),
      });
      window.CockpitApp.toast(res.ok ? res.message : res.error, res.ok ? "success" : "error");
    });

    document.getElementById("btnToggleDemoTel")?.addEventListener("click", () => this.toggleDemoMode());
    document.getElementById("btnToggleDemoSettings")?.addEventListener("click", () => this.toggleDemoMode());
  },
};

document.addEventListener("DOMContentLoaded", () => {
  window.CockpitTelemetry.init();
});
