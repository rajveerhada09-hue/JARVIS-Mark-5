"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : speech.py
PATH    : voice/speech.py

PURPOSE :
Captures microphone input and converts it to text using a fully local
pipeline: sounddevice (recording) -> soundfile (temp WAV) ->
Faster-Whisper (GPU transcription). No cloud STT, no speech_recognition
dependency anywhere in this file.

PUBLIC API (names/behavior preserved from the previous implementation):
    listen(timeout: Optional[float] = None) -> str
    JarvisListener.listen(self, timeout: Optional[float] = None) -> str
    mute_system_audio(mute: bool = True) -> None
    get_best_input_device() -> Optional[int]

EXTENSION POINT FOR SILERO VAD (see JarvisListener docstring):
    Replace _record_audio()'s fixed-duration sd.rec()/sd.wait() call with
    a streaming sd.InputStream + VAD-driven start/stop detection.
    Everything downstream (temp WAV write, Faster-Whisper transcription,
    cleanup) is unchanged by that swap.

LAST UPDATED : 2026-07-11
============================================================
"""

import logging
import subprocess
from typing import Optional

import sounddevice as sd

from voice.tts.voice import is_speaking
from voice.stt.whisper_engine import get_engine
from voice.stt.recorder import get_recorder
_log = logging.getLogger("jarvis.speech")

print("[LISTENER] Initializing with Auto-Mute + Faster-Whisper (local, GPU)...")

engine = get_engine()
recorder = get_recorder()
engine.warmup() 

# ═══════════════════════════════════════════════════════════════════════════
# SYSTEM AUDIO CONTROL — preserved from the original implementation
# ═══════════════════════════════════════════════════════════════════════════

def mute_system_audio(mute: bool = True) -> None:
    """
    Mute or unmute system audio on Windows via NirCmd.

    Logic identical to the original implementation. Only change: the
    bare `except: pass` (which silently swallows everything, including
    KeyboardInterrupt/SystemExit) is replaced with a scoped exception
    catch and a log call, so a missing NirCmd install is visible in logs
    instead of silently invisible.

    Args:
        mute: True to mute, False to unmute.
    """
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
# INPUT DEVICE SELECTION — preserved from the original implementation
# ═══════════════════════════════════════════════════════════════════════════

def get_best_input_device() -> Optional[int]:
    """
    Enumerate audio input devices, print them, and select the first real
    (non "Sound Mapper") device with at least one input channel as the
    default recording device.

    Logic identical to the original implementation, with exception
    handling added around device enumeration (which can fail if no audio
    subsystem is available) so a failure here doesn't crash import.

    Returns:
        The selected device index, or None if no suitable device was found.
    """
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


# Auto-select the best microphone at import time, exactly as the
# original did. Wrapped so a failure here is logged rather than raised —
# it's a convenience default, not a hard dependency (sd.rec() below will
# still work against whatever the system's own default device is).
try:
    get_best_input_device()
except Exception as exc:
    _log.error("[SPEECH] Automatic input device selection failed: %s", exc)



# ═══════════════════════════════════════════════════════════════════════════
# JARVIS LISTENER
# ═══════════════════════════════════════════════════════════════════════════

class JarvisListener:
    """
    Stateful microphone listener wrapping the record -> transcribe ->
    cleanup pipeline. A module-level singleton backs the public listen()
    function; this class can also be instantiated directly by callers
    that want independent state or a different default timeout.

    SILERO VAD EXTENSION POINT:
    _record_audio() currently uses a fixed-duration sd.rec()/sd.wait()
    call — it records for exactly `timeout` seconds regardless of when
    the user actually stops speaking. To add Silero VAD later, replace
    _record_audio()'s body with a streaming sd.InputStream whose
    callback feeds audio chunks into the VAD model, and stop the stream
    once VAD detects a trailing silence. _transcribe() and listen()'s
    surrounding structure (temp file handling, logging, is_speaking()
    guard) do not need to change for that swap.
    """

    DEFAULT_TIMEOUT: float = 5.0
    SAMPLE_RATE: int = 16000

    def __init__(self, default_timeout: float = DEFAULT_TIMEOUT) -> None:
        self.is_listening: bool = False
        self.default_timeout: float = default_timeout

    def listen(self, timeout: Optional[float] = None) -> str:

        if is_speaking():
            return ""

        duration = timeout if timeout is not None else self.default_timeout
        self.is_listening = True

        try:

            audio = recorder.record(
    max_duration=duration
)

            text = engine.transcribe(audio)

            if text:
                print(f"[USER] {text}")
                _log.info("[SPEECH] %s", text)

            return text.lower()

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
    Module-level convenience wrapper around the shared JarvisListener
    singleton. This is the function main.py imports as
    `from voice.speech import listen`.

    Args:
        timeout: Recording duration in seconds. Uses the listener's
                 default (5.0s) if not given.

    Returns:
        Lowercase transcribed text, or "" if nothing was captured.
    """
    return _listener.listen(timeout)