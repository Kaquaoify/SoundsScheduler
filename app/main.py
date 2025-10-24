# ==============================
# app/main.py
# ==============================
from __future__ import annotations
import sys
import threading
from pathlib import Path
from PySide6 import QtWidgets, QtCore
from .storage import Storage
from .models import TaskType, Task, Settings
from .scheduler import TaskScheduler
from .spotify_control import SpotifyController
from .audio_player import AudioPlayer
from .ui.add_task_dialog import AddTaskDialog
from .ui.icons import get_app_icon

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SoundsScheduler")
        self.setWindowIcon(get_app_icon())
        self.resize(880, 540)

        self.storage = Storage()
        self.scheduler = TaskScheduler()
        self.player = AudioPlayer()
        self.settings = self.storage.load_settings()
        self.spotify = SpotifyController(mode=self.settings.spotify_control_mode)

        self._init_ui()
        self._load_settings_to_ui()
        self._reload_tasks()

    def _init_ui(self):
        tabs = QtWidgets.QTabWidget()
        self.setCentralWidget(tabs)

        # Settings tab
        settings_tab = QtWidgets.QWidget(); tabs.addTab(settings_tab, "Réglages")
        s_layout = QtWidgets.QFormLayout(settings_tab)
        self.sound_dir_edit = QtWidgets.QLineEdit()
        btn_browse = QtWidgets.QPushButton("Parcourir…"); btn_browse.clicked.connect(self._choose_sound_dir)
        row = QtWidgets.QHBoxLayout(); row.addWidget(self.sound_dir_edit); row.addWidget(btn_browse)
        s_layout.addRow("Dossier des sons", self._wrap(row))

        self.volume_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal); self.volume_slider.setRange(0,100)
        s_layout.addRow("Volume de sortie", self.volume_slider)

        
        btn_save = QtWidgets.QPushButton("Enregistrer les réglages")
        btn_save.clicked.connect(self._save_settings)
        s_layout.addRow("", btn_save)

        # Spotify controls
        sp_controls = QtWidgets.QHBoxLayout()
        btn_sp_play = QtWidgets.QPushButton("▶️ Play Spotify")
        btn_sp_pause = QtWidgets.QPushButton("⏸ Pause Spotify")
        btn_sp_play.clicked.connect(lambda: self.spotify.play())
        btn_sp_pause.clicked.connect(lambda: self.spotify.pause())
        sp_controls.addWidget(btn_sp_play)
        sp_controls.addWidget(btn_sp_pause)
        s_layout.addRow("Spotify", self._wrap(sp_controls))

        # Manual play sound
        manual_layout = QtWidgets.QHBoxLayout()
        self.manual_sound_combo = QtWidgets.QComboBox(); self._refresh_manual_sounds()
        btn_manual_play = QtWidgets.QPushButton("Lancer le son maintenant")
        btn_manual_play.clicked.connect(self._play_manual_sound)
        manual_layout.addWidget(self.manual_sound_combo)
        manual_layout.addWidget(btn_manual_play)
        s_layout.addRow("Test / Manuel", self._wrap(manual_layout))

        # Tasks tab
        tasks_tab = QtWidgets.QWidget(); tabs.addTab(tasks_tab, "Tâches")
        v = QtWidgets.QVBoxLayout(tasks_tab)
        self.table = QtWidgets.QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(["ID","Nom","Son","Type","Param","Heure","Actif"])
        self.table.horizontalHeader().setStretchLastSection(True)
        v.addWidget(self.table)

        actions = QtWidgets.QHBoxLayout()
        btn_add = QtWidgets.QPushButton("+"); btn_add.clicked.connect(self._add_task)
        btn_edit = QtWidgets.QPushButton("Modifier"); btn_edit.clicked.connect(self._edit_selected)
        btn_del = QtWidgets.QPushButton("Supprimer"); btn_del.clicked.connect(self._delete_selected)
        actions.addWidget(btn_add); actions.addWidget(btn_edit); actions.addWidget(btn_del); actions.addStretch(1)
        v.addLayout(actions)

    def _wrap(self, layout):
        w = QtWidgets.QWidget(); w.setLayout(layout); return w

    def _choose_sound_dir(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Choisir le dossier des sons", self.sound_dir_edit.text() or str(Path.home()/"Music"))
        if d:
            self.sound_dir_edit.setText(d)
            self._refresh_manual_sounds()

    def _refresh_manual_sounds(self):
        from pathlib import Path
        p = Path(self.sound_dir_edit.text() or str(Path.home()/"Music"))
        files = [str(fp) for fp in p.glob("**/*") if fp.suffix.lower() in {".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"}]
        self.manual_sound_combo.clear(); self.manual_sound_combo.addItems(files)

    def _save_settings(self):
        self.settings.sound_dir = self.sound_dir_edit.text().strip() or self.settings.sound_dir
        self.settings.output_volume = self.volume_slider.value()
        self.settings.spotify_control_mode = "linux_mpris"
        self.storage.save_settings(self.settings)
        self.player.set_volume(self.settings.output_volume)
        self.spotify = SpotifyController(mode=self.settings.spotify_control_mode)
        QtWidgets.QMessageBox.information(self, "Réglages", "Enregistrés.")

    def _load_settings_to_ui(self):
        self.sound_dir_edit.setText(self.settings.sound_dir)
        self.volume_slider.setValue(self.settings.output_volume)
        self.player.set_volume(self.settings.output_volume)

    # --- Task CRUD + Scheduling
    def _add_task(self):
        dlg = AddTaskDialog(self, sound_dir=self.settings.sound_dir)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            t = dlg.get_task()
            t.name = t.name or Path(t.sound_path).stem
            new_id = self.storage.add_task(t)
            self._reload_tasks()

    def _edit_selected(self):
        row = self.table.currentRow()
        if row < 0: return
        task_id = int(self.table.item(row, 0).text())
        tasks = {t.id: t for t in self.storage.list_tasks()}
        t = tasks.get(task_id)
        if not t: return
        dlg = AddTaskDialog(self, task=t, sound_dir=self.settings.sound_dir)
        if dlg.exec() == QtWidgets.QDialog.Accepted:
            new_t = dlg.get_task(); new_t.id = t.id
            self.storage.update_task(new_t)
            self._reload_tasks()

    def _delete_selected(self):
        row = self.table.currentRow()
        if row < 0: return
        task_id = int(self.table.item(row, 0).text())
        self.storage.delete_task(task_id)
        self.scheduler.remove(task_id)
        self._reload_tasks()

    def _reload_tasks(self):
        tasks = self.storage.list_tasks()
        self.table.setRowCount(0)
        self.scheduler.clear()
        for t in tasks:
            self._append_task_row(t)
            if t.enabled:
                self._schedule_task(t)

    def _append_task_row(self, t):
        row = self.table.rowCount(); self.table.insertRow(row)
        def setc(c, text):
            item = QtWidgets.QTableWidgetItem(text); self.table.setItem(row, c, item)
        setc(0, str(t.id))
        setc(1, t.name)
        setc(2, t.sound_path)
        setc(3, t.task_type.value)
        setc(4, str(t.param_value))
        setc(5, f"{t.at_hour:02d}:{t.at_minute:02d}" if t.at_hour is not None else "-")
        setc(6, "✔" if t.enabled else "✖")

    def _schedule_task(self, t: Task):
        def job():
            was_playing = self.spotify.is_playing()
            try:
                if was_playing:
                    self.spotify.pause()
                self.player.set_volume(self.settings.output_volume)
                self.player.play_blocking(t.sound_path)
            finally:
                if was_playing:
                    self.spotify.play()
        if t.task_type == TaskType.FIXED_TIME:
            self.scheduler.schedule_daily_fixed(t.id, t.at_hour or 0, t.at_minute or 0, job)
        elif t.task_type == TaskType.EVERY_X_MINUTES:
            self.scheduler.schedule_every_minutes(t.id, t.param_value, job)
        else:
            self.scheduler.schedule_every_hours(t.id, t.param_value, job)

    def _play_manual_sound(self):
        path = self.manual_sound_combo.currentText()
        if not path:
            QtWidgets.QMessageBox.warning(self, "Son", "Aucun fichier sélectionné.")
            return
        def run():
            was_playing = self.spotify.is_playing()
            try:
                if was_playing:
                    self.spotify.pause()
                self.player.set_volume(self.settings.output_volume)
                self.player.play_blocking(path)
            finally:
                if was_playing:
                    self.spotify.play()
        threading.Thread(target=run, daemon=True).start()


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow(); w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()