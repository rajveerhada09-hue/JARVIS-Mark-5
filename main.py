"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : main.py

PURPOSE : Bootstrap layer only. Initializes the kernel and runs the voice loop.
============================================================
"""

import json
import os
import signal
import subprocess
import sys
import threading
import time
import traceback
import warnings
from http.server import SimpleHTTPRequestHandler
from socketserver import TCPServer

from colorama import Fore, init
from dotenv import load_dotenv

from core.kernel import Kernel
from core.greeting_manager import time_aware_greeting
from core.startup_audio import play_startup_audio
from voice.speech import listen
from voice.voice import is_speaking, speak

warnings.filterwarnings("ignore")
init(autoreset=True)
load_dotenv()

CONFIG_PATH = "jarvis_config.json"
HUD_SERVER_PORT = 8000
DEFAULT_WAKE_WORDS = ["jarvis", "jarves", "jervis", "jarvice", "jarwis", "service", "garvis", "hey jarvis"]

kernel = Kernel()
stop_event = threading.Event()
conversation_mode = False
conversation_timeout = 0


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            return json.load(handle)
    except Exception:
        return {}


def start_hud_server():
    class JarvisHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            return

        def do_GET(self):
            if self.path == "/get_hud_data":
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                try:
                    with open("hud_status.json", "r", encoding="utf-8") as handle:
                        self.wfile.write(handle.read().encode())
                except Exception:
                    self.wfile.write(json.dumps({"jarvis_state": "idle", "text": "Offline"}).encode())
            else:
                return super().do_GET()

    try:
        with TCPServer(("", HUD_SERVER_PORT), JarvisHandler) as httpd:
            print(Fore.GREEN + f"[SYSTEM] HUD Server Online at http://localhost:{HUD_SERVER_PORT}")
            httpd.serve_forever()
    except Exception as exc:
        print(Fore.RED + f"[HUD SERVER ERROR] {exc}")


def launch_hud():
    try:
        hud_path = os.path.join(os.getcwd(), "hud", "electron")
        if os.path.exists(hud_path):
            subprocess.Popen(["npm", "start"], cwd=hud_path, shell=True)
            print(Fore.GREEN + "[HUD] Electron HUD launched.")
    except Exception as exc:
        print(Fore.RED + f"[HUD ERROR] {exc}")


#def start_startup_audio():
    #threading.Thread(target=play_startup_audio, daemon=True).start()


def boot_sequence(config):
    print("Booting JARVIS...")

    kernel.initialize()
    #start_startup_audio()

    try:
        greeting = time_aware_greeting(
            memory=kernel.get_service("memory")
        )

        speak(greeting)

    except Exception as exc:
        print(Fore.YELLOW + f"[BOOT] Greeting skipped: {exc}")

    launch_hud()
    return True


def graceful_shutdown():
    print(Fore.YELLOW + "[SYSTEM] Shutting down...")
    try:
        kernel.shutdown()
    except Exception:
        pass
    stop_event.set()


def handle_shutdown(signum, frame):
    graceful_shutdown()


def run_voice_loop(wake_words):
    global conversation_mode, conversation_timeout

    while not stop_event.is_set():
        if is_speaking():
            time.sleep(0.1)
            continue

        try:
            raw_input = listen()
            if not raw_input or not raw_input.strip():
                continue

            print(f"USER: {raw_input}")
            clean_cmd = raw_input.lower().strip()

            current_time = time.time()
            is_wake = (conversation_mode and current_time < conversation_timeout) or any(word in clean_cmd for word in wake_words)

            if not is_wake:
                continue

            for word in wake_words:
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

        except KeyboardInterrupt:
            break
        except Exception:
            print(Fore.RED + "[ERROR]")
            traceback.print_exc()


def main():
    config = load_config()
    wake_words = config.get("wake_words", DEFAULT_WAKE_WORDS)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    threading.Thread(target=start_hud_server, daemon=True).start()
    boot_sequence(config)

    print(Fore.GREEN + "✅ JARVIS Mark 5 Fully Loaded & Ready!")
    run_voice_loop(wake_words)
    graceful_shutdown()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        graceful_shutdown()
    finally:
        sys.exit(0)