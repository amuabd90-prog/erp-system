import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INSTANCE_DIR = BASE_DIR / "instance"
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "ha-business-secret-key-change-me")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{INSTANCE_DIR / 'ha_business.db'}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REMEMBER_COOKIE_HTTPONLY = True
    SESSION_COOKIE_HTTPONLY = True
    TEMPLATES_AUTO_RELOAD = True
    TELEGRAM_ENABLED = os.environ.get("TELEGRAM_ENABLED", "0") == "1"
    TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_IDS = os.environ.get("TELEGRAM_CHAT_IDS", "")
