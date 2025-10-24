# ==============================
# app/spotify_control.py
# ==============================
from __future__ import annotations
import subprocess
import sys
import platform
from typing import Optional

class SpotifyController:
    def __init__(self, mode: str = "linux_mpris"):
        self.mode = mode

    def _playerctl(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(["playerctl", "--player=spotify", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def is_playing(self) -> bool:
        if self.mode == "linux_mpris" and platform.system() == "Linux":
            cp = self._playerctl("status")
            return cp.stdout.strip().lower() == "playing"
        return False

    def pause(self):
        if self.mode == "linux_mpris" and platform.system() == "Linux":
            self._playerctl("pause")
        # else: could add Web API fallback with Spotipy

    def play(self):
        if self.mode == "linux_mpris" and platform.system() == "Linux":
            self._playerctl("play")