"""COCKPIT — AI-Powered Drone Ground Control Station Server Entrypoint."""

import atexit
from flask import Flask, render_template
from flask_socketio import SocketIO

from config import Config
from backend.services.event_logger import EventLogger
from backend.services.system_monitor import SystemMonitor
from backend.telemetry.telemetry_manager import TelemetryManager
from backend.telemetry.udp_receiver import UDPTelemetryReceiver
from backend.telemetry.serial_receiver import SerialTelemetryReceiver
from backend.telemetry.simulator import TelemetrySimulator
from backend.camera.camera_manager import CameraManager
from backend.vision.detection import DetectionEngine
from backend.vision.tracking import TrackingEngine
from backend.vision.camouflage import CamouflageAnalyzer
from backend.api.telemetry_routes import telemetry_bp
from backend.api.camera_routes import camera_bp
from backend.api.detection_routes import detection_bp
from backend.api.tracking_routes import tracking_bp
from backend.api.system_routes import system_bp


socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")


def create_app(start_background: bool = True, config_cls=Config) -> Flask:
    """Create and configure the COCKPIT Flask + SocketIO application."""
    config_cls.ensure_directories()

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.config["SECRET_KEY"] = config_cls.SECRET_KEY

    socketio.init_app(app)

    event_logger = EventLogger(config_cls.DATABASE_PATH, socketio=socketio)
    system_monitor = SystemMonitor()
    telemetry_manager = TelemetryManager(
        timeout_sec=config_cls.ESP32_TIMEOUT_SEC,
        history_size=config_cls.TELEMETRY_HISTORY_SIZE,
        event_logger=event_logger,
        socketio=socketio,
    )
    udp_receiver = UDPTelemetryReceiver(
        telemetry_manager=telemetry_manager,
        host=config_cls.UDP_HOST,
        port=config_cls.UDP_PORT,
        event_logger=event_logger,
    )
    serial_receiver = SerialTelemetryReceiver(
        telemetry_manager=telemetry_manager,
        default_baudrate=config_cls.SERIAL_BAUDRATE,
        event_logger=event_logger,
    )
    telemetry_simulator = TelemetrySimulator(telemetry_manager=telemetry_manager)

    camera_manager = CameraManager(
        captures_dir=config_cls.CAPTURES_DIR,
        source_type=config_cls.CAMERA_SOURCE,
        camera_index=config_cls.CAMERA_INDEX,
        width=config_cls.CAMERA_WIDTH,
        height=config_cls.CAMERA_HEIGHT,
        target_fps=config_cls.CAMERA_FPS,
        esp32_cam_url=config_cls.ESP32_CAM_URL,
        event_logger=event_logger,
    )
    detection_engine = DetectionEngine(
        camera_manager=camera_manager,
        model_path=config_cls.YOLO_MODEL_PATH,
        confidence=config_cls.YOLO_CONFIDENCE,
        device_pref=config_cls.AI_DEVICE,
        frame_skip=config_cls.INFERENCE_FRAME_SKIP,
        event_logger=event_logger,
        socketio=socketio,
    )
    tracking_engine = TrackingEngine(
        camera_manager=camera_manager,
        model_path=config_cls.YOLO_MODEL_PATH,
        confidence=config_cls.YOLO_CONFIDENCE,
        device_pref=config_cls.AI_DEVICE,
        event_logger=event_logger,
        socketio=socketio,
    )
    camouflage_analyzer = CamouflageAnalyzer(
        camera_manager=camera_manager,
        captures_dir=config_cls.CAPTURES_DIR,
        trained_model_path=config_cls.CAMOUFLAGE_MODEL_PATH,
        event_logger=event_logger,
    )

    app.extensions["event_logger"] = event_logger
    app.extensions["system_monitor"] = system_monitor
    app.extensions["telemetry_manager"] = telemetry_manager
    app.extensions["udp_receiver"] = udp_receiver
    app.extensions["serial_receiver"] = serial_receiver
    app.extensions["comm_mode"] = config_cls.COMM_MODE if config_cls.COMM_MODE in ("USB_SERIAL", "UDP_WIFI") else "USB_SERIAL"
    app.extensions["telemetry_simulator"] = telemetry_simulator
    app.extensions["camera_manager"] = camera_manager
    app.extensions["detection_engine"] = detection_engine
    app.extensions["tracking_engine"] = tracking_engine
    app.extensions["camouflage_analyzer"] = camouflage_analyzer

    app.register_blueprint(telemetry_bp)
    app.register_blueprint(camera_bp)
    app.register_blueprint(detection_bp)
    app.register_blueprint(tracking_bp)
    app.register_blueprint(system_bp)

    @app.get("/")
    def index():
        return render_template("index.html")

    @socketio.on("connect")
    def on_ws_connect():
        socketio.emit("telemetry_update", telemetry_manager.get_state())

    def shutdown_services():
        telemetry_simulator.stop()
        detection_engine.stop()
        tracking_engine.stop()
        camera_manager.stop()
        serial_receiver.disconnect()
        udp_receiver.stop()

    app.extensions["shutdown_fn"] = shutdown_services

    if start_background:
        if app.extensions["comm_mode"] == "UDP_WIFI":
            udp_receiver.start()
        elif config_cls.SERIAL_PORT:
            serial_receiver.connect(config_cls.SERIAL_PORT, config_cls.SERIAL_BAUDRATE)
        event_logger.log(
            "SYSTEM",
            f"COCKPIT initialized (REAL HARDWARE MODE | {app.extensions['comm_mode']})",
            level="INFO",
        )
        atexit.register(shutdown_services)

    return app


if __name__ == "__main__":
    application = create_app(start_background=True)
    print("\n============================================================")
    print("  COCKPIT — AI-Powered Drone Ground Control Station")
    print("  See. Analyze. Control.")
    print(f"  Dashboard URL : http://{Config.HOST}:{Config.PORT}")
    print(f"  ESP32 UDP Port: {Config.UDP_HOST}:{Config.UDP_PORT}")
    print("============================================================\n")
    socketio.run(
        application,
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        use_reloader=False,
        allow_unsafe_werkzeug=True,
    )
