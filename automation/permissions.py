"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : permissions.py

PATH    : core\permissions.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

# core/permissions.py

PERMISSIONS = {

    # SAFE
    "open_app": 0,
    "browser": 0,
    "google_search": 0,
    "youtube_search": 0,

    # CONFIRM
    "delete_file": 1,
    "move_file": 1,
    "rename_file": 1,
    "kill_process": 1,

    # CRITICAL
    "shutdown": 2,
    "restart": 2,
    "sleep": 2,
    "lock": 2,

    # RESTRICTED
    "execute_python": 3,
    "registry_edit": 3,
    "format_drive": 3
}