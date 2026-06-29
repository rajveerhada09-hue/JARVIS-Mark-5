"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : task_queue.py

PATH    : core\task_queue.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from core.memory.memory_engine import MemoryEngine
from core.planning_utils import generate_id, normalize_status, task_priority, timestamp_now

STORAGE_KEY = "planner_tasks"


@dataclass
class Task:
    id: str
    mission_id: str
    name: str
    category: str = "default"
    payload: Any = None
    priority: int = 50
    status: str = "Waiting"
    dependencies: List[str] = field(default_factory=list)
    retry_count: int = 0
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    result: Optional[str] = None
    agent: Optional[str] = None
    created_at: str = field(default_factory=timestamp_now)
    updated_at: str = field(default_factory=timestamp_now)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "Task":
        return cls(
            id=raw.get("id", generate_id("task")),
            mission_id=raw.get("mission_id", ""),
            name=raw.get("name", ""),
            category=raw.get("category", "default"),
            payload=raw.get("payload"),
            priority=raw.get("priority", 50),
            status=normalize_status(raw.get("status", "Waiting")),
            dependencies=raw.get("dependencies", []) or [],
            retry_count=raw.get("retry_count", 0),
            start_time=raw.get("start_time"),
            end_time=raw.get("end_time"),
            result=raw.get("result"),
            agent=raw.get("agent"),
            created_at=raw.get("created_at", timestamp_now()),
            updated_at=raw.get("updated_at", timestamp_now()),
        )

    def is_ready(self, task_map: Dict[str, "Task"]) -> bool:
        if self.status != "Waiting":
            return False
        for dependency_id in self.dependencies:
            dependency = task_map.get(dependency_id)
            if dependency is None or dependency.status != "Completed":
                return False
        return True


class TaskQueue:
    def __init__(self):
        self.storage = MemoryEngine()
        self.tasks: List[Task] = self.load_tasks()

    def load_tasks(self) -> List[Task]:
        raw = self.storage.recall(STORAGE_KEY, []) or []
        tasks: List[Task] = []
        for item in raw:
            if isinstance(item, dict):
                tasks.append(Task.from_dict(item))
        return tasks

    def save_tasks(self) -> None:
        payload = [task.to_dict() for task in self.tasks]
        self.storage.remember(STORAGE_KEY, payload)

    def add_task(
        self,
        mission_id: str,
        name: str,
        category: str = "default",
        payload: Any = None,
        priority: Optional[int] = None,
        dependencies: Optional[List[str]] = None,
        task_id: Optional[str] = None,
    ) -> Task:
        task = Task(
            id=task_id or generate_id("task"),
            mission_id=mission_id,
            name=name,
            category=category,
            payload=payload,
            priority=task_priority(category, priority),
            status="Waiting",
            dependencies=dependencies or [],
        )
        self.tasks.append(task)
        self.save_tasks()
        return task

    def get_task(self, task_id: str) -> Optional[Task]:
        for task in self.tasks:
            if task.id == task_id:
                return task
        return None

    def list_tasks(self, mission_id: Optional[str] = None) -> List[Task]:
        if mission_id is None:
            return list(self.tasks)
        return [task for task in self.tasks if task.mission_id == mission_id]

    def next_ready_task(self, mission_id: str) -> Optional[Task]:
        task_map = {task.id: task for task in self.tasks}
        ready = [task for task in self.list_tasks(mission_id) if task.is_ready(task_map)]
        if not ready:
            return None
        ready.sort(key=lambda t: (-t.priority, t.created_at))
        return ready[0]

    def update_task(self, updated_task: Task) -> None:
        for idx, task in enumerate(self.tasks):
            if task.id == updated_task.id:
                self.tasks[idx] = updated_task
                break
        self.save_tasks()

    def mark_running(self, task_id: str) -> Optional[Task]:
        task = self.get_task(task_id)
        if not task:
            return None
        task.status = "Running"
        task.start_time = timestamp_now()
        task.updated_at = timestamp_now()
        self.update_task(task)
        return task

    def mark_completed(self, task_id: str, result: Optional[str] = None) -> Optional[Task]:
        task = self.get_task(task_id)
        if not task:
            return None
        task.status = "Completed"
        task.end_time = timestamp_now()
        task.result = result or "Completed"
        task.updated_at = timestamp_now()
        self.update_task(task)
        return task

    def mark_failed(self, task_id: str, result: Optional[str] = None) -> Optional[Task]:
        task = self.get_task(task_id)
        if not task:
            return None
        task.retry_count += 1
        task.status = "Failed"
        task.end_time = timestamp_now()
        task.result = result or "Failed"
        task.updated_at = timestamp_now()
        self.update_task(task)
        return task

    def mark_cancelled(self, task_id: str, result: Optional[str] = None) -> Optional[Task]:
        task = self.get_task(task_id)
        if not task:
            return None
        task.status = "Cancelled"
        task.end_time = timestamp_now()
        task.result = result or "Cancelled"
        task.updated_at = timestamp_now()
        self.update_task(task)
        return task

    def has_pending_tasks(self, mission_id: str) -> bool:
        return any(
            task.status in ["Waiting", "Running"]
            for task in self.list_tasks(mission_id)
        )

    def reset(self) -> None:
        self.tasks = []
        self.save_tasks()
