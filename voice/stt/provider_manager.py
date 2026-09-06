"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : provider_manager.py
PATH    : voice/stt/provider_manager.py
PURPOSE : STT Provider Manager with Fallback Logic
============================================================
"""

import logging
from typing import Optional, List
import numpy as np

from voice.stt.provider import STTProvider, STTProviderRegistry
from voice.stt.deepgram_stt import DeepgramSTTProvider, create_deepgram_provider
from voice.stt.openai_stt import OpenAISTTProvider, create_openai_provider
from voice.stt.whisper_engine import get_engine as get_whisper_engine

logger = logging.getLogger("jarvis.stt_manager")


# Register providers
STTProviderRegistry.register("deepgram", create_deepgram_provider)
STTProviderRegistry.register("openai", create_openai_provider)


class FasterWhisperProvider:
    """Wrapper for Faster-Whisper to conform to STTProvider interface"""

    def __init__(self):
        self.engine = None
        self._available = False
        self._init_engine()

    def _init_engine(self):
        try:
            self.engine = get_whisper_engine()
            self._available = True
            logger.info("[Faster-Whisper] Ready as offline fallback")
        except Exception as e:
            logger.error("[Faster-Whisper] Failed to initialize: %s", e)
            self._available = False

    @property
    def name(self) -> str:
        return "faster-whisper"

    @property
    def is_available(self) -> bool:
        return self._available and self.engine is not None

    @property
    def requires_network(self) -> bool:
        return False

    def transcribe(self, audio: np.ndarray, language: Optional[str] = None) -> Optional[str]:
        if not self.is_available:
            logger.warning("[Faster-Whisper] Provider not available")
            return None

        if audio is None or len(audio) == 0:
            logger.warning("[Faster-Whisper] Empty audio input")
            return None

        try:
            text = self.engine.transcribe(audio, language=language)
            if text and text.strip():
                logger.info("[Faster-Whisper] Transcript: %s", text)
                return text.strip()
            logger.warning("[Faster-Whisper] Empty transcript")
            return None
        except Exception as e:
            logger.error("[Faster-Whisper] Transcription failed: %s", e)
            return None

    def shutdown(self):
        if self.engine:
            try:
                self.engine.shutdown()
            except Exception:
                pass
        logger.info("[Faster-Whisper] Shutdown")


class STTProviderManager:
    """
    Manages STT providers with ordered fallback.
    Online: Deepgram -> OpenAI -> Faster-Whisper
    Offline: Faster-Whisper
    """

    def __init__(self, offline_mode: bool = False):
        self.offline_mode = offline_mode
        self.providers: List[STTProvider] = []
        self.current_provider: Optional[STTProvider] = None
        self._initialize_providers()

    def _initialize_providers(self):
        """Initialize providers in priority order"""
        if not self.offline_mode:
            # Try online providers first
            deepgram = create_deepgram_provider()
            if deepgram:
                self.providers.append(deepgram)
                logger.info("[STT Manager] Deepgram provider registered")

            openai = create_openai_provider()
            if openai:
                self.providers.append(openai)
                logger.info("[STT Manager] OpenAI provider registered")

        # Always add offline fallback
        whisper = FasterWhisperProvider()
        if whisper.is_available:
            self.providers.append(whisper)
            logger.info("[STT Manager] Faster-Whisper provider registered (offline fallback)")

        if not self.providers:
            logger.error("[STT Manager] NO PROVIDERS AVAILABLE!")
        else:
            self.current_provider = self.providers[0]
            logger.info("[STT Manager] Primary provider: %s", self.current_provider.name)

    def transcribe(self, audio: np.ndarray, language: Optional[str] = None) -> Optional[str]:
        """
        Transcribe with automatic fallback.
        Returns first successful transcript.
        """
        if not self.providers:
            logger.error("[STT Manager] No providers available")
            return None

        for provider in self.providers:
            # Skip online providers if in offline mode
            if self.offline_mode and provider.requires_network:
                logger.debug("[STT Manager] Skipping %s (offline mode)", provider.name)
                continue

            if not provider.is_available:
                logger.debug("[STT Manager] %s not available, trying next", provider.name)
                continue

            logger.info("[STT Manager] Attempting transcription with %s", provider.name)
            try:
                transcript = provider.transcribe(audio, language)
                if transcript:
                    self.current_provider = provider
                    logger.info("[STT Manager] Success with %s", provider.name)
                    return transcript
                else:
                    logger.warning("[STT Manager] %s returned empty transcript", provider.name)
            except Exception as e:
                logger.error("[STT Manager] %s failed: %s", provider.name, e)

            logger.info("[STT Manager] Falling back to next provider...")

        logger.error("[STT Manager] All providers failed")
        return None

    @property
    def current_provider_name(self) -> str:
        return self.current_provider.name if self.current_provider else "none"

    @property
    def available_providers(self) -> List[str]:
        return [p.name for p in self.providers if p.is_available]

    def set_offline_mode(self, offline: bool):
        self.offline_mode = offline
        logger.info("[STT Manager] Offline mode: %s", offline)

    def shutdown(self):
        for provider in self.providers:
            try:
                provider.shutdown()
            except Exception:
                pass
        logger.info("[STT Manager] Shutdown complete")


# Global manager instance
_manager: Optional[STTProviderManager] = None


def get_stt_manager(offline_mode: bool = False) -> STTProviderManager:
    """Get or create the global STT provider manager"""
    global _manager
    if _manager is None:
        _manager = STTProviderManager(offline_mode=offline_mode)
    return _manager


def reset_stt_manager():
    """Reset the global manager (for testing/config changes)"""
    global _manager
    if _manager:
        _manager.shutdown()
    _manager = None