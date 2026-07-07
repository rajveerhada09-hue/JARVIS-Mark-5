"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : tts.py

PATH    : core\tts.py

PURPOSE :
Generates speech using  and manages audio synthesis.

LAST UPDATED :
2026-06-28

============================================================
"""

import pyttsx3
import threading
import time
from colorama import Fore

# Initialize Engine
engine = pyttsx3.init('sapi5') # Windows ke liye fastest driver
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[0].id) # 0 for David (Jarvis style), 1 for Zira
engine.setProperty('rate', 175) # Normal speed se thoda tez (Witty vibe)

# Interrupt Flag
stop_flag = False

def log_voice(msg):
    print(f"{Fore.MAGENTA}[VOICE-ENGINE] {Fore.WHITE}{msg}")

def speak(text):
    """Main speak function that supports interruption"""
    global stop_flag
    stop_flag = False
    
    # Text ko console pe dikhana
    print(f"{Fore.CYAN}JARVIS: {Fore.WHITE}{text}")

    def run_engine():
        global stop_flag
        # Engine starts speaking
        engine.say(text)
        
        # Ye loop check karta rahega ki beech mein 'stop' toh nahi bola gaya
        while engine.isBusy():
            if stop_flag:
                engine.stop()
                break
            time.sleep(0.05)
        
        try:
            engine.runAndWait()
        except Exception:
            pass

    # Voice ko background thread mein chalana taaki 'Mute' command suni ja sake
    voice_thread = threading.Thread(target=run_engine)
    voice_thread.start()

def stop_speak():
    """Baap Level Interruption: Ek baar mein khamosh!"""
    global stop_flag
    stop_flag = True
    try:
        engine.stop()
        log_voice("Protocol Silence: Output Terminated.")
    except:
        pass

# --- TEST (Sirf debug ke liye) ---
if __name__ == "__main__":
    speak("Testing neural voice synchronization. Systems are fully operational.")