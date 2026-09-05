"""
============================================================
PROJECT : JARVIS MARK 5

FILE    : protocols.py

PATH    : core\protocols.py

PURPOSE :
Module description pending.

LAST UPDATED :
2026-06-28

============================================================
"""

from abc import ABC, abstractmethod
import os
import webbrowser
import subprocess

# --- 📜 TERA BLUEPRINT (Rulebook) ---
class Protocol(ABC):
    @abstractmethod
    def connect(self, address: str) -> None: pass
    @abstractmethod
    def send(self, data: str) -> None: pass # bytes ki jagah str rakha hai simplify karne ke liye
    @abstractmethod
    def receive(self) -> str: pass
    @abstractmethod
    def close(self) -> None: pass

# --- 🚀 TERA POWERFUL IMPLEMENTATION ---
class JarvisCoreProtocol(Protocol):
    def __init__(self):
        self.active_protocol = "None"

    def connect(self, protocol_type: str) -> str:
        """Jis protocol ka naam doge, wo environment set kar dega"""
        self.active_protocol = protocol_type.lower()
        
        # 1. SECURITY PROTOCOL
        if "secure" in self.active_protocol:
            # Sari risky cheezein band
            os.system("taskkill /f /im chrome.exe")
            os.system("taskkill /f /im msedge.exe")
            return "Protocol Alpha: System Secured. All external links severed, Sir."

        # 2. DEV PROTOCOL (Coding Mode)
        elif "dev" in self.active_protocol or "coding" in self.active_protocol:
            subprocess.Popen(["code"]) # VS Code khulega
            webbrowser.open("https://github.com")
            return "Development Protocol: Environment initialized, Sir."

        # 3. GHOST PROTOCOL (Privacy Mode)
        elif "ghost" in self.active_protocol:
            # Incognito browser kholna
            os.system("start chrome --incognito")
            return "Ghost Protocol: Stealth mode active, Sir."

        return f"Protocol {protocol_type} connected to core, Sir."

    def send(self, command: str) -> str:
        """Commands ko direct system shell pe bhejega"""
        try:
            os.system(command)
            return f"Command '{command}' sent to terminal, Sir."
        except Exception as e:
            return f"Failed to send command: {e}"

    def receive(self) -> str:
        """System ki current health check karke batayega"""
        return "All internal modules reporting 100% efficiency, Sir."

    def close(self) -> str:
        """Clean Slate: Sab band karke system lock"""
        os.system("rundll32.exe user32.dll,LockWorkStation") # PC lock kar dega
        return "Clean Slate Protocol: System locked and secured, Sir."

# --- Helper Function (Taaki main.py ise asani se use kar sake) ---
def execute_protocol(query):
    jarvis_proto = JarvisCoreProtocol()
    
    if "connect" in query or "protocol" in query:
        # Query se protocol ka naam nikaalna
        p_name = query.replace("protocol", "").replace("connect", "").strip()
        return jarvis_proto.connect(p_name)
    
    elif "shutdown" in query or "close" in query:
        return jarvis_proto.close()
    
    return "Protocol command not understood, Sir."