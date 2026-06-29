"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : mem0_adapter.py

PATH    : core\mem0_adapter.py

PURPOSE :
Provides local Mem0 semantic memory integration.

LAST UPDATED :
2026-06-28

============================================================
"""

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from mem0.configs.base import EmbedderConfig, MemoryConfig, VectorStoreConfig
from mem0.configs.vector_stores.qdrant import QdrantConfig
from mem0.embeddings.huggingface import HuggingFaceEmbedding
from mem0.memory.main import Memory
from qdrant_client import QdrantClient

from core.mem0_config import (
    MEM0_COLLECTION_NAME,
    MEM0_DB_DIR,
    MEM0_EMBEDDING_MODEL,
    MEM0_HISTORY_DB,
    MEM0_VECTOR_DIMS,
    MEM0_SEARCH_THRESHOLD,
    MEMORY_CATEGORIES,
)

LOG_FILE = Path("memory/mem0_adapter.log")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


def _log(message: str) -> None:
    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
    except Exception:
        pass


def _normalize_category(category: Optional[str]) -> str:
    if not category:
        return "conversation"
    normalized = category.strip().lower()
    if normalized in MEMORY_CATEGORIES:
        return normalized
    return "conversation"


def _normalize_metadata(item: Dict[str, Any]) -> Dict[str, Any]:
    metadata = {
        "category": _normalize_category(item.get("category")),
        "importance": float(item.get("importance", 0.5) or 0.5),
        "source": item.get("source", "jarvis"),
        "timestamp": item.get("timestamp") or time.strftime("%Y-%m-%dT%H:%M:%S"),
        "summary": item.get("summary") or (item.get("text", "")[:512] if item.get("text") else ""),
    }
    extra = item.get("metadata") or {}
    metadata.update({k: v for k, v in extra.items() if k not in metadata})
    return metadata


class Mem0Adapter:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if getattr(self, "initialized", False):
            return

        self.storage_path = Path("memory")
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = Path(MEM0_DB_DIR)
        self.db_path.mkdir(parents=True, exist_ok=True)

        self.history_db = Path(MEM0_HISTORY_DB)
        self.history_db.parent.mkdir(parents=True, exist_ok=True)

        self._search_cache: Dict[str, Any] = {}

        self._initialize_vector_store()
        self._initialize_memory()
        self.initialized = True

    def _initialize_vector_store(self) -> None:
        try:
            qdrant_client = QdrantClient(path=str(self.db_path))
            self.vector_store = QdrantConfig(
                collection_name=MEM0_COLLECTION_NAME,
                embedding_model_dims=MEM0_VECTOR_DIMS,
                client=qdrant_client,
                path=str(self.db_path),
                on_disk=True,
            )
            self.qdrant_client = qdrant_client
        except Exception as exc:
            _log(f"Qdrant init failed: {exc}")
            raise

    def _initialize_memory(self) -> None:
        try:
            self.embedder = HuggingFaceEmbedding(
                model_name=MEM0_EMBEDDING_MODEL,
                normalize=True,
            )
            memory_config = MemoryConfig(
                vector_store=VectorStoreConfig(provider="qdrant", config=self.vector_store.dict()),
                embedder=EmbedderConfig(provider="huggingface", config={"model_name": MEM0_EMBEDDING_MODEL}),
                history_db_path=str(self.history_db),
            )
            self.memory = Memory(memory_config)
        except Exception as exc:
            _log(f"Mem0 memory init failed: {exc}")
            raise

    def _make_payload(self, item: Dict[str, Any]) -> Dict[str, Any]:
        metadata = _normalize_metadata(item)
        return {
            "text": item.get("text") or item.get("summary") or "",
            "metadata": metadata,
            "timestamp": metadata["timestamp"],
        }

    def save_memory(self, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not item:
            return None
        try:
            payload = self._make_payload(item)
            return self.memory.add(
                payload["text"],
                metadata=payload["metadata"],
                timestamp=payload["timestamp"],
                infer=False,
            )
        except Exception as exc:
            _log(f"save_memory error: {exc}")
            return None

    def search_memory(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        if not query or not query.strip():
            return []

        cache_key = f"search:{query}:{limit}"
        if cache_key in self._search_cache:
            return self._search_cache[cache_key]

        try:
            results = self.memory.search(query, top_k=limit, threshold=MEM0_SEARCH_THRESHOLD)
            normalized = [self._normalize_result(item) for item in results]
            self._search_cache[cache_key] = normalized
            return normalized
        except Exception as exc:
            _log(f"search_memory error: {exc}")
            return []

    def update_memory(self, mem_id: str, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not mem_id:
            return None
        try:
            return self.memory.update(mem_id, data=item.get("text"), metadata=item.get("metadata"))
        except Exception as exc:
            _log(f"update_memory error: {exc}")
            return None

    def delete_memory(self, mem_id: str) -> bool:
        if not mem_id:
            return False
        try:
            self.memory.delete(mem_id)
            return True
        except Exception as exc:
            _log(f"delete_memory error: {exc}")
            return False

    def get_recent_memories(self, limit: int = 5) -> List[Dict[str, Any]]:
        try:
            results = self.memory.get_all(top_k=limit)
            return [self._normalize_result(item) for item in results]
        except Exception as exc:
            _log(f"get_recent_memories error: {exc}")
            return []

    def get_project_memories(self) -> List[Dict[str, Any]]:
        try:
            results = self.memory.get_all(filters={"metadata.category": "project"}, top_k=10)
            return [self._normalize_result(item) for item in results]
        except Exception as exc:
            _log(f"get_project_memories error: {exc}")
            return []

    def get_user_preferences(self) -> List[Dict[str, Any]]:
        try:
            results = self.memory.get_all(filters={"metadata.category": "preference"}, top_k=10)
            return [self._normalize_result(item) for item in results]
        except Exception as exc:
            _log(f"get_user_preferences error: {exc}")
            return []

    def _normalize_result(self, item: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": item.get("id"),
            "text": item.get("text") or item.get("messages") or "",
            "metadata": item.get("metadata", {}),
            "summary": item.get("metadata", {}).get("summary"),
            "category": item.get("metadata", {}).get("category"),
            "importance": item.get("metadata", {}).get("importance"),
            "source": item.get("metadata", {}).get("source"),
            "timestamp": item.get("metadata", {}).get("timestamp"),
        }
