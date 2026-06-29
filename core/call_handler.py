"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : call_handler.py

PATH    : core\call_handler.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import subprocess

def execute(plan):

    for step in plan:

        action = step["action"]

        # -------------------------
        # OPEN YOUTUBE
        # -------------------------
        if action == "open_youtube":
            subprocess.Popen(
                ["cmd", "/c", "start", "https://youtube.com"]
            )

        # -------------------------
        # SEARCH YOUTUBE (FIXED)
        # -------------------------
        elif action == "youtube_search":
            query = step.get("query", "").strip()

            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

            subprocess.Popen(
                ["cmd", "/c", "start", url]
            )

        # -------------------------
        # CHAT FALLBACK
        # -------------------------
        elif action == "chat":
            print("[JARVIS CHAT]", step["text"])