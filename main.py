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
from core.hud_client import send_hud_state, send_hud_stats, send_hud_message, send_hud_notification, send_hud_provider_status
from utils.logger import logger
from core.greeting_manager import time_aware_greeting
from core.startup_audio import play_startup_audio
from voice.stt.speech import listen, get_stt_status
from voice.wakeword.wakeword import wait_for_wakeword
from voice.tts.voice import is_speaking, speak
from core.system_monitor import get_system_stats

warnings.filterwarnings("ignore")
init(autoreset=True)
load_dotenv()

CONFIG_PATH = "jarvis_config.json"
HUD_SERVER_PORT = 8000

kernel = Kernel()
stop_event = threading.Event()
conversation_mode = False
conversation_timeout = 0

# Stats update thread
_stats_thread = None
_stats_running = False


def global_exception(exc_type, exc_value, exc_traceback):
    logger.exception(
        "UNCAUGHT EXCEPTION",
        exc_info=(exc_type, exc_value, exc_traceback),
    )
    sys.__excepthook__(exc_type, exc_value, exc_traceback)


sys.excepthook = global_exception


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
    except Exception:
        logger.exception("HUD Server Crash")


def launch_hud():
    try:
        hud_path = os.path.join(os.getcwd(), "hud", "electron")
        if os.path.exists(hud_path):
            subprocess.Popen(["npm", "start"], cwd=hud_path, shell=True)
            print(Fore.GREEN + "[HUD] Electron HUD launched.")
    except Exception as exc:
        logger.exception("HUD Launch Failed")
        print(Fore.RED + f"[HUD ERROR] {exc}")


def start_startup_audio():
    threading.Thread(
        target=play_startup_audio,
        daemon=True
    ).start()


def safe_thread(target):
    def wrapper():
        try:
            target()
        except Exception:
            logger.exception("THREAD CRASH")
    return wrapper


def _stats_loop():
    """Background thread to send system stats to HUD"""
    global _stats_running
    _stats_running = True
    while _stats_running and not stop_event.is_set():
        try:
            stats_str = get_system_stats()
            # Parse the stats string into a dict
            stats = {}
            for part in stats_str.split(" | "):
                if ": " in part:
                    key, val = part.split(": ", 1)
                    stats[key.lower().replace(" ", "_")] = val.replace("%", "")
            send_hud_stats(stats)
        except Exception:
            pass
        time.sleep(2)


def start_stats_thread():
    global _stats_thread
    if _stats_thread is None or not _stats_thread.is_alive():
        _stats_thread = threading.Thread(target=_stats_loop, daemon=True)
        _stats_thread.start()


def stop_stats_thread():
    global _stats_running
    _stats_running = False


def boot_sequence(config):
    try:
        print("Booting JARVIS...")

        kernel.initialize()

        # Send initial provider status to HUD
        stt_status = get_stt_status()
        send_hud_provider_status(
            stt_status.get("current_provider", "unknown"),
            stt_status.get("available_providers", [])
        )

        greeting = time_aware_greeting(
            memory=kernel.get_service("memory")
        )

        send_hud_state("speaking")
        send_hud_message("assistant", greeting)
        speak(greeting)

        start_stats_thread()

        send_hud_state("idle")
        send_hud_notification("JARVIS Mark 5 systems online")

        return True

    except Exception:
        logger.exception("Boot sequence failed")
        return False


def graceful_shutdown():
    print(Fore.YELLOW + "[SYSTEM] Shutting down...")
    stop_stats_thread()
    try:
        kernel.shutdown()
    except Exception:
        pass
    send_hud_state("offline")
    stop_event.set()


def handle_shutdown(signum, frame):
    graceful_shutdown()


def run_voice_loop():
    global conversation_mode, conversation_timeout

    while not stop_event.is_set():
        try:
            # Wait until wake word is detected
            if not conversation_mode:
                send_hud_state("idle")
                wait_for_wakeword()
                conversation_mode = True
                conversation_timeout = time.time() + 40
                send_hud_state("listening")
                send_hud_notification("Listening...")
                speak("Yes Sir?")

            if is_speaking():
                time.sleep(0.1)
                continue

            send_hud_state("listening")
            text = listen()

            if not text:
                if time.time() > conversation_timeout:
                    conversation_mode = False
                continue

            send_hud_state("thinking")
            send_hud_message("user", text)
            print(f"USER: {text}")

            reply = kernel.process_query(text)

            if reply:
                send_hud_state("speaking")
                send_hud_message("assistant", reply)
                print(f"[BOT] JARVIS: {reply}")
                speak(reply)

            conversation_timeout = time.time() + 40

        except Exception:
            logger.exception("Voice Loop Crash")
            send_hud_state("error")
            time.sleep(1)


def main():
    config = load_config()

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    threading.Thread(
        target=safe_thread(start_hud_server),
        daemon=True
    ).start()

    boot_sequence(config)

    print(Fore.GREEN + "[OK] JARVIS Mark 5 Fully Loaded & Ready!")
    run_voice_loop()
    graceful_shutdown()


if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        graceful_shutdown()

    except Exception as e:
        logger.exception("FATAL SYSTEM CRASH")
        traceback.print_exc()

    finally:
        sys.exit(0)