"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : main.py

PATH    : main.py

PURPOSE :
Application entry point. Boots the complete JARVIS operating system, initializes all core modules, launches the HUD and starts the voice loop.

LAST UPDATED :
2026-06-29

============================================================
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
from core.speech  import listen
from core.brain import JarvisBrain
from core.intent_engine import IntentEngine
from core.tool_manager import ToolManager
from core.voice import speak, is_speaking
from core.kernel import Kernel

# Existing Modules Integration
from core.conversation_engine import ConversationEngine
from core.greeting_manager import GreetingManager
from core.observer import Observer
from core.memory.memory_engine import MemoryEngine
from core.personality.human_layer import HumanLayer
from core.personality.persona_engine import PersonaEngine
from core.environment_engine import EnvironmentEngine
from core.context_engine import ContextEngine

init(autoreset=True)
load_dotenv()

# ====================== GLOBAL SYSTEM KERNEL ======================
try:
    brain_logic = JarvisBrain()
except Exception as e:
    print(Fore.RED + f"[CRITICAL] Brain failed to load: {e}")
    brain_logic = None

intent_engine = IntentEngine()
tool_manager = ToolManager()
conversation_engine = ConversationEngine()
greeting_manager = GreetingManager()
memory_engine = MemoryEngine()
observer = Observer()
human_layer = HumanLayer()
persona_engine = PersonaEngine()
environment_engine = EnvironmentEngine()
context_engine = ContextEngine()

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

    # Multi Command Split
    commands = re.split(r"\band\b|\bthen\b", q)
    results = []

    for cmd in commands:
        cmd = cmd.strip()
        if not cmd:
            continue

        # Intent + Tool
        intent = intent_engine.classify(cmd)
        tool_result = tool_manager.execute_intent(intent)
        if tool_result:
            results.append(tool_result)
            continue

        # Brain Fallback
        if brain_logic:
            results.append(brain_logic.process_query(cmd))

    if results:
        final_reply = " | ".join([r for r in results if r])
        return final_reply

    return "No valid command detected, Boss."

# ===================================================================
# BOOT SEQUENCE (Professional Orchestration)
# ===================================================================
def boot_sequence():
    os.system('cls' if os.name == 'nt' else 'clear')

    print(Fore.CYAN + Style.BRIGHT + "JARVIS MARK 5 : INITIATING MEGA CORE...")

    print("[INIT] Memory Engine Ready")
    print("[INIT] Context Engine Ready")
    print("[INIT] Environment Engine Ready")
    print("[INIT] Brain Ready")
    print("[INIT] Conversation Engine Ready")
    print("[INIT] Observer Running")
    print("[INIT] HUD Initializing...")

    update_hud_state("idle", "SYSTEM ONLINE")

    # Dynamic Greeting
    greeting = greeting_manager.get_greeting()
    speak(greeting)

    # Launch Electron HUD
    try:
        hud_path = os.path.join(os.getcwd(), "hud", "electron")
        if os.path.exists(hud_path):
            subprocess.Popen(["npm", "start"], cwd=hud_path, shell=True)
            print(Fore.GREEN + "[HUD] Electron HUD launched.")
    except Exception as e:
        print(Fore.RED + f"[HUD ERROR] {e}")

# ===================================================================
# HTTP HANDLER FOR HUD
# ===================================================================
class JarvisHandler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path == "/get_hud_data":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            try:
                with open("hud_status.json", "r", encoding="utf-8") as f:
                    self.wfile.write(f.read().encode())
            except:
                self.wfile.write(json.dumps({"jarvis_state": "idle", "text": "Offline"}).encode())
        else:
            return super().do_GET()

# ===================================================================
# MAIN LOOP
# ===================================================================
if __name__ == "__main__":
    def start_server():
        with socketserver.TCPServer(("", 8000), JarvisHandler) as httpd:
            print(Fore.GREEN + "[SYSTEM] HUD Server Online at http://localhost:8000")
            httpd.serve_forever()

    threading.Thread(target=start_server, daemon=True).start()

    boot_sequence()

    print(Fore.GREEN + "✅ JARVIS Mark 5 Fully Loaded & Ready!")

    while True:
        if is_speaking():
            time.sleep(0.1)
            continue

        try:
            raw_input = listen()

            if not raw_input or raw_input.strip() == "":
                continue

            print(f"USER: {raw_input}")

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
                speak("Yes Boss?")
                continue

            print(f"➤ ACTION: {clean_cmd.upper()}")

            reply = process_query(clean_cmd)

            if reply:
                print(f"🤖 JARVIS: {reply}")
                speak(reply)

        except Exception as e:
            print(Fore.RED + "[ERROR]")
            traceback.print_exc()