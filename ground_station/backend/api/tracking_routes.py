"""Multi-Object Tracking API Routes."""

from flask import Blueprint, Response, current_app, jsonify, request


tracking_bp = Blueprint("tracking_api", __name__)


@tracking_bp.get("/api/tracking/status")
def tracking_status():
    trk = current_app.extensions["tracking_engine"]
    return jsonify({"ok": True, "tracking": trk.get_status()})


@tracking_bp.get("/api/tracking/stream")
def tracking_stream():
    trk = current_app.extensions["tracking_engine"]
    if not trk.get_status().get("running"):
        return jsonify({"ok": False, "error": "Object tracking is not running"}), 409
    return Response(
        trk.mjpeg_generator(),
        mimetype="multipart/x-mixed-replace; boundary=frame",
    )


@tracking_bp.post("/api/tracking/start")
def tracking_start():
    trk = current_app.extensions["tracking_engine"]
    body = request.get_json(silent=True) or {}
    try:
        trk.configure(
            model_path=body.get("model_path"),
            confidence=body.get("confidence"),
            device_pref=body.get("device"),
        )
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid tracking parameters"}), 400

    ok, msg = trk.start()
    code = 200 if ok else 409
    return jsonify({"ok": ok, "message": msg, "tracking": trk.get_status()}), code


@tracking_bp.post("/api/tracking/stop")
def tracking_stop():
    trk = current_app.extensions["tracking_engine"]
    trk.stop()
    return jsonify({"ok": True, "message": "Object tracking stopped", "tracking": trk.get_status()})


@tracking_bp.post("/api/tracking/select")
def tracking_select():
    trk = current_app.extensions["tracking_engine"]
    body = request.get_json(silent=True) or {}
    tid = body.get("track_id")
    try:
        trk.set_selected_track(int(tid) if tid is not None and tid != "" else None)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid track_id"}), 400
    return jsonify({"ok": True, "selected_track_id": trk.get_status()["selected_track_id"]})
