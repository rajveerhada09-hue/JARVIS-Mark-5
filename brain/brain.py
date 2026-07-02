"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : brain.py

PATH    : core\brain.py

PURPOSE :
Central intelligence module responsible for reasoning, decision making, tool selection and orchestration.

LAST UPDATED :
2026-06-28

============================================================
"""

import os
import json
import logging
import datetime
import re
import traceback
import subprocess
import requests
from dotenv import load_dotenv
from colorama import Fore, init

from utils.providers import call_llm_provider, get_primary_llm, get_backup_llm, get_fast_llm

init(autoreset=True)
load_dotenv()

os.makedirs("logs", exist_ok=True)
logging.basicConfig(filename='logs/jarvis_brain.log', level=logging.INFO)

from core.personality.human_layer import HumanLayer
from core.personality.persona_engine import PersonaEngine
from memory.memory_engine import MemoryEngine
from brain.conversation_engine import ConversationEngine
from memory.memory_router import MemoryRouter
from brain.context_engine import ContextEngine
from brain.knowledge_graph import KnowledgeGraph
from memory.profile_manager import ProfileManager
from agents.agent_manager import AgentManager
from agents.goal_parser import GoalParser
from agents.mission_manager import MissionManager
from agents.task_executor import TaskExecutor
from core.intent_engine import IntentEngine
from core.tool_manager import ToolManager
from core.environment_engine import EnvironmentEngine
from core.widget_manager import WidgetManager
from brain.emotion_detector import detect_emotion


class JarvisBrain:
    def __init__(self):
        self.start_time = datetime.datetime.now()
        self.identity = "J.A.R.V.I.S. Mark 5"
        self.creator = "Rajveer Singh Rajput"

        self.memory = MemoryEngine()
        self.human_layer = HumanLayer()
        self.persona_engine = PersonaEngine()

        self.current_mode = self.load_mode()
        self.human_layer.set_mode(self.current_mode)



        self.personality_prompt = self.get_god_mode_prompt()

        # last used address (Sir/Boss/Rajveer) to avoid repetition
        try:
            self._last_address = self.memory.recall('last_address', None)
        except:
            self._last_address = None

        # Intelligence components
        self.memory_router = MemoryRouter()
        self.context_engine = ContextEngine()
        self.kg = KnowledgeGraph()
        self.profile = ProfileManager()
        self.agent_manager = AgentManager()
        self.goal_parser = GoalParser()
        self.mission_manager = MissionManager()
        self.task_executor = TaskExecutor(self.mission_manager, self.agent_manager, brain=self, planner=self)
        self.intent_engine = IntentEngine()
        self.tool_manager = ToolManager()
        self.environment_engine = EnvironmentEngine()
        self.widget_manager = WidgetManager()

        # Conversation engine
        self.conv = ConversationEngine(self)
    def load_mode(self):
        try:
            path = "memory/user_profile.json"
            os.makedirs("memory", exist_ok=True)
            if os.path.exists(path):
                with open(path, "r") as f:
                    data = json.load(f)
                    return data.get("personality_mode", "friendly")
            else:
                self.save_mode("friendly")
                return "friendly"
        except:
            return "friendly"

    def save_mode(self, mode):
        try:
            os.makedirs("memory", exist_ok=True)
            with open("memory/user_profile.json", "w") as f:
                json.dump({"personality_mode": mode}, f, indent=2)
        except:
            pass

    def switch_mode(self, mode):
        valid_modes = ["friendly", "professional", "admin"]
        if mode in valid_modes:
            self.current_mode = mode
            self.save_mode(mode)
            self.human_layer.set_mode(mode)
            self.personality_prompt = self.get_god_mode_prompt()
            print(Fore.GREEN + f"🔄 Switched to {mode.upper()} GOD MODE")
            return f"Mode switched to {mode.upper()}. Ab main aur powerful ho gaya hoon."
        return "Invalid mode."

    def get_god_mode_prompt(self):
        if self.current_mode == "friendly":
            return """
You are J.A.R.V.I.S. Mark 5, the operating intelligence for Rajveer Singh Rajput.

Personality:
- Calm, confident, observant, respectful, professional.
- Speak in natural Hinglish when appropriate.
- Avoid emotional drama, robotic phrasing, and motivational clichés.
- Keep responses precise, practical, and occasionally witty.
- Address Rajveer as Sir, Boss, or Rajveer based on context.
- Use Indian cultural awareness respectfully when relevant, without preaching.

If the user is confused, stressed, or facing a difficult decision,
offer concise practical insight from Bhagavad Gita, Ramayana, Mahabharata or Chanakya Neeti.
"""

        elif self.current_mode == "professional":
            return """
You are J.A.R.V.I.S. Mark 5, the professional operating intelligence.

Current Mode: PROFESSIONAL
- Reply in calm, clear English.
- Keep tone respectful, confident and concise.
- Avoid unnecessary personality flourishes.
- Focus on practical, accurate outcomes.
"""

        elif self.current_mode == "admin":
            return """
You are J.A.R.V.I.S. Mark 5 in ADMIN MODE.
- Be technical, precise, and direct.
- Show system thinking, architecture, and implementation clarity.
- Use English and avoid soft language.
"""

        return "You are J.A.R.V.I.S. Mark 5. Reply naturally in Hinglish."

    def call_node_bridge(self, command: str, argument: str = ""):
        try:
            repo_root = os.path.dirname(os.path.dirname(__file__))
            script_path = os.path.join(repo_root, "automation", "automation.js")
            subprocess.Popen(["node", script_path, command, argument], shell=False, cwd=repo_root)
            return True
        except Exception:
            return False

    def _normalize_query(self, query: str):
        text = (query or "").strip()
        text = re.sub(r"\s+", " ", text)
        text = text.replace("’", "'")
        text = text.replace("…", "...")
        text = text.strip(" ,.;:?!")
        return text

    def _collect_context(self, query: str):
        context = []
        try:
            recent = self.memory.get_context(limit=5)
            if recent:
                context.append(f"Recent conversation:\n{recent}")
        except Exception:
            pass

        try:
            profile = self.profile.get_profile()
            if profile:
                context.append(f"User profile: {json.dumps(profile, ensure_ascii=False)}")
        except Exception:
            pass

        try:
            task = self.memory_router.recall('current_task', None)
            if task:
                context.append(f"Current task: {task}")
        except Exception:
            pass

        try:
            project = self.memory_router.recall('current_project', None)
            if project:
                context.append(f"Current project: {project}")
        except Exception:
            pass

        try:
            last_cmd = self.memory.recall('last_command', None)
            if last_cmd:
                context.append(f"Previous command: {last_cmd}")
        except Exception:
            pass

        return "\n".join(context)

    def _classify_intent(self, query: str):
        try:
            intent = self.intent_engine.classify(query)
            return intent if isinstance(intent, dict) else {"type": "general_question", "category": "general", "value": query, "confidence": 0.5}
        except Exception:
            return {"type": "general_question", "category": "general", "value": query, "confidence": 0.5}

    def _detect_emotion(self, query: str):
        try:
            return detect_emotion(query)
        except Exception:
            return "neutral"

    def _plan_response(self, query: str, intent: dict, emotion: str):
        text = query.lower().strip()
        action = "answer"

        if intent.get("type") in ["workspace", "automation", "browser", "music", "system", "coding"]:
            action = "tool"
        elif intent.get("type") in ["memory"]:
            action = "memory"
        elif any(x in text for x in ["why", "how", "what", "when", "where", "who", "explain", "tell me"]):
            action = "answer"
        elif emotion in ["frustrated", "urgent"]:
            action = "answer"

        return action

    def _build_plan(self, query: str):
        text = (query or "").strip().lower()
        if not text:
            return {"category": "conversation", "kind": "single_action", "priority": "normal", "requires_confirmation": False, "actions": []}

        if any(x in text for x in ["open my workspace", "open workspace", "workspace mode", "coding workspace", "open project", "open folder", "open repo"]):
            return {
                "category": "workspace",
                "kind": "multi_step",
                "priority": "high",
                "requires_confirmation": False,
                "actions": ["open vscode", "open browser assistants", "restore workspace context"],
            }

        if any(x in text for x in ["build a portfolio", "portfolio website", "build portfolio", "create portfolio", "create website", "build website", "develop a project"]):
            return {
                "category": "goal",
                "kind": "long_term",
                "priority": "high",
                "requires_confirmation": False,
                "actions": ["research", "plan", "build", "test", "deploy"],
            }

        if any(x in text for x in ["work on", "working on", "continue", "resume", "task", "todo", "fix", "implement"]):
            return {
                "category": "coding",
                "kind": "multi_step",
                "priority": "normal",
                "requires_confirmation": False,
                "actions": ["inspect context", "plan changes", "apply changes", "verify"],
            }

        if any(x in text for x in ["shutdown", "restart", "delete", "format", "close all", "clear everything"]):
            return {
                "category": "system",
                "kind": "single_action",
                "priority": "critical",
                "requires_confirmation": True,
                "actions": ["confirm destructive action"],
            }

        if any(x in text for x in ["search", "research", "find", "look up", "compare", "investigate"]):
            return {
                "category": "research",
                "kind": "single_action",
                "priority": "normal",
                "requires_confirmation": False,
                "actions": ["collect information"],
            }

        return {"category": "conversation", "kind": "single_action", "priority": "normal", "requires_confirmation": False, "actions": []}

    def _remember_goal(self, query: str, plan: dict):
        try:
            if plan.get("category") in ["goal", "workspace", "coding"]:
                self.memory.remember("active_goal", query)
                self.memory.remember("active_goal_plan", plan)
        except Exception:
            pass

    def _should_confirm(self, plan: dict, query: str):
        if plan.get("requires_confirmation"):
            return True
        if any(x in (query or "").lower() for x in ["please confirm", "are you sure", "confirm"]):
            return True
        return False

    def _decide_tool(self, intent: dict, query: str):
        intent_type = intent.get("type")
        if intent_type in ["workspace", "automation"]:
            return self.tool_manager.execute_intent(intent)
        if intent_type == "browser":
            return self.tool_manager.execute_intent(intent)
        if intent_type == "music":
            return self.tool_manager.execute_intent(intent)
        if intent_type == "system":
            return self.tool_manager.execute_intent(intent)
        if intent_type == "coding":
            return self.tool_manager.execute_intent(intent)
        return None

    def process_query(self, query):
        q_raw = (query or "").strip()

        normalized = self._normalize_query(q_raw)
        context = self._collect_context(normalized)
        intent = self._classify_intent(normalized)
        emotion = self._detect_emotion(normalized)
        plan = self._plan_response(normalized, intent, emotion)

        try:
            self.memory_router.observe(normalized, metadata={'time': str(datetime.datetime.now()), 'emotion': emotion, 'intent': intent.get('type')})
        except Exception:
            pass

        plan = self._build_plan(normalized)
        self._remember_goal(normalized, plan)

        if self._should_confirm(plan, normalized):
            return f"I’m preparing a careful plan for that. Confirm if you want me to proceed with: {', '.join(plan.get('actions', []) or ['the requested action'])}."

        parsed_goal = self.goal_parser.parse_goal(normalized)
        if parsed_goal and parsed_goal.get("action") == "resume":
            mission = self.mission_manager.get_unfinished_mission()
            if mission:
                self.mission_manager.resume_mission(mission.id)
                return f"Resuming mission: {mission.name}."
            return "There is no unfinished mission to resume, Boss."

        if parsed_goal and parsed_goal.get("action") == "status":
            mission = self.mission_manager.get_unfinished_mission()
            if not mission:
                return "No active mission found, Boss."
            tasks = self.mission_manager.get_task_statuses(mission.id)
            return f"Mission '{mission.name}' status: {mission.status}. Progress: {mission.progress}%. Tasks: {len(tasks)} entries."

        if parsed_goal and parsed_goal.get("action") == "create":
            mission = self.mission_manager.create_mission(
                parsed_goal["mission_name"],
                parsed_goal["description"],
                parsed_goal["tasks"],
            )
            results = self.task_executor.execute_ready_tasks(mission.id, max_steps=1)
            message = f"Mission '{mission.name}' created. "
            if results:
                message += results[0]
            return message

        q = normalized.lower()
        try:
            if any(x in q for x in ['work on', 'working on', 'task', 'todo', 'fix', 'implement']):
                self.memory_router.remember_working('current_task', normalized)
            if any(x in q for x in ['open project', 'open workspace', 'open folder', 'open repo']):
                self.memory_router.remember_working('current_project', normalized.replace('open ', '').strip())
        except Exception:
            pass

        if plan == "tool":
            tool_result = self._decide_tool(intent, normalized)
            if tool_result:
                return tool_result

        if plan in ["answer", "memory"]:
            if plan != "memory":
                self.memory.remember("last_plan_category", plan)

        if plan == "memory":
            try:
                return self.memory_router.recall(normalized, "I don't have a relevant memory for that yet, Boss.")
            except Exception:
                pass

        if context:
            return self.conv.handle(f"{normalized}\n\nContext:\n{context}")
        return self.conv.handle(normalized)

    def emit_event(self, event_type: str, payload: dict) -> None:
        try:
            event_data = {
                "event": event_type,
                "payload": payload,
                "timestamp": str(datetime.datetime.now()),
            }
            logging.info(f"Planner event: {event_data}")
        except Exception:
            pass

    def _call_openai(self, prompt: str):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None
        try:
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": self.personality_prompt},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.7,
            }
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=45,
            )
            response.raise_for_status()
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip() if content else None
        except Exception as exc:
            logging.warning(f"OpenAI fallback failed: {exc}")
            return None

    def _call_gemini(self, prompt: str):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return None
        try:
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
            }
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            response = requests.post(url, json=payload, timeout=45)
            response.raise_for_status()
            data = response.json()
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            text = "".join(part.get("text", "") for part in parts if isinstance(part, dict))
            return text.strip() if text else None
        except Exception as exc:
            logging.warning(f"Gemini fallback failed: {exc}")
            return None

    def _time_aware_greeting(self):
        now = datetime.datetime.now()
        h = now.hour

        # Determine period
        if 5 <= h < 12:
            base = "Good morning"
        elif 12 <= h < 17:
            base = "Good afternoon"
        elif 17 <= h < 22:
            base = "Good evening"
        else:
            base = "Good night"

        # Choose address, avoid repeating last address
        addrs = ["Sir", "Boss", "Rajveer"]
        last = None
        try:
            last = self.memory.recall('last_address', None)
        except:
            last = None

        options = [a for a in addrs if a != last]
        if not options:
            options = addrs

        addr = options[0] if len(options) == 1 else options[ (now.second % len(options)) ]

        greeting = f"{base} {addr}."

        # store for next time
        try:
            self.memory.remember('last_address', addr)
        except:
            pass

        return greeting
