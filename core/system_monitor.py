"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : system_monitor.py

PATH    : core\system_monitor.py

PURPOSE :
Collects CPU, RAM, GPU, battery and operating system statistics.

LAST UPDATED :
2026-06-28

============================================================
"""

import psutil
import platform

def get_system_stats():
    # Ye function laptop ki details nikalta hai
    cpu_usage = psutil.cpu_percent(interval=1)
    ram_usage = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    battery_percent = battery.percent if battery else "N/A"
    
    stats = f"CPU: {cpu_usage}% | RAM: {ram_usage}% | Battery: {battery_percent}%"
    return stats