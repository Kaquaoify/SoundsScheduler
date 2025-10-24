# ==============================
# app/models.py
# ==============================
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any

class TaskType(Enum):
    FIXED_TIME = "fixed_time"        # e.g., 14:30 every day
    EVERY_X_MINUTES = "every_x_minutes"
    EVERY_X_HOURS = "every_x_hours"

@dataclass
class Settings:
    sound_dir: str
    output_volume: int  # 0..100
    spotify_control_mode: str  # "linux_mpris" | "web_api"

@dataclass
class Task:
    id: Optional[int]
    name: str
    sound_path: str
    task_type: TaskType
    param_value: int  # minutes or hours depending on type; unused for FIXED_TIME
    at_hour: Optional[int] = None
    at_minute: Optional[int] = None
    enabled: bool = True