# ==============================
# app/storage.py
# ==============================
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import List
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
    enabled INTEGER NOT NULL DEFAULT 1,
    max_occurrences INTEGER,
    start_now INTEGER DEFAULT 1,
    start_at_hour INTEGER,
    start_at_minute INTEGER,
    after_task_id INTEGER,
    run_count INTEGER DEFAULT 0
);
"""

class Storage:
    def __init__(self, path: Path = DB_PATH):
        self.path = path
        # Autoriser l'accès depuis le thread APScheduler
        self.conn = sqlite3.connect(self.path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        with self.conn:
            # Appliquer le schéma
            self.conn.executescript(SCHEMA)

            # Migrations si ancienne base
            cols = {r[1] for r in self.conn.execute("PRAGMA table_info(tasks)")}
            if "max_occurrences" not in cols:
                self.conn.execute("ALTER TABLE tasks ADD COLUMN max_occurrences INTEGER")
            if "start_now" not in cols:
                self.conn.execute("ALTER TABLE tasks ADD COLUMN start_now INTEGER DEFAULT 1")
            if "start_at_hour" not in cols:
                self.conn.execute("ALTER TABLE tasks ADD COLUMN start_at_hour INTEGER")
            if "start_at_minute" not in cols:
                self.conn.execute("ALTER TABLE tasks ADD COLUMN start_at_minute INTEGER")
            if "after_task_id" not in cols:
                self.conn.execute("ALTER TABLE tasks ADD COLUMN after_task_id INTEGER")
            if "run_count" not in cols:
                self.conn.execute("ALTER TABLE tasks ADD COLUMN run_count INTEGER DEFAULT 0")

            # Migration de compat: anciens types -> nouveaux (user_version < 2)
            (uv,) = self.conn.execute("PRAGMA user_version").fetchone()
            if (uv or 0) < 2:
                # every_x_minutes -> after_duration (minutes -> secondes)
                self.conn.execute(
                    "UPDATE tasks SET param_value = param_value * 60, task_type = 'after_duration' "
                    "WHERE task_type = 'every_x_minutes'"
                )
                # every_x_hours -> after_duration (heures -> secondes)
                self.conn.execute(
                    "UPDATE tasks SET param_value = param_value * 3600, task_type = 'after_duration' "
                    "WHERE task_type = 'every_x_hours'"
                )
                # after_task (legacy minutes) -> secondes
                self.conn.execute(
                    "UPDATE tasks SET param_value = param_value * 60 WHERE task_type = 'after_task'"
                )
                self.conn.execute("PRAGMA user_version = 2")

            # Seed settings si absent
            cur = self.conn.execute("SELECT 1 FROM settings WHERE id=1")
            if not cur.fetchone():
                self.conn.execute(
                    "INSERT INTO settings (id, sound_dir, output_volume, spotify_control_mode) VALUES (1, ?, ?, ?)",
                    (str(Path.home() / "Music"), 80, "linux_mpris"),
                )

    # -- settings
    def load_settings(self) -> Settings:
        row = self.conn.execute("SELECT * FROM settings WHERE id=1").fetchone()
        return Settings(
            sound_dir=row["sound_dir"],
            output_volume=row["output_volume"],
            spotify_control_mode=row["spotify_control_mode"],
        )

    def save_settings(self, s: Settings):
        with self.conn:
            self.conn.execute(
                "UPDATE settings SET sound_dir=?, output_volume=?, spotify_control_mode=? WHERE id=1",
                (s.sound_dir, s.output_volume, s.spotify_control_mode),
            )

    # -- tasks
    def list_tasks(self) -> List[Task]:
        rows = self.conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
        out: List[Task] = []
        for r in rows:
            raw_type = r["task_type"]
            # tolérance si des anciens types traînent
            if raw_type in ("every_x_minutes", "every_x_hours"):
                raw_type = "after_duration"
            out.append(Task(
                id=r["id"], name=r["name"], sound_path=r["sound_path"],
                task_type=TaskType(raw_type), param_value=r["param_value"],
                at_hour=r["at_hour"], at_minute=r["at_minute"], enabled=bool(r["enabled"]),
                max_occurrences=r["max_occurrences"],
                start_now=bool(r["start_now"]) if r["start_now"] is not None else True,
                start_at_hour=r["start_at_hour"], start_at_minute=r["start_at_minute"],
                after_task_id=r["after_task_id"], run_count=r["run_count"] or 0,
            ))
        return out

    def add_task(self, t: Task) -> int:
        with self.conn:
            cur = self.conn.execute(
                """
                INSERT INTO tasks
                (name, sound_path, task_type, param_value, at_hour, at_minute, enabled,
                 max_occurrences, start_now, start_at_hour, start_at_minute, after_task_id, run_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (t.name, t.sound_path, t.task_type.value, t.param_value, t.at_hour, t.at_minute, int(t.enabled),
                 t.max_occurrences, int(t.start_now), t.start_at_hour, t.start_at_minute, t.after_task_id, t.run_count),
            )
            return cur.lastrowid

    def update_task(self, t: Task):
        assert t.id is not None
        with self.conn:
            self.conn.execute(
                """
                UPDATE tasks SET
                    name=?, sound_path=?, task_type=?, param_value=?, at_hour=?, at_minute=?, enabled=?,
                    max_occurrences=?, start_now=?, start_at_hour=?, start_at_minute=?, after_task_id=?, run_count=?
                WHERE id=?
                """,
                (t.name, t.sound_path, t.task_type.value, t.param_value, t.at_hour, t.at_minute, int(t.enabled),
                 t.max_occurrences, int(t.start_now), t.start_at_hour, t.start_at_minute, t.after_task_id, t.run_count, t.id),
            )

    def delete_task(self, task_id: int):
        with self.conn:
            self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))

    # Helpers occurrences
    def increment_run_count(self, task_id: int) -> int:
        with self.conn:
            self.conn.execute("UPDATE tasks SET run_count = COALESCE(run_count,0) + 1 WHERE id=?", (task_id,))
            (val,) = self.conn.execute("SELECT run_count FROM tasks WHERE id=?", (task_id,)).fetchone()
            return val

    def set_enabled(self, task_id: int, enabled: bool):
        with self.conn:
            self.conn.execute("UPDATE tasks SET enabled=? WHERE id=?", (1 if enabled else 0, task_id))