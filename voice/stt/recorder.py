"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : recorder.py

PATH    : voice/stt/recorder.py

PURPOSE :
Handles microphone recording only.

Returns raw NumPy audio for Whisper.

============================================================
"""

import logging
import sounddevice as sd
import numpy as np
from voice.stt.silero_vad import get_vad

logger = logging.getLogger("jarvis.recorder")


class AudioRecorder:

    def __init__(
        self,
        samplerate=16000,
        channels=1,
        dtype="float32",
    ):

        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype

    # --------------------------------------------------

    def record(self, max_duration=15):



        vad = get_vad()

        logger.info("[Recorder] Waiting for speech...")

        chunk = 512
        silence_timeout = 0.8

        audio_buffer = []

        speech_started = False

        silence_chunks = 0

        max_chunks = int(
            max_duration * self.samplerate / chunk
        )

        with sd.InputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype=self.dtype,
            blocksize=chunk,
        ) as stream:

            for _ in range(max_chunks):

                audio, overflow = stream.read(chunk)

                audio = audio.flatten()

                if vad.is_speech(audio):

                    if not speech_started:

                        logger.info("[Recorder] Speech Detected")

                        speech_started = True

                    silence_chunks = 0

                    audio_buffer.append(audio)

                else:

                    if speech_started:

                        silence_chunks += 1

                        audio_buffer.append(audio)

                        if (
                            silence_chunks
                            > silence_timeout
                            * self.samplerate
                            / chunk
                        ):

                            logger.info("[Recorder] Speech End")

                            break

        if len(audio_buffer) == 0:

            return np.zeros(
                (16000,),
                dtype=np.float32,
            )

        return np.concatenate(audio_buffer)

# --------------------------------------------------

def available_devices(self):

    return sd.query_devices()

    # --------------------------------------------------

    def select_device(self, index):

        sd.default.device = (index, sd.default.device[1])

        logger.info(f"[Recorder] Using Input Device {index}")


# ============================================================

_recorder = AudioRecorder()


def get_recorder():

    return _recorder