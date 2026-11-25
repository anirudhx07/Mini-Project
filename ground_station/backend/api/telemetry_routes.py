"""Telemetry REST API Routes."""

from flask import Blueprint, current_app, jsonify, request
from backend.telemetry.serial_receiver import list_serial_ports


telemetry_bp = Blueprint("telemetry_api", __name__)


@telemetry_bp.get("/api/telemetry")
def get_telemetry():
    tm = current_app.extensions["telemetry_manager"]
    sr = current_app.extensions["serial_receiver"]
    udp = current_app.extensions["udp_receiver"]
    state = tm.get_state()
    state["comm_mode"] = current_app.extensions.get("comm_mode", "USB_SERIAL")
    state["serial"] = sr.get_status()
    state["udp_listening"] = udp.is_running()
    return jsonify({"ok": True, "telemetry": state})


@telemetry_bp.get("/api/serial/ports")
def get_serial_ports():
    ports = list_serial_ports()
    return jsonify({"ok": True, "ports": ports, "count": len(ports)})


@telemetry_bp.get("/api/serial/status")
def get_serial_status():
    sr = current_app.extensions["serial_receiver"]
    return jsonify({
        "ok": True,
        "comm_mode": current_app.extensions.get("comm_mode", "USB_SERIAL"),
        "serial": sr.get_status(),
    })


@telemetry_bp.post("/api/serial/connect")
def connect_serial():
    sr = current_app.extensions["serial_receiver"]
    tm = current_app.extensions["telemetry_manager"]
    udp = current_app.extensions["udp_receiver"]
    body = request.get_json(silent=True) or {}

    port = str(body.get("port", "")).strip()
    if not port:
        return jsonify({"ok": False, "error": "COM port selection is required"}), 400

    try:
        baudrate = int(body.get("baudrate", 115200))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "Invalid baud rate"}), 400

    # Ensure UDP and Serial never run simultaneously against the same telemetry stream
    if udp.is_running():
        udp.stop()
    current_app.extensions["comm_mode"] = "USB_SERIAL"

    ok, msg = sr.connect(port=port, baudrate=baudrate)
    tm.broadcast_state()
    code = 200 if ok else 409
    return jsonify({
        "ok": ok,
        "message": msg,
        "comm_mode": "USB_SERIAL",
        "serial": sr.get_status(),
    }), code


@telemetry_bp.post("/api/serial/disconnect")
def disconnect_serial():
    sr = current_app.extensions["serial_receiver"]
    tm = current_app.extensions["telemetry_manager"]
    sr.disconnect()
    tm.broadcast_state()
    return jsonify({
        "ok": True,
        "message": "USB Serial disconnected",
        "comm_mode": current_app.extensions.get("comm_mode", "USB_SERIAL"),
        "serial": sr.get_status(),
    })


@telemetry_bp.get("/api/telemetry/history")
def get_telemetry_history():
    tm = current_app.extensions["telemetry_manager"]
    try:
        limit = int(request.args.get("limit", 120))
    except ValueError:
        return jsonify({"ok": False, "error": "Invalid limit parameter"}), 400
    return jsonify({"ok": True, "history": tm.get_history(limit=limit), "demo_mode": tm.is_demo_mode()})


@telemetry_bp.post("/api/telemetry/calibrate")
def calibrate_telemetry():
    tm = current_app.extensions["telemetry_manager"]
    body = request.get_json(silent=True) or {}
    action = str(body.get("action", "zero")).lower()

    if action == "reset":
        tm.calibration.reset()
        return jsonify({"ok": True, "calibration": tm.calibration.get_offsets(), "message": "Calibration offsets reset"})

    state = tm.get_state()
    data = state.get("data")
    if not data:
        return jsonify({"ok": False, "error": "Cannot zero-calibrate without active telemetry data"}), 400

    tm.calibration.set_zero(data["raw_pitch"], data["raw_roll"])
    return jsonify({"ok": True, "calibration": tm.calibration.get_offsets(), "message": "Zero level calibrated"})


@telemetry_bp.post("/api/telemetry/demo")
def toggle_demo_mode():
    tm = current_app.extensions["telemetry_manager"]
    sim = current_app.extensions["telemetry_simulator"]
    body = request.get_json(silent=True) or {}
    if "enabled" not in body or not isinstance(body["enabled"], bool):
        return jsonify({"ok": False, "error": "Boolean 'enabled' field is required"}), 400

    enabled = body["enabled"]
    tm.set_demo_mode(enabled)
    if enabled:
        sim.start()
    else:
        sim.stop()
    return jsonify({"ok": True, "demo_mode": tm.is_demo_mode()})
