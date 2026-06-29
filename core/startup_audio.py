import time
import threading
import subprocess
import os

SPOTIFY_TRACK_URL = "https://open.spotify.com/track/39shmbIHICJ2Wxnk1fPSdz"

def play_spotify_intro():
    try:
        # Open Spotify track
        subprocess.Popen(f'start {SPOTIFY_TRACK_URL}', shell=True)

        # let it load
        time.sleep(2)

        # 10 second timer
        time.sleep(10)

        # stop playback using media keys (Windows trick)
        import pyautogui

        pyautogui.press("playpause")

    except Exception as e:
        print(f"[AUDIO ERROR] {e}")


def start_intro_audio():
    t = threading.Thread(target=play_spotify_intro, daemon=True)
    t.start()