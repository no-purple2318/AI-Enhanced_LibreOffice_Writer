"""AIModel abstraction representing an underlying AI/NLP model."""

import uuid
from abc import ABC, abstractmethod


class AIModel(ABC):
    """Abstract base class for AI Models."""

    def __init__(
        self,
        modelId: str = None,
        modelName: str = "RuleBasedNLP",
        version: str = "1.0.0",
        modelPath: str = "",
    ):
        self.modelId: str = modelId or str(uuid.uuid4())
        self.modelName: str = modelName
        self.version: str = version
        self.modelPath: str = modelPath
        self._is_loaded: bool = False

    @abstractmethod
    def loadModel(self) -> bool:
        """Load or initialize model resources."""
        pass

    @abstractmethod
    def predict(self, input_text: str) -> str:
        """Execute inference or prediction on the input text."""
        pass

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded
