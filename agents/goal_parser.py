"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : goal_parser.py

PATH    : core\goal_parser.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional

from agents.planning_utils import generate_id, task_priority


class GoalParser:
    def parse_goal(self, query: str) -> Optional[Dict[str, Any]]:
        q = query.lower().strip()

        if any(key in q for key in ["continue tomorrow", "we'll continue tomorrow", "resume", "continue", "pick up", "carry on"]):
            return {"action": "resume"}

        if any(key in q for key in ["mission status", "status of mission", "how is my", "progress", "show mission", "task status"]):
            return {"action": "status"}

        if "open my coding workspace" in q or "open coding workspace" in q or "start my coding workspace" in q:
            tasks = []
            tasks.append({
                "id": generate_id("task"),
                "name": "Check if VS Code is already running",
                "category": "automation",
                "payload": "vscode",
                "priority": task_priority("automation", 100),
                "dependencies": [],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Launch VS Code",
                "category": "automation",
                "payload": "vscode",
                "dependencies": [tasks[0]["id"]],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Open Claude in browser",
                "category": "automation",
                "payload": "open claude.ai",
                "dependencies": [tasks[1]["id"]],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Open ChatGPT in browser",
                "category": "automation",
                "payload": "open chat.openai.com",
                "dependencies": [tasks[1]["id"]],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Open Grok in browser",
                "category": "automation",
                "payload": "open grok.com",
                "dependencies": [tasks[1]["id"]],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Launch Spotify in background",
                "category": "automation",
                "payload": "spotify",
                "dependencies": [tasks[1]["id"]],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Update planning status for coding workspace",
                "category": "memory",
                "payload": "Coding workspace opened and assistants ready.",
                "dependencies": [tasks[5]["id"]],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Report completion of coding workspace setup",
                "category": "planning",
                "payload": "Coding workspace setup is complete.",
                "dependencies": [tasks[6]["id"]],
            })
            return {
                "action": "create",
                "mission_name": "Open Coding Workspace",
                "description": "Prepare the developer environment and launch the most useful research tools.",
                "tasks": tasks,
            }

        if "portfolio website" in q or "build portfolio" in q or "create portfolio" in q:
            tasks = []
            tasks.append({
                "id": generate_id("task"),
                "name": "Research portfolio website goals",
                "category": "research",
                "payload": "Understand the requirements and style for a portfolio website.",
                "priority": task_priority("research", 90),
                "dependencies": [],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Plan the website structure",
                "category": "planning",
                "payload": "Outline pages, sections, and technology choices for the portfolio site.",
                "dependencies": [tasks[0]["id"]],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Create initial website scaffold",
                "category": "coding",
                "payload": "Generate starter HTML, CSS, and project structure for the portfolio website.",
                "dependencies": [tasks[1]["id"]],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Test the initial website locally",
                "category": "testing",
                "payload": "Verify the site loads and the core pages render correctly.",
                "dependencies": [tasks[2]["id"]],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Prepare deployment notes",
                "category": "deployment",
                "payload": "Choose deployment strategy and record the next steps.",
                "dependencies": [tasks[3]["id"]],
            })
            return {
                "action": "create",
                "mission_name": "Build Portfolio Website",
                "description": "Take the portfolio website from research through deployment.",
                "tasks": tasks,
            }

        if any(key in q for key in ["help me build", "help me create", "i need to build", "create a website", "build a website", "develop a project"]):
            tasks = []
            tasks.append({
                "id": generate_id("task"),
                "name": "Research the objective",
                "category": "research",
                "payload": q,
                "priority": task_priority("research", 85),
                "dependencies": [],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Create a plan for the project",
                "category": "planning",
                "payload": q,
                "dependencies": [tasks[0]["id"]],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Produce initial code or structure",
                "category": "coding",
                "payload": q,
                "dependencies": [tasks[1]["id"]],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Validate the draft and test assumptions",
                "category": "testing",
                "payload": q,
                "dependencies": [tasks[2]["id"]],
            })
            tasks.append({
                "id": generate_id("task"),
                "name": "Prepare deployment or next steps",
                "category": "deployment",
                "payload": q,
                "dependencies": [tasks[3]["id"]],
            })
            return {
                "action": "create",
                "mission_name": "Execute Project Goal",
                "description": "Break the requested goal into research, planning, coding, testing, and deployment.",
                "tasks": tasks,
            }

        return None
