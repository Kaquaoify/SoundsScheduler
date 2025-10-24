from __future__ import annotations
from PySide6 import QtWidgets, QtCore
from pathlib import Path
from ..models import Task, TaskType

class AddTaskDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, task: Task | None = None, sound_dir: str | None = None, existing_tasks: list[Task] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Nouvelle tâche" if task is None else "Modifier la tâche")
        self.resize(520, 360)

        self.name_edit = QtWidgets.QLineEdit()
        self.sound_combo = QtWidgets.QComboBox()
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(["à heure fixe", "toutes les X minutes", "toutes les X heures", "X minutes après une tâche"])

        self.value_spin = QtWidgets.QSpinBox(); self.value_spin.setRange(1, 10080)
        self.hour_spin = QtWidgets.QSpinBox(); self.hour_spin.setRange(0, 23)
        self.min_spin = QtWidgets.QSpinBox(); self.min_spin.setRange(0, 59)
        self.enabled_check = QtWidgets.QCheckBox("Activée"); self.enabled_check.setChecked(True)

        # Interval options
        self.max_occ_spin = QtWidgets.QSpinBox(); self.max_occ_spin.setRange(0, 100000); self.max_occ_spin.setValue(0)
        self.start_now_check = QtWidgets.QCheckBox("Démarrer maintenant"); self.start_now_check.setChecked(True)
        self.start_at_hour = QtWidgets.QSpinBox(); self.start_at_hour.setRange(0,23)
        self.start_at_min = QtWidgets.QSpinBox(); self.start_at_min.setRange(0,59)

        # Dependency
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
        form.addRow("Valeur (min/heure)", self.value_spin)

        fixed_time_layout = QtWidgets.QHBoxLayout()
        fixed_time_layout.addWidget(self.hour_spin); fixed_time_layout.addWidget(QtWidgets.QLabel("h")); fixed_time_layout.addWidget(self.min_spin)
        form.addRow("Heure fixe", self._wrap(fixed_time_layout))

        start_row = QtWidgets.QHBoxLayout()
        start_row.addWidget(self.start_now_check)
        start_row.addWidget(QtWidgets.QLabel("Sinon à:"))
        start_row.addWidget(self.start_at_hour); start_row.addWidget(QtWidgets.QLabel("h")); start_row.addWidget(self.start_at_min)
        form.addRow("Départ intervalle", self._wrap(start_row))

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
        is_interval = idx in (1, 2)
        is_after = idx == 3

        self.hour_spin.setEnabled(is_fixed)
        self.min_spin.setEnabled(is_fixed)

        self.value_spin.setEnabled(not is_fixed)
        self.max_occ_spin.setEnabled(is_interval)
        self.start_now_check.setEnabled(is_interval)
        self.start_at_hour.setEnabled(is_interval and not self.start_now_check.isChecked())
        self.start_at_min.setEnabled(is_interval and not self.start_now_check.isChecked())
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
        elif t.task_type == TaskType.EVERY_X_MINUTES:
            self.type_combo.setCurrentIndex(1)
            self.value_spin.setValue(t.param_value)
        elif t.task_type == TaskType.EVERY_X_HOURS:
            self.type_combo.setCurrentIndex(2)
            self.value_spin.setValue(t.param_value)
        else:
            self.type_combo.setCurrentIndex(3)
            self.value_spin.setValue(t.param_value)
            if t.after_task_id is not None:
                i = self.after_task_combo.findData(t.after_task_id)
                if i >= 0:
                    self.after_task_combo.setCurrentIndex(i)

        self.max_occ_spin.setValue(t.max_occurrences or 0)
        self.start_now_check.setChecked(bool(t.start_now))
        if t.start_at_hour is not None: self.start_at_hour.setValue(t.start_at_hour)
        if t.start_at_minute is not None: self.start_at_min.setValue(t.start_at_minute)
        self._on_type_change()

    def get_task(self) -> Task:
        idx = self.type_combo.currentIndex()
        if idx == 0:
            ttype = TaskType.FIXED_TIME
        elif idx == 1:
            ttype = TaskType.EVERY_X_MINUTES
        elif idx == 2:
            ttype = TaskType.EVERY_X_HOURS
        else:
            ttype = TaskType.AFTER_TASK

        after_id = self.after_task_combo.currentData() if ttype == TaskType.AFTER_TASK else None

        return Task(
            id=None,
            name=self.name_edit.text().strip() or "Tâche",
            sound_path=self.sound_combo.currentText(),
            task_type=ttype,
            param_value=self.value_spin.value(),
            at_hour=self.hour_spin.value(),
            at_minute=self.min_spin.value(),
            enabled=self.enabled_check.isChecked(),
            max_occurrences=(self.max_occ_spin.value() or None),
            start_now=self.start_now_check.isChecked(),
            start_at_hour=self.start_at_hour.value() if not self.start_now_check.isChecked() else None,
            start_at_minute=self.start_at_min.value() if not self.start_now_check.isChecked() else None,
            after_task_id=after_id,
        )
