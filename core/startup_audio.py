import os
import subprocess
import threading
import webbrowser


_STARTUP_TRACK_URL = "https://open.spotify.com/track/39shmbIHICJ2Wxnk1fPSdz"
_STARTUP_AUDIO_LOCK = threading.Lock()
_STARTUP_AUDIO_STOP_EVENT = threading.Event()
_STARTUP_AUDIO_THREAD = None


def _launch_spotify_desktop():
    try:
        spotify_path = None
        candidates = [
            r"C:\Program Files\Spotify\Spotify.exe",
            r"C:\Users\%USERNAME%\AppData\Roaming\Spotify\Spotify.exe",
        ]

        for candidate in candidates:
            expanded = os.path.expandvars(candidate)
            if os.path.exists(expanded):
                spotify_path = expanded
                break

        if spotify_path:
            subprocess.Popen([spotify_path, "--start-minimized"], shell=True)
            return True

        return False
    except Exception:
        return False


def _set_spotify_volume(low: bool = True):
    try:
        if os.name != "nt":
            return False
        subprocess.run(["cmd", "/c", "powershell", "-NoProfile", "-Command", "(New-Object -ComObject WScript.Shell).SendKeys('%')"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


def _run_startup_audio():
    try:
        _STARTUP_AUDIO_STOP_EVENT.clear()
        if _launch_spotify_desktop():
            webbrowser.open(_STARTUP_TRACK_URL)
        else:
            webbrowser.open(_STARTUP_TRACK_URL)

        print("[AUDIO] Startup track launched (Spotify)")
        _set_spotify_volume(True)

        while not _STARTUP_AUDIO_STOP_EVENT.is_set():
            if os.name == "nt":
                subprocess.run(["tasklist", "/FI", "IMAGENAME eq Spotify.exe"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["pgrep", "-f", "Spotify"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            _STARTUP_AUDIO_STOP_EVENT.wait(5)

        if not _STARTUP_AUDIO_STOP_EVENT.is_set():
            stop_startup_audio()
        else:
            print("[AUDIO] Startup track stopped manually")
    except Exception as exc:
        print(f"[AUDIO ERROR] {exc}")
    finally:
        with _STARTUP_AUDIO_LOCK:
            global _STARTUP_AUDIO_THREAD
            if _STARTUP_AUDIO_THREAD is not None and _STARTUP_AUDIO_THREAD.is_alive():
                _STARTUP_AUDIO_THREAD = None


def play_startup_audio():
    with _STARTUP_AUDIO_LOCK:
        global _STARTUP_AUDIO_THREAD
        if _STARTUP_AUDIO_THREAD is not None and _STARTUP_AUDIO_THREAD.is_alive():
            return

        _STARTUP_AUDIO_STOP_EVENT.clear()
        _STARTUP_AUDIO_THREAD = threading.Thread(target=_run_startup_audio, daemon=True)
        _STARTUP_AUDIO_THREAD.start()


def stop_startup_audio():
    _STARTUP_AUDIO_STOP_EVENT.set()
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/F", "/IM", "Spotify.exe"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def is_startup_audio_playing():
    return _STARTUP_AUDIO_THREAD is not None and _STARTUP_AUDIO_THREAD.is_alive() and not _STARTUP_AUDIO_STOP_EVENT.is_set()