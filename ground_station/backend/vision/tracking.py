"""Multi-Object Tracking Engine (YOLO + ByteTrack with IoU Fallback)."""

from collections import deque
import threading
import time
from pathlib import Path
from typing import Any, Deque, Dict, Generator, List, Optional, Tuple
import cv2
import numpy as np

from .detection import resolve_compute_device


class _SimpleIoUTracker:
    """Lightweight IoU association fallback when ByteTrack extra dependencies are unavailable."""

    def __init__(self, max_lost: int = 12, iou_thresh: float = 0.25):
        self.next_id = 1
        self.tracks: Dict[int, Dict[str, Any]] = {}
        self.max_lost = max_lost
        self.iou_thresh = iou_thresh

    @staticmethod
    def _iou(a: List[int], b: List[int]) -> float:
        ax1, ay1, ax2, ay2 = a
        bx1, by1, bx2, by2 = b
        ix1, iy1 = max(ax1, bx1), max(ay1, by1)
        ix2, iy2 = min(ax2, bx2), min(ay2, by2)
        inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
        if inter <= 0:
            return 0.0
        area_a = max(1, (ax2 - ax1) * (ay2 - ay1))
        area_b = max(1, (bx2 - bx1) * (by2 - by1))
        return inter / float(area_a + area_b - inter)

    def update(self, detections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        matched_tids = set()
        results: List[Dict[str, Any]] = []

        for det in detections:
            best_tid = None
            best_iou = self.iou_thresh
            for tid, tr in self.tracks.items():
                if tid in matched_tids:
                    continue
                score = self._iou(det["bbox"], tr["bbox"])
                if score > best_iou:
                    best_iou = score
                    best_tid = tid

            if best_tid is None:
                best_tid = self.next_id
                self.next_id += 1

            matched_tids.add(best_tid)
            self.tracks[best_tid] = {"bbox": det["bbox"], "lost": 0}
            results.append({**det, "track_id": best_tid})

        for tid in list(self.tracks.keys()):
            if tid not in matched_tids:
                self.tracks[tid]["lost"] += 1
                if self.tracks[tid]["lost"] > self.max_lost:
                    del self.tracks[tid]

        return results


class TrackingEngine:
    """Runs multi-object tracking on real camera frames with persistent IDs and movement trails."""

    def __init__(
        self,
        camera_manager,
        model_path: str,
        confidence: float = 0.40,
        device_pref: str = "auto",
        trail_length: int = 30,
        event_logger=None,
        socketio=None,
    ):
        self.camera_manager = camera_manager
        self.model_path = str(model_path)
        self.confidence = float(confidence)
        self.device_pref = device_pref
        self.trail_length = int(trail_length)
        self._event_logger = event_logger
        self._socketio = socketio

        self._lock = threading.Lock()
        self._model = None
        self._model_loaded = False
        self._model_status = "NOT_LOADED"
        self._model_error = ""
        self._active_device = resolve_compute_device(device_pref)
        self._tracker_mode = "ByteTrack"
        self._class_names: Dict[int, str] = {}

        self._running = False
        self._thread: Optional[threading.Thread] = None

        self._trails: Dict[int, Deque[Tuple[int, int]]] = {}
        self._selected_track_id: Optional[int] = None
        self._active_tracks: List[Dict[str, Any]] = []
        self._total_unique_ids = 0
        self._seen_ids = set()
        self._inference_ms = 0.0
        self._tracking_fps = 0.0
        self._latest_jpeg: Optional[bytes] = None
        self._output_seq = 0

    def set_socketio(self, socketio):
        self._socketio = socketio

    def set_selected_track(self, track_id: Optional[int]):
        with self._lock:
            self._selected_track_id = int(track_id) if track_id is not None else None

    def configure(self, model_path: Optional[str] = None, confidence: Optional[float] = None, device_pref: Optional[str] = None):
        with self._lock:
            if model_path is not None:
                self.model_path = str(model_path).strip()
            if confidence is not None:
                self.confidence = max(0.05, min(float(confidence), 0.99))
            if device_pref is not None:
                self.device_pref = device_pref
                self._active_device = resolve_compute_device(device_pref)

    def load_model(self) -> Tuple[bool, str]:
        path_obj = Path(self.model_path)
        if not path_obj.exists():
            msg = f"Tracking model not found at '{self.model_path}'. Place YOLO weights in ground_station/models/."
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
            return True, f"Tracking model loaded on {device.upper()}"
        except Exception as exc:
            msg = f"Failed to load tracking model: {exc}"
            with self._lock:
                self._model = None
                self._model_loaded = False
                self._model_status = "LOAD_ERROR"
                self._model_error = msg
            return False, msg

    def start(self) -> Tuple[bool, str]:
        with self._lock:
            if self._running:
                return True, "Object tracking already running"
            loaded = self._model_loaded

        if not loaded:
            ok, msg = self.load_model()
            if not ok:
                return False, msg

        if not self.camera_manager.get_status().get("running"):
            return False, "Camera is not running. Start the camera before starting Object Tracking."

        with self._lock:
            self._trails.clear()
            self._seen_ids.clear()
            self._total_unique_ids = 0
            self._active_tracks = []
            self._running = True
            self._thread = threading.Thread(target=self._tracking_loop, name="ObjectTrackingLoop", daemon=True)
            self._thread.start()

        if self._event_logger:
            self._event_logger.log("AI", f"Object tracking started ({self._tracker_mode})", level="INFO")
        return True, "Object tracking started"

    def stop(self):
        with self._lock:
            was_running = self._running
            self._running = False
            thread = self._thread
            self._thread = None

        if thread and thread.is_alive():
            thread.join(timeout=2.0)

        with self._lock:
            self._tracking_fps = 0.0
            self._inference_ms = 0.0
            self._active_tracks = []

        if was_running and self._event_logger:
            self._event_logger.log("AI", "Object tracking stopped", level="INFO")

    def _tracking_loop(self):
        last_fid = -1
        fps_count = 0
        fps_t0 = time.monotonic()
        iou_fallback = _SimpleIoUTracker()
        bytetrack_failed = False

        while True:
            with self._lock:
                if not self._running or self._model is None:
                    break
                model = self._model
                conf = self.confidence
                device = self._active_device
                sel_id = self._selected_track_id

            frame, fid = self.camera_manager.get_latest_frame()
            if frame is None or fid == last_fid:
                time.sleep(0.015)
                continue
            last_fid = fid

            t0 = time.perf_counter()
            tracks_out: List[Dict[str, Any]] = []

            if not bytetrack_failed:
                try:
                    results = model.track(frame, conf=conf, device=device, persist=True, tracker="bytetrack.yaml", verbose=False)
                    if results and len(results) > 0 and results[0].boxes is not None:
                        boxes = results[0].boxes
                        for b in boxes:
                            cls_id = int(b.cls[0].item())
                            cls_name = self._class_names.get(cls_id, str(cls_id))
                            score = float(b.conf[0].item())
                            x1, y1, x2, y2 = [int(v) for v in b.xyxy[0].tolist()]
                            tid = int(b.id[0].item()) if b.id is not None else -1
                            if tid >= 0:
                                tracks_out.append({
                                    "track_id": tid,
                                    "class_name": cls_name,
                                    "confidence": round(score * 100.0, 1),
                                    "bbox": [x1, y1, x2, y2],
                                })
                except Exception:
                    bytetrack_failed = True
                    with self._lock:
                        self._tracker_mode = "IoU-Fallback"

            if bytetrack_failed:
                try:
                    results = model.predict(frame, conf=conf, device=device, verbose=False)
                    raw_dets = []
                    if results and len(results) > 0 and results[0].boxes is not None:
                        for b in results[0].boxes:
                            cls_id = int(b.cls[0].item())
                            cls_name = self._class_names.get(cls_id, str(cls_id))
                            score = float(b.conf[0].item())
                            x1, y1, x2, y2 = [int(v) for v in b.xyxy[0].tolist()]
                            raw_dets.append({
                                "class_name": cls_name,
                                "confidence": round(score * 100.0, 1),
                                "bbox": [x1, y1, x2, y2],
                            })
                    tracks_out = iou_fallback.update(raw_dets)
                except Exception:
                    time.sleep(0.1)
                    continue

            inf_ms = (time.perf_counter() - t0) * 1000.0
            annotated = frame.copy()

            with self._lock:
                for tr in tracks_out:
                    tid = tr["track_id"]
                    self._seen_ids.add(tid)
                    x1, y1, x2, y2 = tr["bbox"]
                    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                    if tid not in self._trails:
                        self._trails[tid] = deque(maxlen=self.trail_length)
                    self._trails[tid].append((cx, cy))
                    tr["trail_len"] = len(self._trails[tid])
                    tr["selected"] = (sel_id is not None and tid == sel_id)

                    is_sel = tr["selected"]
                    box_color = (104, 82, 255) if is_sel else (255, 167, 54)
                    thickness = 3 if is_sel else 2
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), box_color, thickness)

                    pts = list(self._trails[tid])
                    for idx in range(1, len(pts)):
                        cv2.line(annotated, pts[idx - 1], pts[idx], (154, 214, 37), 2)

                    label = f"ID:{tid} {tr['class_name']} {tr['confidence']:.0f}%"
                    cv2.putText(
                        annotated,
                        label,
                        (x1, max(16, y1 - 6)),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        box_color,
                        1,
                        cv2.LINE_AA,
                    )

                self._total_unique_ids = len(self._seen_ids)
                self._active_tracks = tracks_out
                self._inference_ms = round(inf_ms, 1)

            ok_enc, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 82])
            if ok_enc:
                with self._lock:
                    self._latest_jpeg = buf.tobytes()
                    self._output_seq += 1

            fps_count += 1
            now = time.monotonic()
            if now - fps_t0 >= 1.0:
                with self._lock:
                    self._tracking_fps = round(fps_count / (now - fps_t0), 1)
                fps_count = 0
                fps_t0 = now

            if self._socketio is not None and (self._output_seq % 3 == 0):
                try:
                    self._socketio.emit("tracking_update", self.get_status())
                except Exception:
                    pass

    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "running": self._running,
                "model_loaded": self._model_loaded,
                "model_status": self._model_status,
                "tracker_mode": self._tracker_mode,
                "device": self._active_device.upper(),
                "selected_track_id": self._selected_track_id,
                "active_count": len(self._active_tracks),
                "total_unique_ids": self._total_unique_ids,
                "tracks": list(self._active_tracks),
                "inference_ms": self._inference_ms,
                "fps": self._tracking_fps,
                "error": self._model_error,
            }

    def mjpeg_generator(self) -> Generator[bytes, None, None]:
        last_seq = -1
        while True:
            with self._lock:
                running = self._running
                jpeg = self._latest_jpeg
                seq = self._output_seq
            if not running:
                break
            if jpeg is not None and seq != last_seq:
                last_seq = seq
                yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"
            else:
                time.sleep(0.02)
