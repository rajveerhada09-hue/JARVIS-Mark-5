"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : speech.py
PATH    : voice/stt/speech.py
PURPOSE : Voice pipeline - captures audio, runs VAD, transcribes via STT Manager
============================================================
"""

import logging
import subprocess
from typing import Optional
import numpy as np
import sounddevice as sd

from voice.tts.voice import is_speaking
from voice.stt.recorder import get_recorder
from voice.stt.provider_manager import get_stt_manager, STTProviderManager
from utils.config import get

_log = logging.getLogger("jarvis.speech")

print("[LISTENER] Initializing with Multi-Provider STT (Deepgram -> OpenAI -> Faster-Whisper)...")

recorder = get_recorder()
stt_manager = get_stt_manager(offline_mode=get("offline_mode", False))


# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM AUDIO CONTROL
# ═══════════════════════════════════════════════════════════════════════════

def mute_system_audio(mute: bool = True) -> None:
    """Mute or unmute system audio on Windows via NirCmd."""
    try:
        state = "1" if mute else "0"
        subprocess.run(
            ["nircmd.exe", "mutesysvolume", state],
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception as exc:
        _log.warning("[SPEECH] mute_system_audio failed (NirCmd not found?): %s", exc)


# ═══════════════════════════════════════════════════════════════════════════
# INPUT DEVICE SELECTION
# ═══════════════════════════════════════════════════════════════════════════

def get_best_input_device() -> Optional[int]:
    """Select the best available input device."""
    try:
        devices = sd.query_devices()
    except Exception as exc:
        _log.error("[SPEECH] Could not query audio devices: %s", exc)
        return None

    print("\n=== AVAILABLE AUDIO DEVICES ===")
    for i, dev in enumerate(devices):
        print(f"{i}: {dev['name']} (in:{dev['max_input_channels']})")

    for i, dev in enumerate(devices):
        name = dev["name"].lower()
        if dev["max_input_channels"] > 0 and "sound mapper" not in name:
            print(f"[LISTENER] Selected: {dev['name']} (index {i})")
            try:
                sd.default.device = (i, sd.default.device[1])
            except Exception as exc:
                _log.error("[SPEECH] Could not set default input device: %s", exc)
                return None
            return i

    _log.warning("[SPEECH] No suitable input device found.")
    return None


try:
    get_best_input_device()
except Exception as exc:
    _log.error("[SPEECH] Automatic input device selection failed: %s", exc)


# ═══════════════════════════════════════════════════════════════════════════
# JARVIS LISTENER
# ═══════════════════════════════════════════════════════════════════════════

class JarvisListener:
    """Stateful microphone listener using STT Provider Manager."""

    DEFAULT_TIMEOUT: float = 5.0
    SAMPLE_RATE: int = 16000

    def __init__(self, default_timeout: float = DEFAULT_TIMEOUT, stt_manager: Optional[STTProviderManager] = None) -> None:
        self.is_listening: bool = False
        self.default_timeout: float = default_timeout
        self._stt_manager = stt_manager or get_stt_manager()

    def listen(self, timeout: Optional[float] = None) -> str:
        if is_speaking():
            return ""

        duration = timeout if timeout is not None else self.default_timeout
        self.is_listening = True

        try:
            audio = recorder.record(max_duration=duration)

            if audio is None or len(audio) == 0:
                return ""

            text = self._stt_manager.transcribe(audio)

            if text:
                print(f"[USER] {text}")
                _log.info("[SPEECH] %s (via %s)", text, self._stt_manager.current_provider_name)

            return text.lower() if text else ""

        except Exception:
            _log.exception("[SPEECH] Listen Failed")
            return ""

        finally:
            self.is_listening = False


# ═══════════════════════════════════════════════════════════════════════════
# MODULE-LEVEL PUBLIC API
# ═══════════════════════════════════════════════════════════════════════════

_listener = JarvisListener()


def listen(timeout: Optional[float] = None) -> str:
    """
    Module-level convenience wrapper around the shared JarvisListener singleton.
    """
    return _listener.listen(timeout)


def get_stt_status() -> dict:
    """Get current STT provider status for HUD."""
    return {
        "current_provider": stt_manager.current_provider_name,
        "available_providers": stt_manager.available_providers,
        "offline_mode": stt_manager.offline_mode,
    }


def set_offline_mode(offline: bool):
    """Switch STT manager to offline mode."""
    stt_manager.set_offline_mode(offline)