"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : persona_engine.py
PATH    : core\personality\persona_engine.py

CHANGES vs original:
  1. Added 'showcase' mode for demo presentations.
  2. Added 'focused' mode for deep work sessions.
  3. Expanded keyword lists for better detection accuracy.
  4. style_injection() now returns richer prompts per mode.
  5. All original method signatures preserved (detect_mode, style_injection).
  6. self.mode default remains "normal".
============================================================
"""

import random


class PersonaEngine:
    def __init__(self):
        self.mode = "normal"

    def detect_mode(self, user_input: str) -> str:
        """Detect persona mode from user input. Original signature preserved."""
        q = user_input.lower()

        # SHOWCASE MODE
        if any(x in q for x in [
            "show you to", "introducing", "my friend", "my father", "my dad",
            "my mom", "my family", "meet jarvis", "wants to see", "presenting",
        ]):
            self.mode = "showcase"
            return self.mode

        # FRIEND / EMOTIONAL MODE
        if any(x in q for x in [
            "bro", "bhai", "yaar", "help me", "sad", "tired", "lonely",
            "frustrated", "upset", "stressed", "need motivation",
        ]):
            self.mode = "friend"
            return self.mode

        # ADMIN / SYSTEM MODE
        if any(x in q for x in [
            "system", "cpu", "ram", "diagnostic", "error", "log",
            "performance", "status", "debug", "stack", "trace", "exception",
            "architecture", "deploy", "server", "database", "api", "backend",
        ]):
            self.mode = "admin"
            return self.mode

        # FOCUSED / DEEP WORK MODE
        if any(x in q for x in [
            "focus", "deep work", "no distraction", "work mode",
            "concentrate", "building", "coding session",
        ]):
            self.mode = "focused"
            return self.mode

        self.mode = "normal"
        return self.mode

    def style_injection(self) -> str:
        """Return style hints to inject into the LLM prompt. Original signature preserved."""
        if self.mode == "friend":
            return (
                "Tone: Friendly, casual, human-like, slightly relaxed. "
                "Reply in natural Hinglish. Be warm, brief, and never robotic. "
                "User might be emotional — respond with calm support."
            )
        if self.mode == "admin":
            return (
                "Tone: System administrator mode. "
                "Be precise, analytical, structured. "
                "Use English for technical explanations. "
                "Do NOT hallucinate. No emotional language. "
                "Be direct and solution-focused."
            )
        if self.mode == "showcase":
            return (
                "Tone: Professional, confident, impressive. "
                "Speak in clean English. Be articulate. "
                "Represent the project professionally. "
                "Mention being built by Rajveer Singh Rajput if relevant. "
                "Never be arrogant — be quietly impressive."
            )
        if self.mode == "focused":
            return (
                "Tone: Minimal. No small talk. "
                "Respond only with what is needed. "
                "Keep it short. Respect the work session."
            )
        # normal / default
        return (
            "Tone: Balanced assistant mode. Natural, slightly conversational, controlled intelligence. "
            "Default language: Hinglish for casual topics, English for professional/technical. "
            "Never sound like ChatGPT. Never use filler phrases."
        )