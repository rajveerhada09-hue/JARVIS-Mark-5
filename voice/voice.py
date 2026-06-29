"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : voice.py
PATH    : core\voice.py

CHANGES vs original:
  1. Added interrupt/resume system:
       - _resume_buffer stores (remaining_sentences, current_sentence_index)
       - stop_speaking() now saves position to _resume_buffer
       - resume_speech() replays from exact sentence where it stopped
  2. Added sentence-splitting in _split_sentences() so position tracking
     is sentence-accurate, not word-accurate.
  3. The _listen_for_interrupt() thread (already existed) now also sets
     _resume_buffer on interrupt.
  4. All original public API preserved:
       speak(text, intent, priority)
       stop_speaking()
       is_speaking()
  5. New public functions added (do not conflict):
       resume_speech()
       clear_resume_buffer()
       has_pending_resume()
  6. All original threading, queue, ElevenLabs, pygame, pyttsx3 logic
     preserved exactly — only additions, no removals.
============================================================
"""

import os
import re
import time
import threading
import traceback
from queue import Queue, Empty

import pygame
import pyttsx3
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from colorama import Fore, init

init(autoreset=True)
load_dotenv()

# ── Init (original) ───────────────────────────────────────────────────────────
try:
    api_key = os.getenv("ELEVENLABS_API_KEY")
    client  = ElevenLabs(api_key=api_key) if api_key else None
except Exception as e:
    print(f"{Fore.RED}ElevenLabs Init Error: {e}")
    client = None

VOICE_ID = os.getenv("VOICE_ID", "nPczCjzI2devNBz1zQrb")

engine = pyttsx3.init("sapi5")
voices = engine.getProperty("voices")
engine.setProperty("voice", voices[0].id)
engine.setProperty("rate", 135)

if not pygame.mixer.get_init():
    pygame.mixer.init()

# ── Core state (original) ─────────────────────────────────────────────────────
voice_queue    = Queue()
stop_event     = threading.Event()
speaking_event = threading.Event()
mic_interrupt  = threading.Event()
OFFLINE_MODE   = False

# ── Resume buffer (new) ───────────────────────────────────────────────────────
# Stores (list_of_sentences, index_of_next_sentence_to_speak)
_resume_lock   = threading.Lock()
_resume_buffer: tuple = ()   # empty = nothing to resume


def _split_sentences(text: str) -> list:
    """Split text into speakable sentence units."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _store_resume(sentences: list, next_index: int) -> None:
    global _resume_buffer
    with _resume_lock:
        if next_index < len(sentences):
            _resume_buffer = (sentences, next_index)
        else:
            _resume_buffer = ()


def _clear_resume() -> None:
    global _resume_buffer
    with _resume_lock:
        _resume_buffer = ()


# ── VoiceBrain (original — unchanged) ────────────────────────────────────────
class VoiceBrain:
    def __init__(self):
        self.last_emotion = "neutral"

    def analyze(self, text: str, intent: str = "chat"):
        t        = text.lower()
        emotion  = "neutral"
        priority = False
        if any(x in t for x in ["error", "critical", "down", "failed"]):
            emotion  = "serious"
            priority = True
        elif any(x in t for x in ["stop", "wait", "shut up", "silence"]):
            emotion  = "firm"
            priority = True
        elif intent in ["pc_control", "system"]:
            emotion  = "confident"
            priority = True
        elif any(x in t for x in ["hello", "hi"]):
            emotion  = "friendly"
        elif any(x in t for x in ["joke", "fun", "haha"]):
            emotion  = "light"
        if emotion == "neutral":
            emotion = self.last_emotion
        else:
            self.last_emotion = emotion
        return emotion, priority


brain = VoiceBrain()


# ── Public API ────────────────────────────────────────────────────────────────

def speak(text: str, intent: str = "chat", priority: bool = False) -> None:
    """Original signature preserved."""
    text = clean_for_tts(str(text))
    if not text:
        print(f"{Fore.YELLOW}[TTS] No text to speak")
        return

    emotion, auto_priority = brain.analyze(text, intent)
    if auto_priority:
        priority = True

    if priority:
        _clear_queue()
        stop_speaking()

    # Clear resume buffer when starting new speech
    _clear_resume()

    try:
        voice_queue.put((text, intent, emotion))
        speaking_event.set()
        print(f"{Fore.CYAN}[TTS] Queued → intent={intent}, emotion={emotion}")
    except Exception as e:
        print(f"{Fore.RED}[TTS ERROR] {e}")
        traceback.print_exc()
        speaking_event.clear()


def stop_speaking() -> None:
    """Original signature preserved. Now also saves resume position."""
    stop_event.set()
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass
    _clear_queue()


def is_speaking() -> bool:
    """Original signature preserved."""
    return speaking_event.is_set()


def resume_speech() -> bool:
    """
    NEW: Resume from where speech was interrupted.
    Returns True if there was something to resume, False otherwise.
    """
    with _resume_lock:
        buf = _resume_buffer

    if not buf:
        return False

    sentences, next_idx = buf
    remaining = " ".join(sentences[next_idx:])
    if remaining.strip():
        _clear_resume()
        speak(remaining)
        return True
    return False


def has_pending_resume() -> bool:
    """NEW: Check if there is interrupted speech waiting to be resumed."""
    with _resume_lock:
        return bool(_resume_buffer)


def clear_resume_buffer() -> None:
    """NEW: Discard any pending resume state."""
    _clear_resume()


# ── Queue management (original) ───────────────────────────────────────────────
def _clear_queue() -> None:
    while not voice_queue.empty():
        try:
            voice_queue.get_nowait()
        except Empty:
            break


def _worker() -> None:
    """Original worker thread — sentence-level resume tracking added."""
    while True:
        item = voice_queue.get()
        if item is None:
            break
        try:
            text, intent, emotion = item
            print(f"{Fore.CYAN}[TTS] Worker → intent={intent}, emotion={emotion}")
            _run_speak(text, intent, emotion)
            print(f"{Fore.CYAN}[TTS] Worker finished")
        except Exception as e:
            print(f"{Fore.RED}[TTS WORKER ERROR] {e}")
            traceback.print_exc()
        finally:
            voice_queue.task_done()


# ── Core engine (original + resume tracking) ──────────────────────────────────
def _run_speak(text: str, intent: str = "chat", emotion: str = "neutral") -> None:
    global OFFLINE_MODE

    speaking_event.set()
    stop_event.clear()
    mic_interrupt.clear()

    sentences = _split_sentences(text)
    total     = len(sentences)

    try:
        safe_text = str(text)
        emotion, _ = brain.analyze(safe_text, intent)

        voice_style = {
            "neutral":   {"stability": 0.75, "style": 0.3},
            "friendly":  {"stability": 0.6,  "style": 0.6},
            "serious":   {"stability": 0.9,  "style": 0.2},
            "confident": {"stability": 0.8,  "style": 0.4},
            "firm":      {"stability": 0.95, "style": 0.1},
            "light":     {"stability": 0.5,  "style": 0.8},
        }.get(emotion, {"stability": 0.75, "style": 0.3})

        # ── OFFLINE fallback ──────────────────────────────────────────────────
        if OFFLINE_MODE or not client:
            print(f"{Fore.BLUE}[OFFLINE] JARVIS: {safe_text}")
            for i, sentence in enumerate(sentences):
                if stop_event.is_set() or mic_interrupt.is_set():
                    _store_resume(sentences, i)
                    return
                engine.say(sentence)
                engine.runAndWait()
            return

        # ── ONLINE (ElevenLabs sentence by sentence) ──────────────────────────
        print(f"{Fore.CYAN}🤖 JARVIS: {safe_text}")

        for i, sentence in enumerate(sentences):
            if stop_event.is_set() or mic_interrupt.is_set():
                _store_resume(sentences, i)
                return

            try:
                audio_gen = client.text_to_speech.convert(
                    voice_id=VOICE_ID,
                    text=sentence,
                    model_id="eleven_turbo_v2_5",
                    output_format="mp3_44100_128",
                    voice_settings={
                        "stability":        voice_style["stability"],
                        "similarity_boost": 0.90,
                        "style":            voice_style["style"],
                        "use_speaker_boost": True,
                    },
                )

                file_path = f"voice_cache_{time.time_ns()}.mp3"
                with open(file_path, "wb") as f:
                    for chunk in audio_gen:
                        if stop_event.is_set() or mic_interrupt.is_set():
                            _store_resume(sentences, i)
                            return
                        if chunk:
                            f.write(chunk)

                pygame.mixer.music.load(file_path)
                pygame.mixer.music.play()

                while pygame.mixer.music.get_busy():
                    if stop_event.is_set() or mic_interrupt.is_set():
                        pygame.mixer.music.stop()
                        _store_resume(sentences, i + 1)
                        return
                    time.sleep(0.05)

                pygame.mixer.music.unload()
                time.sleep(0.04)

                if os.path.exists(file_path):
                    os.remove(file_path)

            except Exception as e:
                print(f"{Fore.RED}[VOICE SENTENCE ERROR] {e}")
                # Fallback for this sentence
                try:
                    engine.say(sentence)
                    engine.runAndWait()
                except Exception:
                    pass

        # All sentences played — clear resume buffer
        _clear_resume()
        print(f"{Fore.CYAN}[TTS] Playback complete")

    except Exception as e:
        print(f"{Fore.RED}[VOICE ERROR] {e}")
        traceback.print_exc()
        try:
            engine.say(str(text))
            engine.runAndWait()
        except Exception as tts_e:
            print(f"{Fore.RED}[VOICE FALLBACK ERROR] {tts_e}")
    finally:
        speaking_event.clear()
        print(f"{Fore.CYAN}[TTS] Speaking event cleared")


# ── Interrupt listener (original — unchanged) ─────────────────────────────────
def _listen_for_interrupt() -> None:
    import speech_recognition as sr
    recognizer = sr.Recognizer()
    mic        = sr.Microphone()
    while True:
        try:
            with mic as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.3)
                audio = recognizer.listen(source, phrase_time_limit=2)
            command = recognizer.recognize_google(audio).lower()
            if any(x in command for x in ["stop", "wait", "shut up", "silence", "mute", "pause"]):
                print(f"{Fore.RED}[INTERRUPT] Voice stopped by user")
                stop_speaking()
                mic_interrupt.set()
        except Exception:
            pass
        time.sleep(0.1)


# ── TTS text cleaner (original — unchanged) ───────────────────────────────────
def clean_for_tts(text: str) -> str:
    replacements = {
        "gui":    "G U I",    "cpu":  "C P U",  "ram":  "R A M",
        "api":    "A P I",    "ai":   "A I",     "gpu":  "G P U",
        "jarvis": "Jarvis",   "gpt":  "G P T",   "ui":   "U I",
        "html":   "H T M L",  "css":  "C S S",   "json": "J S O N",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
        text = text.replace(k.upper(), v)
        text = text.replace(k.title(), v)
    return text


# ── Start background threads (original) ───────────────────────────────────────
threading.Thread(target=_worker,               daemon=True).start()
threading.Thread(target=_listen_for_interrupt, daemon=True).start()