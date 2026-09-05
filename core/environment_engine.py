"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : environment_engine.py

PATH    : core\environment_engine.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import os
import platform
import socket
import time
from typing import Dict

import psutil


class EnvironmentEngine:
    """Encapsulates environment and system awareness for Jarvis."""

    def __init__(self):
        self.os = platform.system()
        self.arch = platform.machine()
        self.python_version = platform.python_version()
        self.cwd = os.getcwd()
        self.last_active = time.time()

    def get_environment_snapshot(self) -> Dict[str, str]:
        return {
            "os": self.os,
            "architecture": self.arch,
            "python_version": self.python_version,
            "working_directory": self.cwd,
            "cpu_count": str(psutil.cpu_count(logical=True) or 0),
            "memory_total_gb": f"{psutil.virtual_memory().total / (1024 ** 3):.1f}",
        }

    def get_system_status(self) -> Dict[str, str]:
        memory = psutil.virtual_memory()
        return {
            "cpu_percent": f"{psutil.cpu_percent(interval=0.5)}",
            "memory_percent": f"{memory.percent}",
            "disk_percent": f"{psutil.disk_usage(self.cwd).percent}",
            "uptime_seconds": str(int(time.time() - psutil.boot_time())),
        }

    def is_morning(self) -> bool:
        hour = time.localtime().tm_hour
        return 5 <= hour < 12

    def is_afternoon(self) -> bool:
        hour = time.localtime().tm_hour
        return 12 <= hour < 17

    def is_evening(self) -> bool:
        hour = time.localtime().tm_hour
        return 17 <= hour < 22

    def internet_connected(self) -> bool:
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2).close()
            return True
        except OSError:
            return False

    def low_battery(self) -> bool:
        try:
            battery = psutil.sensors_battery()
            if battery is None:
                return False
            return battery.percent <= 20 and not battery.power_plugged
        except Exception:
            return False

    def current_app(self) -> str:
        try:
            if self.os == "Windows":
                import psutil
                for proc in psutil.process_iter(attrs=["name"]):
                    if proc.name().lower() in ["code.exe", "chrome.exe", "spotify.exe"]:
                        return proc.name()
            return "unknown"
        except Exception:
            return "unknown"

    def update_activity(self) -> None:
        self.last_active = time.time()

    def idle_time_seconds(self) -> float:
        return time.time() - self.last_active
