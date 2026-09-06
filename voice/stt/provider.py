"""
============================================================
PROJECT : JARVIS MARK 5
FILE    : provider.py
PATH    : voice/stt/provider.py
PURPOSE : STT Provider Base Interface
============================================================
"""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class STTProvider(ABC):
    """Abstract base class for STT providers"""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider identifier"""
        pass

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Whether provider is ready to use"""
        pass

    @property
    @abstractmethod
    def requires_network(self) -> bool:
        """Whether provider requires internet connection"""
        pass

    @abstractmethod
    def transcribe(self, audio: np.ndarray, language: Optional[str] = None) -> Optional[str]:
        """Transcribe audio to text"""
        pass

    @abstractmethod
    def shutdown(self):
        """Cleanup resources"""
        pass


class STTProviderRegistry:
    """Registry of available STT providers"""

    _providers = {}

    @classmethod
    def register(cls, name: str, factory_func):
        """Register a provider factory"""
        cls._providers[name] = factory_func

    @classmethod
    def create(cls, name: str, **kwargs) -> Optional[STTProvider]:
        """Create a provider instance"""
        if name in cls._providers:
            return cls._providers[name](**kwargs)
        return None

    @classmethod
    def list_available(cls) -> list:
        """List registered provider names"""
        return list(cls._providers.keys())