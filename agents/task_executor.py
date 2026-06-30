"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : task_executor.py

PATH    : core\task_executor.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

from typing import Any, List, Optional

from agents.agent_manager import AgentManager
from agents.goal_parser import GoalParser
from agents.mission_manager import MissionManager
from agents.planning_utils import timestamp_now
from agents.task_queue import Task


MAX_RETRIES = 2


class TaskExecutor:
    def __init__(self, mission_manager: MissionManager, agent_manager: AgentManager, brain: Any = None, planner: Any = None):
        self.mission_manager = mission_manager
        self.agent_manager = agent_manager
        self.brain = brain
        self.planner = planner

    def execute_ready_tasks(self, mission_id: str, max_steps: int = 1) -> List[str]:
        results: List[str] = []
        for _ in range(max_steps):
            task = self.mission_manager.next_ready_task(mission_id)
            if not task:
                break
            result = self.execute_task(task)
            results.append(result)
            if task.status == "Failed" and task.retry_count >= MAX_RETRIES:
                break
        return results

    def execute_task(self, task: Task) -> str:
        self.mission_manager.task_queue.mark_running(task.id)
        self.publish_event("task.started", task)

        try:
            result = self.agent_manager.execute_task(task, brain=self.brain)
            if result is None:
                result = "Task executed with no direct output."
            self.mission_manager.task_completed(task.id, result)
            self.publish_event("task.completed", task, result)
            return result
        except Exception as exc:
            self.mission_manager.task_failed(task.id, str(exc))
            self.publish_event("task.failed", task, str(exc))
            return f"Task failed: {exc}"

    def publish_event(self, event_type: str, task: Task, result: Optional[str] = None) -> None:
        if self.planner is not None and hasattr(self.planner, "emit_event"):
            payload = {
                "task_id": task.id,
                "mission_id": task.mission_id,
                "task_name": task.name,
                "status": task.status,
                "agent": task.agent,
                "result": result,
                "timestamp": timestamp_now(),
            }
            self.planner.emit_event(event_type, payload)
