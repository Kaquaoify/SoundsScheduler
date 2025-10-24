# ==============================
# app/ui/icons.py
# ==============================
from __future__ import annotations
from pathlib import Path
from PySide6.QtGui import QIcon
from ..config import APP_DIR

def get_app_icon() -> QIcon:
    """Return app icon from custom SVG/PNG or fallback to theme icon."""
    candidates = [
        APP_DIR/"icon.svg",
        APP_DIR/"icon.png",
        Path(__file__).with_name("icon.svg"),
        Path(__file__).with_name("icon.png"),
    ]
    for p in candidates:
        if p.exists():
            return QIcon(str(p))
    ic = QIcon.fromTheme("applications-multimedia")
    if not ic.isNull():
        return ic
    return QIcon()