/* COCKPIT Camouflage Visual Analysis Controller */

window.CockpitCamouflage = {
  applyStatus(camo) {
    if (!camo) return;
    document.getElementById("camoModeBadge").textContent = camo.active_mode || "BASELINE VISUAL ANALYSIS";
    document.getElementById("camoModelBadge").textContent = `TRAINED MODEL: ${camo.trained_model_status || "NOT CONFIGURED"}`;
  },

  init() {
    const slider = document.getElementById("camoSensSlider");
    const label = document.getElementById("camoSensVal");
    slider?.addEventListener("input", () => {
      label.textContent = parseFloat(slider.value).toFixed(2);
    });

    document.getElementById("btnCamoAnalyze")?.addEventListener("click", async () => {
      const res = await window.CockpitApp.api("/api/camouflage/analyze", {
        method: "POST",
        body: JSON.stringify({ sensitivity: parseFloat(slider.value), save_result: true }),
      });
      if (!res.ok) {
        window.CockpitApp.toast(res.error || "Camouflage analysis failed", "error");
        return;
      }

      const a = res.analysis;
      document.getElementById("camoDisclaimer").textContent = a.disclaimer;
      document.getElementById("camoResultMeta").textContent = `${a.region_count} suspicious regions • ${a.processing_ms} ms`;

      const origImg = document.getElementById("camoOrigImg");
      const anaImg = document.getElementById("camoAnaImg");
      origImg.src = `data:image/jpeg;base64,${a.original_b64}`;
      anaImg.src = `data:image/jpeg;base64,${a.analyzed_b64}`;
      origImg.classList.remove("hidden");
      anaImg.classList.remove("hidden");
      document.getElementById("camoOrigPlaceholder").classList.add("hidden");
      document.getElementById("camoAnaPlaceholder").classList.add("hidden");

      window.CockpitApp.toast(`Analysis complete (${a.region_count} regions, ${a.processing_ms} ms)`, "success");
    });
  },
};

document.addEventListener("DOMContentLoaded", () => {
  window.CockpitCamouflage.init();
});
