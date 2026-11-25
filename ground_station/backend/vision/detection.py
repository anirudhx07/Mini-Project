"""Ultralytics YOLO Object Detection Engine with CUDA/CPU fallback."""

import threading
import time
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional, Tuple
import cv2
import numpy as np


def resolve_compute_device(preference: str = "auto") -> str:
    """Resolve requested compute device honestly based on actual PyTorch CUDA availability."""
    pref = (preference or "auto").lower()
    try:
        import torch
        cuda_ok = bool(torch.cuda.is_available())
    except ImportError:
        cuda_ok = False

    if pref == "cpu":
        return "cpu"
    if pref == "cuda":
        return "cuda" if cuda_ok else "cpu"
    return "cuda" if cuda_ok else "cpu"


class DetectionEngine:
    """Independent worker running YOLO inference on frames from CameraManager."""

    def __init__(
        self,
        camera_manager,
        model_path: str,
        confidence: float = 0.40,
        device_pref: str = "auto",
        frame_skip: int = 1,
        event_logger=None,
        socketio=None,
    ):
        self.camera_manager = camera_manager
        self.model_path = str(model_path)
        self.confidence = float(confidence)
        self.device_pref = device_pref
        self.frame_skip = max(1, int(frame_skip))
        self._event_logger = event_logger
        self._socketio = socketio

        self._lock = threading.Lock()
        self._model = None
        self._model_loaded = False
        self._model_status = "NOT_LOADED"
        self._model_error = ""
        self._active_device = resolve_compute_device(device_pref)
        self._class_names: Dict[int, str] = {}
        self._selected_classes: List[str] = []

        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._latest_annotated_jpeg: Optional[bytes] = None
        self._latest_annotated_frame: Optional[np.ndarray] = None
        self._latest_detections: List[Dict[str, Any]] = []
        self._inference_ms = 0.0
        self._ai_fps = 0.0
        self._output_seq = 0

    def set_socketio(self, socketio):
        self._socketio = socketio

    def configure(
        self,
        model_path: Optional[str] = None,
        confidence: Optional[float] = None,
        device_pref: Optional[str] = None,
        frame_skip: Optional[int] = None,
        selected_classes: Optional[List[str]] = None,
    ):
        reload_needed = False
        with self._lock:
            if model_path is not None and str(model_path).strip() != self.model_path:
                self.model_path = str(model_path).strip()
                reload_needed = True
            if confidence is not None:
                self.confidence = max(0.05, min(float(confidence), 0.99))
            if device_pref is not None and device_pref != self.device_pref:
                self.device_pref = device_pref
                self._active_device = resolve_compute_device(device_pref)
                reload_needed = True
            if frame_skip is not None:
                self.frame_skip = max(1, int(frame_skip))
            if selected_classes is not None:
                self._selected_classes = [c.strip() for c in selected_classes if c.strip()]

        if reload_needed and self._model_loaded:
            self.load_model()

    def load_model(self) -> Tuple[bool, str]:
        """Load Ultralytics YOLO model without auto-downloading missing weights."""
        path_obj = Path(self.model_path)
        if not path_obj.exists():
            msg = f"YOLO model file not found at '{self.model_path}'. Place weights in ground_station/models/."
            with self._lock:
                self._model = None
                self._model_loaded = False
                self._model_status = "MODEL_NOT_FOUND"
                self._model_error = msg
            return False, msg

        try:
            from ultralytics import YOLO
        except ImportError:
            msg = "Ultralytics package is not installed. Run: pip install ultralytics torch"
            with self._lock:
                self._model = None
                self._model_loaded = False
                self._model_status = "DEPENDENCY_MISSING"
                self._model_error = msg
            return False, msg

        try:
            device = resolve_compute_device(self.device_pref)
            model = YOLO(str(path_obj))
            model.to(device)
            names = getattr(model, "names", {}) or {}
            with self._lock:
                self._model = model
                self._model_loaded = True
                self._model_status = "LOADED"
                self._model_error = ""
                self._active_device = device
                self._class_names = {int(k): str(v) for k, v in names.items()}
            msg = f"YOLO model loaded ({path_obj.name}) on {device.upper()}"
            if self._event_logger:
                self._event_logger.log("AI", msg, level="INFO")
            return True, msg
        except Exception as exc:
            msg = f"Failed to load YOLO model: {exc}"
            with self._lock:
                self._model = None
                self._model_loaded = False
                self._model_status = "LOAD_ERROR"
                self._model_error = msg
            if self._event_logger:
                self._event_logger.log("AI", msg, level="ERROR")
            return False, msg

    def start(self) -> Tuple[bool, str]:
        """Start background YOLO object detection worker."""
        with self._lock:
            if self._running:
                return True, "Object detection already running"
            loaded = self._model_loaded

        if not loaded:
            ok, msg = self.load_model()
            if not ok:
                return False, msg

        cam_status = self.camera_manager.get_status()
        if not cam_status.get("running"):
            return False, "Camera is not running. Start the camera before starting Object Detection."

        with self._lock:
            self._running = True
            self._thread = threading.Thread(target=self._inference_loop, name="YOLODetectionLoop", daemon=True)
            self._thread.start()

        if self._event_logger:
            self._event_logger.log("AI", f"Object detection started on {self._active_device.upper()}", level="INFO")
        return True, "Object detection started"

    def stop(self):
        """Stop detection worker cleanly."""
        with self._lock:
            was_running = self._running
            self._running = False
            thread = self._thread
            self._thread = None

        if thread and thread.is_alive():
            thread.join(timeout=2.0)

        with self._lock:
            self._ai_fps = 0.0
            self._inference_ms = 0.0
            self._latest_detections = []

        if was_running and self._event_logger:
            self._event_logger.log("AI", "Object detection stopped", level="INFO")

    def _inference_loop(self):
        last_frame_id = -1
        fps_count = 0
        fps_t0 = time.monotonic()
        processed_idx = 0

        while True:
            with self._lock:
                if not self._running or self._model is None:
                    break
                model = self._model
                conf = self.confidence
                device = self._active_device
                skip = self.frame_skip
                selected = set(self._selected_classes)

            frame, fid = self.camera_manager.get_latest_frame()
            if frame is None or fid == last_frame_id:
                time.sleep(0.015)
                continue

            last_frame_id = fid
            processed_idx += 1
            if skip > 1 and (processed_idx % skip) != 0:
                continue

            t0 = time.perf_counter()
            try:
                results = model.predict(frame, conf=conf, device=device, verbose=False)
                inf_ms = (time.perf_counter() - t0) * 1000.0
            except Exception as exc:
                with self._lock:
                    self._model_error = f"Inference error: {exc}"
                time.sleep(0.1)
                continue

            detections: List[Dict[str, Any]] = []
            annotated = frame.copy()

            if results and len(results) > 0 and results[0].boxes is not None:
                boxes = results[0].boxes
                for b in boxes:
                    cls_id = int(b.cls[0].item())
                    cls_name = self._class_names.get(cls_id, str(cls_id))
                    if selected and cls_name not in selected:
                        continue
                    score = float(b.conf[0].item())
                    x1, y1, x2, y2 = [int(v) for v in b.xyxy[0].tolist()]
                    detections.append({
                        "class_id": cls_id,
                        "class_name": cls_name,
                        "confidence": round(score * 100.0, 1),
                        "bbox": [x1, y1, x2, y2],
                    })
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), (255, 167, 54), 2)
                    label = f"{cls_name} {score * 100.0:.0f}%"
                    cv2.putText(
                        annotated,
                        label,
                        (x1, max(16, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (154, 214, 37),
                        1,
                        cv2.LINE_AA,
                    )

            ok_enc, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 82])
            jpeg_bytes = buf.tobytes() if ok_enc else None

            fps_count += 1
            now = time.monotonic()
            elapsed = now - fps_t0

            with self._lock:
                self._latest_detections = detections
                self._latest_annotated_frame = annotated
                if jpeg_bytes is not None:
                    self._latest_annotated_jpeg = jpeg_bytes
                self._inference_ms = round(inf_ms, 1)
                self._output_seq += 1
                if elapsed >= 1.0:
                    self._ai_fps = round(fps_count / elapsed, 1)
                    fps_count = 0
                    fps_t0 = now

            if self._socketio is not None and (self._output_seq % 3 == 0):
                try:
                    self._socketio.emit("detection_update", self.get_status())
                except Exception:
                    pass

    def capture_snapshot(self) -> Tuple[bool, str]:
        with self._lock:
            frame = self._latest_annotated_frame.copy() if self._latest_annotated_frame is not None else None
        if frame is None:
            return False, "No active detection frame available to save"
        return self.camera_manager.capture_snapshot(prefix="detection", custom_frame=frame)

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "model_loaded": self._model_loaded,
                "model_status": self._model_status,
                "model_path": self.model_path,
                "device": self._active_device.upper(),
                "confidence_threshold": self.confidence,
                "frame_skip": self.frame_skip,
                "selected_classes": list(self._selected_classes),
                "available_classes": list(self._class_names.values()),
                "detection_count": len(self._latest_detections),
                "detections": list(self._latest_detections),
                "inference_ms": self._inference_ms,
                "fps": self._ai_fps,
                "error": self._model_error,
            }

    def mjpeg_generator(self) -> Generator[bytes, None, None]:
        last_seq = -1
        while True:
            with self._lock:
                running = self._running
                jpeg = self._latest_annotated_jpeg
                seq = self._output_seq

            if not running:
                break
            if jpeg is not None and seq != last_seq:
                last_seq = seq
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
            else:
                time.sleep(0.02)
