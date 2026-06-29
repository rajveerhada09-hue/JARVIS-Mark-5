"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : intelligent_brain.py

PATH    : core\intelligent_brain.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import re

def process(text: str):
    text = text.lower().strip()

    # -------------------------
    # STRONG YOUTUBE DETECTION
    # -------------------------
    if "youtube" in text and "search" in text:

        # STEP 1: split ONLY after keyword "search"
        parts = re.split(r"\bsearch\b", text, maxsplit=1)

        query = ""
        if len(parts) > 1:
            query = parts[1].strip()

        # STEP 2: REMOVE COMMAND WORDS LEAKING INTO QUERY
        junk_words = ["open", "youtube", "and", "please"]

        for w in junk_words:
            query = query.replace(w, "")

        query = query.strip()

        return [
            {"action": "open_youtube"},
            {"action": "youtube_search", "query": query}
        ]

    # -------------------------
    # ONLY OPEN YOUTUBE
    # -------------------------
    if "open youtube" in text:
        return [{"action": "open_youtube"}]

    return [{"action": "chat", "text": text}]