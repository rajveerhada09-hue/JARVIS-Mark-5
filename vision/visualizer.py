"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : visualizer.py

PATH    : core\visualizer.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import sounddevice as sd
import numpy as np
import os

# Visualizer settings
WIDTH = 80  # Terminal width ke hisaab se
GAIN = 10   # Wave ki height kitni ho

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    
    # Audio data ko analyze karna
    volume_norm = np.linalg.norm(indata) * GAIN
    magnitude = int(volume_norm)
    
    # Waveform string banana
    line = "-" * (magnitude % WIDTH)
    # Terminal mein ek hi line par update karna (\r use karke)
    print(f"\r[AUDIO WAVE]: {line}>", end="")

def start_visualizer():
    print("\n" + "="*30)
    print(" JARVIS AUDIO LINK ACTIVE ")
    print("="*30 + "\n")
    
    with sd.InputStream(callback=audio_callback):
        while True:
            sd.sleep(100)

if __name__ == "__main__":
    start_visualizer()