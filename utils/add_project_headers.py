"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : add_project_headers.py

PATH    : utils\add_project_headers.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import os
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================

PROJECT_ROOT = r"C:\Users\WINDOWS 11\Desktop\JARVIS"

PROJECT_NAME = "JARVIS MARK 5"

SUPPORTED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".html",
    ".css",
    ".json",
    ".md"
}

SKIP_DIRS = {
    "venv",
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
    "node_modules",
    "dist",
    "build"
}

# ============================================================
# PURPOSE DATABASE
# ============================================================

PURPOSES = {

    "main.py":
        "Application entry point. Boots the complete JARVIS operating system, initializes all core modules, launches the HUD and starts the voice loop.",

    "brain.py":
        "Central intelligence module responsible for reasoning, decision making, tool selection and orchestration.",

    "conversation_engine.py":
        "Handles natural conversations, context management, personality flow and response generation.",

    "voice.py":
        "Controls voice playback, speech queue, interruption, resume and speaking state.",

    "tts.py":
        

    "speech.py"
        "Captures microphone input and converts speech into text.",

    "intent_engine.py":
        "Classifies user intent and routes commands to the correct subsystem.",

    "tool_manager.py":
        "Executes tools and automation requested by the Intent Engine.",

    "context_engine.py":
        "Maintains conversational context and retrieves relevant information.",

    "context_manager.py":
        "Stores and updates runtime conversation context.",

    "memory_manager.py":
        "Coordinates short-term, long-term and semantic memory.",

    "memory_engine.py":
        "Primary memory processing engine.",

    "mem0_adapter.py":
        "Provides local Mem0 semantic memory integration.",

    "observer.py":
        "Monitors the system continuously and generates proactive suggestions.",

    "system_monitor.py":
        "Collects CPU, RAM, GPU, battery and operating system statistics.",

    "emotion_detector.py":
        "Detects emotional tone from user conversations.",

    "greeting_manager.py":
        "Creates dynamic greetings based on time, context and previous interactions.",

    "persona_engine.py":
        "Controls personality modes and communication behaviour.",

    "human_layer.py":
        "Makes responses natural, conversational and human-like.",

    "response_variations.py":
        "Generates varied responses to reduce repetition.",

    "profile_manager.py":
        "Stores user profile and long-term preferences.",

    "widget_manager.py":
        "Controls HUD widget lifecycle and communication.",

    "vision.py":
        "Processes webcam input and computer vision tasks.",

    "browser_control.py":
        "Handles browser automation and web interactions.",

    "pc_control.py":
        "Controls desktop applications and operating system functions.",

    "automation.js":
        "Node.js automation bridge for fast desktop control.",

    "script.js":
        "Main Electron HUD frontend logic.",

    "online_mode.js":
        "Controls Online Mode interface and widgets.",

    "offline_mode.js":
        "Controls Offline Mode interface.",

    "processor_mode.js":
        "Controls Mission Control / Processor diagnostics interface.",

    "transition_manager.js":
        "Handles HUD transitions and visual animations.",

    "widget_engine.js":
        "Creates, updates and manages draggable HUD widgets."
}

# ============================================================
# HEADER
# ============================================================

def make_header(filename, relative_path):

    purpose = PURPOSES.get(
        filename,
        "Module description pending."
    )

    date = datetime.now().strftime("%Y-%m-%d")

    if filename.endswith(".py"):

        return f'''"""
============================================================
PROJECT : {PROJECT_NAME}

FILE    : {filename}

PATH    : {relative_path}

PURPOSE :
{purpose}

LAST UPDATED :
{date}

============================================================
"""

'''

    else:

        return f'''/*
============================================================
PROJECT : {PROJECT_NAME}

FILE    : {filename}

PATH    : {relative_path}

PURPOSE :
{purpose}

LAST UPDATED :
{date}

============================================================
*/

'''

# ============================================================
# MAIN
# ============================================================

updated = 0
skipped = 0

for root, dirs, files in os.walk(PROJECT_ROOT):

    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]

    for file in files:

        ext = os.path.splitext(file)[1].lower()

        if ext not in SUPPORTED_EXTENSIONS:
            continue

        filepath = os.path.join(root, file)
        relative = os.path.relpath(filepath, PROJECT_ROOT)

        try:

            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()

            if "PROJECT :" in content[:500]:
                skipped += 1
                print(f"Skipped : {relative}")
                continue

            header = make_header(file, relative)

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(header + content)

            updated += 1
            print(f"Updated : {relative}")

        except Exception as e:
            print(f"Error : {relative}")
            print(e)

print("\n=========================================")
print(f"Updated : {updated}")
print(f"Skipped : {skipped}")
print("Done.")
print("=========================================")
