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

from typing import Optional, Dict, Any

from automation.pc_control import open_app, pc_control_master
from automation.browser_control import BrowserController


class WorkspaceManager:
    """Workspace and development environment manager."""

    def _build_status(self, vscode: bool = False, chrome: bool = False,
                      chatgpt: bool = False, claude: bool = False,
                      spotify: bool = False) -> Dict[str, Any]:
        return {
            "vscode": {"opened": vscode},
            "chrome": {"opened": chrome},
            "chatgpt": {"focused": chatgpt},
            "claude": {"focused": claude},
            "spotify": {"opened": spotify},
        }

    def launch_workspace(self, command: str) -> Optional[str]:
        if not command:
            return None

        text = command.lower().strip()

        if any(keyword in text for keyword in ["workspace", "work mode", "ready the workspace", "let's work", "i'm back", "work chalu", "chalu karo"]):
            self.open_workspace_mode()
            return "Workspace mode activated."

        if any(keyword in text for keyword in ["vscode", "project", "repo", "code"]):
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

    def open_workspace_mode(self) -> Dict[str, Any]:
        open_app("vscode")
        open_app("chrome")
        open_app("spotify")

        BrowserController.execute("open google")
        BrowserController.execute("open chatgpt")
        BrowserController.execute("open claude")

        return self._build_status(
            vscode=True,
            chrome=True,
            chatgpt=True,
            claude=True,
            spotify=True,
        )
