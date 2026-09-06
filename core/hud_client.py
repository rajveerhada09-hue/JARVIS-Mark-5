"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : hud_client.py
PATH    : core/hud_client.py
PURPOSE : HUD Client - disabled (HUD frontend removed)
============================================================
"""

import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("jarvis.hud")


# HUD frontend has been removed; all operations are no-ops
def send_hud_state(state: str) -> bool:
    return False


def send_hud_stats(stats: Dict[str, Any]) -> bool:
    return False


def send_hud_message(role: str, text: str) -> bool:
    return False


def send_hud_notification(text: str) -> bool:
    return False


def send_hud_provider_status(provider: str, available: list) -> bool:
    return False