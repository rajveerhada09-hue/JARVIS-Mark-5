"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : planning_utils.py

PATH    : core\planning_utils.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import datetime
import time
import uuid

TASK_STATES = ["Waiting", "Running", "Completed", "Failed", "Cancelled"]
MISSION_STATUSES = ["Active", "Paused", "Completed", "Failed", "Cancelled"]
DEFAULT_TASK_PRIORITY = 50
EVENT_STORAGE_FILE = "core/agent_memory/planning_events.json"
STATUS_STORAGE_FILE = "core/agent_memory/planning_status.json"

CATEGORY_PRIORITIES = {
    "automation": 90,
    "planning": 80,
    "research": 70,
    "coding": 60,
    "testing": 55,
    "deployment": 55,
    "memory": 50,
    "vision": 50,
    "default": 50,
}

SUGGESTION_COOLDOWN_SECONDS = 60 * 60 * 24


def generate_id(prefix: str = "item") -> str:
    return f"{prefix}-{int(time.time() * 1000)}-{uuid.uuid4().hex[:6]}"


def timestamp_now() -> str:
    return datetime.datetime.now().isoformat()


def task_priority(category: str, manual_priority: int | None = None) -> int:
    if manual_priority is not None:
        return manual_priority
    return CATEGORY_PRIORITIES.get(category, CATEGORY_PRIORITIES["default"])


def normalize_status(status: str) -> str:
    normalized = status.capitalize()
    if normalized not in TASK_STATES:
        return "Waiting"
    return normalized


def normalize_mission_status(status: str) -> str:
    normalized = status.capitalize()
    if normalized not in MISSION_STATUSES:
        return "Active"
    return normalized
