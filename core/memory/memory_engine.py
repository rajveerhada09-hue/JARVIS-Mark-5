"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : memory_engine.py

PATH    : core\memory\memory_engine.py

PURPOSE :
Primary memory processing engine.

LAST UPDATED :
2026-06-28

============================================================
"""

import json
import os
from datetime import datetime

BASE = "memory"


def _path(name):
    return os.path.join(BASE, name)


class MemoryEngine:

    def __init__(self):

        os.makedirs(BASE, exist_ok=True)
        os.makedirs(_path("conversations"), exist_ok=True)

        self.pattern_file = _path("learned_patterns.json")
        self.profile_file = _path("user_profile.json")
        self.command_file = _path("commands.json")
        self.memory_store_file = _path("memory_store.json")

    # -------------------------
    # QUICK LOG
    # -------------------------
    def log(self, text):
        self.log_conversation(
            text,
            "chat",
            ""
        )

    # -------------------------
    # PATTERN LEARNING
    # -------------------------
    def save_pattern(self, cmd, mapped):

        data = {}

        try:
            if os.path.exists(self.pattern_file):
                with open(self.pattern_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
        except:
            data = {}

        data[cmd] = mapped

        with open(self.pattern_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_pattern(self, cmd):

        if not os.path.exists(self.pattern_file):
            return cmd

        try:
            with open(self.pattern_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return data.get(cmd, cmd)

        except:
            return cmd

    # -------------------------
    # CONVERSATION LOGGING
    # -------------------------
    def log_conversation(self, user_input, intent, response):

        file = _path(
            f"conversations/{datetime.now().date()}.json"
        )

        try:

            if os.path.exists(file):
                with open(file, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            else:
                logs = []

            logs.append({
                "input": user_input,
                "intent": intent,
                "response": response,
                "time": str(datetime.now())
            })

            with open(file, "w", encoding="utf-8") as f:
                json.dump(logs, f, indent=2)

        except Exception:
            pass

    # -------------------------
    # CONTEXT RETRIEVAL
    # -------------------------
    def get_context(self, limit=10):

        file = _path(
            f"conversations/{datetime.now().date()}.json"
        )

        if not os.path.exists(file):
            return ""

        try:

            with open(file, "r", encoding="utf-8") as f:
                logs = json.load(f)

            context = ""

            for item in logs[-limit:]:

                user_msg = item.get("input", "")
                bot_msg = item.get("response", "")

                context += (
                    f"User: {user_msg}\n"
                    f"Jarvis: {bot_msg}\n\n"
                )

            return context

        except:
            return ""

    # -------------------------
    # USER PROFILE
    # -------------------------
    def save_user_data(self, key, value):

        data = {}

        try:
            if os.path.exists(self.profile_file):
                with open(self.profile_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
        except:
            data = {}

        data[key] = value

        with open(self.profile_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def get_user_data(self, key, default=None):

        if not os.path.exists(self.profile_file):
            return default

        try:
            with open(self.profile_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return data.get(key, default)

        except:
            return default

    # -------------------------
    # COMMAND TRACKING
    # -------------------------
    def save_command(self, command):

        data = {}

        try:
            if os.path.exists(self.command_file):
                with open(self.command_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
        except:
            data = {}

        data[command] = data.get(command, 0) + 1

        with open(self.command_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    # -------------------------
    # MEMORY STORE
    # -------------------------
    def remember(self, key, value):

        data = {}

        try:
            if os.path.exists(self.memory_store_file):
                with open(self.memory_store_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
        except:
            data = {}

        data[key] = value

        with open(self.memory_store_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def recall(self, key, default=None):

        if not os.path.exists(self.memory_store_file):
            return default

        try:
            with open(self.memory_store_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            return data.get(key, default)

        except:
            return default