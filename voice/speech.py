"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : speech.py

PATH    : core\speech.py

PURPOSE :
Captures microphone input and converts speech into text.

LAST UPDATED :
2026-06-28

============================================================
"""

import queue
import sounddevice as sd
import os
import time
import numpy as np
import subprocess
import traceback
import speech_recognition as sr   # ← New lightweight recognizer

print("[LISTENER] Initializing with Auto-Mute + Google Speech Recognition...")

# =========================
# GLOBAL STATES
# =========================
MUTED = False

def mute_system_audio(mute=True):
    """Mute / Unmute system audio on Windows using NirCmd"""
    try:
        if mute:
            subprocess.run(["nircmd.exe", "mutesysvolume", "1"], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["nircmd.exe", "mutesysvolume", "0"], shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        pass  # NirCmd not found, ignore

def get_best_input_device():
    devices = sd.query_devices()
    print("\n=== AVAILABLE AUDIO DEVICES ===")
    for i, dev in enumerate(devices):
        print(f"{i}: {dev['name']} (in:{dev['max_input_channels']})")

    for i, dev in enumerate(devices):
        name = dev['name'].lower()
        if dev['max_input_channels'] > 0 and "sound mapper" not in name:
            print(f"[LISTENER] Selected: {dev['name']} (index {i})")
            sd.default.device = (i, sd.default.device[1])
            return i
    return None

get_best_input_device()

class JarvisListener:
    def __init__(self):
        self.is_listening = False
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 50
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

    def listen(self, timeout=50):
        print(">>> [VOICE] Listening... Speak clearly... (System audio muted)")

        self.is_listening = True
        mute_system_audio(True)   # Mute TTS

        try:
            with sr.Microphone() as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                print("[VOICE] Listening active")
                audio = self.recognizer.listen(source, timeout=timeout, phrase_time_limit=8)

            print("[VOICE] Speech Recognized")
            text = self.recognizer.recognize_google(audio, language='en-in')
            print(f"[VOICE] Final transcript: {text}")
            return text.lower()

        except sr.WaitTimeoutError:
            print("[VOICE] Listen timeout")
            return ""
        except sr.UnknownValueError:
            print("[VOICE] Could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"[VOICE] Google API Error: {e}")
            traceback.print_exc()
            return ""
        except Exception as e:
            print(f"[VOICE ERROR] {e}")
            traceback.print_exc()
            return ""
        finally:
            mute_system_audio(False)   # Unmute TTS
            self.is_listening = False
            print("[VOICE] Listening ended")

    def _callback(self, indata, frames, time_info, status):
        pass  # Not used in this implementation (kept for compatibility)

# =========================
# COMPATIBILITY
# =========================
def listen():
    listener = JarvisListener()
    return listener.listen()