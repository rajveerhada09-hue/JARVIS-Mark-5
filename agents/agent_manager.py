"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : agent_manager.py

PATH    : core\agent_manager.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import webbrowser
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from automation.pc_control import open_app, pc_control_master
from agents.task_queue import Task


class BaseAgent(ABC):
    name: str
    categories: List[str]

    def __init__(self):
        self.name = self.__class__.__name__
        self.categories = []

    def can_handle(self, task: Task) -> bool:
        return task.category in self.categories

    @abstractmethod
    def execute(self, task: Task, brain: Any = None) -> str:
        pass


class AutomationAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.categories = ["automation", "open", "setup", "environment"]

    def execute(self, task: Task, brain: Any = None) -> str:
        payload = task.payload or task.name
        command = str(payload).strip()

        if command.lower().startswith("http"):
            webbrowser.open(command)
            return f"Opened URL: {command}"

        if "spotify" in command.lower():
            open_app("spotify")
            return "Launching Spotify in background."

        if "code" in command.lower() or "vscode" in command.lower():
            open_app("vscode")
            return "Opening VS Code."

        if "browser" in command.lower() or "chatgpt" in command.lower() or "grok" in command.lower() or "claude" in command.lower():
            if "chatgpt" in command.lower():
                webbrowser.open("https://chat.openai.com")
                return "Opening ChatGPT in browser."
            if "claude" in command.lower():
                webbrowser.open("https://claude.ai")
                return "Opening Claude in browser."
            if "grok" in command.lower():
                webbrowser.open("https://grok.com")
                return "Opening Grok in browser."
            if "claude" in command.lower():
                webbrowser.open("https://claude.ai")
                return "Opening Claude in browser."

        if command:
            pc_control_master(f"open {command}")
            return f"Opening {command}."

        return "Automation task completed."


class ResearchAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.categories = ["research"]

    def execute(self, task: Task, brain: Any = None) -> str:
        prompt = f"Research the following objective and summarize the results:\n{task.payload or task.name}"
        if brain is not None and hasattr(brain, "_local_llm_response"):
            response = brain._local_llm_response(prompt)
            return response or "Research completed."
        return f"Research completed for: {task.name}."


class PlanningAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.categories = ["planning", "strategy"]

    def execute(self, task: Task, brain: Any = None) -> str:
        prompt = f"Create a structured plan for the following objective:\n{task.payload or task.name}"
        if brain is not None and hasattr(brain, "_local_llm_response"):
            response = brain._local_llm_response(prompt)
            return response or "Planning step completed."
        return f"Planning step completed for: {task.name}."


class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.categories = ["coding", "development", "write_code", "generate_structure", "testing", "deployment"]

    def execute(self, task: Task, brain: Any = None) -> str:
        prompt = f"Execute a coding-oriented task:\n{task.payload or task.name}"
        if brain is not None and hasattr(brain, "_local_llm_response"):
            response = brain._local_llm_response(prompt)
            return response or "Coding task completed."
        return f"Coding task completed: {task.name}."


class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.categories = ["memory"]

    def execute(self, task: Task, brain: Any = None) -> str:
        if brain is not None and hasattr(brain, "memory"):
            try:
                brain.memory.remember(task.name, task.payload)
                return f"Remembered: {task.name}."
            except Exception:
                pass
        return f"Memory task completed: {task.name}."


class VisionAgent(BaseAgent):
    def __init__(self):
        super().__init__()
        self.categories = ["vision"]

    def execute(self, task: Task, brain: Any = None) -> str:
        return f"Vision task completed: {task.name}."


class AgentManager:
    def __init__(self):
        self.agents: List[BaseAgent] = [
            AutomationAgent(),
            ResearchAgent(),
            PlanningAgent(),
            CodingAgent(),
            MemoryAgent(),
            VisionAgent(),
        ]

    def find_agent(self, task: Task) -> BaseAgent:
        for agent in self.agents:
            if agent.can_handle(task):
                return agent
        return AutomationAgent()

    def execute_task(self, task: Task, brain: Any = None) -> str:
        agent = self.find_agent(task)
        return agent.execute(task, brain=brain)
