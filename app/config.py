# ==============================
# app/config.py
# ==============================
from __future__ import annotations
import os
from pathlib import Path

APP_NAME = "py-spotify-interrupter"

HOME = Path.home()
APP_DIR = HOME/ f".{APP_NAME}"
DB_PATH = APP_DIR/"app.db"
LOG_PATH = APP_DIR/"app.log"
DEFAULT_SOUND_DIR = APP_DIR/"sounds"

APP_DIR.mkdir(parents=True, exist_ok=True)
DEFAULT_SOUND_DIR.mkdir(parents=True, exist_ok=True)