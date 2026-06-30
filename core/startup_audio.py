import time
import os
from voice.voice import speak

def play_startup_audio():
    try:
        import webbrowser

        url = "https://open.spotify.com/track/39shmbIHICJ2Wxnk1fPSdz"
        webbrowser.open(url)

        print("[AUDIO] Startup track launched (Spotify)")

        time.sleep(10)

        print("[AUDIO] 10s preview done")

    except Exception as e:
        print("[AUDIO ERROR]", e)