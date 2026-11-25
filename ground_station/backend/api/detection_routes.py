"""Object Detection and Camouflage Analysis API Routes."""

from flask import Blueprint, Response, current_app, jsonify, request


detection_bp = Blueprint("detection_api", __name__)


@detection_bp.get("/api/detection/status")
def detection_status():
    det = current_app.extensions["detection_engine"]
    return jsonify({"ok": True, "detection": det.get_status()})


@detection_bp.get("/api/detection/stream")
def detection_stream():
    det = current_app.extensions["detection_engine"]
    if not det.get_status().get("running"):
        return jsonify({"ok": False, "error": "Object detection is not running"}), 409
    return Response(
        det.mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@detection_bp.post("/api/detection/start")
def detection_start():
    det = current_app.extensions["detection_engine"]
    body = request.get_json(silent=True) or {}
    try:
        det.configure(
            model_path=body.get("model_path"),
            confidence=body.get("confidence"),
            device_pref=body.get("device"),
            frame_skip=body.get("frame_skip"),
            selected_classes=body.get("selected_classes"),
        )
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid detection configuration parameter"}), 400

    ok, msg = det.start()
    code = 200 if ok else 409
    return jsonify({"ok": ok, "message": msg, "detection": det.get_status()}), code


@detection_bp.post("/api/detection/stop")
def detection_stop():
    det = current_app.extensions["detection_engine"]
    det.stop()
    return jsonify({"ok": True, "message": "Object detection stopped", "detection": det.get_status()})


@detection_bp.post("/api/detection/config")
def detection_config():
    det = current_app.extensions["detection_engine"]
    body = request.get_json(silent=True) or {}
    try:
        det.configure(
            model_path=body.get("model_path"),
            confidence=body.get("confidence"),
            device_pref=body.get("device"),
            frame_skip=body.get("frame_skip"),
            selected_classes=body.get("selected_classes"),
        )
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid detection parameter"}), 400
    return jsonify({"ok": True, "detection": det.get_status()})


@detection_bp.post("/api/detection/capture")
def detection_capture():
    det = current_app.extensions["detection_engine"]
    ok, result = det.capture_snapshot()
    if not ok:
        return jsonify({"ok": False, "error": result}), 409
    return jsonify({"ok": True, "filename": result, "url": f"/api/captures/{result}"})


@detection_bp.get("/api/camouflage/status")
def camouflage_status():
    camo = current_app.extensions["camouflage_analyzer"]
    return jsonify({"ok": True, "camouflage": camo.get_status()})


@detection_bp.post("/api/camouflage/analyze")
def camouflage_analyze():
    camo = current_app.extensions["camouflage_analyzer"]
    body = request.get_json(silent=True) or {}
    try:
        sensitivity = float(body.get("sensitivity", 0.60))
        save_result = bool(body.get("save_result", True))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid camouflage analysis parameters"}), 400

    ok, res = camo.analyze_current_frame(sensitivity=sensitivity, save_result=save_result)
    if not ok:
        return jsonify({"ok": False, "error": res.get("error", "Analysis failed")}), 409
    return jsonify({"ok": True, "analysis": res})
