"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : tasks.py

PATH    : core\tasks.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

import json
import time
import threading
import subprocess
import os
import traceback


class TaskManager:

    def __init__(self):

        self.base_dir = "core/agent_memory"
        os.makedirs(self.base_dir, exist_ok=True)

        self.task_file = os.path.join(
            self.base_dir,
            "tasks.json"
        )

        self.running = True

        self.tools = {
            "screenshot": self._tool_screenshot,
            "shutdown": self._tool_shutdown,
            "open_url": self._tool_open_url,
            "shell": self._tool_shell
        }

    # =================================================
    # STORAGE
    # =================================================

    def _load(self):

        if not os.path.exists(self.task_file):
            return []

        try:
            with open(
                self.task_file,
                "r",
                encoding="utf-8"
            ) as f:
                return json.load(f)

        except:
            return []

    def _save(self, tasks):

        with open(
            self.task_file,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                tasks,
                f,
                indent=4
            )

    # =================================================
    # PUBLIC API
    # =================================================

    def add_task(
        self,
        task_name,
        delay=0,
        action="shell",
        payload=None
    ):

        tasks = self._load()

        task = {
            "id": str(time.time_ns()),
            "task": task_name,
            "run_at": time.time() + delay,
            "action": action,
            "payload": payload,
            "status": "pending",
            "retries": 0
        }

        tasks.append(task)

        self._save(tasks)

        return f"Task scheduled: {task_name}"

    def start(self):

        thread = threading.Thread(
            target=self._loop,
            daemon=True
        )

        thread.start()

    # =================================================
    # TASK VIEWING
    # =================================================

    def get_schedule(self):

        tasks = self._load()

        if not tasks:
            return "No scheduled tasks found."

        output = []

        for i, task in enumerate(tasks, start=1):

            output.append(
                f"{i}. {task['task']} | "
                f"Status: {task['status']}"
            )

        return "\n".join(output)

    # =================================================
    # CLEAR ALL TASKS
    # =================================================

    def clear_schedule(self):

        self._save([])

        return "All scheduled tasks cleared."

    # =================================================
    # CANCEL SINGLE TASK
    # =================================================

    def cancel_task(self, task_number):

        tasks = self._load()

        if not tasks:
            return "No tasks available."

        index = task_number - 1

        if index < 0 or index >= len(tasks):
            return "Invalid task number."

        removed = tasks.pop(index)

        self._save(tasks)

        return (
            f"Cancelled task: "
            f"{removed['task']}"
        )

    # =================================================
    # MAIN LOOP
    # =================================================

    def _loop(self):

        while self.running:

            try:

                tasks = self._load()

                now = time.time()

                updated = []

                for task in tasks:

                    if task["status"] != "pending":
                        updated.append(task)
                        continue

                    if task["run_at"] > now:
                        updated.append(task)
                        continue

                    result = self._execute_task(task)

                    task["status"] = (
                        "done"
                        if result
                        else "failed"
                    )

                    task["last_run"] = now

                    updated.append(task)

                self._save(updated)

                time.sleep(1)

            except Exception as e:

                print(
                    "[TASK AGENT ERROR]",
                    e
                )

    # =================================================
    # EXECUTION ENGINE
    # =================================================

    def _execute_task(self, task):

        action = task.get("action")

        try:

            print(
                f"\n[TASK AGENT] Executing: "
                f"{task['task']} "
                f"| action={action}"
            )

            tool = self.tools.get(action)

            if not tool:

                print(
                    "[TASK AGENT] "
                    "No tool found:"
                    f" {action}"
                )

                return False

            tool(task)

            return True

        except Exception as e:

            print(
                "[TASK EXECUTION ERROR]",
                e
            )

            print(
                traceback.format_exc()
            )

            return False

    # =================================================
    # TOOLS
    # =================================================

    def _tool_screenshot(self, task):

        import pyautogui

        os.makedirs(
            "captures",
            exist_ok=True
        )

        file = (
            f"captures/"
            f"{task['id']}.png"
        )

        pyautogui.screenshot(file)

        print(
            "[TASK] Screenshot saved:",
            file
        )

    def _tool_shutdown(self, task):

        print(
            "[TASK] Shutdown initiated"
        )

        subprocess.run(
            ["shutdown", "/s", "/t", "0"]
        )

    def _tool_open_url(self, task):

        import webbrowser

        url = task.get("payload")

        if url:
            webbrowser.open(url)

    def _tool_shell(self, task):

        cmd = task.get("payload")

        if cmd:
            subprocess.Popen(
                cmd,
                shell=True
            )