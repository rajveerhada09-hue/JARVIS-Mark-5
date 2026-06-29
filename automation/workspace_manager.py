"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : workspace_manager.py

PATH    : core\workspace_manager.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

from typing import Optional

from core.pc_control import open_app, pc_control_master


class WorkspaceManager:
    """Workspace and development environment manager."""

    def launch_workspace(self, command: str) -> Optional[str]:
        if not command:
            return None

        text = command.lower().strip()

        if any(keyword in text for keyword in ["vscode", "workspace", "project", "repo", "code"]):
            open_app("vscode")
            return "Opening development workspace."

        if any(keyword in text for keyword in ["chatgpt", "claude", "grok", "perplexity"]):
            if "chatgpt" in text:
                return open_app("https://chat.openai.com")
            if "claude" in text:
                return open_app("https://claude.ai")
            if "grok" in text:
                return open_app("https://grok.com")
            if "perplexity" in text:
                return open_app("https://www.perplexity.ai")

        if "spotify" in text:
            open_app("spotify")
            return "Opening Spotify."

        if text.startswith("open "):
            target = text.replace("open ", "", 1).strip()
            open_app(target)
            return f"Opening {target}."

        return pc_control_master(command)
