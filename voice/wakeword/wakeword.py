"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : wakeword.py

PATH    : voice/wakeword/wakeword.py

PURPOSE :
Detects the wake word ("Jarvis") using OpenWakeWord.

============================================================
"""

import logging
import numpy as np
import sounddevice as sd
from openwakeword.model import Model

logger = logging.getLogger("jarvis.wakeword")


class WakeWordDetector:

    def __init__(self):

        logger.info("[WakeWord] Loading OpenWakeWord...")

        self.model = Model()

        self.sample_rate = 16000
        self.chunk_size = 1280

        logger.info("[WakeWord] Ready")

    # -----------------------------------------------------

    def listen(self):

        logger.info("[WakeWord] Waiting for wake word...")

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

                        logger.info(
                            f"[WakeWord] Detected: {name} ({score:.2f})"
                        )

                        return True

    # -----------------------------------------------------

    def shutdown(self):

        logger.info("[WakeWord] Shutdown")


# =========================================================

_detector = WakeWordDetector()


def wait_for_wakeword():

    return _detector.listen()

