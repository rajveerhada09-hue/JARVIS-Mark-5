"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : browser_control.py

PATH    : core\browser_control.py

PURPOSE :
Handles browser automation and web interactions.

LAST UPDATED :
2026-06-28

============================================================
"""

import webbrowser


class BrowserController:

    @staticmethod
    def execute(cmd):
        cmd = cmd.lower().strip()

        try:

            if "open youtube" in cmd:

                if "search" not in cmd:
                    webbrowser.open("https://www.youtube.com")
                    return "Opening YouTube."

                query = cmd.split("search", 1)[1].strip()

                webbrowser.open(
                    f"https://www.youtube.com/results?search_query={query}"
                )

                return f"Searching {query} on YouTube."

            elif "open google" in cmd:

                if "search" not in cmd:
                    webbrowser.open("https://www.google.com")
                    return "Opening Google."

                query = cmd.split("search", 1)[1].strip()

                webbrowser.open(
                    f"https://www.google.com/search?q={query}"
                )

                return f"Searching Google for {query}."

            elif "open facebook" in cmd:
                webbrowser.open("https://www.facebook.com")
                return "Facebook opened."

            elif "open instagram" in cmd:
                webbrowser.open("https://www.instagram.com")
                return "Instagram opened."

            return None

        except Exception as e:
            return f"Browser Error: {e}"