"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : command_router.py

PATH    : core\command_router.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import re


def normalize_command(cmd: str) -> str:
    if not cmd:
        return ""

    normalized = cmd.lower().strip()
    normalized = normalized.replace("’", "'")

    replacements = {
        r"\bwork ?space\b": "workspace",
        r"\bvisual studio code\b": "vscode",
        r"\bvisual studio\b": "vscode",
        r"\bvs ?code\b": "vscode",
        r"\bchat gpt\b": "chatgpt",
        r"\brestart computer\b": "restart pc",
        r"\bshutdown computer\b": "shutdown",
        r"\bshutdown pc\b": "shutdown",
        r"\bopen google search\b": "open google",
        r"\bstart coding\b": "open workspace",
        r"\bworkspace mode\b": "open workspace",
        r"\bcoding mode\b": "open workspace",
        r"\bdeveloper mode\b": "open workspace",
        r"\bwork mode\b": "open workspace",
        r"\blaunch workspace\b": "open workspace",
        r"\bopen development\b": "open workspace",
        r"\blet's code\b": "open workspace",
        r"\blets code\b": "open workspace",
    }

    for pattern, replacement in replacements.items():
        normalized = re.sub(pattern, replacement, normalized)

    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def route_command(cmd: str, gui=None, brain=None):
    """
    Main routing function for Jarvis.
    Returns a standardized intent dictionary.
    """

    cmd = normalize_command(cmd)

    if not cmd:
        return {
            "type": "brain",
            "category": "chat",
            "value": cmd,
            "confidence": 0.50,
        }

    # =================================================
    # 1. MULTI COMMAND DETECTION (AND / THEN)
    # =================================================
    if " and " in cmd or " then " in cmd:
        return {
            "type": "multi",
            "category": "compound",
            "value": cmd,
            "confidence": 0.90,
        }

    # =================================================
    # 2. WORKSPACE / CODING MODE
    # =================================================
    workspace_phrases = [
        "open workspace",
        "workspace",
        "start coding",
        "coding mode",
        "developer mode",
        "work mode",
        "launch workspace",
        "open development",
        "open project",
        "open repo",
        "open folder",
    ]

    if any(phrase in cmd for phrase in workspace_phrases):
        return {
            "type": "workspace",
            "category": "workspace",
            "value": cmd,
            "confidence": 0.96,
        }

    # =================================================
    # 3. SCHEDULED TASKS
    # =================================================
    if any(x in cmd for x in ["after", "minute", "minutes", "schedule"]):
        return {
            "type": "brain",
            "category": "scheduled_task",
            "value": cmd,
            "confidence": 0.75,
        }

    # =================================================
    # 4. APP OPENING (MULTI SAFE PARSER)
    # =================================================
    if cmd.startswith("open "):
        cleaned = cmd.replace("open ", "").strip()

        if cleaned in ["workspace", "vscode", "visual studio code", "visual studio"]:
            return {
                "type": "workspace",
                "category": "workspace",
                "value": cmd,
                "confidence": 0.95,
            }

        separators = [" and ", ",", " & "]
        apps = [cleaned]

        for sep in separators:
            temp = []
            for item in apps:
                if sep in item:
                    temp.extend([x.strip() for x in item.split(sep)])
                else:
                    temp.append(item)
            apps = temp

        apps = [a for a in apps if a]

        return {
            "type": "node",
            "category": "multi_open" if len(apps) > 1 else "open_app",
            "value": apps,
            "confidence": 0.90,
        }

    # =================================================
    # 5. BROWSER / SEARCH COMMANDS
    # =================================================
    browser_keywords = [
        "youtube",
        "google",
        "instagram",
        "facebook",
        "chatgpt",
        "claude",
        "grok",
        "perplexity",
    ]

    if any(x in cmd for x in browser_keywords):
        if "search" in cmd or cmd.startswith("open "):
            return {
                "type": "search",
                "category": "search",
                "value": cmd,
                "confidence": 0.92,
            }

        if " and " in cmd:
            return {
                "type": "multi",
                "category": "mixed_browser",
                "value": cmd,
                "confidence": 0.88,
            }

        return {
            "type": "browser",
            "category": "web",
            "value": cmd,
            "confidence": 0.94,
        }

    # =================================================
    # 6. SYSTEM COMMANDS
    # =================================================
    if any(x in cmd for x in [
        "shutdown",
        "restart",
        "sleep",
        "lock",
        "sign out",
        "log off"
    ]):
        return {
            "type": "pc",
            "category": "system",
            "value": cmd,
            "confidence": 0.95,
        }

    # =================================================
    # 7. MEDIA / MUSIC
    # =================================================
    if any(x in cmd for x in ["play ", "spotify", "song", "music", "playlist", "playlists"]):
        return {
            "type": "music",
            "category": "music",
            "value": cmd,
            "confidence": 0.88,
        }

    # =================================================
    # 8. WEATHER
    # =================================================
    if any(x in cmd for x in ["weather", "temperature", "rain", "sunny", "forecast", "climate"]):
        return {
            "type": "weather",
            "category": "weather",
            "value": cmd,
            "confidence": 0.88,
        }

    # =================================================
    # 9. MAPS
    # =================================================
    if any(x in cmd for x in ["map", "directions", "navigate", "route", "near me", "location"]):
        return {
            "type": "maps",
            "category": "maps",
            "value": cmd,
            "confidence": 0.88,
        }

    # =================================================
    # 10. MEMORY
    # =================================================
    if any(x in cmd for x in ["remember", "forget", "recall", "memory", "note"]):
        return {
            "type": "memory",
            "category": "memory",
            "value": cmd,
            "confidence": 0.88,
        }

    # =================================================
    # 11. INFORMATION / QUESTION
    # =================================================
    question_phrases = [
        "what ",
        "who ",
        "why ",
        "how ",
        "when ",
        "where ",
        "explain",
        "tell me",
        "define",
        "describe",
        "kya",
        "kaisa",
        "kaise",
        "kitna",
        "kab",
    ]

    if any(cmd.startswith(phrase) or f" {phrase}" in cmd for phrase in question_phrases):
        return {
            "type": "information",
            "category": "general_question",
            "value": cmd,
            "confidence": 0.86,
        }

    # =================================================
    # 12. CONVERSATION
    # =================================================
    conversation_phrases = [
        "hello",
        "hi",
        "good morning",
        "good afternoon",
        "good evening",
        "good night",
        "goodnight",
        "hey",
        "tu kaisa",
        "kaisa hai",
        "kaise ho",
        "kya haal",
        "kya kar rahe ho",
        "aaj mood",
        "mood kharab",
    ]

    if any(phrase in cmd for phrase in conversation_phrases):
        return {
            "type": "conversation",
            "category": "chat",
            "value": cmd,
            "confidence": 0.92,
        }

    # =================================================
    # 13. DEFAULT CHAT FALLBACK
    # =================================================
    return {
        "type": "brain",
        "category": "chat",
        "value": cmd,
        "confidence": 0.65,
    }
