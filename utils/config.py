"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : config.py

PATH    : utils\config.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import os
import json

CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', 'jarvis_config.json')

DEFAULT_CONFIG = {
    "assistant_name": "JARVIS Mark V",
    "user_name": "Rajveer",
    "wake_word": "jarvis",
    "model_primary": "gemini-pro",
    "model_fallback": "gpt-4-mini",
    "voice_accent": "en-uk",
    "memory_file": "memory_db.json"
}

def load_config():
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULT_CONFIG)
    with open(CONFIG_PATH, 'r') as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(data, f, indent=4)

CONFIG = load_config()
