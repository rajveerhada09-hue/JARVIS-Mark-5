import traceback
from core.intent_engine import IntentEngine
from core.tool_manager import ToolManager


class Kernel:
    """
    Central orchestrator (NOT logic owner)
    """

    def __init__(self):
        self.intent_engine = IntentEngine()
        self.tool_manager = ToolManager()
        self.context_engine = None
        self.memory_engine = None
        self.workspace_manager = None
        self.brain = None
        self.voice = None
        self.vision = None

        self.event_bus = {}
        self._running = False
        self._paused = False
        self._register_default_events()
        self._load_context()
        self._load_memory()
        self._load_workspace()
        self._load_brain()
        self._load_voice()
        self._load_vision()

    def _load_context(self):
        try:
            from brain.context_engine import ContextEngine
            self.context_engine = ContextEngine()
        except Exception as e:
            print(f"[KERNEL] Context engine unavailable: {e}")
            self.context_engine = None

    def _load_memory(self):
        try:
            from memory.memory_engine import MemoryEngine
            self.memory_engine = MemoryEngine()
        except Exception as e:
            print(f"[KERNEL] Memory engine unavailable: {e}")
            self.memory_engine = None

    def _load_workspace(self):
        try:
            from automation.workspace_manager import WorkspaceManager
            self.workspace_manager = WorkspaceManager()
        except Exception as e:
            print(f"[KERNEL] Workspace manager unavailable: {e}")
            self.workspace_manager = None

    def _load_brain(self):
        try:
            from brain.brain import JarvisBrain
            self.brain = JarvisBrain()
        except Exception as e:
            print(f"[KERNEL] Brain unavailable: {e}")
            self.brain = None

    def _load_voice(self):
        try:
            from voice import voice as voice_module
            self.voice = voice_module
        except Exception as e:
            print(f"[KERNEL] Voice module unavailable: {e}")
            self.voice = None

    def _load_vision(self):
        try:
            from vision import vision as vision_module
            self.vision = vision_module
        except Exception as e:
            print(f"[KERNEL] Vision module unavailable: {e}")
            self.vision = None

    # ---------------- INIT ----------------
    def initialize(self):
        print("[KERNEL] Booting JARVIS Core Systems...")
        if hasattr(self.brain, "initialize"):
            self.brain.initialize()

        self._running = True
        self._paused = False
        print("[KERNEL] All systems online.")
        return True

    def boot(self):
        return self.initialize()

    # ---------------- EVENT SYSTEM ----------------
    def _register_default_events(self):
        self.event_bus = {
            "intent": self.handle_intent,
            "brain": self.handle_brain,
            "tool": self.handle_tool,
            "workspace": self.handle_workspace,
        }

    def emit(self, event_type, payload):
        try:
            handler = self.event_bus.get(event_type)
            if handler:
                return handler(payload)
            return f"[KERNEL] No handler for {event_type}"
        except Exception as e:
            traceback.print_exc()
            return f"[KERNEL ERROR] {e}"

    # ---------------- QUERY PIPELINE ----------------
    def process_query(self, query: str):
        if self._paused:
            return "System is paused, Boss."

        query = query.lower().strip()
        intent = self.intent_engine.classify(query)

        if intent.get("type") == "workspace":
            return self.emit("workspace", query)

        tool_result = self.emit("tool", intent)
        if tool_result:
            return tool_result

        if self.brain is not None:
            return self.emit("brain", query)

        return "Brain is currently unavailable, Boss."

    def pause(self):
        self._paused = True
        if self.voice is not None and hasattr(self.voice, "stop_speaking"):
            self.voice.stop_speaking()
        return "System paused."

    def resume(self):
        self._paused = False
        if self.voice is not None and hasattr(self.voice, "resume_speech"):
            self.voice.resume_speech()
        return "System resumed."

    def shutdown(self):
        self._running = False
        self._paused = False
        if self.voice is not None and hasattr(self.voice, "stop_speaking"):
            self.voice.stop_speaking()
        return "System shutting down."

    def system_status(self):
        return {
            "running": self._running,
            "paused": self._paused,
            "brain_ready": self.brain is not None,
            "voice_ready": self.voice is not None,
            "vision_ready": self.vision is not None,
            "memory_ready": self.memory_engine is not None,
            "context_ready": self.context_engine is not None,
        }

    # ---------------- HANDLERS ----------------
    def handle_tool(self, intent):
        return self.tool_manager.execute_intent(intent)

    def handle_workspace(self, query):
        if self.workspace_manager is None:
            return "Workspace manager is currently unavailable, Boss."
        return self.workspace_manager.launch_workspace(query)

    def handle_brain(self, query):
        if self.brain is None:
            return "Brain is currently unavailable, Boss."
        return self.brain.process_query(query)

    def handle_intent(self, query):
        return self.intent_engine.classify(query)