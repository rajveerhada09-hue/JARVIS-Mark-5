"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : config.py

PATH    : utils/config.py

PURPOSE :
Central configuration manager for the entire JARVIS system.
Loads, validates and auto-generates jarvis_config.json.

LAST UPDATED :
2026-06-30
============================================================
"""

import json
import os
from pathlib import Path

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CONFIG_PATH = PROJECT_ROOT / "jarvis_config.json"

# ============================================================
# DEFAULT CONFIG
# ============================================================

DEFAULT_CONFIG = {

    # --------------------------------------------------------
    # Identity
    # --------------------------------------------------------

    "assistant_name": "JARVIS Mark V",
    "user_name": "Rajveer",

    # --------------------------------------------------------
    # Wake Word
    # --------------------------------------------------------

    "wake_words": [
        "jarvis",
        "jarves",
        "jarvice",
        "jarwis",
        "jervis",
        "garvis",
        "hey jarvis"
        "jarvice"
    ],

    # --------------------------------------------------------
    # AI Models
    # --------------------------------------------------------

    "model_primary": "gemini-2.5-flash",
    "model_fallback": "",

    # --------------------------------------------------------
    # Voice
    # --------------------------------------------------------

    "voice_provider": "",

    "voice_id": "",

    "voice_rate": 135,

    "voice_volume": 1.0,

    "voice_interrupt": True,

    "voice_cache_dir": ".voice_cache",

    # --------------------------------------------------------
    # Startup
    # --------------------------------------------------------

    "startup_audio": True,

    "startup_audio_volume": 25,

    # --------------------------------------------------------
    # Memory
    # --------------------------------------------------------

    "memory_enabled": True,

    "memory_file": "memory_db.json",

    # --------------------------------------------------------
    # HUD
    # --------------------------------------------------------

    "hud_enabled": True,

    "hud_port": 8000,

    # --------------------------------------------------------
    # Modes
    # --------------------------------------------------------

    "offline_mode": False,

    # --------------------------------------------------------
    # Directories
    # --------------------------------------------------------

    "cache_dir": ".voice_cache",

    "log_dir": "logs",

    "models_dir": "models"
}


# ============================================================
# SAVE CONFIG
# ============================================================

def save_config(config: dict):

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)


# ============================================================
# LOAD CONFIG
# ============================================================

def load_config():

    if not CONFIG_PATH.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    try:

        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)

    except Exception:

        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()

    # Auto-add newly introduced keys
    updated = False

    for key, value in DEFAULT_CONFIG.items():

        if key not in config:
            config[key] = value
            updated = True

    if updated:
        save_config(config)

    return config


# ============================================================
# GLOBAL CONFIG
# ============================================================

CONFIG = load_config()


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get(key, default=None):
    return CONFIG.get(key, default)


def set(key, value):

    CONFIG[key] = value

    save_config(CONFIG)


def reload():

    global CONFIG

    CONFIG = load_config()

    return CONFIG