"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : context_manager.py

PATH    : core\context_manager.py

PURPOSE :
Stores and updates runtime conversation context.

LAST UPDATED :
2026-06-28

============================================================
"""

class ContextManager:
    def __init__(self, memory):
        self.memory = memory

    def recent_context(self, limit=8):
        try:
            return self.memory.get_context(limit=limit)
        except:
            return ''

    def remember_file(self, path):
        try:
            self.memory.remember('last_file', path)
        except:
            pass

    def remember_project(self, name):
        try:
            self.memory.remember('last_project', name)
        except:
            pass
