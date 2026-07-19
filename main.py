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
from utils.logger import logger
from core.greeting_manager import time_aware_greeting
from core.startup_audio import play_startup_audio
from voice.stt.speech import listen
from voice.wakeword.wakeword import wait_for_wakeword
from voice.tts.voice import is_speaking, speak


warnings.filterwarnings("ignore")
init(autoreset=True)
load_dotenv()

CONFIG_PATH = "jarvis_config.json"
HUD_SERVER_PORT = 8000

kernel = Kernel()
stop_event = threading.Event()
conversation_mode = False
conversation_timeout = 0

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


def boot_sequence(config):
    try:
        print("Booting JARVIS...")

        kernel.initialize()

        greeting = time_aware_greeting(
            memory=kernel.get_service("memory")
        )

        speak(greeting)

        launch_hud()

        return True

    except Exception:
        logger.exception("Boot sequence failed")
        return False


def graceful_shutdown():
    print(Fore.YELLOW + "[SYSTEM] Shutting down...")
    try:
        kernel.shutdown()
    except Exception:
        pass
    stop_event.set()


def handle_shutdown(signum, frame):
    graceful_shutdown()


def run_voice_loop():
    global conversation_mode, conversation_timeout

    while not stop_event.is_set():

        try:

            # Wait until wake word is detected
            if not conversation_mode:
                wait_for_wakeword()
                conversation_mode = True
                conversation_timeout = time.time() + 40
                speak("Yes Sir?")

            if is_speaking():
                time.sleep(0.1)
                continue

            text = listen()

            if not text:
                if time.time() > conversation_timeout:
                    conversation_mode = False
                continue

            print(f"USER: {text}")

            reply = kernel.process_query(text)

            if reply:
                print(f"🤖 JARVIS: {reply}")
                speak(reply)

            conversation_timeout = time.time() + 40

        except Exception:
            logger.exception("Voice Loop Crash")


def main():
    config = load_config()
    

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    threading.Thread(
    target=safe_thread(start_hud_server),
    daemon=True
).start()
    boot_sequence(config)

    print(Fore.GREEN + "✅ JARVIS Mark 5 Fully Loaded & Ready!")
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