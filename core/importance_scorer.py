"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : importance_scorer.py

PATH    : core\importance_scorer.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import re
from typing import Dict, Any

KEY_IMPORTANT_PHRASES = [
    r"\bmy favorite\b",
    r"\bI use\b",
    r"\bI'm building\b",
    r"\bI am building\b",
    r"\bremember that\b",
    r"\bnote that\b",
    r"\bfavorite\b",
    r"\bprefer\b",
    r"\bcoding style\b",
    r"\bcurrent project\b",
    r"\bcurrent bug\b",
    r"\broadmap\b",
    r"\btask\b",
    r"\bproject\b",
]

CATEGORY_MAP = {
    'preference': [
        'favorite', 'prefer', 'preference', 'my editor', 'my favourite', 'use', 'like', 'love', 'hate'
    ],
    'project': ['project', 'repo', 'repository', 'architecture', 'roadmap', 'progress', 'current project'],
    'task': ['task', 'todo', 'fix', 'implement', 'work on', 'bug', 'issue'],
    'personal': ['rajveer', 'name', 'personal', 'family', 'home'],
    'coding': ['code', 'python', 'javascript', 'debug', 'compile', 'build', 'stack'],
    'learning': ['learn', 'study', 'understand', 'research'],
    'reminder': ['remember', 'remind', 'note', 'later', 'tomorrow', 'next'],
    'relationship': ['related', 'dependency', 'depends', 'connected', 'architecture'],
}

IGNORED_PATTERNS = [
    r"\bhi\b",
    r"\bhello\b",
    r"\bthanks\b",
    r"\bthank you\b",
    r"\bopen chrome\b",
    r"\bwhat('s| is) the time\b",
    r"\bgood (morning|afternoon|evening|night)\b",
    r"\bopen (browser|chrome|edge|firefox)\b",
]


class ImportanceScorer:
    """Score a text for memory importance.

    Returns a float 0.0-1.0 where higher means more important to persist.
    """

    def __init__(self):
        self.weights = {
            'explicit_phrase': 0.55,
            'technical_terms': 0.15,
            'personal_info': 0.15,
            'length': 0.1,
        }

    def score(self, text: str, metadata: Dict[str, Any] = None) -> float:
        if not text or not text.strip():
            return 0.0

        t = text.lower().strip()

        for pattern in IGNORED_PATTERNS:
            if re.search(pattern, t):
                return 0.0

        score = 0.0
        for pat in KEY_IMPORTANT_PHRASES:
            if re.search(pat, t):
                score += self.weights['explicit_phrase']
                break

        if any(x in t for x in ['project', 'repo', 'bug', 'issue', 'error', 'stack', 'debug', 'architecture', 'module', 'file', 'task', 'roadmap']):
            score += self.weights['technical_terms']

        if any(x in t for x in ['favorite', 'prefer', 'preference', 'my editor', 'my favourite', 'i use', 'i like', 'i love', 'i hate']):
            score += self.weights['personal_info']

        length = len(t.split())
        if length > 8:
            score += min(0.1, (length - 8) * 0.01)

        return max(0.0, min(1.0, score))

    def category(self, text: str) -> str:
        t = text.lower()
        for category, keywords in CATEGORY_MAP.items():
            if any(keyword in t for keyword in keywords):
                return category
        return 'conversation'

    def evaluate(self, text: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        score = self.score(text, metadata=metadata)
        return {
            'score': score,
            'category': self.category(text) if score >= 0.4 else 'conversation',
            'important': score >= 0.6,
        }
