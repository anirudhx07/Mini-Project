"""Modular Camouflage Visual Analysis Engine.

Clearly distinguishes:
1. BASELINE_VISUAL_ANALYSIS: Local color/texture/edge saliency heuristics (not a trained COD classifier).
2. TRAINED_MODEL: Pluggable trained camouflage segmentation model (when configured).
3. MODEL_NOT_CONFIGURED: Reported honestly when no trained weights are supplied.
"""

import base64
from datetime import datetime
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np


class CamouflageAnalyzer:
    """Performs visual anomaly/camouflage saliency analysis with pluggable model support."""

    def __init__(
        self,
        camera_manager,
        captures_dir: Path,
        trained_model_path: str = "",
        event_logger=None,
    ):
        self.camera_manager = camera_manager
        self.captures_dir = Path(captures_dir)
        self.captures_dir.mkdir(parents=True, exist_ok=True)
        self.trained_model_path = (trained_model_path or "").strip()
        self._event_logger = event_logger

        self._trained_model = None
        self._model_state = "MODEL_NOT_CONFIGURED"
        self._last_result: Optional[Dict[str, Any]] = None
        self._try_load_trained_model()

    def _try_load_trained_model(self):
        if not self.trained_model_path:
            self._model_state = "MODEL_NOT_CONFIGURED"
            return
        p = Path(self.trained_model_path)
        if not p.exists():
            self._model_state = "MODEL_NOT_FOUND"
            return
        try:
            import torch  # noqa: F401
            self._model_state = "TRAINED_MODEL_READY"
        except ImportError:
            self._model_state = "MODEL_NOT_CONFIGURED"

    def get_status(self) -> Dict[str, Any]:
        return {
            "baseline_available": True,
            "trained_model_status": self._model_state,
            "trained_model_path": self.trained_model_path,
            "active_mode": "BASELINE_VISUAL_ANALYSIS" if self._model_state != "TRAINED_MODEL_READY" else "TRAINED_MODEL",
            "last_analysis": self._last_result,
        }

    def analyze_current_frame(self, sensitivity: float = 0.60, save_result: bool = True) -> Tuple[bool, Dict[str, Any]]:
        """Capture latest frame from camera and run baseline camouflage visual analysis."""
        frame, _ = self.camera_manager.get_latest_frame()
        if frame is None:
            return False, {"error": "No active camera frame available. Start the camera first."}

        return True, self.analyze_frame(frame, sensitivity=sensitivity, save_result=save_result)

    def analyze_frame(self, frame: np.ndarray, sensitivity: float = 0.60, save_result: bool = True) -> Dict[str, Any]:
        """Run honest baseline visual analysis (LAB color contrast + texture variance + edge density)."""
        t0 = time.perf_counter()
        sensitivity = max(0.2, min(float(sensitivity), 0.95))

        # 1. LAB perceptual color distance from global median background
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB).astype(np.float32)
        blurred_lab = cv2.GaussianBlur(lab, (11, 11), 0)
        median_color = np.median(blurred_lab.reshape(-1, 3), axis=0)
        color_dist = np.linalg.norm(blurred_lab - median_color, axis=2)
        color_norm = cv2.normalize(color_dist, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # 2. Local texture variance (standard deviation in 9x9 window)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
        mean_g = cv2.blur(gray, (9, 9))
        sq_mean_g = cv2.blur(gray ** 2, (9, 9))
        texture_std = np.sqrt(np.maximum(0.0, sq_mean_g - mean_g ** 2))
        texture_norm = cv2.normalize(texture_std, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # 3. Sobel edge density
        gx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        edges = cv2.magnitude(gx, gy)
        edge_norm = cv2.normalize(edges, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Combine into baseline visual saliency map
        saliency = cv2.addWeighted(color_norm, 0.45, texture_norm, 0.35, 0)
        saliency = cv2.addWeighted(saliency, 0.85, edge_norm, 0.15, 0)

        thresh_val = int(255 * (1.0 - sensitivity * 0.45))
        _, mask = cv2.threshold(saliency, thresh_val, 255, cv2.THRESH_BINARY)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        # Overlay saliency heatmap and suspicious region contours
        heatmap = cv2.applyColorMap(saliency, cv2.COLORMAP_TURBO)
        analyzed = cv2.addWeighted(frame, 0.62, heatmap, 0.38, 0)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        regions: List[Dict[str, Any]] = []
        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area >= 220:
                x, y, w, h = cv2.boundingRect(cnt)
                regions.append({"bbox": [x, y, w, h], "area_px": int(area)})
                cv2.rectangle(analyzed, (x, y), (x + w, y + h), (77, 184, 255), 2)
                cv2.putText(
                    analyzed,
                    "SUSPICIOUS REGION",
                    (x, max(15, y - 5)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.42,
                    (77, 184, 255),
                    1,
                    cv2.LINE_AA,
                )

        proc_ms = round((time.perf_counter() - t0) * 1000.0, 1)

        saved_orig = ""
        saved_analyzed = ""
        if save_result:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            orig_name = f"camo_orig_{ts}.jpg"
            ana_name = f"camo_analyzed_{ts}.jpg"
            cv2.imwrite(str(self.captures_dir / orig_name), frame)
            cv2.imwrite(str(self.captures_dir / ana_name), analyzed)
            saved_orig = orig_name
            saved_analyzed = ana_name
            if self._event_logger:
                self._event_logger.log(
                    "AI",
                    f"Camouflage baseline analysis complete ({len(regions)} regions, {proc_ms} ms)",
                    level="INFO",
                    image_ref=ana_name,
                )

        _, orig_buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        _, ana_buf = cv2.imencode(".jpg", analyzed, [cv2.IMWRITE_JPEG_QUALITY, 85])

        result = {
            "analysis_type": "BASELINE_VISUAL_ANALYSIS",
            "trained_model_status": self._model_state,
            "disclaimer": "Baseline color/texture/edge saliency analysis. Not a trained camouflage classifier.",
            "processing_ms": proc_ms,
            "region_count": len(regions),
            "regions": regions,
            "original_file": saved_orig,
            "analyzed_file": saved_analyzed,
            "original_b64": base64.b64encode(orig_buf.tobytes()).decode("ascii"),
            "analyzed_b64": base64.b64encode(ana_buf.tobytes()).decode("ascii"),
        }
        self._last_result = {k: v for k, v in result.items() if not k.endswith("_b64")}
        return result
