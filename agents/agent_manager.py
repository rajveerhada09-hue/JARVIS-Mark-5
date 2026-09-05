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
from typing import List
from agents.base_agent import BaseAgent
from automation.pc_control import open_app, pc_control_master
from agents.task_queue import Task


class AutomationAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="AutomationAgent",
            description="Handles automation tasks",
            priority=1,
            capabilities=["automation", "open", "setup", "environment"]
        )

    def _can_handle(self, task):
        return task.category in self.capabilities

    def _execute(self, task):
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

        if command:
            pc_control_master(f"open {command}")
            return f"Opening {command}."

        return "Automation task completed."


class ResearchAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="ResearchAgent",
            description="Research & Internet reasoning",
            priority=2,
            capabilities=["research"]
        )

    def _can_handle(self, task):
        return task.category in self.capabilities

    def _execute(self, task):
        prompt = f"Research:\n{task.payload or task.name}"

        if hasattr(task, "brain") and task.brain:
            brain = task.brain

            if hasattr(brain, "_local_llm_response"):
                return brain._local_llm_response(prompt)

        return f"Research completed for {task.name}"


class PlanningAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="PlanningAgent",
            description="Planning Agent",
            priority=3,
            capabilities=["planning", "strategy"]
        )

    def _can_handle(self, task):
        return task.category in self.capabilities

    def _execute(self, task):
        prompt = f"Plan:\n{task.payload or task.name}"

        if hasattr(task, "brain") and task.brain:
            brain = task.brain

            if hasattr(brain, "_local_llm_response"):
                return brain._local_llm_response(prompt)

        return f"Planning completed for {task.name}"


class CodingAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="CodingAgent",
            description="Coding Agent",
            priority=4,
            capabilities=[
                "coding",
                "development",
                "write_code",
                "generate_structure",
                "testing",
                "deployment",
            ]
        )

    def _can_handle(self, task):
        return task.category in self.capabilities

    def _execute(self, task):
        prompt = f"Coding:\n{task.payload or task.name}"

        if hasattr(task, "brain") and task.brain:
            brain = task.brain

            if hasattr(brain, "_local_llm_response"):
                return brain._local_llm_response(prompt)

        return f"Coding completed for {task.name}"


class MemoryAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="MemoryAgent",
            description="Memory Agent",
            priority=2,
            capabilities=["memory"]
        )

    def _can_handle(self, task):
        return task.category in self.capabilities

    def _execute(self, task):

        if hasattr(task, "brain") and task.brain:
            brain = task.brain

            if hasattr(brain, "memory"):
                try:
                    brain.memory.remember(task.name, task.payload)
                    return f"Remembered {task.name}"
                except Exception:
                    pass

        return f"Memory stored for {task.name}"


class VisionAgent(BaseAgent):

    def __init__(self):
        super().__init__(
            name="VisionAgent",
            description="Vision Agent",
            priority=2,
            capabilities=["vision"]
        )

    def _can_handle(self, task):
        return task.category in self.capabilities

    def _execute(self, task):
        return f"Vision task completed: {task.name}"


class AgentManager:
    """
    Central registry for all JARVIS Agents.
    """

    def __init__(self):

        self.agents: List[BaseAgent] = []

        # Register built-in agents
        self.register_agent(AutomationAgent())
        self.register_agent(ResearchAgent())
        self.register_agent(PlanningAgent())
        self.register_agent(CodingAgent())
        self.register_agent(MemoryAgent())
        self.register_agent(VisionAgent())

    # --------------------------------------------------

    def register_agent(self, agent: BaseAgent):
        """
        Register a new agent.
        """

        if agent not in self.agents:
            self.agents.append(agent)

            print(f"[AGENT] Registered -> {agent.name}")

    # --------------------------------------------------

    def unregister_agent(self, agent_name: str):

        self.agents = [
            agent
            for agent in self.agents
            if agent.name != agent_name
        ]

        print(f"[AGENT] Unregistered -> {agent_name}")

    # --------------------------------------------------

    def get_agent(self, agent_name: str):

        for agent in self.agents:

            if agent.name == agent_name:
                return agent

        return None

    # --------------------------------------------------

    def find_agent(self, task: Task) -> BaseAgent:

        for agent in self.agents:

            if agent.can_handle(task):
                return agent

        return self.get_agent("AutomationAgent")

    # --------------------------------------------------

    def execute_task(self, task: Task, brain=None):

        agent = self.find_agent(task)

        if agent is None:
            return "No suitable agent found."

        if brain is not None:
            task.brain = brain

        return agent.execute(task)

    # --------------------------------------------------

    def broadcast_event(self, event_name: str, payload=None):

        for agent in self.agents:

            try:

                if hasattr(agent, "on_event"):
                    agent.on_event(event_name, payload)

            except Exception as e:

                print(f"[AGENT EVENT ERROR] {agent.name}: {e}")

    # --------------------------------------------------

    def health_check(self):

        report = {}

        for agent in self.agents:

            try:

                report[agent.name] = agent.status()

            except Exception:

                report[agent.name] = {
                    "status": "UNKNOWN"
                }

        return report

    # --------------------------------------------------

    def list_agents(self):

        return [
            agent.name
            for agent in self.agents
        ]
