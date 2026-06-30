"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : __init__.py

PATH    : core\__init__.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

# JARVIS Core Package Initializer
import logging

# Logging setup taaki errors ka pata chale
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("JARVIS_CORE")

try:
    # Saare modules ko yahan link kar rahe hain
    from brain.brain import JarvisBrain
    from voice.voice import speak
    from .intent_engine import IntentEngine
    from .tool_manager import ToolManager
    from automation.workspace_manager import WorkspaceManager
    from .environment_engine import EnvironmentEngine
    from .widget_manager import WidgetManager
    
    # Ye line confirm karti hai ki core folder load ho gaya hai
    print("Neural Handshake: Core systems initialized, Boss.")
    
except ImportError as e:
    print(f"Neural Link Error: Module missing in core. {e}")
except Exception as e:
    print(f"Critical System Failure during initialization: {e}")

# Versioning
__version__ = "5.0.1"