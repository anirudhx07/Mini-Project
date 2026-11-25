"""System Status, Settings, Diagnostics, and Mission Logs API Routes."""

from flask import Blueprint, Response, current_app, jsonify, request


system_bp = Blueprint("system_api", __name__)


@system_bp.get("/api/status")
def overall_status():
    tm = current_app.extensions["telemetry_manager"]
    cm = current_app.extensions["camera_manager"]
    det = current_app.extensions["detection_engine"]
    trk = current_app.extensions["tracking_engine"]
    camo = current_app.extensions["camouflage_analyzer"]
    udp = current_app.extensions["udp_receiver"]
    sr = current_app.extensions["serial_receiver"]
    mon = current_app.extensions["system_monitor"]
    comm_mode = current_app.extensions.get("comm_mode", "USB_SERIAL")

    tel_state = tm.get_state()
    tel_state["comm_mode"] = comm_mode

    return jsonify({
        "ok": True,
        "app": "COCKPIT",
        "backend": "ONLINE",
        "comm_mode": comm_mode,
        "serial": sr.get_status(),
        "udp_listening": udp.is_running(),
        "udp_port": udp.port,
        "telemetry": tel_state,
        "camera": cm.get_status(),
        "detection": det.get_status(),
        "tracking": trk.get_status(),
        "camouflage": camo.get_status(),
        "system": mon.get_info(),
    })


@system_bp.get("/api/system/info")
def system_info():
    mon = current_app.extensions["system_monitor"]
    udp = current_app.extensions["udp_receiver"]
    sr = current_app.extensions["serial_receiver"]
    tm = current_app.extensions["telemetry_manager"]
    cm = current_app.extensions["camera_manager"]
    det = current_app.extensions["detection_engine"]
    comm_mode = current_app.extensions.get("comm_mode", "USB_SERIAL")

    return jsonify({
        "ok": True,
        "comm_mode": comm_mode,
        "serial": sr.get_status(),
        "system": mon.get_info(),
        "network": {
            "udp_host": udp.host,
            "udp_port": udp.port,
            "udp_running": udp.is_running(),
            "esp32_timeout_sec": tm.timeout_sec,
            "history_size": tm.history_size,
        },
        "storage": {
            "captures_dir": str(cm.captures_dir),
            "database_path": str(current_app.extensions["event_logger"].db_path),
        },
        "ai": {
            "model_path": det.model_path,
            "confidence": det.confidence,
            "device_pref": det.device_pref,
            "active_device": det.get_status()["device"],
            "frame_skip": det.frame_skip,
        },
    })


@system_bp.get("/api/logs")
def get_logs():
    logger = current_app.extensions["event_logger"]
    search = request.args.get("search", "")
    category = request.args.get("category", "")
    level = request.args.get("level", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    try:
        limit = int(request.args.get("limit", 200))
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid limit parameter"}), 400

    rows = logger.query(
        search=search,
        category=category,
        level=level,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return jsonify({"ok": True, "logs": rows, "count": len(rows)})


@system_bp.get("/api/logs/export")
def export_logs_csv():
    logger = current_app.extensions["event_logger"]
    csv_data = logger.export_csv(
        search=request.args.get("search", ""),
        category=request.args.get("category", ""),
        level=request.args.get("level", ""),
        date_from=request.args.get("date_from", ""),
        date_to=request.args.get("date_to", ""),
    )
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=cockpit_mission_logs.csv"},
    )


@system_bp.post("/api/logs/clear")
def clear_logs():
    logger = current_app.extensions["event_logger"]
    deleted = logger.clear()
    logger.log("SYSTEM", f"Mission logs cleared ({deleted} records removed)", level="WARNING")
    return jsonify({"ok": True, "deleted": deleted})


@system_bp.post("/api/settings")
def update_settings():
    body = request.get_json(silent=True) or {}
    tm = current_app.extensions["telemetry_manager"]
    udp = current_app.extensions["udp_receiver"]
    sr = current_app.extensions["serial_receiver"]
    cm = current_app.extensions["camera_manager"]
    det = current_app.extensions["detection_engine"]
    trk = current_app.extensions["tracking_engine"]
    logger = current_app.extensions["event_logger"]

    try:
        if "comm_mode" in body:
            new_mode = str(body["comm_mode"]).upper()
            if new_mode not in ("USB_SERIAL", "UDP_WIFI"):
                return jsonify({"ok": False, "error": "comm_mode must be USB_SERIAL or UDP_WIFI"}), 400
            current_app.extensions["comm_mode"] = new_mode
            if new_mode == "USB_SERIAL":
                if udp.is_running():
                    udp.stop()
            else:
                sr.disconnect()
                if not udp.is_running():
                    udp.start()
        if "udp_port" in body and int(body["udp_port"]) != udp.port:
            new_port = int(body["udp_port"])
            if not (1024 <= new_port <= 65535):
                return jsonify({"ok": False, "error": "UDP port must be between 1024 and 65535"}), 400
            if current_app.extensions.get("comm_mode") == "UDP_WIFI":
                udp.restart(new_port)
            else:
                udp.port = new_port
        if "esp32_timeout_sec" in body:
            tm.set_timeout(float(body["esp32_timeout_sec"]))
        if "history_size" in body:
            tm.set_history_size(int(body["history_size"]))
        if any(k in body for k in ("camera_source", "camera_index", "camera_width", "camera_height", "camera_fps", "esp32_cam_url")):
            cm.configure(
                source_type=body.get("camera_source"),
                camera_index=body.get("camera_index"),
                width=body.get("camera_width"),
                height=body.get("camera_height"),
                target_fps=body.get("camera_fps"),
                esp32_cam_url=body.get("esp32_cam_url"),
            )
        if any(k in body for k in ("model_path", "confidence", "ai_device", "frame_skip")):
            det.configure(
                model_path=body.get("model_path"),
                confidence=body.get("confidence"),
                device_pref=body.get("ai_device"),
                frame_skip=body.get("frame_skip"),
            )
            trk.configure(
                model_path=body.get("model_path"),
                confidence=body.get("confidence"),
                device_pref=body.get("ai_device"),
            )
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid settings value provided"}), 400

    logger.log("SYSTEM", "System settings updated via dashboard", level="INFO")
    return jsonify({"ok": True, "message": "Settings applied"})
