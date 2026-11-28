"""COCKPIT Ground Control Station Configuration Management."""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Central configuration for COCKPIT Ground Control Station."""

    APP_NAME = "COCKPIT"
    APP_TAGLINE = "See. Analyze. Control."
    VERSION = "1.0.0"

    # Flask / Server
    SECRET_KEY = os.getenv("COCKPIT_SECRET_KEY", "cockpit-local-gcs-secret-change-me")
    HOST = os.getenv("COCKPIT_HOST", "127.0.0.1")
    PORT = int(os.getenv("COCKPIT_PORT", "5000"))
    DEBUG = os.getenv("COCKPIT_DEBUG", "false").lower() == "true"

    # Communication Mode ("UDP_WIFI" default for wireless Main ESP32 | "USB_SERIAL")
    COMM_MODE = os.getenv("COCKPIT_COMM_MODE", "UDP_WIFI").upper()

    # ESP32 USB Serial Telemetry
    SERIAL_PORT = os.getenv("COCKPIT_SERIAL_PORT", "")
    SERIAL_BAUDRATE = int(os.getenv("COCKPIT_SERIAL_BAUDRATE", "115200"))

    # ESP32 UDP Telemetry
    UDP_HOST = os.getenv("COCKPIT_UDP_HOST", "0.0.0.0")
    UDP_PORT = int(os.getenv("COCKPIT_UDP_PORT", "4210"))
    ESP32_TIMEOUT_SEC = float(os.getenv("COCKPIT_ESP32_TIMEOUT", "3.0"))
    TELEMETRY_HISTORY_SIZE = int(os.getenv("COCKPIT_TELEMETRY_HISTORY", "300"))

    # Camera Settings (ESP32-CAM OV2640 default, Laptop Webcam fallback)
    CAMERA_SOURCE = os.getenv("COCKPIT_CAMERA_SOURCE", "esp32cam")
    CAMERA_INDEX = int(os.getenv("COCKPIT_CAMERA_INDEX", "0"))
    CAMERA_WIDTH = int(os.getenv("COCKPIT_CAMERA_WIDTH", "640"))
    CAMERA_HEIGHT = int(os.getenv("COCKPIT_CAMERA_HEIGHT", "480"))
    CAMERA_FPS = int(os.getenv("COCKPIT_CAMERA_FPS", "30"))
    CAMERA_IP = os.getenv("CAMERA_IP", "10.159.217.26")
    CAMERA_STREAM_PORT = int(os.getenv("CAMERA_STREAM_PORT", "81"))
    CAMERA_BASE_URL = os.getenv("CAMERA_BASE_URL", f"http://{CAMERA_IP}")
    CAMERA_STREAM_URL = os.getenv(
        "CAMERA_STREAM_URL",
        os.getenv("COCKPIT_ESP32_CAM_URL", f"http://{CAMERA_IP}:{CAMERA_STREAM_PORT}/stream"),
    )
    ESP32_CAM_URL = CAMERA_STREAM_URL
    CAMERA_AUTO_RECONNECT = os.getenv("CAMERA_AUTO_RECONNECT", "true").lower() == "true"
    CAMERA_CONNECT_TIMEOUT = float(os.getenv("CAMERA_CONNECT_TIMEOUT", "4.0"))

    # AI / Vision Settings
    YOLO_MODEL_PATH = os.getenv("COCKPIT_YOLO_MODEL", str(BASE_DIR / "models" / "yolov8n.pt"))
    YOLO_CONFIDENCE = float(os.getenv("COCKPIT_YOLO_CONF", "0.40"))
    AI_DEVICE = os.getenv("COCKPIT_AI_DEVICE", "auto")  # auto, cuda, cpu
    INFERENCE_FRAME_SKIP = int(os.getenv("COCKPIT_FRAME_SKIP", "1"))
    CAMOUFLAGE_MODEL_PATH = os.getenv("COCKPIT_CAMO_MODEL", "")

    # Storage & Database
    CAPTURES_DIR = Path(os.getenv("COCKPIT_CAPTURES_DIR", str(BASE_DIR / "captures")))
    DATABASE_PATH = Path(os.getenv("COCKPIT_DB_PATH", str(BASE_DIR / "database" / "cockpit_logs.db")))
    MODELS_DIR = Path(os.getenv("COCKPIT_MODELS_DIR", str(BASE_DIR / "models")))
    LOG_RETENTION_DAYS = int(os.getenv("COCKPIT_LOG_RETENTION_DAYS", "30"))

    # Operation Mode (Always defaults to REAL HARDWARE MODE)
    DEMO_MODE = False

    @classmethod
    def ensure_directories(cls):
        """Ensure required runtime directories exist."""
        cls.CAPTURES_DIR.mkdir(parents=True, exist_ok=True)
        cls.DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        cls.MODELS_DIR.mkdir(parents=True, exist_ok=True)
