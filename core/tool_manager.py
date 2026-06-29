"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : tool_manager.py

PATH    : core\tool_manager.py

PURPOSE :
Executes tools and automation requested by the Intent Engine.

LAST UPDATED :
2026-06-28

============================================================
"""

import webbrowser
from typing import Any, Dict, Optional

from core.browser_control import BrowserController
from core.pc_control import open_app, pc_control_master
from core.workspace_manager import WorkspaceManager


class ToolManager:
    """Central tool execution layer for Jarvis.

    Routes structured intent metadata to the correct environment
    or application controller.
    """

    def __init__(self):
        self.workspace_manager = WorkspaceManager()

    def execute_intent(self, intent: Dict[str, Any]) -> Optional[str]:
        if not intent or not isinstance(intent, dict):
            return None

        intent_type = intent.get("type")
        value = intent.get("value", "")

        if intent_type == "browser":
            return self._handle_browser_intent(value)

        if intent_type == "workspace":
            return self.workspace_manager.launch_workspace(value)

        if intent_type == "pc":
            return pc_control_master(value)

        if intent_type == "music":
            return self._handle_music_intent(value)

        if intent_type == "weather":
            return self._handle_weather_intent(value)

        if intent_type == "maps":
            return self._handle_maps_intent(value)

        if intent_type == "memory":
            return self._handle_memory_intent(value)

        if intent_type == "search":
            return self._handle_search_intent(value)

        if intent_type == "research":
            return self._handle_research_intent(value)

        if intent_type == "planning":
            return self._handle_planning_intent(value)

        if intent_type == "coding":
            return self._handle_coding_intent(value)

        if intent_type == "vision":
            return self._handle_vision_intent(value)

        return None

    def _handle_browser_intent(self, value: str) -> Optional[str]:
        result = BrowserController.execute(value)
        if result:
            return result
        if value.startswith("open "):
            url = value.replace("open ", "").strip()
            webbrowser.open(url)
            return f"Opening {url}."
        return None

    def _handle_music_intent(self, value: str) -> Optional[str]:
        text = str(value or "").lower()
        if "spotify" in text:
            open_app("spotify")
            return "Launching Spotify."
        if "play" in text:
            return self._handle_search_intent(text)
        return None

    def _handle_weather_intent(self, value: str) -> Optional[str]:
        query = str(value or "").strip()
        if not query:
            return None
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Searching weather for: {query}."

    def _handle_maps_intent(self, value: str) -> Optional[str]:
        query = str(value or "").strip()
        if not query:
            return None
        url = f"https://www.google.com/maps/search/{query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Opening maps for: {query}."

    def _handle_memory_intent(self, value: str) -> Optional[str]:
        return None

    def _handle_search_intent(self, value: str) -> Optional[str]:
        query = str(value or "").strip()
        if not query:
            return None
        url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        webbrowser.open(url)
        return f"Searching Google for: {query}."

    def _handle_research_intent(self, value: str) -> Optional[str]:
        return None

    def _handle_planning_intent(self, value: str) -> Optional[str]:
        return None

    def _handle_coding_intent(self, value: str) -> Optional[str]:
        return None

    def _handle_vision_intent(self, value: str) -> Optional[str]:
        return None
