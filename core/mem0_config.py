"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : mem0_config.py

PATH    : core\mem0_config.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
MEMORY_DIR = REPO_ROOT / "memory"
MEM0_DB_DIR = REPO_ROOT / "mem0_db"
MEM0_HISTORY_DB = MEMORY_DIR / "mem0_history.db"
MEM0_COLLECTION_NAME = "jarvis_mem0"
MEM0_EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
MEM0_VECTOR_DIMS = 1536
MEM0_SEARCH_THRESHOLD = 0.1
MEM0_SEARCH_CACHE_LIMIT = 128

MEMORY_CATEGORIES = [
    "conversation",
    "preference",
    "project",
    "task",
    "reminder",
    "person",
    "location",
    "system",
    "knowledge",
    "goal",
]

os.makedirs(MEMORY_DIR, exist_ok=True)
os.makedirs(MEM0_DB_DIR, exist_ok=True)
