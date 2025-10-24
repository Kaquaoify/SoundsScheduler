# ==============================
# app/storage.py
# ==============================
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List, Optional
from .config import DB_PATH
from .models import Settings, Task, TaskType

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    sound_dir TEXT NOT NULL,
    output_volume INTEGER NOT NULL,
    spotify_control_mode TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    sound_path TEXT NOT NULL,
    task_type TEXT NOT NULL,
    param_value INTEGER NOT NULL,
    at_hour INTEGER,
    at_minute INTEGER,
    enabled INTEGER NOT NULL DEFAULT 1
);
"""

class Storage:
    def __init__(self, path: Path = DB_PATH):
        self.path = path
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        with self.conn:
            self.conn.executescript(SCHEMA)
            cur = self.conn.execute("SELECT 1 FROM settings WHERE id=1")
            if not cur.fetchone():
                self.conn.execute(
                    "INSERT INTO settings (id, sound_dir, output_volume, spotify_control_mode) VALUES (1, ?, ?, ?)",
                    (str(Path.home()/"Music"), 80, "linux_mpris"),
                )

    def load_settings(self) -> Settings:
        row = self.conn.execute("SELECT * FROM settings WHERE id=1").fetchone()
        return Settings(sound_dir=row["sound_dir"], output_volume=row["output_volume"], spotify_control_mode=row["spotify_control_mode"]) 

    def save_settings(self, s: Settings):
        with self.conn:
            self.conn.execute(
                "UPDATE settings SET sound_dir=?, output_volume=?, spotify_control_mode=? WHERE id=1",
                (s.sound_dir, s.output_volume, s.spotify_control_mode),
            )

    def list_tasks(self) -> List[Task]:
        rows = self.conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
        return [Task(id=r["id"], name=r["name"], sound_path=r["sound_path"], task_type=TaskType(r["task_type"]), param_value=r["param_value"], at_hour=r["at_hour"], at_minute=r["at_minute"], enabled=bool(r["enabled"])) for r in rows]

    def add_task(self, t: Task) -> int:
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO tasks (name, sound_path, task_type, param_value, at_hour, at_minute, enabled) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (t.name, t.sound_path, t.task_type.value, t.param_value, t.at_hour, t.at_minute, int(t.enabled)),
            )
            return cur.lastrowid

    def update_task(self, t: Task):
        assert t.id is not None
        with self.conn:
            self.conn.execute(
                "UPDATE tasks SET name=?, sound_path=?, task_type=?, param_value=?, at_hour=?, at_minute=?, enabled=? WHERE id=?",
                (t.name, t.sound_path, t.task_type.value, t.param_value, t.at_hour, t.at_minute, int(t.enabled), t.id),
            )

    def delete_task(self, task_id: int):
        with self.conn:
            self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
