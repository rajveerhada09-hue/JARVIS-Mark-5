"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : pc_control.py

PATH    : core\pc_control.py

PURPOSE :
Controls desktop applications and operating system functions.

LAST UPDATED :
2026-06-28

============================================================
"""

import os
import subprocess
import pyautogui
import psutil
import ctypes
import sys
import io
from voice.voice import speak

APPS = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "vscode": "code",
    "notepad": "notepad",
    "chrome": "chrome",
    "calculator": "calc"
}

def call_node_engine(command, argument=""):
    """Python-to-Node Bridge linking with automation/automation.js"""
    try:
        script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'automation', 'automation.js')
        subprocess.Popen(['node', script_path, command, argument], shell=True)
    except Exception as e:
        print(f"Bhai, Node Engine Error: {e}")
        os.system(f"start {argument}")

def open_app(query):
    query = query.lower().strip()
    if query in APPS:
        speak(f"Opening {query}, Boss.")
        call_node_engine("open_app", APPS[query])
    else:
        speak(f"Searching for {query} on your environment.")
        call_node_engine("open_app", query)

def system_status():
    cpu = psutil.cpu_percent()
    ram = psutil.virtual_memory().percent
    report = f"Boss, the CPU utilization stands at {cpu} percent, while the memory load is at {ram} percent."
    speak(report)
    return report

def volume_control(action):
    if action == "up":
        for _ in range(5): pyautogui.press("volumeup")
    elif action == "down":
        for _ in range(5): pyautogui.press("volumedown")
    speak("Adjustment complete, Boss.")

def lock_pc():
    speak("Securing the primary workstation immediately, Boss.")
    ctypes.windll.user32.LockWorkStation()

# =========================================================================
# 🔥 THE AUTONOMOUS CODE EXECUTOR
# =========================================================================
def execute_autonomous_logic(generated_python_code):
    """Executes dynamic on-the-fly synthesized code inside the workspace safely."""
    dangerous_keywords = ["rmdir /s", "del /f", "format", "system32", "os.environ"]
    if any(keyword in generated_python_code.lower() for keyword in dangerous_keywords):
        return "Operation terminated. The synthesized code violated safe operating procedures."

    old_stdout = sys.stdout
    redirected_output = sys.stdout = io.StringIO()
    
    try:
        local_vars = {
            "os": os, "pyautogui": pyautogui, "psutil": psutil,
            "subprocess": subprocess, "time": __import__("time"),
            "webbrowser": __import__("webbrowser"), "ctypes": ctypes
        }
        
        exec(generated_python_code, {"__builtins__": __import__("builtins")}, local_vars)
        
        sys.stdout = old_stdout
        execution_output = redirected_output.getvalue()
        return execution_output if execution_output else "Execution finalized successfully."
        
    except Exception as e:
        sys.stdout = old_stdout
        return f"Runtime error during script execution: {str(e)}"
    
def pc_control_master(cmd):

    cmd = cmd.lower().strip()

    # OPEN APPS
    if cmd.startswith("open "):

        app = cmd.replace("open ", "").strip()

        open_app(app)

        return f"Opening {app}, Boss."

    # SYSTEM STATUS
    elif "system status" in cmd:
        return system_status()

    # VOLUME
    elif "volume up" in cmd:
        volume_control("up")
        return "Volume increased."

    elif "volume down" in cmd:
        volume_control("down")
        return "Volume decreased."

    # LOCK
    elif "lock" in cmd:
        lock_pc()
        return "Locking workstation."

    # SHUTDOWN
    elif "shutdown" in cmd:
        os.system("shutdown /s /t 0")
        return "Shutting down the system."

    # RESTART
    elif "restart" in cmd:
        os.system("shutdown /r /t 0")
        return "Restarting the system."

    # SLEEP
    elif "sleep" in cmd:
        os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
        return "Entering sleep mode."

    return None