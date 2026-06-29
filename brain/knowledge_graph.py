"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : knowledge_graph.py

PATH    : core\knowledge_graph.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

from collections import defaultdict
from typing import Dict, List


class KnowledgeGraph:
    """Lightweight in-memory relationship graph.

    Nodes are strings, edges are adjacency lists with optional metadata.
    This is intentionally simple and stored in memory; persistence is handled
    externally if needed.
    """

    def __init__(self):
        self.edges = defaultdict(list)

    def add_relation(self, a: str, b: str, meta: Dict = None):
        self.edges[a].append({'node': b, 'meta': meta or {}})

    def related(self, a: str) -> List[Dict]:
        return self.edges.get(a, [])

    def remove_relation(self, a: str, b: str):
        self.edges[a] = [e for e in self.edges.get(a, []) if e.get('node') != b]

    def nodes(self):
        return list(self.edges.keys())
