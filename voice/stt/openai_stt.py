"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : openai_stt.py
PATH    : voice/stt/openai_stt.py
PURPOSE : OpenAI Transcription STT Provider (Secondary Online)
============================================================
"""

import os
import logging
import tempfile
import numpy as np
import soundfile as sf
from typing import Optional
from openai import OpenAI

logger = logging.getLogger("jarvis.openai_stt")


class OpenAISTTProvider:
    """OpenAI Whisper Transcription Provider - Secondary Online STT"""

    def __init__(self, api_key: Optional[str] = None, model: str = "whisper-1", language: str = "en"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.language = language
        self.client = None
        self._available = False

        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                self._available = True
                logger.info("[OpenAI STT] Initialized with model: %s", self.model)
            except Exception as e:
                logger.error("[OpenAI STT] Initialization failed: %s", e)
                self._available = False
        else:
            logger.warning("[OpenAI STT] No API key found (OPENAI_API_KEY)")

    @property
    def name(self) -> str:
        return "openai"

    @property
    def is_available(self) -> bool:
        return self._available and self.client is not None

    @property
    def requires_network(self) -> bool:
        return True

    def transcribe(self, audio: np.ndarray, language: Optional[str] = None) -> Optional[str]:
        """Transcribe audio using OpenAI Whisper API"""
        if not self.is_available:
            logger.warning("[OpenAI STT] Provider not available")
            return None

        if audio is None or len(audio) == 0:
            logger.warning("[OpenAI STT] Empty audio input")
            return None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, audio, 16000)
                audio_path = tmp.name

            with open(audio_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=language or self.language,
                    response_format="text",
                )

            transcript = response.strip() if response else ""

            if transcript:
                logger.info("[OpenAI STT] Transcript: %s", transcript)
                return transcript

            logger.warning("[OpenAI STT] Empty transcript returned")
            return None

        except Exception as e:
            logger.error("[OpenAI STT] Transcription failed: %s", e)
            return None
        finally:
            try:
                os.remove(audio_path)
            except Exception:
                pass

    def shutdown(self):
        logger.info("[OpenAI STT] Shutdown")


def create_openai_provider(api_key: Optional[str] = None) -> Optional[OpenAISTTProvider]:
    """Factory function to create OpenAI STT provider"""
    provider = OpenAISTTProvider(api_key=api_key)
    if provider.is_available:
        return provider
    return None