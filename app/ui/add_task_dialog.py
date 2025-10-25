# ==============================
# app/ui/add_task_dialog.py
# ==============================
from __future__ import annotations
from PySide6 import QtWidgets, QtCore
from pathlib import Path
from ..models import Task, TaskType

class AddTaskDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, task: Task | None = None, sound_dir: str | None = None, existing_tasks: list[Task] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Nouvelle tâche" if task is None else "Modifier la tâche")
        self.resize(560, 380)

        self.name_edit = QtWidgets.QLineEdit()
        self.sound_combo = QtWidgets.QComboBox()
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(["à heure fixe", "après X temps (répété)", "après X temps une tâche"])  # FIXED_TIME, AFTER_DURATION, AFTER_TASK

        # Durée h/m/s
        self.dur_h = QtWidgets.QSpinBox(); self.dur_h.setRange(0, 9999)
        self.dur_m = QtWidgets.QSpinBox(); self.dur_m.setRange(0, 59)
        self.dur_s = QtWidgets.QSpinBox(); self.dur_s.setRange(0, 59)

        self.hour_spin = QtWidgets.QSpinBox(); self.hour_spin.setRange(0, 23)
        self.min_spin  = QtWidgets.QSpinBox(); self.min_spin.setRange(0, 59)
        self.enabled_check = QtWidgets.QCheckBox("Activée"); self.enabled_check.setChecked(True)

        # Options intervalle
        self.max_occ_spin = QtWidgets.QSpinBox(); self.max_occ_spin.setRange(0, 100000); self.max_occ_spin.setValue(0)
        self.start_now_check = QtWidgets.QCheckBox("Démarrer maintenant (désactivé pour 'après X temps')"); self.start_now_check.setChecked(False)
        self.start_at_hour = QtWidgets.QSpinBox(); self.start_at_hour.setRange(0,23)
        self.start_at_min  = QtWidgets.QSpinBox(); self.start_at_min.setRange(0,59)

        # Dépendance
        self.after_task_combo = QtWidgets.QComboBox(); self.after_task_combo.setEnabled(False)
        if existing_tasks:
            for t in existing_tasks:
                if task is None or t.id != getattr(task, 'id', None):
                    self.after_task_combo.addItem(f"#{t.id} — {t.name}", t.id)

        if sound_dir:
            self.refresh_sounds(sound_dir)

        form = QtWidgets.QFormLayout()
        form.addRow("Nom", self.name_edit)
        form.addRow("Son", self.sound_combo)
        form.addRow("Type", self.type_combo)

        dur_row = QtWidgets.QHBoxLayout()
        dur_row.addWidget(self.dur_h); dur_row.addWidget(QtWidgets.QLabel("h"))
        dur_row.addWidget(self.dur_m); dur_row.addWidget(QtWidgets.QLabel("m"))
        dur_row.addWidget(self.dur_s); dur_row.addWidget(QtWidgets.QLabel("s"))
        form.addRow("Durée", self._wrap(dur_row))

        fixed_time_layout = QtWidgets.QHBoxLayout()
        fixed_time_layout.addWidget(self.hour_spin); fixed_time_layout.addWidget(QtWidgets.QLabel("h")); fixed_time_layout.addWidget(self.min_spin)
        form.addRow("Heure fixe", self._wrap(fixed_time_layout))

        start_row = QtWidgets.QHBoxLayout()
        start_row.addWidget(self.start_now_check)
        start_row.addWidget(QtWidgets.QLabel("Sinon à:"))
        start_row.addWidget(self.start_at_hour); start_row.addWidget(QtWidgets.QLabel("h")); start_row.addWidget(self.start_at_min)
        form.addRow("Départ (répété)", self._wrap(start_row))

        form.addRow("Occurrences max (0 = illimité)", self.max_occ_spin)
        form.addRow("Après la tâche", self.after_task_combo)
        form.addRow("", self.enabled_check)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        root = QtWidgets.QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(btns)

        self.type_combo.currentIndexChanged.connect(self._on_type_change)
        self.start_now_check.stateChanged.connect(self._on_type_change)
        self._on_type_change(0)

        if task:
            self._load_task(task)

    def _wrap(self, layout):
        w = QtWidgets.QWidget(); w.setLayout(layout); return w

    def refresh_sounds(self, sound_dir: str):
        self.sound_combo.clear()
        p = Path(sound_dir)
        files = [str(fp) for fp in p.glob("**/*") if fp.suffix.lower() in {".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"}]
        self.sound_combo.addItems(files)

    def _on_type_change(self, *_):
        idx = self.type_combo.currentIndex()
        is_fixed = idx == 0
        is_duration = idx == 1
        is_after = idx == 2

        # champs actifs selon type
        self.hour_spin.setEnabled(is_fixed)
        self.min_spin.setEnabled(is_fixed)

        for w in (self.dur_h, self.dur_m, self.dur_s):
            w.setEnabled(is_duration or is_after)

        self.max_occ_spin.setEnabled(is_duration)
        # Pour 'après X temps' : démarrage manuel uniquement -> désactive les contrôles de départ
        self.start_now_check.setEnabled(False if is_duration else True)
        self.start_at_hour.setEnabled(False if is_duration else (not self.start_now_check.isChecked()))
        self.start_at_min.setEnabled(False if is_duration else (not self.start_now_check.isChecked()))
        self.after_task_combo.setEnabled(is_after)

    def _load_task(self, t: Task):
        self.name_edit.setText(t.name)
        idx = self.sound_combo.findText(t.sound_path)
        if idx >= 0:
            self.sound_combo.setCurrentIndex(idx)
        self.enabled_check.setChecked(t.enabled)

        if t.task_type == TaskType.FIXED_TIME:
            self.type_combo.setCurrentIndex(0)
            self.hour_spin.setValue(t.at_hour or 0)
            self.min_spin.setValue(t.at_minute or 0)
        elif t.task_type == TaskType.AFTER_DURATION:
            self.type_combo.setCurrentIndex(1)
        else:
            self.type_combo.setCurrentIndex(2)
            if t.after_task_id is not None:
                i = self.after_task_combo.findData(t.after_task_id)
                if i >= 0:
                    self.after_task_combo.setCurrentIndex(i)

        # décomposer secondes -> h/m/s
        secs = int(t.param_value or 0)
        self.dur_h.setValue(secs // 3600)
        self.dur_m.setValue((secs % 3600) // 60)
        self.dur_s.setValue(secs % 60)

        self.max_occ_spin.setValue(t.max_occurrences or 0)
        self.start_now_check.setChecked(bool(t.start_now))
        if t.start_at_hour is not None: self.start_at_hour.setValue(t.start_at_hour)
        if t.start_at_minute is not None: self.start_at_min.setValue(t.start_at_minute)
        self._on_type_change()

    def _duration_seconds(self) -> int:
        return self.dur_h.value()*3600 + self.dur_m.value()*60 + self.dur_s.value()

    def get_task(self) -> Task:
        idx = self.type_combo.currentIndex()
        if idx == 0:
            ttype = TaskType.FIXED_TIME
        elif idx == 1:
            ttype = TaskType.AFTER_DURATION
        else:
            ttype = TaskType.AFTER_TASK

        after_id = self.after_task_combo.currentData() if ttype == TaskType.AFTER_TASK else None
        duration_sec = self._duration_seconds()
        if duration_sec <= 0 and ttype != TaskType.FIXED_TIME:
            duration_sec = 1  # garde‑fou

        return Task(
            id=None,
            name=self.name_edit.text().strip() or "Tâche",
            sound_path=self.sound_combo.currentText(),
            task_type=ttype,
            param_value=duration_sec,
            at_hour=self.hour_spin.value(),
            at_minute=self.min_spin.value(),
            enabled=self.enabled_check.isChecked(),
            max_occurrences=(self.max_occ_spin.value() or None),
            start_now=(False if ttype == TaskType.AFTER_DURATION else self.start_now_check.isChecked()),
            start_at_hour=(None if ttype == TaskType.AFTER_DURATION else (self.start_at_hour.value() if not self.start_now_check.isChecked() else None)),
            start_at_minute=(None if ttype == TaskType.AFTER_DURATION else (self.start_at_min.value() if not self.start_now_check.isChecked() else None)),
            after_task_id=after_id,
        )
