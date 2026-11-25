/* COCKPIT Camera Feed Controller */

window.CockpitCamera = {
  streaming: false,

  applyStatus(cam) {
    if (!cam) return;
    const running = Boolean(cam.running);
    const status = cam.status || "STOPPED";

    document.getElementById("topCamStatus").textContent = status;
    document.getElementById("dotCamera").className =
      running ? "dot dot-success" : status === "UNAVAILABLE" ? "dot dot-critical" : "dot dot-muted";

    document.getElementById("ovCamStatus").textContent = status;
    document.getElementById("ovCamFps").textContent = `${cam.actual_fps || 0} FPS`;
    document.getElementById("camFeedMeta").textContent = `${cam.source_label} • ${status} • ${cam.actual_fps || 0} FPS`;

    const ovImg = document.getElementById("ovCamImg");
    const ovPh = document.getElementById("ovCamPlaceholder");
    const liveImg = document.getElementById("camLiveImg");
    const livePh = document.getElementById("camLivePlaceholder");

    if (running && !this.streaming) {
      const streamUrl = `/api/camera/stream?t=${Date.now()}`;
      ovImg.src = streamUrl;
      liveImg.src = streamUrl;
      ovImg.classList.remove("hidden");
      liveImg.classList.remove("hidden");
      ovPh.classList.add("hidden");
      livePh.classList.add("hidden");
      this.streaming = true;
    } else if (!running && this.streaming) {
      ovImg.removeAttribute("src");
      liveImg.removeAttribute("src");
      ovImg.classList.add("hidden");
      liveImg.classList.add("hidden");
      ovPh.classList.remove("hidden");
      livePh.classList.remove("hidden");
      this.streaming = false;
    }
  },

  init() {
    document.getElementById("btnCamStart")?.addEventListener("click", async () => {
      const [w, h] = (document.getElementById("camResSelect").value || "640x480").split("x").map(Number);
      const payload = {
        source_type: document.getElementById("camSourceSelect").value,
        camera_index: parseInt(document.getElementById("camIndexInput").value, 10),
        width: w,
        height: h,
        fps: parseInt(document.getElementById("camFpsInput").value, 10),
        esp32_cam_url: document.getElementById("setEsp32CamUrl")?.value || "",
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
        window.CockpitApp.toast(res.message || res.error || "Camera start failed", "error");
      }
    });

    document.getElementById("btnCamStop")?.addEventListener("click", async () => {
      const res = await window.CockpitApp.api("/api/camera/stop", { method: "POST" });
      if (res.ok) {
        this.applyStatus(res.camera);
        window.CockpitApp.toast("Camera stopped", "info");
      }
    });

    document.getElementById("btnCamCapture")?.addEventListener("click", async () => {
      const res = await window.CockpitApp.api("/api/camera/capture", { method: "POST" });
      if (res.ok) {
        const box = document.getElementById("camSnapshotBox");
        box.innerHTML = `<img src="${res.url}?t=${Date.now()}" alt="Snapshot" />`;
        window.CockpitApp.toast(`Saved ${res.filename}`, "success");
      } else {
        window.CockpitApp.toast(res.error || "Capture failed", "error");
      }
    });
  },
};

document.addEventListener("DOMContentLoaded", () => {
  window.CockpitCamera.init();
});
