"""AnalysisModule base class for all intelligent document inspection components."""

import uuid
from abc import ABC, abstractmethod
from typing import List, Optional

from src.ai.ai_provider import AIProvider
from src.models.document import Document
from src.models.suggestion import Suggestion


class AnalysisModule(ABC):
    """Abstract base class for all document analysis modules."""

    def __init__(
        self,
        moduleId: Optional[str] = None,
        moduleName: str = "GenericAnalysisModule",
        ai_provider: Optional[AIProvider] = None,
    ):
        self.moduleId: str = moduleId or str(uuid.uuid4())
        self.moduleName: str = moduleName
        self.ai_provider: Optional[AIProvider] = ai_provider

    @abstractmethod
    def analyze(self, document: Document) -> List[Suggestion]:
        """Execute domain-specific analysis on the provided document.
        
        Must return a list of Suggestion objects. Must NOT modify the document.
        """
        pass

    def __str__(self) -> str:
        return f"{self.moduleName} (ID: {self.moduleId[:8]})"
