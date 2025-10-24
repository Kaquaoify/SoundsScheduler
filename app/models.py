from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class TaskType(Enum):
    FIXED_TIME = "fixed_time"          # ex: 14:30 chaque jour
    EVERY_X_MINUTES = "every_x_minutes"
    EVERY_X_HOURS   = "every_x_hours"
    AFTER_TASK      = "after_task"     # N minutes après une autre tâche

@dataclass
class Settings:
    sound_dir: str
    output_volume: int                 # 0..100
    spotify_control_mode: str          # toujours "linux_mpris"

@dataclass
class Task:
    id: Optional[int]
    name: str
    sound_path: str
    task_type: TaskType
    param_value: int                   # minutes/heures; pour AFTER_TASK: décalage en minutes
    at_hour: Optional[int] = None      # pour FIXED_TIME
    at_minute: Optional[int] = None
    enabled: bool = True

    # Options intervalle
    max_occurrences: Optional[int] = None   # None ou 0 => illimité
    start_now: bool = True
    start_at_hour: Optional[int] = None     # si start_now = False
    start_at_minute: Optional[int] = None

    # Dépendance
    after_task_id: Optional[int] = None

    # Runtime
    run_count: int = 0
