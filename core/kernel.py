import importlib
import traceback
from core.intent_engine import IntentEngine
from core.tool_manager import ToolManager
from brain.brain import Brain

class Kernel:
    """
    Central orchestrator (NOT logic owner)
    """

    def __init__(self):
        self.intent_engine = IntentEngine()
        self.tool_manager = ToolManager()
        self.brain = Brain()

        self.event_bus = {}
        self._register_default_events()

    # ---------------- INIT ----------------
    def initialize(self):
        print("[KERNEL] Booting JARVIS Core Systems...")
        self.brain.initialize() if hasattr(self.brain, "initialize") else None
        print("[KERNEL] All systems online.")

    # ---------------- EVENT SYSTEM ----------------
    def _register_default_events(self):
        self.event_bus = {
            "intent": self.handle_intent,
            "brain": self.handle_brain,
            "tool": self.handle_tool
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
        query = query.lower().strip()

        intent = self.intent_engine.classify(query)

        # 1. TOOL LAYER FIRST
        tool_result = self.emit("tool", intent)
        if tool_result:
            return tool_result

        # 2. BRAIN LAYER SECOND
        return self.emit("brain", query)

    # ---------------- HANDLERS ----------------
    def handle_tool(self, intent):
        return self.tool_manager.execute_intent(intent)

    def handle_brain(self, query):
        return self.brain.process_query(query)

    def handle_intent(self, query):
        return self.intent_engine.classify(query)