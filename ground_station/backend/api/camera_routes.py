"""Camera Control and MJPEG Streaming API Routes."""

from flask import Blueprint, Response, current_app, jsonify, request, send_from_directory


camera_bp = Blueprint("camera_api", __name__)


@camera_bp.get("/api/camera/status")
def camera_status():
    cm = current_app.extensions["camera_manager"]
    return jsonify({"ok": True, "camera": cm.get_status()})


@camera_bp.get("/api/camera/stream")
def camera_stream():
    cm = current_app.extensions["camera_manager"]
    if not cm.get_status().get("running"):
        return jsonify({"ok": False, "error": "Camera is not running"}), 409
    return Response(
        cm.mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@camera_bp.post("/api/camera/start")
def camera_start():
    cm = current_app.extensions["camera_manager"]
    body = request.get_json(silent=True) or {}
    try:
        cm.configure(
            source_type=body.get("source_type"),
            camera_index=body.get("camera_index"),
            width=body.get("width"),
            height=body.get("height"),
            target_fps=body.get("fps"),
            esp32_cam_url=body.get("esp32_cam_url"),
            camera_ip=body.get("camera_ip"),
            stream_port=body.get("stream_port"),
            auto_reconnect=body.get("auto_reconnect"),
            connect_timeout=body.get("connect_timeout"),
        )
    except (TypeError, ValueError) as exc:
        return jsonify({"ok": False, "error": str(exc) or "Invalid camera configuration parameter"}), 400

    ok, msg = cm.start()
    status_code = 200 if ok else 503
    return jsonify({"ok": ok, "message": msg, "camera": cm.get_status()}), status_code


@camera_bp.post("/api/camera/config")
def camera_config():
    cm = current_app.extensions["camera_manager"]
    body = request.get_json(silent=True) or {}
    try:
        cm.configure(
            source_type=body.get("source_type"),
            camera_index=body.get("camera_index"),
            width=body.get("width"),
            height=body.get("height"),
            target_fps=body.get("fps"),
            esp32_cam_url=body.get("esp32_cam_url"),
            camera_ip=body.get("camera_ip"),
            stream_port=body.get("stream_port"),
            auto_reconnect=body.get("auto_reconnect"),
            connect_timeout=body.get("connect_timeout"),
        )
    except (TypeError, ValueError) as exc:
        return jsonify({"ok": False, "error": str(exc) or "Invalid camera configuration parameter"}), 400
    return jsonify({"ok": True, "message": "Camera configuration updated", "camera": cm.get_status()})


@camera_bp.post("/api/camera/test")
def camera_test():
    cm = current_app.extensions["camera_manager"]
    body = request.get_json(silent=True) or {}
    if body:
        try:
            cm.configure(
                source_type=body.get("source_type"),
                esp32_cam_url=body.get("esp32_cam_url"),
                camera_ip=body.get("camera_ip"),
                stream_port=body.get("stream_port"),
                connect_timeout=body.get("connect_timeout"),
            )
        except (TypeError, ValueError) as exc:
            return jsonify({"ok": False, "error": str(exc)}), 400
    ok, msg, latency_ms = cm.test_connection()
    return jsonify({
        "ok": ok,
        "message": msg,
        "latency_ms": latency_ms,
        "camera": cm.get_status(),
    }), (200 if ok else 503)


@camera_bp.post("/api/camera/stop")
def camera_stop():
    cm = current_app.extensions["camera_manager"]
    det = current_app.extensions["detection_engine"]
    trk = current_app.extensions["tracking_engine"]
    det.stop()
    trk.stop()
    cm.stop()
    return jsonify({"ok": True, "message": "Camera stopped", "camera": cm.get_status()})


@camera_bp.post("/api/camera/capture")
def camera_capture():
    cm = current_app.extensions["camera_manager"]
    ok, result = cm.capture_snapshot(prefix="cam")
    if not ok:
        return jsonify({"ok": False, "error": result}), 409
    return jsonify({"ok": True, "filename": result, "url": f"/api/captures/{result}"})


@camera_bp.get("/api/captures/<path:filename>")
def serve_capture(filename: str):
    cm = current_app.extensions["camera_manager"]
    return send_from_directory(str(cm.captures_dir), filename)


@camera_bp.get("/api/camera/serial/status")
def cam_serial_status():
    csm = current_app.extensions["cam_serial_monitor"]
    return jsonify({"ok": True, "cam_serial": csm.get_status()})


@camera_bp.post("/api/camera/serial/connect")
def cam_serial_connect():
    csm = current_app.extensions["cam_serial_monitor"]
    body = request.get_json(silent=True) or {}
    port = str(body.get("port", "")).strip()
    if not port:
        return jsonify({"ok": False, "error": "COM port selection is required"}), 400
    try:
        baudrate = int(body.get("baudrate", 115200))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid baud rate"}), 400

    ok, msg = csm.connect(port=port, baudrate=baudrate)
    return jsonify({"ok": ok, "message": msg, "cam_serial": csm.get_status()}), (200 if ok else 409)


@camera_bp.post("/api/camera/serial/disconnect")
def cam_serial_disconnect():
    csm = current_app.extensions["cam_serial_monitor"]
    csm.disconnect()
    return jsonify({"ok": True, "message": "ESP32-CAM USB serial disconnected", "cam_serial": csm.get_status()})
