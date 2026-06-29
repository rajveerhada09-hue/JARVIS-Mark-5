"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : sandbox.py

PATH    : core\sandbox.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

# ==================================================
# FILE: core/sandbox.py
# JARVIS MARK 5 SECURITY ENGINE
# ==================================================

import json
import os

# ==================================================
# TRUST STORAGE
# ==================================================

TRUST_FILE = "core/memory/user_trust.json"


class Sandbox:

    def __init__(self):

        self.safe_keywords = [
            "youtube",
            "google",
            "instagram",
            "facebook",
            "chatgpt",
            "search",
            "open",
            "notepad",
            "calculator",
            "chrome",
            "vscode"
        ]

        self.medium_keywords = [
            "close",
            "taskkill",
            "volume",
            "mute",
            "screenshot",
            "lock"
        ]

        self.high_keywords = [
            "shutdown",
            "restart",
            "sleep"
        ]

        self.critical_keywords = [
            "format",
            "delete",
            "remove",
            "powershell",
            "cmd",
            "regedit",
            "system32",
            "diskpart",
            "netsh",
            "takeown",
            "bcdedit",
            "cipher",
            "attrib",
            "rd /s",
            "del /s",
            "rm -rf",
            "mkfs",
            "wipe",
            "factory reset"
        ]

        self.trust_score = self.load_trust()

    # ==================================================
    # TRUST SYSTEM
    # ==================================================

    def load_trust(self):

        if not os.path.exists(TRUST_FILE):

            os.makedirs(
                os.path.dirname(TRUST_FILE),
                exist_ok=True
            )

            with open(TRUST_FILE, "w") as f:
                json.dump({"trust": 50}, f)

            return 50

        try:

            with open(TRUST_FILE, "r") as f:
                data = json.load(f)

            return data.get("trust", 50)

        except:
            return 50

    def save_trust(self):

        with open(TRUST_FILE, "w") as f:
            json.dump(
                {"trust": self.trust_score},
                f,
                indent=4
            )

    def increase_trust(self, amount=1):

        self.trust_score = min(
            100,
            self.trust_score + amount
        )

        self.save_trust()

    def decrease_trust(self, amount=5):

        self.trust_score = max(
            0,
            self.trust_score - amount
        )

        self.save_trust()

    # ==================================================
    # RISK SCORING
    # ==================================================

    def classify(self, intent):

        if not isinstance(intent, dict):
            return 1

        intent_type = intent.get("type", "")
        text = str(intent.get("value", "")).lower()

        # ----------------------------------
        # BRAIN COMMANDS ARE ALWAYS SAFE
        # ----------------------------------
        if intent_type == "brain":
            return 0

        # SAFE
        if any(x in text for x in self.safe_keywords):
            return 0

        # LOW
        if any(x in text for x in self.medium_keywords):
            return 1

        # HIGH
        if any(x in text for x in self.high_keywords):
            return 2

        # CRITICAL
        if any(x in text for x in self.critical_keywords):
            return 4

        return 1

    # ==================================================
    # CONFIRMATION ENGINE
    # ==================================================

    def requires_confirmation(self, risk):

        if risk <= 1:
            return False

        if risk == 2:

            if self.trust_score >= 80:
                return False

            return True

        if risk >= 3:
            return True

        return False

    # ==================================================
    # RESPONSE ENGINE
    # ==================================================

    def explain_risk(self, risk):

        if risk == 0:
            return "Safe"

        if risk == 1:
            return "Low Risk"

        if risk == 2:
            return "High Risk"

        if risk >= 3:
            return "Critical Risk"

        return "Unknown"


# ==================================================
# GLOBAL INSTANCE
# ==================================================

sandbox = Sandbox()