"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : whisper_engine.py

PATH    : voice/stt/whisper_engine.py

PURPOSE :
Loads Faster Whisper once and provides GPU-accelerated
speech transcription.

============================================================
"""

import logging
import os
import tempfile

import numpy as np
import soundfile as sf
from faster_whisper import WhisperModel

logger = logging.getLogger("jarvis.whisper")


class WhisperEngine:

    def __init__(
        self,
        model_size="small",
        device="cuda",
        compute_type="float16",
    ):

        self.model_size = model_size

        try:

            self.model = WhisperModel(
                model_size,
                device=device,
                compute_type=compute_type,
            )

            self.device = device

            logger.info(
                f"[Whisper] Loaded {model_size} on {device}"
            )

        except Exception as e:

            logger.warning(
                f"[Whisper] CUDA unavailable ({e})"
            )

            logger.warning(
                "[Whisper] Falling back to CPU..."
            )

            self.model = WhisperModel(
                model_size,
                device="cpu",
                compute_type="int8",
            )

            self.device = "cpu"

def is_gpu(self):
    return self.device == "cuda"
    # --------------------------------------------------

    def warmup(self):

        logger.info("[Whisper] Warmup...")

        dummy = np.zeros((16000, 1), dtype=np.float32)

        self.transcribe(dummy)

        logger.info("[Whisper] Warmup Complete")

    # --------------------------------------------------

def transcribe(
    self,
    audio,
    language=None,
    beam_size=1,
    vad_filter=False,
):
    """
    Accepts:
    1. numpy array
    2. wav path
    """

    if isinstance(audio, np.ndarray):

        with tempfile.NamedTemporaryFile(
            suffix=".wav",
            delete=False,
        ) as tmp:

            sf.write(
                tmp.name,
                audio,
                16000,
            )

            audio_path = tmp.name

        delete_after = True

    else:

        audio_path = audio
        delete_after = False

    try:

        segments, info = self.model.transcribe(
            audio_path,
            beam_size=beam_size,
            language=language,
            vad_filter=vad_filter,
        )

        text = " ".join(
            segment.text
            for segment in segments
        ).strip()

        return text

    finally:

        if delete_after:
            try:
                os.remove(audio_path)
            except OSError as e:
                logger.warning(e)

    # --------------------------------------------------

    def info(self):

        return {

            "model": self.model_size,

            "device": self.device,

        }

    # --------------------------------------------------

    def shutdown(self):

        logger.info("[Whisper] Shutdown")

        del self.model


# ============================================================

_engine = WhisperEngine()


def get_engine():

    return _engine