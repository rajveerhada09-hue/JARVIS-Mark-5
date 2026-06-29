"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : memory_manager.py

PATH    : core\memory_manager.py

PURPOSE :
Coordinates short-term, long-term and semantic memory.

LAST UPDATED :
2026-06-28

============================================================
"""

import json
import os
from typing import Any, Dict, Optional

from core.importance_scorer import ImportanceScorer
from core.mem0_adapter import Mem0Adapter
from core.memory.memory_engine import MemoryEngine


class MemoryManager:
    """Layered memory manager implementing Working, Long-term, and Semantic layers.

    - Working memory: ephemeral, cleared after inactivity
    - Long-term memory: stored via MemoryEngine.memory_store and Mem0
    """

    WORKING_KEY = 'working_memory'

    def __init__(self):
        self.storage = MemoryEngine()
        self.scorer = ImportanceScorer()
        self.mem0 = Mem0Adapter()
        try:
            self.storage.remember(self.WORKING_KEY, {})
        except:
            pass

    # --- Working Memory API ---
    def set_working(self, key: str, value: Any):
        wm = self.storage.recall(self.WORKING_KEY, {}) or {}
        wm[key] = value
        self.storage.remember(self.WORKING_KEY, wm)

    def get_working(self, key: str, default: Any = None):
        wm = self.storage.recall(self.WORKING_KEY, {}) or {}
        return wm.get(key, default)

    def clear_working(self):
        self.storage.remember(self.WORKING_KEY, {})

    # --- Long Term API (semantic store via Mem0) ---
    def save_long_term(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.mem0.save_memory(item)

    def search_long_term(self, query: str, limit: int = 5):
        return self.mem0.search_memory(query, limit=limit)

    def update_long_term(self, mem_id: str, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return self.mem0.update_memory(mem_id, item)

    def delete_long_term(self, mem_id: str) -> bool:
        return self.mem0.delete_memory(mem_id)

    def get_recent_long_term(self, limit: int = 5):
        return self.mem0.get_recent_memories(limit=limit)

    def get_project_memory(self):
        return self.mem0.get_project_memory()

    def get_user_preferences(self):
        return self.mem0.get_user_preferences()

    def get_long_term(self, key: str, default: Any = None):
        try:
            return self.storage.get_user_data(key, default)
        except:
            return default

    def save_personal_data(self, key: str, value: Any):
        try:
            self.storage.save_user_data(key, value)
        except:
            pass

    def get_personal_data(self, key: str, default: Any = None):
        return self.get_long_term(key, default)

    # --- Decision: Should we store? ---
    def should_persist(self, text: str) -> float:
        return self.scorer.score(text)
