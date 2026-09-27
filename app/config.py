import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings:
    PROJECT_NAME = "okDriver CCTV Video Analytics Platform"
    VERSION = "1.0.0"
    API_V1_PREFIX = "/api/v1"
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/okdriver_cctv.db")
    ANPR_DEDUP_WINDOW_SECONDS = int(os.getenv("ANPR_DEDUP_WINDOW_SECONDS", "15"))
    CAMERA_HEARTBEAT_TIMEOUT = int(os.getenv("CAMERA_HEARTBEAT_TIMEOUT", "45"))
    MIN_ALERT_CONFIDENCE = float(os.getenv("MIN_ALERT_CONFIDENCE", "0.75"))
    STATIC_DIR = BASE_DIR / "static"

settings = Settings()
