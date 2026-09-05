"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : memory_agent.py
PATH    : agents/memory_agent.py

PURPOSE :
Remember / recall / forget / search via the existing MemoryManager only
(same import used by MemoryRouter and ContextEngine: core.memory_manager).

LAST UPDATED : 2026-07-03
============================================================
"""

from typing import Any, Optional, Tuple

from agents.base_agent import BaseAgent
from agents.task_queue import Task
from memory.memory_manager import MemoryManager


class MemoryAgent(BaseAgent):  
    def __init__(self):
        super().__init__(
            name="MemoryAgent",
            description="Remembers, recalls, forgets, and searches memories via MemoryManager.",
            capabilities=["memory"],
        )
        self.mm = MemoryManager()

    def _can_handle(self, task: Task) -> bool:
        return task.category in self.capabilities

    def _execute(self, task: Task) -> str:
        action, key, value, query = self._parse(task)

        if action == "forget":
            return self._forget(key or task.name)
        if action == "search":
            return self._search(query or key or "")
        if action == "recall":
            return self._recall(key or task.name)
        return self._remember(key or task.name, value)

    # ── action parsing ──────────────────────────────────────────────
    def _parse(self, task: Task) -> Tuple[str, Optional[str], Any, Optional[str]]:
        payload = task.payload

        if isinstance(payload, dict):
            action = str(payload.get("action", "remember")).lower()
            return action, payload.get("key"), payload.get("value"), payload.get("query")

        text = str(payload if payload is not None else task.name).strip()
        lowered = text.lower()

        if "forget" in lowered:
            return "forget", text.replace("forget", "", 1).strip(" :-") or None, None, None
        if "search" in lowered:
            q = text.replace("search", "", 1).strip(" :-")
            return "search", None, None, q or text
        if "recall" in lowered or lowered.startswith("what"):
            k = text.replace("recall", "", 1).strip(" :-")
            return "recall", k or None, None, None

        return "remember", task.name, text, None

    # ── operations ────────────────────────────────────────────────────
    def _remember(self, key: str, value: Any) -> str:
        try:
            self.mm.set_working(key, value)
        except Exception:
            pass
        try:
            self.mm.set_working(key, value)
        except Exception:
            pass

        try:
            self.mm.set_working(key, value)
            self.mm.save_personal_data(key, value)
        except Exception:
            pass

    def _recall(self, key: str) -> str:
        try:
            working = self.mm.get_working(key, None)
            if working is not None:
                return str(working)
        except Exception:
            pass
        try:
            long_term = self.mm.get_long_term(key, None)
            if long_term is not None:
                return str(long_term)
        except Exception:
            pass
        return f"No memory found for: {key}."

    def _forget(self, key: str) -> str:
        cleared = False
        try:
            self.mm.set_working(key, None)
            cleared = True
        except Exception:
            pass
        # No dedicated long-term delete method is confirmed on
        # MemoryManager's interface — probe common candidate names
        # defensively rather than assume one exists. Safe no-op if none
        # match; starts working automatically if one is added later.
        for method_name in ("delete_long_term", "forget_long_term", "delete", "remove_long_term"):
            method = getattr(self.mm, method_name, None)
            if callable(method):
                try:
                    method(key)
                    cleared = True
                except Exception:
                    pass
                break
        return f"Forgot: {key}." if cleared else f"Could not forget: {key}."

    def _search(self, query: str) -> str:
        try:
            results = self.mm.search_long_term(query, limit=5)
        except Exception:
            results = []
        lines = []
        for item in results or []:
            text = item.get("text") or item.get("summary") or ""
            if text:
                lines.append(f"- {text}")
        return "\n".join(lines) if lines else f"No memories found for: {query}."