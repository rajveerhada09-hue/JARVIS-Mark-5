"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : __init__.py
PATH    : voice/stt/__init__.py
PURPOSE : STT Module Public API
============================================================
"""

from voice.stt.speech import listen, get_stt_status, set_offline_mode
from voice.stt.provider_manager import get_stt_manager, STTProviderManager, FasterWhisperProvider
from voice.stt.provider import STTProvider, STTProviderRegistry
from voice.stt.deepgram_stt import DeepgramSTTProvider, create_deepgram_provider
from voice.stt.openai_stt import OpenAISTTProvider, create_openai_provider
from voice.stt.whisper_engine import WhisperEngine, get_engine
from voice.stt.recorder import AudioRecorder, get_recorder
from voice.stt.silero_vad import SileroVAD, get_vad

__all__ = [
    "listen",
    "get_stt_status",
    "set_offline_mode",
    "get_stt_manager",
    "STTProviderManager",
    "FasterWhisperProvider",
    "STTProvider",
    "STTProviderRegistry",
    "DeepgramSTTProvider",
    "create_deepgram_provider",
    "OpenAISTTProvider",
    "create_openai_provider",
    "WhisperEngine",
    "get_engine",
    "AudioRecorder",
    "get_recorder",
    "SileroVAD",
    "get_vad",
]