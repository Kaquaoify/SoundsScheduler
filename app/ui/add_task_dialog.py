# ==============================
# app/ui/add_task_dialog.py
# ==============================
from __future__ import annotations
from PySide6 import QtWidgets, QtCore
from pathlib import Path
from ..models import Task, TaskType

class AddTaskDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, task: Task | None = None, sound_dir: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Nouvelle tâche" if task is None else "Modifier la tâche")
        self.resize(480, 260)

        self.name_edit = QtWidgets.QLineEdit()
        self.sound_combo = QtWidgets.QComboBox()
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.addItems(["à heure fixe", "toutes les X minutes", "toutes les X heures"])
        self.value_spin = QtWidgets.QSpinBox(); self.value_spin.setRange(1, 10080)
        self.hour_spin = QtWidgets.QSpinBox(); self.hour_spin.setRange(0, 23)
        self.min_spin = QtWidgets.QSpinBox(); self.min_spin.setRange(0, 59)
        self.enabled_check = QtWidgets.QCheckBox("Activée"); self.enabled_check.setChecked(True)

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
        form.addRow("", self.enabled_check)

        btns = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)

        root = QtWidgets.QVBoxLayout(self)
        root.addLayout(form)
        root.addWidget(btns)

        self.type_combo.currentIndexChanged.connect(self._on_type_change)
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

    def _on_type_change(self, idx: int):
        is_fixed = idx == 0
        self.hour_spin.setEnabled(is_fixed)
        self.min_spin.setEnabled(is_fixed)
        self.value_spin.setEnabled(not is_fixed)

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
        else:
            self.type_combo.setCurrentIndex(2)
            self.value_spin.setValue(t.param_value)

    def get_task(self) -> Task:
        idx = self.type_combo.currentIndex()
        if idx == 0:
            ttype = TaskType.FIXED_TIME
        elif idx == 1:
            ttype = TaskType.EVERY_X_MINUTES
        else:
            ttype = TaskType.EVERY_X_HOURS
        return Task(
            id=None,
            name=self.name_edit.text().strip() or "Tâche",
            sound_path=self.sound_combo.currentText(),
            task_type=ttype,
            param_value=self.value_spin.value(),
            at_hour=self.hour_spin.value(),
            at_minute=self.min_spin.value(),
            enabled=self.enabled_check.isChecked(),
        )