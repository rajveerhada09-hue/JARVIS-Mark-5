"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : silero_vad.py

PATH    : voice/stt/silero_vad.py

PURPOSE :
Voice Activity Detection using Silero VAD.

Returns True when speech is detected.

============================================================
"""

import torch
import numpy as np


class SileroVAD:

    def __init__(
        self,
        threshold=0.50,
        sample_rate=16000,
    ):

        self.threshold = threshold
        self.sample_rate = sample_rate

        print("[VAD] Loading Silero VAD...")

        (
            self.model,
            self.utils,
        ) = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad",
            trust_repo=True,
        )

        print("[VAD] Ready")

    # ----------------------------------------------------

    def is_speech(self, audio: np.ndarray) -> bool:

        """
        audio:
            numpy float32
            shape = (N,)
        """

        if audio.ndim > 1:
            audio = audio.squeeze()

        audio = torch.from_numpy(audio)

        probability = self.model(
            audio,
            self.sample_rate,
        ).item()

        return probability > self.threshold

    # ----------------------------------------------------

    def speech_probability(self, audio):

        if audio.ndim > 1:
            audio = audio.squeeze()

        audio = torch.from_numpy(audio)

        return self.model(
            audio,
            self.sample_rate,
        ).item()


# ========================================================

_vad = SileroVAD()


def get_vad():

    return _vad

