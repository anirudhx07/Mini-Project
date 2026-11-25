/* COCKPIT Multi-Object Tracking Controller */

window.CockpitTracking = {
  streaming: false,

  applyStatus(trk) {
    if (!trk) return;
    const running = Boolean(trk.running);
    document.getElementById("trkStateBadge").textContent = running ? "ACTIVE" : "INACTIVE";
    document.getElementById("trkStateBadge").className = running ? "badge badge-success mono" : "badge badge-muted mono";
    document.getElementById("trkModeText").textContent = trk.tracker_mode || "ByteTrack";
    document.getElementById("trkActiveCount").textContent = trk.active_count || 0;
    document.getElementById("trkUniqueCount").textContent = trk.total_unique_ids || 0;
    document.getElementById("trkPerfMeta").textContent = `${trk.inference_ms || 0} ms • ${trk.fps || 0} FPS`;

    const img = document.getElementById("trkLiveImg");
    const ph = document.getElementById("trkLivePlaceholder");
    const msg = document.getElementById("trkPlaceholderMsg");
    if (msg && trk.error) msg.textContent = trk.error;

    if (running && !this.streaming) {
      img.src = `/api/tracking/stream?t=${Date.now()}`;
      img.classList.remove("hidden");
      ph.classList.add("hidden");
      this.streaming = true;
    } else if (!running && this.streaming) {
      img.removeAttribute("src");
      img.classList.add("hidden");
      ph.classList.remove("hidden");
      this.streaming = false;
    }

    const tbody = document.getElementById("trkTableBody");
    if (tbody) {
      const list = trk.tracks || [];
      if (!list.length) {
        tbody.innerHTML = `<tr><td colspan="4" class="text-muted">${running ? "No active tracks" : "Tracking inactive"}</td></tr>`;
      } else {
        tbody.innerHTML = list
          .map(
            (t) => `<tr class="${t.selected ? "text-warning" : ""}">
              <td>#${t.track_id}</td>
              <td>${window.CockpitApp.escapeHtml(t.class_name)}</td>
              <td>${t.confidence}%</td>
              <td>${t.trail_len || 0} pts</td>
            </tr>`
          )
          .join("");
      }
    }
  },

  init() {
    document.getElementById("btnTrkStart")?.addEventListener("click", async () => {
      const res = await window.CockpitApp.api("/api/tracking/start", { method: "POST", body: JSON.stringify({}) });
      if (res.ok) {
        this.streaming = false;
        this.applyStatus(res.tracking);
        window.CockpitApp.toast(res.message, "success");
      } else {
        this.applyStatus(res.tracking);
        window.CockpitApp.toast(res.message || res.error, "error");
      }
    });

    document.getElementById("btnTrkStop")?.addEventListener("click", async () => {
      const res = await window.CockpitApp.api("/api/tracking/stop", { method: "POST" });
      if (res.ok) {
        this.applyStatus(res.tracking);
        window.CockpitApp.toast("Object tracking stopped", "info");
      }
    });

    document.getElementById("btnTrkSelect")?.addEventListener("click", async () => {
      const val = document.getElementById("trkSelectInput").value;
      const res = await window.CockpitApp.api("/api/tracking/select", {
        method: "POST",
        body: JSON.stringify({ track_id: val === "" ? null : parseInt(val, 10) }),
      });
      window.CockpitApp.toast(res.ok ? `Highlight ID updated` : res.error, res.ok ? "success" : "error");
    });
  },
};

document.addEventListener("DOMContentLoaded", () => {
  window.CockpitTracking.init();
});
