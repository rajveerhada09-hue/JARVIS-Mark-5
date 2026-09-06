"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : __init__.py
PATH    : voice/__init__.py
PURPOSE : Voice Module Public API
============================================================
"""

from voice.stt import listen, get_stt_status, set_offline_mode, get_stt_manager
from voice.tts.voice import speak, stop_speaking, is_speaking, resume_speech, has_pending_resume, clear_resume_buffer
from voice.wakeword.wakeword import wait_for_wakeword

__all__ = [
    "listen",
    "get_stt_status",
    "set_offline_mode",
    "get_stt_manager",
    "speak",
    "stop_speaking",
    "is_speaking",
    "resume_speech",
    "has_pending_resume",
    "clear_resume_buffer",
    "wait_for_wakeword",
]