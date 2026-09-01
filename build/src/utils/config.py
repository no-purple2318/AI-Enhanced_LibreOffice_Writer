"""Configuration loader and manager for AI-Enhanced LibreOffice Writer."""

import json
import os
from typing import Any, Dict


class Config:
    """Manages application-wide configuration settings with sensible defaults."""

    DEFAULT_CONFIG: Dict[str, Any] = {
        "aiProvider": "local",
        "model": "rule-based-nlp-v1",
        "analysisTimeout": 30,
        "enableGrammar": True,
        "enableSpelling": True,
        "enableStyle": True,
        "enableConsistency": True,
        "enableFormatting": True,
        "enableReadability": True,
        "enablePrivacyDetection": True,
        "privacyMode": True,
        "qualityWeights": {
            "writing": 0.25,
            "consistency": 0.20,
            "formatting": 0.20,
            "readability": 0.20,
            "privacy": 0.15,
        },
        "severityDeductions": {
            "critical": 20.0,
            "high": 10.0,
            "medium": 5.0,
            "low": 2.0,
        },
        "connection": {
            "host": "localhost",
            "port": 2002,
            "pipeName": "uno_ai_pipe",
            "connectionType": "socket",
        },
        "logging": {
            "level": "INFO",
            "sanitizeDocumentContent": True,
        },
    }

    def __init__(self, config_path: str = None):
        self._data: Dict[str, Any] = dict(self.DEFAULT_CONFIG)
        if config_path and os.path.exists(config_path):
            self.load_from_file(config_path)
        else:
            default_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "config",
                "default_config.json",
            )
            if os.path.exists(default_path):
                self.load_from_file(default_path)

    def load_from_file(self, file_path: str) -> None:
        """Load configuration from a JSON file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                self._update_deep(self._data, loaded)
        except Exception as e:
            # Fall back to existing configuration
            pass

    def _update_deep(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        for k, v in source.items():
            if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                self._update_deep(target[k], v)
            else:
                target[k] = v

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a config value by dot-notation or top-level key."""
        if "." in key:
            parts = key.split(".")
            curr = self._data
            for p in parts:
                if isinstance(curr, dict) and p in curr:
                    curr = curr[p]
                else:
                    return default
            return curr
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a config value."""
        if "." in key:
            parts = key.split(".")
            curr = self._data
            for p in parts[:-1]:
                if p not in curr or not isinstance(curr[p], dict):
                    curr[p] = {}
                curr = curr[p]
            curr[parts[-1]] = value
        else:
            self._data[key] = value

    @property
    def quality_weights(self) -> Dict[str, float]:
        return self.get("qualityWeights", self.DEFAULT_CONFIG["qualityWeights"])

    @property
    def severity_deductions(self) -> Dict[str, float]:
        return self.get("severityDeductions", self.DEFAULT_CONFIG["severityDeductions"])
