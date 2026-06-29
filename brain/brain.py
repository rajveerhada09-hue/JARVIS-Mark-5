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
import traceback
import subprocess
from dotenv import load_dotenv
from colorama import Fore, init

init(autoreset=True)
load_dotenv()

logging.basicConfig(filename='logs/jarvis_brain.log', level=logging.INFO)

from core.personality.human_layer import HumanLayer
from core.personality.persona_engine import PersonaEngine
from core.memory.memory_engine import MemoryEngine
from core.conversation_engine import ConversationEngine
from core.memory_router import MemoryRouter
from core.context_engine import ContextEngine
from core.knowledge_graph import KnowledgeGraph
from core.profile_manager import ProfileManager
from core.agent_manager import AgentManager
from core.goal_parser import GoalParser
from core.mission_manager import MissionManager
from core.task_executor import TaskExecutor
from core.intent_engine import IntentEngine
from core.tool_manager import ToolManager
from core.environment_engine import EnvironmentEngine
from core.widget_manager import WidgetManager

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

        print(Fore.CYAN + f"🧠 God Mode Brain Initialized | Mode: {self.current_mode.upper()}")

        self.ollama_model = "qwen2:7b"
        print(Fore.GREEN + f"✅ Local Brain Active → Ollama ({self.ollama_model})")

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
            script_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "core", "automation.js")
            subprocess.Popen(["node", script_path, command, argument], shell=True)
            return True
        except:
            return False

    def process_query(self, query):
        q_raw = query.strip()

        # Observe the utterance for possible persistence
        try:
            self.memory_router.observe(q_raw, metadata={'time': str(datetime.datetime.now())})
        except:
            pass

        parsed_goal = self.goal_parser.parse_goal(q_raw)
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

        # Simple task/project cue detection and working memory updates
        q = q_raw.lower()
        try:
            if any(x in q for x in ['work on', 'working on', 'task', 'todo', 'fix', 'implement']):
                self.memory_router.remember_working('current_task', q_raw)
            if any(x in q for x in ['open project', 'open workspace', 'open folder', 'open repo']):
                self.memory_router.remember_working('current_project', q_raw.replace('open ', '').strip())
        except:
            pass

        # Delegate to ConversationEngine for conversation handling
        return self.conv.handle(query)

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

    def _local_llm_response(self, user_input, extra_context: str = ""):
        try:
            prompt = f"{self.personality_prompt}\n{extra_context}\n\nUser: {user_input}"

            result = subprocess.run([
                "ollama", "run", self.ollama_model, prompt
            ], capture_output=True, text=True, timeout=75)

            response = result.stdout.strip()
            return response if response else "Boss, soch raha hoon ek minute..."
        except Exception as e:
            logging.error(f"Ollama Error: {e}")
            return "Boss, abhi mera local brain thoda busy hai. Thoda wait kar."

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
