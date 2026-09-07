import os
import wave
import numpy as np
from PyQt5.QtMultimedia import QSoundEffect, QMediaPlayer, QMediaContent
from PyQt5.QtCore import QUrl, QTimer
import logging

logger = logging.getLogger("Stegano")

AUDIO_SAMPLE_RATE = 44100
AUDIO_FADE_DURATION = 0.05

class AudioManager:
    def __init__(self):
        self.sfx = {}
        self.music_player = QMediaPlayer()
        self.music_enabled = True
        self.sfx_enabled = True
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self._ensure_audio_files()
        self._load_sounds()
        self.set_music("idle")
        self.music_player.mediaStatusChanged.connect(self._handle_media_status)
    def _ensure_audio_files(self):
        sfx_dir = os.path.join(self.base_dir, "audio", "sfx")
        music_dir = os.path.join(self.base_dir, "audio", "music")
        os.makedirs(sfx_dir, exist_ok=True)
        os.makedirs(music_dir, exist_ok=True)
        sfx_map = {'click.wav': (800, 0.08, 0.3), 'action.wav': (600, 0.15, 0.4), 'success.wav': (880, 0.4, 0.3), 'error.wav': (250, 0.3, 0.4)}
        music_map = {'idle.wav': (110, 12.0, 0.15)}
        try:
            for name, (freq, dur, vol) in {**sfx_map, **music_map}.items():
                folder = sfx_dir if name in sfx_map else music_dir
                path = os.path.join(folder, name)
                if not os.path.exists(path):
                    self._create_audio(path, freq, dur, vol, is_music=(name in music_map))
        except Exception as e:
            logger.warning(f"Could not generate default audio files: {e}")
    def _create_audio(self, filepath, base_freq, duration, volume, sr=AUDIO_SAMPLE_RATE, is_music=False):
        t = np.linspace(0, duration, int(sr * duration), False)
        audio = np.zeros_like(t)
        if is_music:
            for f in [base_freq, base_freq*1.25, base_freq*1.5, base_freq*2.0]:
                audio += np.sin(2 * np.pi * f * t) * 0.15
            lfo = 0.5 + 0.5 * np.sin(2 * np.pi * 0.1 * t)
            audio *= lfo
        else:
            audio = np.sin(2 * np.pi * base_freq * t) * 0.5 * np.exp(-t * 15)
        env = np.ones_like(t)
        fade = int(sr * AUDIO_FADE_DURATION)
        if fade < len(env):
            env[:fade] = np.linspace(0, 1, fade)
            env[-fade:] = np.linspace(1, 0, fade)
        audio *= env * volume
        data = (audio * 32767).astype(np.int16).tobytes()
        with wave.open(filepath, 'wb') as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sr)
            w.writeframes(data)
    def _load_sounds(self):
        sfx_dir = os.path.join(self.base_dir, "audio", "sfx")
        if not os.path.exists(sfx_dir): return
        for name in ["click", "action", "success", "error"]:
            path = os.path.join(sfx_dir, f"{name}.wav")
            if os.path.exists(path):
                eff = QSoundEffect()
                eff.setSource(QUrl.fromLocalFile(path))
                eff.setVolume(0.7)
                self.sfx[name] = eff
    def play_sfx(self, name):
        if self.sfx_enabled and name in self.sfx:
            try: self.sfx[name].play()
            except Exception as e: logger.debug(f"Could not play sound effect '{name}': {e}")
    def set_music(self, mode):
        if not self.music_enabled: return
        music_dir = os.path.join(self.base_dir, "audio", "music")
        for ext in [".mp3", ".wav"]:
            path = os.path.join(music_dir, f"{mode}{ext}")
            if os.path.exists(path):
                self.music_player.stop()
                self.music_player.setMedia(QMediaContent(QUrl.fromLocalFile(path)))
                self.music_player.setVolume(60)
                self.music_player.play()
                return
    def _handle_media_status(self, state):
        if state == QMediaPlayer.EndOfMedia and self.music_enabled:
            self.music_player.setPosition(0)
            self.music_player.play()
    def set_music_volume(self, vol):
        self.music_player.setVolume(max(0, min(100, vol)))
    def toggle_music(self):
        self.music_enabled = not self.music_enabled
        if not self.music_enabled:
            self.music_player.stop()
        else:
            self.set_music("idle")
        return self.music_enabled
    def toggle_sfx(self):
        self.sfx_enabled = not self.sfx_enabled
        return self.sfx_enabled
