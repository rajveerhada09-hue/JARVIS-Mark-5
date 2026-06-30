"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : main.py

PURPOSE : Bootstrap layer only. Initializes kernel and runs voice loop.
============================================================
"""

import warnings
warnings.filterwarnings("ignore")

import threading
import time
import os
import subprocess
import sys
import json
import datetime
import traceback

from http.server import SimpleHTTPRequestHandler
import socketserver
from colorama import init, Fore, Style
from dotenv import load_dotenv
from voice.voice import listen

# Core Imports
from core.kernel import Kernel
from voice.voice import speak, is_speaking

init(autoreset=True)
load_dotenv()

# ====================== KERNEL (Central Orchestrator) ======================
kernel = Kernel()

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
# BOOT SEQUENCE
# ===================================================================
def boot_sequence():
    os.system('cls' if os.name == 'nt' else 'clear')

    print(Fore.CYAN + Style.BRIGHT + "JARVIS MARK 5 : INITIATING MEGA CORE...")

    kernel.initialize()

    update_hud_state("idle", "SYSTEM ONLINE")

    speak(kernel.get_greeting())

    try:
        hud_path = os.path.join(os.getcwd(), "hud", "electron")
        if os.path.exists(hud_path):
            subprocess.Popen(["npm", "start"], cwd=hud_path, shell=True)
            print(Fore.GREEN + "[HUD] Electron HUD launched.")
    except Exception as e:
        print(Fore.RED + f"[HUD ERROR] {e}")

    try:
        from core.kernel import Kernel
    except Exception as e:
        print("[KERNEL ERROR]", e)
        exit()
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

            reply = kernel.process_query(clean_cmd)

            if reply:
                print(f"🤖 JARVIS: {reply}")
                speak(reply)

        except Exception as e:
            print(Fore.RED + "[ERROR]")
            traceback.print_exc()