"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : context_engine.py

PATH    : core\context_engine.py

PURPOSE :
Maintains conversational context and retrieves relevant information.

LAST UPDATED :
2026-06-28

============================================================
"""

from typing import Dict, Any

from core.memory_manager import MemoryManager


class ContextEngine:
    """Provide consolidated context to the conversation engine.

    Builds a summary of recent conversation, working memory, project memory,
    user preferences, and top relevant Mem0 memories.
    """

    def __init__(self):
        self.mm = MemoryManager()

    def build_context(self, query: str, limit: int = 8) -> Dict[str, Any]:
        context: Dict[str, Any] = {}
        try:
            context['recent'] = self.mm.storage.get_context(limit=limit)
        except:
            context['recent'] = ''

        try:
            context['working'] = self.mm.get_working('current_task', None)
        except:
            context['working'] = None

        try:
            context['project'] = {
                'name': self.mm.get_working('current_project', None),
                'last_files': self.mm.get_working('recent_files', []),
            }
        except:
            context['project'] = {}

        try:
            context['profile'] = self.mm.get_long_term('profile', {})
        except:
            context['profile'] = {}

        try:
            memories = self.mm.search_long_term(query, limit=5)
            context['memories'] = [self._extract_memory_summary(m) for m in memories]
        except:
            context['memories'] = []

        return context

    def _extract_memory_summary(self, item: Dict[str, Any]) -> Dict[str, Any]:
        text = ''
        if isinstance(item.get('text'), str):
            text = item['text']
        elif isinstance(item.get('messages'), list) and item['messages']:
            first = item['messages'][0]
            if isinstance(first, dict):
                text = first.get('content', '') or first.get('text', '') or ''
            else:
                text = str(first)
        elif isinstance(item.get('messages'), str):
            text = item['messages']

        summary = item.get('metadata', {}).get('summary')
        if not summary:
            summary = text if len(text.split()) <= 40 else ' '.join(text.split()[:40]) + '...'

        return {
            'id': item.get('id') or item.get('memory_id'),
            'text': text,
            'category': item.get('metadata', {}).get('category'),
            'importance': item.get('metadata', {}).get('importance'),
            'summary': summary,
        }
