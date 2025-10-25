# ==============================
# app/spotify_control.py
# ==============================
from __future__ import annotations
import subprocess
import sys
import platform
import time
from typing import Optional

class SpotifyController:
    def __init__(self, mode: str = "linux_mpris"):
        self.mode = mode
        self._cached_volume: Optional[float] = None  # 0.0 - 1.0

    # --- low-level
    def _playerctl(self, *args) -> subprocess.CompletedProcess:
        return subprocess.run(["playerctl", "--player=spotify", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    # --- state
    def is_playing(self) -> bool:
        if self.mode == "linux_mpris" and platform.system() == "Linux":
            cp = self._playerctl("status")
            return cp.stdout.strip().lower() == "playing"
        return False

    # --- volume helpers (0.0..1.0)
    def get_volume(self) -> Optional[float]:
        if self.mode != "linux_mpris" or platform.system() != "Linux":
            return None
        cp = self._playerctl("volume")
        try:
            v = float(cp.stdout.strip())
            return max(0.0, min(1.0, v))
        except Exception:
            return None

    def set_volume(self, v: float):
        if self.mode != "linux_mpris" or platform.system() != "Linux":
            return
        v = max(0.0, min(1.0, float(v)))
        self._playerctl("volume", str(v))

    def fade_to(self, target: float, duration_ms: int = 800, steps: int = 16):
        if self.mode != "linux_mpris" or platform.system() != "Linux":
            return
        start = self.get_volume()
        if start is None:
            return
        target = max(0.0, min(1.0, float(target)))
        steps = max(1, int(steps))
        delay = max(1, int(duration_ms/steps)) / 1000.0
        for i in range(1, steps+1):
            cur = start + (target - start) * (i/steps)
            self.set_volume(cur)
            time.sleep(delay)

    # --- transport
    def pause(self):
        if self.mode == "linux_mpris" and platform.system() == "Linux":
            self._playerctl("pause")

    def play(self):
        if self.mode == "linux_mpris" and platform.system() == "Linux":
            self._playerctl("play")

    # --- high-level with fade
    def fade_out_and_pause(self, fade_ms: int = 800):
        """Fade out current Spotify volume, remember it, then pause."""
        cur = self.get_volume()
        if cur is not None:
            self._cached_volume = cur
            self.fade_to(0.0, duration_ms=fade_ms)
        self.pause()

    def play_and_fade_in(self, fade_ms: int = 800):
        """Resume playback and fade back to the previous volume (or 0.8 if unknown)."""
        self.play()
        target = self._cached_volume if self._cached_volume is not None else 0.8
        # Small delay to ensure playback resumes before fading in
        time.sleep(0.05)
        self.fade_to(target, duration_ms=fade_ms)
