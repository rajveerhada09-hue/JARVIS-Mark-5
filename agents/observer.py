"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : observer.py
PATH    : core\observer.py

CHANGES vs original:
  1. Refactored monitor_user_activity() to use EnvironmentEngine instead
     of duplicating psutil/battery logic.
  2. Removed OCR/screen capture from the background loop — it was causing
     high CPU usage and is not needed for proactive alerts.
  3. Added cooldown tracking — each alert type fires at most once per
     ALERT_COOLDOWN_SECONDS to prevent spam.
  4. Added speak_callback parameter so alerts reach TTS without circular imports.
  5. Original check_system_health(), load_habits(), save_habit()
     functions preserved for backward compatibility.
  6. monitor_user_activity() now designed to run as a daemon thread.
  7. All imports that were already in requirements.txt retained.
============================================================
"""

import json
import os
import time
import traceback
import threading
from typing import Callable, Optional

import psutil

from core.environment_engine import EnvironmentEngine

HABIT_FILE             = "memory/habits.json"
ALERT_COOLDOWN_SECONDS = 300   # 5 minutes minimum between same-type alerts
IDLE_ALERT_MINUTES     = 45    # Alert after 45 minutes of no voice activity
HIGH_CPU_THRESHOLD     = 85    # % CPU usage to trigger alert
CHECK_INTERVAL         = 30    # seconds between each observation cycle

os.makedirs("memory", exist_ok=True)

# ── Cooldown tracker ──────────────────────────────────────────────────────────
_last_alert: dict = {}

def _can_alert(alert_type: str) -> bool:
    now  = time.time()
    last = _last_alert.get(alert_type, 0)
    if now - last >= ALERT_COOLDOWN_SECONDS:
        _last_alert[alert_type] = now
        return True
    return False


# ── Original functions (signatures preserved) ─────────────────────────────────

def check_system_health() -> list:
    """Original function — preserved for backward compatibility."""
    try:
        battery = psutil.sensors_battery()
        if battery is None:
            return []
        percent      = battery.percent
        power_plugged = battery.power_plugged
        alerts = []
        if percent < 20 and not power_plugged:
            alerts.append(f"Warning Sir: Battery is low at {percent} percent. Please connect the power supply.")
        if percent == 100 and power_plugged:
            alerts.append("Notification Sir: Battery is fully charged. You may disconnect the charger.")
        return alerts
    except Exception:
        return []


def load_habits() -> list:
    """Original function — preserved."""
    if os.path.exists(HABIT_FILE):
        try:
            with open(HABIT_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_habit(action: dict) -> None:
    """Original function — preserved."""
    habits = load_habits()
    habits.append({"time": time.time(), "action": action})
    # Keep last 200 habits only to prevent unbounded growth
    habits = habits[-200:]
    try:
        with open(HABIT_FILE, "w") as f:
            json.dump(habits, f, indent=2)
    except Exception:
        pass


# ── Active window (Windows-safe) ──────────────────────────────────────────────
def get_active_window() -> str:
    try:
        import pygetwindow as gw
        win = gw.getActiveWindow()
        return win.title if win else "Unknown"
    except Exception:
        return "Unknown"


# ── Main observer loop ────────────────────────────────────────────────────────
def monitor_user_activity(
    interval:        int                      = CHECK_INTERVAL,
    speak_callback:  Optional[Callable]       = None,
    activity_event:  Optional[threading.Event] = None,
) -> None:
    """
    Runs as a daemon thread.

    Parameters
    ----------
    interval        : seconds between each check cycle
    speak_callback  : function(text: str) to deliver proactive alerts via TTS
    activity_event  : threading.Event set by main loop on each user utterance,
                      used to measure idle time accurately
    """
    env              = EnvironmentEngine()
    _idle_alerted    = False

    def _speak(text: str) -> None:
        if speak_callback:
            try:
                speak_callback(text)
            except Exception:
                pass
        else:
            print(f"[OBSERVER] {text}")

    while True:
        try:
            # ── Battery ──────────────────────────────────────────────────────
            if env.low_battery() and _can_alert("battery"):
                battery = psutil.sensors_battery()
                pct     = int(battery.percent) if battery else 0
                _speak(f"Sir, battery {pct} percent pe hai. Charger lagao.")

            # ── High CPU ─────────────────────────────────────────────────────
            try:
                cpu = psutil.cpu_percent(interval=1)
                if cpu >= HIGH_CPU_THRESHOLD and _can_alert("high_cpu"):
                    _speak(f"Sir, CPU {int(cpu)} percent pe hai. Kuch heavy process chal raha hai.")
            except Exception:
                pass

            # ── Internet ─────────────────────────────────────────────────────
            if not env.internet_connected() and _can_alert("no_internet"):
                _speak("Sir, internet connection nahi hai. Check karo.")

            # ── Idle time ────────────────────────────────────────────────────
            if activity_event is not None:
                # activity_event is cleared on each voice command by main.py
                idle_secs = env.idle_time_seconds()
                if idle_secs >= IDLE_ALERT_MINUTES * 60 and _can_alert("idle"):
                    _speak(
                        f"Sir, {int(idle_secs // 60)} minutes se koi activity nahi. "
                        "Break le lo ya batao kya karna hai."
                    )

            # ── Active window habit tracking ─────────────────────────────────
            try:
                app_name = get_active_window()
                save_habit({"app": app_name, "time": time.time()})
            except Exception:
                pass

            time.sleep(interval)

        except Exception as e:
            print(f"[OBSERVER ERROR] {e}")
            time.sleep(interval)