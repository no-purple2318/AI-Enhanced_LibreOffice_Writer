"""AIProvider interface defining pluggable AI backends."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class AIProvider(ABC):
    """Abstract interface for swappable AI providers."""

    @abstractmethod
    def analyze_grammar(self, text: str) -> List[Dict[str, Any]]:
        """Return list of detected grammar issues with original and suggested replacement."""
        pass

    @abstractmethod
    def analyze_spelling(self, text: str) -> List[Dict[str, Any]]:
        """Return list of spelling errors with suggested replacements."""
        pass

    @abstractmethod
    def analyze_style(self, text: str) -> List[Dict[str, Any]]:
        """Return style and clarity suggestions."""
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return human-readable provider name."""
        pass
