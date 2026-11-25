/* COCKPIT YOLO Object Detection Controller */

window.CockpitDetection = {
  streaming: false,

  applyStatus(det) {
    if (!det) return;
    const running = Boolean(det.running);
    const meta = document.getElementById("detMetricsMeta");
    const countBadge = document.getElementById("detCountBadge");
    if (meta) {
      meta.textContent = `${running ? "RUNNING" : det.model_status} • ${det.device} • ${det.inference_ms} ms • ${det.fps} FPS`;
    }
    if (countBadge) countBadge.textContent = det.detection_count || 0;

    const liveImg = document.getElementById("detLiveImg");
    const ph = document.getElementById("detLivePlaceholder");
    const msgEl = document.getElementById("detPlaceholderMsg");
    if (msgEl && det.error) msgEl.textContent = det.error;

    if (running && !this.streaming) {
      liveImg.src = `/api/detection/stream?t=${Date.now()}`;
      liveImg.classList.remove("hidden");
      ph.classList.add("hidden");
      this.streaming = true;
    } else if (!running && this.streaming) {
      liveImg.removeAttribute("src");
      liveImg.classList.add("hidden");
      ph.classList.remove("hidden");
      this.streaming = false;
    }

    const tbody = document.getElementById("detTableBody");
    if (tbody) {
      const list = det.detections || [];
      if (!list.length) {
        tbody.innerHTML = `<tr><td colspan="3" class="text-muted">${running ? "No objects detected" : "Detection inactive"}</td></tr>`;
      } else {
        tbody.innerHTML = list
          .map(
            (d) => `<tr>
              <td>${window.CockpitApp.escapeHtml(d.class_name)}</td>
              <td>${d.confidence}%</td>
              <td>[${d.bbox.join(", ")}]</td>
            </tr>`
          )
          .join("");
      }
    }
  },

  init() {
    const slider = document.getElementById("detConfSlider");
    const confLabel = document.getElementById("detConfVal");
    slider?.addEventListener("input", () => {
      confLabel.textContent = parseFloat(slider.value).toFixed(2);
    });
    slider?.addEventListener("change", async () => {
      await window.CockpitApp.api("/api/detection/config", {
        method: "POST",
        body: JSON.stringify({ confidence: parseFloat(slider.value) }),
      });
    });

    document.getElementById("btnDetStart")?.addEventListener("click", async () => {
      const classesRaw = document.getElementById("detClassesInput").value || "";
      const selectedClasses = classesRaw ? classesRaw.split(",").map((s) => s.trim()).filter(Boolean) : [];
      const payload = {
        model_path: document.getElementById("detModelInput").value,
        confidence: parseFloat(slider.value),
        selected_classes: selectedClasses,
      };
      const res = await window.CockpitApp.api("/api/detection/start", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        this.streaming = false;
        this.applyStatus(res.detection);
        window.CockpitApp.toast(res.message, "success");
      } else {
        this.applyStatus(res.detection);
        window.CockpitApp.toast(res.message || res.error, "error");
      }
    });

    document.getElementById("btnDetStop")?.addEventListener("click", async () => {
      const res = await window.CockpitApp.api("/api/detection/stop", { method: "POST" });
      if (res.ok) {
        this.applyStatus(res.detection);
        window.CockpitApp.toast("Object detection stopped", "info");
      }
    });

    document.getElementById("btnDetCapture")?.addEventListener("click", async () => {
      const res = await window.CockpitApp.api("/api/detection/capture", { method: "POST" });
      window.CockpitApp.toast(res.ok ? `Snapshot saved: ${res.filename}` : res.error, res.ok ? "success" : "error");
    });
  },
};

document.addEventListener("DOMContentLoaded", () => {
  window.CockpitDetection.init();
});
