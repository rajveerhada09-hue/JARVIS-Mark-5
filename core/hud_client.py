"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : hud_client.py
PATH    : core/hud_client.py
PURPOSE : HUD Client - sends events to WebSocket bridge (Node.js server)
============================================================
"""

import json
import logging
import requests
import threading
import time
from typing import Dict, Any, Optional

logger = logging.getLogger("jarvis.hud")


class HUDClient:
    """Sends events to the HUD WebSocket bridge via HTTP"""

    def __init__(self, host: str = "127.0.0.1", port: int = 8766):
        self.base_url = f"http://{host}:{port}"
        self.event_endpoint = f"{self.base_url}/event"
        self._available = False
        self._lock = threading.Lock()
        self._last_check = 0
        self._check_interval = 10  # seconds

    def _check_availability(self) -> bool:
        """Check if HUD bridge is available (cached)"""
        now = time.time()
        if now - self._last_check < self._check_interval:
            return self._available

        try:
            resp = requests.get(f"{self.base_url}/health", timeout=1)
            self._available = resp.status_code == 200
        except Exception:
            self._available = False

        self._last_check = now
        return self._available

    def send_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """Send event to HUD bridge"""
        if not self._check_availability():
            return False

        payload = {"type": event_type, "data": data}

        try:
            resp = requests.post(
                self.event_endpoint,
                json=payload,
                timeout=0.5
            )
            return resp.status_code == 200
        except Exception as e:
            logger.debug(f"[HUD] Failed to send {event_type}: {e}")
            self._available = False
            return False

    # Convenience methods for common events
    def send_state(self, state: str) -> bool:
        """Send AI state (idle, listening, thinking, speaking, etc.)"""
        return self.send_event("state", {"state": state})

    def send_stats(self, stats: Dict[str, Any]) -> bool:
        """Send system stats"""
        return self.send_event("stats", stats)

    def send_message(self, role: str, text: str) -> bool:
        """Send conversation message"""
        return self.send_event("message", {"role": role, "text": text})

    def send_notification(self, text: str) -> bool:
        """Send notification"""
        return self.send_event("notification", {"text": text})

    def send_provider_status(self, provider: str, available: list) -> bool:
        """Send current STT provider status"""
        return self.send_event("provider_status", {
            "current": provider,
            "available": available
        })


# Global instance
_hud_client: Optional[HUDClient] = None


def get_hud_client() -> HUDClient:
    global _hud_client
    if _hud_client is None:
        _hud_client = HUDClient()
    return _hud_client


def send_hud_state(state: str) -> bool:
    return get_hud_client().send_state(state)


def send_hud_stats(stats: Dict[str, Any]) -> bool:
    return get_hud_client().send_stats(stats)


def send_hud_message(role: str, text: str) -> bool:
    return get_hud_client().send_message(role, text)


def send_hud_notification(text: str) -> bool:
    return get_hud_client().send_notification(text)


def send_hud_provider_status(provider: str, available: list) -> bool:
    return get_hud_client().send_provider_status(provider, available)