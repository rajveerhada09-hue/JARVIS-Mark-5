"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : brain.py
PATH    : core\brain.py

PURPOSE :
Central orchestrator. Owns the LLM-generation pipeline stage of the
conversation flow:

    Persona Decision (read) -> Layered Prompt Building -> Gemini Response
    (primary) -> ChatGPT (fallback) -> HumanLayer (opt-in)

CHANGES vs original:
  1. Added `import re`, `from typing import Optional` — needed internally.
  2. Added self.gemini_model, loaded from jarvis_config.json (safe default
     "gemini-pro" if config missing/unreadable).
  3. Added _load_gemini_model_name() — small, defensive config reader,
     mirrors the existing try/except style already used in load_mode().
  4. Added _build_layered_prompt() — replaces the old single f-string with
     clearly labelled [SYSTEM]/[PERSONA]/[CONTEXT]/[USER] sections.
  5. Added _gemini_response() — primary LLM call via google-generativeai
     (confirmed dependency in requirements.txt). Returns None on any
     failure instead of raising, so the caller can fall back cleanly.
  6. Added _ollama_response() — the ORIGINAL Ollama subprocess call,
     extracted verbatim into its own method. Same command, same model,
     same timeout. Now returns None on failure instead of a hardcoded
     string, so the caller owns the single final fallback message.
  7. Rewrote _local_llm_response() to orchestrate the chain above.
     SIGNATURE IS BACKWARD COMPATIBLE: existing call site in
     conversation_engine.py — `self.brain._local_llm_response(q_raw,
     extra_context=extra)` — behaves IDENTICALLY to before (returns a
     plain, non-humanized string). Two NEW optional keyword args were
     added at the end with safe defaults:
        humanize: bool = False  — opt-in HumanLayer pass before returning
        emotion:  str = "neutral" — only used when humanize=True
     Default behavior is unchanged specifically to avoid a double-
     humanization bug: conversation_engine.py ALREADY calls
     self.human.enhance() on whatever this method returns (line 228 of
     conversation_engine.py). If this method humanized by default too,
     every response would be humanized twice. See explanation sent
     alongside this file for the full reasoning.
  8. process_query() unchanged in behavior — added phase comments for
     readability and wrapped the ConversationEngine delegation in a
     try/except so a bug inside conv.handle() can never crash JARVIS or
     propagate past brain.py.
  9. Every other method (load_mode, save_mode, switch_mode,
     get_god_mode_prompt, call_node_bridge, emit_event,
     _time_aware_greeting) is UNCHANGED — copied verbatim.

COMPATIBILITY:
  - JarvisBrain() constructor: same, no required args.
  - Public attributes (.memory, .human_layer, .persona_engine,
    .context_engine, .conv, etc.): all present, all unchanged, same
    init order preserved (self.conv = ConversationEngine(self) still
    constructed LAST, after every attribute it reads is set).
  - .process_query(query): same signature, same return type (str).
  - .switch_mode(mode): unchanged.
  - .call_node_bridge(command, argument): unchanged.
  - ._local_llm_response(user_input, extra_context=""): existing call
    sites unaffected; two new optional kwargs added at the end only.

LAST UPDATED : 2026-07-03
============================================================
"""

import os
import re
import json
import logging
import datetime
import traceback
import subprocess
from typing import Optional
from dotenv import load_dotenv
from colorama import Fore, init

init(autoreset=True)
load_dotenv()

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
        # NEW: primary LLM is Gemini (per jarvis_config.json model_primary),
        # Ollama remains the local fallback — see _local_llm_response().
        self.gemini_model = self._load_gemini_model_name()
        print(Fore.GREEN + f"✅ | Gemini primary → {self.gemini_model}")

        self.personality_prompt = self.get_god_mode_prompt()

        # last used address (Sir/Sir/Rajveer) to avoid repetition
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

        # Conversation engine — constructed LAST: it reads .memory,
        # .human_layer, .persona_engine, .context_engine off `self`,
        # all of which must already exist by this point.
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
- Address Rajveer as Sir, Sir, or Rajveer based on context.
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

        # ── Phase 1: Memory observation ─────────────────────────────────────
        # Log the raw utterance for possible persistence; never blocks flow.
        try:
            self.memory_router.observe(q_raw, metadata={'time': str(datetime.datetime.now())})
        except:
            pass

        # ── Phase 2: Goal / Mission parsing ─────────────────────────────────
        parsed_goal = self.goal_parser.parse_goal(q_raw)
        if parsed_goal and parsed_goal.get("action") == "resume":
            mission = self.mission_manager.get_unfinished_mission()
            if mission:
                self.mission_manager.resume_mission(mission.id)
                return f"Resuming mission: {mission.name}."
            return "There is no unfinished mission to resume, Sir."

        if parsed_goal and parsed_goal.get("action") == "status":
            mission = self.mission_manager.get_unfinished_mission()
            if not mission:
                return "No active mission found, Sir."
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

        # ── Phase 3: Working-memory cue extraction ──────────────────────────
        q = q_raw.lower()
        try:
            if any(x in q for x in ['work on', 'working on', 'task', 'todo', 'fix', 'implement']):
                self.memory_router.remember_working('current_task', q_raw)
            if any(x in q for x in ['open project', 'open workspace', 'open folder', 'open repo']):
                self.memory_router.remember_working('current_project', q_raw.replace('open ', '').strip())
        except:
            pass

        # ── Phase 4: Delegate to ConversationEngine ─────────────────────────
        # ConversationEngine owns: persona detection, context/memory
        # retrieval, calling _local_llm_response() below, memory storage
        # (_persist_exchange), and HumanLayer.enhance(). Wrapped so a bug
        # anywhere in that chain can never crash JARVIS or propagate up.
        try:
            return self.conv.handle(query)
        except Exception as e:
            logging.error(f"process_query fatal error: {e}\n{traceback.format_exc()}")
            return "Sir, kuch internal issue aa gaya. Main recover kar raha hoon — phir se try karo."

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

    # ── NEW: config reader for the primary Gemini model name ────────────────
    def _load_gemini_model_name(self) -> str:
        """
        Read model_primary from jarvis_config.json. Safe/defensive: any
        failure (missing file, bad JSON, missing key) falls back to
        "gemini-pro" — mirrors the existing try/except style in load_mode().
        """
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), "jarvis_config.json"
            )
            if os.path.exists(config_path):
                with open(config_path, "r", encoding="utf-8") as f:
                    raw = f.read()
                    raw = re.sub(r"/\*.*?\*/", "", raw, flags=re.DOTALL)  # strip JS-style comment block
                    data = json.loads(raw)
                    return data.get("model_primary", "gemini-pro")
        except Exception:
            pass
        return "gemini-pro"

    # ── NEW: layered prompt builder ──────────────────────────────────────────
    def _build_layered_prompt(self, user_input: str, extra_context: str = "") -> str:
        """
        Build the LLM prompt in clearly labelled layers instead of one flat
        string:
            [SYSTEM]  — self.personality_prompt (mode-specific)
            [PERSONA] — which mode is currently active (explicit, auditable
                        read of self.current_mode — does NOT re-run persona
                        detection, so this never duplicates the persona
                        lookup ConversationEngine already performed)
            [CONTEXT] — extra_context: memory/Mem0/working-memory/style
                        hints already retrieved upstream by ConversationEngine
                        + ContextEngine. NOT re-fetched here, to avoid
                        duplicate memory calls.
            [USER]    — the current query
        """
        layers = [f"[SYSTEM]\n{self.personality_prompt.strip()}"]
        layers.append(f"[PERSONA]\nActive mode: {self.current_mode.upper()}")

        if extra_context and extra_context.strip():
            layers.append(f"[CONTEXT]\n{extra_context.strip()}")

        layers.append(f"[USER]\n{user_input.strip()}")
        return "\n\n".join(layers)

    # ── NEW: Gemini primary LLM call ─────────────────────────────────────────
    def _gemini_response(self, prompt: str) -> Optional[str]:
        """
        Primary LLM call via google-generativeai (confirmed dependency in
        requirements.txt). Returns None on ANY failure — missing SDK,
        missing API key, network error, empty response — so the caller
        can fall back to Ollama. Never raises.
        """
        try:
            import google.generativeai as genai
        except ImportError:
            logging.warning("google-generativeai not installed — falling back to Ollama.")
            return None

        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            logging.warning("GEMINI_API_KEY not set — falling back to Ollama.")
            return None

        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.gemini_model)
            result = model.generate_content(prompt)
            text = (getattr(result, "text", "") or "").strip()
            return text or None
        except Exception as e:
            logging.error(f"Gemini Error: {e}")
            return None

    # ── Ollama fallback (original subprocess call, extracted verbatim) ──────
    def _ollama_response(self, prompt: str) -> Optional[str]:
        """
        Fallback LLM: local Ollama model (self.ollama_model). Same command,
        same timeout as the original implementation. Returns None on
        failure instead of a hardcoded string — the caller
        (_local_llm_response) owns the single final fallback message.
        """
        try:
            result = subprocess.run(
                ["ollama", "run", self.ollama_model, prompt],
                capture_output=True, text=True, timeout=75,
            )
            response = result.stdout.strip()
            return response or None
        except Exception as e:
            logging.error(f"Ollama Error: {e}")
            return None

    def _local_llm_response(
        self,
        user_input,
        extra_context: str = "",
        humanize: bool = False,
        emotion: str = "neutral",
    ):
        """
        LLM-generation pipeline stage: Layered Prompt Building -> Gemini
        (primary) -> Ollama (fallback) -> static safe string (final
        fallback) -> optional HumanLayer pass.

        BACKWARD COMPATIBLE: existing call site in conversation_engine.py
        (`self.brain._local_llm_response(q_raw, extra_context=extra)`)
        behaves EXACTLY as before — returns a plain, non-humanized string.

        `humanize` defaults to False deliberately: conversation_engine.py
        already calls self.human.enhance() on this method's return value
        right after calling it. Setting humanize=True here by default
        would humanize every response twice. Pass humanize=True only from
        a NEW call site that does not separately call HumanLayer itself.
        """
        prompt = self._build_layered_prompt(user_input, extra_context)

        response = self._gemini_response(prompt)
        if response is None:
            response = self._ollama_response(prompt)
        if response is None:
            response = "Sir, abhi mera brain thoda busy hai. Thoda wait kar."

        if humanize:
            try:
                metadata = {"emotion": emotion, "detected_mode": self.current_mode}
                response = self.human_layer.enhance(response, metadata=metadata)
            except Exception as e:
                logging.error(f"HumanLayer enhancement failed: {e}")

        return response

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
        addrs = ["Sir", "Rajveer"]
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