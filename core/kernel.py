import traceback
import logging
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
        self.services = {}
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
            context = ContextEngine()

            self.register_service(
                    "context",
                    context
                )

            self.context_engine = self.get_service("context")
        except Exception as e:
            print(f"[KERNEL] Context engine unavailable: {e}")
            self.context_engine = None

    def _load_memory(self):
        try:
            from memory.memory_engine import MemoryEngine
            memory = MemoryEngine()

            self.register_service("memory", memory)
            self.memory_engine = self.get_service("memory")
            
        except Exception as e:
            print(f"[KERNEL] Memory engine unavailable: {e}")
            self.memory_engine = None

    def _load_workspace(self):
        try:
            from automation.workspace_manager import WorkspaceManager
            workspace = WorkspaceManager()

            self.register_service(
                "workspace",
                workspace
            )

            self.workspace_manager = self.get_service("workspace")

        except Exception as e:
            print(f"[KERNEL] Workspace manager unavailable: {e}")
            self.workspace_manager = None

    def _load_brain(self):
        try:
            from brain.brain import JarvisBrain
            brain = JarvisBrain()

            self.register_service(
                "brain",
                brain
            )
            self.brain = brain

        except Exception as e:
            print(f"[KERNEL] Brain unavailable: {e}")
            self.brain = None

    def _load_voice(self):
        try:
            from voice.tts import voice as voice_module

            self.register_service(
                "voice",
                voice_module
            )

            self.voice = self.get_service("voice")
        except Exception as e:
            print(f"[KERNEL] Voice module unavailable: {e}")
            self.voice = None

    def _load_vision(self):
        try:
            from vision import vision as vision_module
            
            self.register_service(
                "vision",
                vision_module
            )

            self.vision = self.get_service("vision")
        except Exception as e:
            print(f"[KERNEL] Vision module unavailable: {e}")
            self.vision = None

    # ---------------- INIT ----------------
    def initialize(self):
        print("[KERNEL] Booting JARVIS Core Systems...")
        brain = self.get_service("brain")

        if brain and hasattr(brain, "initialize"):
            brain.initialize()
           

        self._running = True
        self.subscribe("intent", self.handle_intent)
        self.subscribe("brain", self.handle_brain)
        self.subscribe("tool", self.handle_tool)
        self.subscribe("workspace", self.handle_workspace)
        self._paused = False
        print("[KERNEL] All systems online.")
        return True

    def boot(self):
        return self.initialize()

    # ---------------- EVENT SYSTEM ----------------
    def _register_default_events(self):
        self.event_bus = {}

    def emit(self, event_name, payload=None):
        listeners = self.event_bus.get(event_name, [])

        result = None

        for callback in listeners:
            try:
                result = callback(payload)

            except Exception as e:
                logging.exception("Kernel Event Crash")
                traceback.print_exc()

        return result


    # ---------------- QUERY PIPELINE ----------------
    def process_query(self, query: str):
        if self._paused:
            return "System is paused, Sir."

        query = query.lower().strip()
        intent = self.intent_engine.classify(query)

        if intent.get("type") == "workspace":
            return self.emit("workspace", query)

        tool_result = self.emit("tool", intent)

        if tool_result is not None:
                return tool_result

        brain = self.get_service("brain")

        if brain:
            return brain.process_query(query)
           

        return "Brain is currently unavailable, Sir."

    def pause(self):
        self._paused = True

        voice = self.get_service("voice")

        if voice and hasattr(voice, "stop_speaking"):
            voice.stop_speaking()

        return "System paused."

    def resume(self):
        self._paused = False

        voice = self.get_service("voice")

        if voice and hasattr(voice, "resume_speech"):
            voice.resume_speech()

        return "System resumed."

    def shutdown(self):
        self._running = False
        self._paused = False
        voice = self.get_service("voice")

        if voice and hasattr(voice, "stop_speaking"):
            voice.stop_speaking()
        return "System shutting down."

    def system_status(self):
        return {
        "running": self._running,
        "paused": self._paused,

        "memory_ready": self.get_service("memory") is not None,
        "context_ready": self.get_service("context") is not None,
        "workspace_ready": self.get_service("workspace") is not None,
        "brain_ready": self.get_service("brain") is not None,
        "voice_ready": self.get_service("voice") is not None,
        "vision_ready": self.get_service("vision") is not None,

        "services": len(self.services),
        "registered": list(self.services.keys()),
    }

    # ---------------- HANDLERS ----------------
    def handle_tool(self, intent):
        return self.tool_manager.execute_intent(intent)

    def handle_workspace(self, query):
        workspace = self.get_service("workspace")

        if workspace is None:
            return "Workspace manager is currently unavailable, Sir."

        return workspace.launch_workspace(query)

    def handle_brain(self, query):
        brain = self.get_service("brain")

        if brain is None:
            return "Brain is currently unavailable, Sir."

        return brain.process_query(query)

    def handle_intent(self, query):
        return self.intent_engine.classify(query)
    
    def register_service(self, name: str, service):
        """
        Register a service inside the kernel.
        """

        self.services[name] = service
        setattr(self, name, service)


    def get_service(self, name: str):
        """
        Retrieve a registered service.
        """

        return self.services.get(name)
    
    def subscribe(self, event_name, callback):
        if event_name not in self.event_bus:
            self.event_bus[event_name] = []

        self.event_bus[event_name].append(callback)

    def unsubscribe(self, event_name, callback):
        if event_name in self.event_bus:
            if callback in self.event_bus[event_name]:
                self.event_bus[event_name].remove(callback)
