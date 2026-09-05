"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : intent_engine.py

PATH    : core\intent_engine.py

PURPOSE :
Classifies user intent and routes commands to the correct subsystem.

LAST UPDATED :
2026-06-28

============================================================
"""

import re
from typing import Dict

from core.command_router import route_command, normalize_command


class IntentEngine:
    """Intent classification layer for the Jarvis command pipeline.

    This engine is the single source of truth for supported intents.
    It uses the legacy command router only as a fallback classification helper.
    """

    SUPPORTED_INTENTS = [
        "conversation",
        "workspace",
        "browser",
        "automation",
        "memory",
        "research",
        "weather",
        "music",
        "maps",
        "coding",
        "vision",
        "planning",
        "pc",
        "unknown",
    ]

    def __init__(self):
        pass

    def normalize(self, raw_text: str) -> str:
        return normalize_command(raw_text)

    def classify(self, raw_text: str) -> Dict[str, object]:
        normalized = self.normalize(raw_text)
        text = normalized.lower().strip()

        if not text:
            return self._make_intent("unknown", "empty", text, 0.20)

        if self.is_multi_command(text):
            return self._make_intent("automation", "compound", text, 0.92)

        if any(phrase in text for phrase in ["good morning", "good afternoon", "good evening", "good night", "hello", "hi", "hey", "kaisa", "kya haal", "tum kaise", "tu kaisa"]):
            return self._make_intent("conversation", "greeting", text, 0.95)

        if any(phrase in text for phrase in ["open workspace", "open vscode", "open code", "workspace", "launch workspace", "open project", "open repo", "open folder", "code mode"]):
            return self._make_intent("workspace", "workspace", text, 0.98)

        if any(phrase in text for phrase in ["chatgpt", "claude", "grok", "perplexity", "open chatgpt", "open claude", "open grok", "open perplexity"]):
            return self._make_intent("workspace", "workspace", text, 0.96)

        if any(phrase in text for phrase in ["youtube", "google", "instagram", "facebook", "search", "open youtube", "open google"]):
            return self._make_intent("browser", "search", text, 0.92)

        if any(phrase in text for phrase in ["shutdown", "restart", "sleep", "lock", "sign out", "log off", "volume up", "volume down", "system status"]):
            return self._make_intent("pc", "system", text, 0.95)

        if any(phrase in text for phrase in ["play ", "spotify", "song", "music", "playlist", "playlists"]):
            return self._make_intent("music", "music", text, 0.90)

        if any(phrase in text for phrase in ["weather", "temperature", "rain", "sunny", "forecast", "climate"]):
            return self._make_intent("weather", "weather", text, 0.90)

        if any(phrase in text for phrase in ["map", "directions", "navigate", "route", "near me", "location"]):
            return self._make_intent("maps", "navigation", text, 0.90)

        if any(phrase in text for phrase in ["remember", "forget", "recall", "note", "memo", "remind"]):
            return self._make_intent("memory", "memory", text, 0.90)

        if any(phrase in text for phrase in ["research", "find out", "look up", "investigate", "analyze"]):
            return self._make_intent("research", "research", text, 0.88)

        if any(phrase in text for phrase in ["plan", "strategy", "roadmap", "organize", "schedule"]):
            return self._make_intent("planning", "planning", text, 0.88)

        if any(phrase in text for phrase in ["code", "develop", "write code", "implement", "debug", "fix", "refactor"]):
            return self._make_intent("coding", "coding", text, 0.88)

        if any(phrase in text for phrase in ["camera", "vision", "webcam", "photo", "scan", "detect"]):
            return self._make_intent("vision", "vision", text, 0.88)

        if any(phrase in text for phrase in ["what ", "who ", "why ", "how ", "when ", "where ", "explain", "tell me", "define", "describe"]):
            return self._make_intent("conversation", "question", text, 0.85)

        # Legacy keyword fallback
        fallback = route_command(text)
        intent_type = fallback.get("type", "unknown")
        confidence = float(fallback.get("confidence", 0.65))
        if intent_type == "brain":
            intent_type = "conversation"
        return self._make_intent(intent_type, fallback.get("category", "unknown"), text, confidence)

    def is_multi_command(self, raw_text: str) -> bool:
        if not raw_text:
            return False
        text = raw_text.lower()
        return " and " in text or " then " in text

    def _make_intent(self, intent_type: str, category: str, value: str, confidence: float) -> Dict[str, object]:
        if intent_type not in self.SUPPORTED_INTENTS:
            intent_type = "unknown"
        return {
            "type": intent_type,
            "category": category,
            "value": value,
            "confidence": round(min(max(confidence, 0.0), 1.0), 2),
        }
