"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : wakeword.py

PATH    : voice/wakeword/wakeword.py

PURPOSE :
Detects the wake word ("Jarvis") using OpenWakeWord.
Optional - gracefully degrades if dependencies unavailable.
============================================================
"""

import logging
import numpy as np
import sounddevice as sd

logger = logging.getLogger("jarvis.wakeword")


class WakeWordDetector:
    """Wake word detector using OpenWakeWord (optional)"""

    def __init__(self):
        self.model = None
        self.sample_rate = 16000
        self.chunk_size = 1280
        self._available = False

        try:
            from openwakeword.model import Model
            self.model = Model()
            self._available = True
            logger.info("[WakeWord] OpenWakeWord loaded")
        except Exception as e:
            logger.warning("[WakeWord] OpenWakeWord unavailable: %s", e)
            self._available = False

    def listen(self) -> bool:
        """Wait for wake word. Returns True immediately if unavailable."""
        if not self._available:
            logger.info("[WakeWord] Unavailable - returning immediately (simulated wake)")
            return True

        logger.info("[WakeWord] Waiting for wake word...")

        try:
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                dtype="int16",
                blocksize=self.chunk_size,
            ) as stream:

                while True:
                    audio, _ = stream.read(self.chunk_size)
                    audio = audio.flatten().astype(np.int16)
                    prediction = self.model.predict(audio)

                    for name, score in prediction.items():
                        if score > 0.5:
                            logger.info(f"[WakeWord] Detected: {name} ({score:.2f})")
                            return True

        except Exception as e:
            logger.error("[WakeWord] Listen error: %s", e)
            return True  # Fail open - don't block the pipeline

    def shutdown(self):
        logger.info("[WakeWord] Shutdown")


# =========================================================

_detector = WakeWordDetector()


def wait_for_wakeword() -> bool:
    """Wait for wake word detection. Always returns True if detector unavailable."""
    return _detector.listen()