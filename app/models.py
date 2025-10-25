# ==============================
# app/models.py
# ==============================
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class TaskType(Enum):
    FIXED_TIME     = "fixed_time"       # ex: 14:30 chaque jour
    AFTER_DURATION = "after_duration"   # répéter après X temps (secondes)
    AFTER_TASK     = "after_task"       # X temps après la fin d’une autre tâche

@dataclass
class Settings:
    sound_dir: str
    output_volume: int                  # 0..100
    spotify_control_mode: str           # toujours "linux_mpris"

@dataclass
class Task:
    id: Optional[int]
    name: str
    sound_path: str
    task_type: TaskType
    # "param_value" stocke désormais une DURÉE EN SECONDES (pour AFTER_DURATION et AFTER_TASK)
    param_value: int                    # secondes
    at_hour: Optional[int] = None       # pour FIXED_TIME
    at_minute: Optional[int] = None
    enabled: bool = True

    # Options pour AFTER_DURATION
    max_occurrences: Optional[int] = None   # None ou 0 => illimité
    start_now: bool = True                  # si False, démarrer à l’heure définie ci‑dessous
    start_at_hour: Optional[int] = None
    start_at_minute: Optional[int] = None

    # Dépendance
    after_task_id: Optional[int] = None

    # Runtime
    run_count: int = 0