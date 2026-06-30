"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : core/kernel.py

PURPOSE : Central Orchestrator for the entire system.
============================================================
"""

import os
import json
import logging
import datetime
import subprocess

from brain.brain import JarvisBrain
from core.intent_engine import IntentEngine
from core.tool_manager import ToolManager
from brain.conversation_engine import ConversationEngine
from core.greeting_manager import GreetingManager
from memory.memory_engine import MemoryEngine
from core.personality.human_layer import HumanLayer
from core.personality.persona_engine import PersonaEngine

class Kernel:
    def __init__(self):
        self.brain = JarvisBrain()
        self.intent_engine = IntentEngine()
        self.tool_manager = ToolManager()
        self.conversation_engine = ConversationEngine()
        self.greeting_manager = GreetingManager()
        self.memory = MemoryEngine()
        self.human_layer = HumanLayer()
        self.persona_engine = PersonaEngine()

        logging.basicConfig(filename='logs/kernel.log', level=logging.INFO)

    def initialize(self):
        print("[KERNEL] Initializing all subsystems...")
        self.memory.load()
        print("[KERNEL] Memory Ready")
        print("[KERNEL] All systems initialized.")

    def process_query(self, query):
        context = self.conversation_engine.get_context(query)
        memory_context = self.memory.get_relevant_memory(query)

        intent = self.intent_engine.classify(query)
        tool_result = self.tool_manager.execute_intent(intent)

        if tool_result:
            return tool_result

        raw_response = self.brain.process_query(query)
        return self.human_layer.enhance(raw_response)

    def get_greeting(self):
        return self.greeting_manager.get_greeting()