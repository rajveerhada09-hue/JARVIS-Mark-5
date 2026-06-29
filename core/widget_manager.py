"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : widget_manager.py

PATH    : core\widget_manager.py

PURPOSE :
Controls HUD widget lifecycle and communication.

LAST UPDATED :
2026-06-28

============================================================
"""

import json
import os
from typing import Dict, Optional


class WidgetManager:
    """Backend widget event layer for dashboard / HUD updates."""

    STATUS_FILE = "hud_widget.json"

    def __init__(self):
        self.listeners = []

    def emit_widget(self, widget_type: str, payload: Dict) -> None:
        try:
            if not widget_type:
                return
            data = {
                "type": "widget",
                "data": {
                    "id": widget_type,
                    "action": payload.get("action", "show"),
                    **payload,
                },
            }
            with open(self.STATUS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self._broadcast(data)
        except Exception:
            pass

    def show(self, widget_type: str, payload: Dict) -> None:
        self.emit_widget(widget_type, {**payload, "action": "show"})

    def hide(self, widget_type: str) -> None:
        self.emit_widget(widget_type, {"action": "hide"})

    def update(self, widget_type: str, payload: Dict) -> None:
        self.emit_widget(widget_type, {**payload, "action": "update"})

    def move(self, widget_type: str, payload: Dict) -> None:
        self.emit_widget(widget_type, {**payload, "action": "move"})

    def show_notification(self, title: str, message: str) -> None:
        self.show("notification", {"title": title, "message": message})

    def register_listener(self, listener) -> None:
        if listener not in self.listeners:
            self.listeners.append(listener)

    def _broadcast(self, message: Dict) -> None:
        for listener in self.listeners:
            try:
                listener(message)
            except Exception:
                pass
