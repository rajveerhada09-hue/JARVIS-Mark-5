"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : deepgram_stt.py
PATH    : voice/stt/deepgram_stt.py
PURPOSE : Deepgram Nova-3 STT Provider (Deepgram SDK v3+)
============================================================
"""

import os
import logging
import tempfile
import numpy as np
import soundfile as sf
from typing import Optional
from deepgram import DeepgramClient

logger = logging.getLogger("jarvis.deepgram")


class DeepgramSTTProvider:
    """Deepgram Nova-3 STT Provider - Primary Online STT"""

    def __init__(self, api_key: Optional[str] = None, model: str = "nova-3", language: str = "en"):
        self.api_key = api_key or os.getenv("Deepgram_API_KEY")
        self.model = model
        self.language = language
        self.client = None
        self._available = False

        if self.api_key:
            try:
                self.client = DeepgramClient(api_key=self.api_key)
                self._available = True
                logger.info("[Deepgram] Initialized with model: %s", self.model)
            except Exception as e:
                logger.error("[Deepgram] Initialization failed: %s", e)
                self._available = False
        else:
            logger.warning("[Deepgram] No API key found (Deepgram_API_KEY)")

    @property
    def name(self) -> str:
        return "deepgram"

    @property
    def is_available(self) -> bool:
        return self._available and self.client is not None

    @property
    def requires_network(self) -> bool:
        return True

    def transcribe(self, audio: np.ndarray, language: Optional[str] = None) -> Optional[str]:
        """Transcribe audio using Deepgram Nova-3"""
        if not self.is_available:
            logger.warning("[Deepgram] Provider not available")
            return None

        if audio is None or len(audio) == 0:
            logger.warning("[Deepgram] Empty audio input")
            return None

        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                sf.write(tmp.name, audio, 16000)
                audio_path = tmp.name

            with open(audio_path, "rb") as audio_file:
                buffer_data = audio_file.read()

            response = self.client.listen.v1.media.transcribe_file(
                request=buffer_data,
                model=self.model,
                language=language or self.language,
                smart_format=True,
                punctuate=True,
                utterances=True,
                encoding="linear16",
            )

            if response and response.results:
                channels = response.results.channels
                if channels and len(channels) > 0:
                    alternatives = channels[0].alternatives
                    if alternatives and len(alternatives) > 0:
                        transcript = alternatives[0].transcript.strip()
                        if transcript:
                            logger.info("[Deepgram] Transcript: %s", transcript)
                            return transcript

            logger.warning("[Deepgram] Empty transcript returned")
            return None

        except Exception as e:
            logger.error("[Deepgram] Transcription failed: %s", e)
            return None
        finally:
            try:
                os.remove(audio_path)
            except Exception:
                pass

    def shutdown(self):
        logger.info("[Deepgram] Shutdown")


def create_deepgram_provider(api_key: Optional[str] = None) -> Optional[DeepgramSTTProvider]:
    """Factory function to create Deepgram provider"""
    provider = DeepgramSTTProvider(api_key=api_key)
    if provider.is_available:
        return provider
    return None