# ==============================
# app/audio_player.py
# ==============================
from __future__ import annotations
import vlc
import time
from pathlib import Path

class AudioPlayer:
    def __init__(self):
        self._instance = vlc.Instance()
        self._player = self._instance.media_player_new()

    def set_volume(self, vol: int):
        self._player.audio_set_volume(max(0, min(100, vol)))

    def play_blocking(self, file_path: str):
        media = self._instance.media_new(str(Path(file_path)))
        self._player.set_media(media)
        self._player.play()
        # Wait until it starts
        time.sleep(0.1)
        # Busy-wait until finished
        while True:
            state = self._player.get_state()
            if state in (vlc.State.Ended, vlc.State.Stopped, vlc.State.Error):
                break
            time.sleep(0.1)
