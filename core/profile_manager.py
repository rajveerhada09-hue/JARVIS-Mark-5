"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : profile_manager.py

PATH    : core\profile_manager.py

PURPOSE :
Stores user profile and long-term preferences.

LAST UPDATED :
2026-06-28

============================================================
"""

from typing import Any, Dict

from core.memory_manager import MemoryManager


class ProfileManager:
    def __init__(self):
        self.mm = MemoryManager()

    def get_profile(self) -> Dict:
        return self.mm.get_personal_data('profile', {}) or {}

    def update_profile(self, key: str, value: Any):
        profile = self.get_profile()
        profile[key] = value
        self.mm.save_personal_data('profile', profile)

    def set_preference(self, key: str, value: Any):
        self.update_profile(key, value)

    def get_preference(self, key: str, default=None):
        profile = self.get_profile()
        return profile.get(key, default)
