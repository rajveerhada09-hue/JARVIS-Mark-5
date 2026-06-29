"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : main.py

PATH    : main.py

PURPOSE :
Application entry point. Boots the complete JARVIS operating system, initializes all core modules, launches the HUD and starts the voice loop.

LAST UPDATED :
2026-06-28

============================================================
"""

"""
====================================================================================================
PROJECT: JARVIS MARK 5 - ADVANCED NEURAL OPERATING SYSTEM
AUTHOR: BOSS
VERSION: 5.3.0 (SPEECH_RECOGNITION + HINGLISH)
FILE: main.py
====================================================================================================
"""

import warnings
warnings.filterwarnings("ignore")

import threading
import time
import sys
import os
import json
import datetime
import traceback
import re
import subprocess

from http.server import SimpleHTTPRequestHandler
import socketserver
from colorama import init, Fore, Style
from dotenv import load_dotenv

# Core Imports
from core.speech  import listen   # ab sr wala
from core.brain import JarvisBrain
from core.intent_engine import IntentEngine
from core.tool_manager import ToolManager
from core.voice import speak, is_speaking

init(autoreset=True)
load_dotenv()

# Global Brain
try:
    brain_logic = JarvisBrain()
except Exception as e:
    print(Fore.RED + f"[CRITICAL] Brain failed to load: {e}")
    brain_logic = None

intent_engine = IntentEngine()
tool_manager = ToolManager()

conversation_mode = False
conversation_timeout = 0

class SystemState:
    def __init__(self):
        self.HUD_TEXT = "Systems Online Boss."
        self.JARVIS_MODE = "STANDBY"
        self.CURRENT_TASK = "IDLE"
        self.START_TIME = time.time()
        self.COMMAND_COUNT = 0
        self.LAST_QUERY = ""
        self.WAKE_WORDS = ["jarvis", "jarves", "jervis", "jarvice", "jarwis", "service", "garvis", "hey jarvis"]

state = SystemState()
pending_action = None

def update_hud_state(mode="idle", text=""):
    try:
        state.JARVIS_MODE = mode
        state.HUD_TEXT = text
        data = {
            "jarvis_state": mode,
            "text": text,
            "current_task": state.CURRENT_TASK,
            "uptime": str(datetime.timedelta(seconds=int(time.time() - state.START_TIME)))
        }
        with open("hud_status.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except:
        pass

# ===================================================================
# CENTRAL COMMAND PROCESSOR
# ===================================================================
def process_query(query: str):
    global pending_action, conversation_mode, conversation_timeout

    q = query.lower().strip()

    state.COMMAND_COUNT += 1
    state.LAST_QUERY = q
    state.CURRENT_TASK = f"PROCESSING: {q}"

    update_hud_state("thinking", f"Processing: {q}")

    if pending_action:
        yes = ["yes", "yes sir", "yes jarvis", "confirm", "do it"]
        no = ["no", "cancel", "stop", "abort", "nah"]
        if q in yes:
            intent = pending_action["intent"]
            pending_action = None
            from core.pc_control import pc_control_master
            return pc_control_master(intent["value"])
        elif q in no:
            pending_action = None
            return "Operation cancelled."
        else:
            pending_action = None
            return "Previous action cancelled."

    # Multi Command
    commands = re.split(r"\band\b|\bthen\b", q)
    results = []

    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue

            intent = intent_engine.classify(cmd)

            if intent["type"] == "pc":
                pending_action = {"intent": intent}
                return f"Confirmation required for: {intent['value']}"

            tool_result = tool_manager.execute_intent(intent)
            if tool_result:
                results.append(tool_result)
                continue
        return " | ".join([r for r in results if r])

    if brain_logic:
        return brain_logic.process_query(q)

    return "Boss, I didn't catch that clearly. Could you say that again, Boss?"

# ===================================================================
# BOOT SEQUENCE
# ===================================================================
def boot_sequence():
    os.system('cls' if os.name == 'nt' else 'clear')

    print(Fore.CYAN + Style.BRIGHT + "JARVIS MARK 5 : INITIATING MEGA CORE...")

    update_hud_state("idle", "SYSTEM ONLINE")

    speak("Now may to introduce myself. I am Jarvis, a Virtual Artificial Intelligence. I was created by Rajveer to solve your problems and make your life easier. How can I help you today, Boss?")

    # HUD
    try:
        hud_path = os.path.join(os.getcwd(), "hud", "electron")
        if os.path.exists(hud_path):
            subprocess.Popen(["npm", "start"], cwd=hud_path, shell=True)
            print(Fore.GREEN + "[HUD] Electron HUD launched.")
    except Exception as e:
        print(Fore.RED + f"[HUD ERROR] {e}")

# ===================================================================
# MAIN LOOP
# ===================================================================
if __name__ == "__main__":
    def start_server():
        with socketserver.TCPServer(("", 8000), SimpleHTTPRequestHandler) as httpd:
            print(Fore.GREEN + "[SYSTEM] HUD Server Online at http://localhost:8000")
            httpd.serve_forever()

    threading.Thread(target=start_server, daemon=True).start()

    boot_sequence()

    print(Fore.GREEN + "✅ JARVIS Mark 5 Ready!")

    while True:
        if is_speaking():
            time.sleep(0.1)
            continue

        try:
            print(">>> [VOICE] Listening loop ready")
            raw_input = listen()

            if not raw_input or raw_input.strip() == "":
                print("[VOICE] No user input captured, restarting listen loop")
                continue

            print(f"[VOICE] USER: {raw_input}")

            clean_cmd = raw_input.lower().strip()

            current_time = time.time()

            is_wake = (conversation_mode and current_time < conversation_timeout) or any(word in clean_cmd for word in state.WAKE_WORDS)

            if not is_wake:
                continue

            for word in state.WAKE_WORDS:
                clean_cmd = clean_cmd.replace(word, "").strip()

            conversation_mode = True
            conversation_timeout = time.time() + 40

            if not clean_cmd:
                print("[VOICE] No command after wake word, prompting user")
                speak("Yes Boss?")
                continue

            print(f"➤ ACTION: {clean_cmd.upper()}")
            print("[BRAIN] Processing query")
            reply = process_query(clean_cmd)

            if reply:
                print(f"[BRAIN] Reply generated: {reply}")
            else:
                print("[BRAIN] No reply generated, using fallback response")
                reply = "I could not process that request, Boss."

            update_hud_state("speaking", reply if len(reply) < 80 else reply[:80] + "...")
            print("[DEBUG] Calling speak()")
            speak(reply)
            print("[DEBUG] speak() returned")  
            print("[VOICE] Waiting for speech to finish before listening again")
            while is_speaking():
                time.sleep(0.1)
            update_hud_state("idle", "Awaiting command")
            print("[VOICE] Ready again")

        except Exception as e:
            print(Fore.RED + "[ERROR]")
            traceback.print_exc()