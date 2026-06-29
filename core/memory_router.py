"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : memory_router.py

PATH    : core\memory_router.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

from typing import Any, Dict

from core.memory_manager import MemoryManager


class MemoryRouter:
    """Route memory operations to appropriate layers.

    Responsible for deciding where to write and read memory items.
    """

    def __init__(self):
        self.mm = MemoryManager()

    def observe(self, text: str, metadata: Dict = None):
        score = self.mm.should_persist(text)
        evaluation = self.mm.scorer.evaluate(text, metadata=metadata)
        if evaluation['important']:
            memory_item = {
                'text': text,
                'summary': text if len(text.split()) <= 40 else ' '.join(text.split()[:40]) + '...',
                'category': evaluation['category'],
                'importance': evaluation['score'],
                'source': 'user',
                'timestamp': metadata.get('timestamp') if metadata else None,
                'metadata': metadata or {},
            }
            existing = self._find_duplicate(text, evaluation['category'])
            if existing:
                mem_id = existing.get('id') or existing.get('memory_id')
                if mem_id:
                    self.mm.update_long_term(mem_id, {'text': text, 'metadata': memory_item['metadata'], 'timestamp': memory_item['timestamp']})
                    return True
            self.mm.save_long_term(memory_item)
            return True
        return False

    def _find_duplicate(self, text: str, category: str):
        results = self.mm.search_long_term(text, limit=5)
        for item in results:
            metadata = item.get('metadata', {})
            if metadata.get('category') == category and item.get('text', '').lower() == text.lower():
                return item
        return None

    def remember_working(self, key: str, value: Any):
        self.mm.set_working(key, value)

    def recall(self, key: str, default=None):
        w = self.mm.get_working(key, None)
        if w is not None:
            return w
        return self.mm.get_long_term(key, default)
