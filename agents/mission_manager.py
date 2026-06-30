"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : mission_manager.py

PATH    : core\mission_manager.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from memory.memory_engine import MemoryEngine
from agents.planning_utils import generate_id, normalize_mission_status, timestamp_now
from agents.task_queue import TaskQueue, Task

STORAGE_KEY = "planner_missions"


@dataclass
class Mission:
    id: str
    name: str
    description: str
    status: str = "Active"
    created_at: str = field(default_factory=timestamp_now)
    updated_at: str = field(default_factory=timestamp_now)
    completed_at: Optional[str] = None
    current_task_id: Optional[str] = None
    progress: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, raw: Dict[str, Any]) -> "Mission":
        return cls(
            id=raw.get("id", generate_id("mission")),
            name=raw.get("name", ""),
            description=raw.get("description", ""),
            status=normalize_mission_status(raw.get("status", "Active")),
            created_at=raw.get("created_at", timestamp_now()),
            updated_at=raw.get("updated_at", timestamp_now()),
            completed_at=raw.get("completed_at"),
            current_task_id=raw.get("current_task_id"),
            progress=raw.get("progress", 0.0),
        )


class MissionManager:
    def __init__(self):
        self.storage = MemoryEngine()
        self.task_queue = TaskQueue()
        self.missions: List[Mission] = self.load_missions()

    def load_missions(self) -> List[Mission]:
        raw = self.storage.recall(STORAGE_KEY, []) or []
        missions: List[Mission] = []
        for item in raw:
            if isinstance(item, dict):
                missions.append(Mission.from_dict(item))
        return missions

    def save_missions(self) -> None:
        payload = [mission.to_dict() for mission in self.missions]
        self.storage.remember(STORAGE_KEY, payload)

    def create_mission(
        self,
        name: str,
        description: str,
        task_definitions: List[Dict[str, Any]],
    ) -> Mission:
        mission_id = generate_id("mission")
        mission = Mission(
            id=mission_id,
            name=name,
            description=description,
            status="Active",
        )
        self.missions.append(mission)
        self.save_missions()

        for task_definition in task_definitions:
            self.task_queue.add_task(
                mission_id=mission.id,
                name=task_definition.get("name", "Unnamed Task"),
                category=task_definition.get("category", "default"),
                payload=task_definition.get("payload"),
                priority=task_definition.get("priority"),
                dependencies=task_definition.get("dependencies", []),
            )

        self.update_mission_progress(mission.id)
        self.emit_mission_event(mission.id)
        return mission

    def emit_mission_event(self, mission_id: str) -> None:
        mission = self.get_mission(mission_id)
        if mission:
            mission.current_task_id = self.next_ready_task_id(mission_id)
            mission.updated_at = timestamp_now()
            self.save_missions()

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        for mission in self.missions:
            if mission.id == mission_id:
                return mission
        return None

    def list_missions(self, status_filter: Optional[str] = None) -> List[Mission]:
        if status_filter is None:
            return list(self.missions)
        return [mission for mission in self.missions if mission.status == status_filter]

    def get_active_mission(self) -> Optional[Mission]:
        for mission in self.missions:
            if mission.status == "Active":
                return mission
        return None

    def get_unfinished_mission(self) -> Optional[Mission]:
        for mission in self.missions:
            if mission.status in ["Active", "Paused"]:
                return mission
        return None

    def pause_mission(self, mission_id: str) -> Optional[Mission]:
        mission = self.get_mission(mission_id)
        if not mission:
            return None
        mission.status = "Paused"
        mission.updated_at = timestamp_now()
        self.save_missions()
        return mission

    def resume_mission(self, mission_id: str) -> Optional[Mission]:
        mission = self.get_mission(mission_id)
        if not mission:
            return None
        mission.status = "Active"
        mission.updated_at = timestamp_now()
        self.save_missions()
        return mission

    def complete_mission(self, mission_id: str) -> Optional[Mission]:
        mission = self.get_mission(mission_id)
        if not mission:
            return None
        mission.status = "Completed"
        mission.completed_at = timestamp_now()
        mission.updated_at = timestamp_now()
        mission.current_task_id = None
        self.save_missions()
        return mission

    def next_ready_task_id(self, mission_id: str) -> Optional[str]:
        task = self.task_queue.next_ready_task(mission_id)
        return task.id if task else None

    def update_mission_progress(self, mission_id: str) -> None:
        mission = self.get_mission(mission_id)
        if not mission:
            return
        tasks = self.task_queue.list_tasks(mission_id)
        if not tasks:
            mission.progress = 0.0
        else:
            completed = len([task for task in tasks if task.status == "Completed"])
            mission.progress = round((completed / len(tasks)) * 100.0, 1)
        mission.current_task_id = self.next_ready_task_id(mission_id)
        mission.updated_at = timestamp_now()
        self.save_missions()

    def next_ready_task(self, mission_id: str) -> Optional[Task]:
        return self.task_queue.next_ready_task(mission_id)

    def get_task_statuses(self, mission_id: str) -> List[Dict[str, Any]]:
        return [task.to_dict() for task in self.task_queue.list_tasks(mission_id)]

    def task_completed(self, task_id: str, result: Optional[str] = None) -> None:
        task = self.task_queue.mark_completed(task_id, result)
        if task:
            self.update_mission_progress(task.mission_id)
            if not self.task_queue.has_pending_tasks(task.mission_id):
                self.complete_mission(task.mission_id)

    def task_failed(self, task_id: str, result: Optional[str] = None) -> None:
        task = self.task_queue.mark_failed(task_id, result)
        if task:
            self.update_mission_progress(task.mission_id)
            mission = self.get_mission(task.mission_id)
            if mission and task.retry_count > 1:
                mission.status = "Failed"
                mission.updated_at = timestamp_now()
                self.save_missions()

    def cancel_mission(self, mission_id: str) -> None:
        mission = self.get_mission(mission_id)
        if not mission:
            return
        mission.status = "Cancelled"
        mission.updated_at = timestamp_now()
        for task in self.task_queue.list_tasks(mission_id):
            if task.status in ["Waiting", "Running"]:
                self.task_queue.mark_cancelled(task.id, "Mission cancelled")
        self.save_missions()
