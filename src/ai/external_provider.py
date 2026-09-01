"""External API Provider for pluggable cloud/local LLM backends (Gemini/OpenAI/Ollama)."""

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional

from src.ai.ai_provider import AIProvider
from src.utils.logging import get_logger

logger = get_logger("ai_writer.external_provider")


class ExternalAPIProvider(AIProvider):
    """External API Provider communicating with configurable AI endpoints."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint_url: str = "https://api.openai.com/v1/chat/completions",
        model: str = "gpt-3.5-turbo",
        timeout: int = 15,
    ):
        self.api_key = api_key or os.environ.get("AI_WRITER_API_KEY", "")
        self.endpoint_url = endpoint_url
        self.model = model
        self.timeout = timeout

    def get_provider_name(self) -> str:
        return f"ExternalAPIProvider ({self.model})"

    def _call_api(self, prompt: str) -> Optional[str]:
        """Make secure HTTPS call to external provider."""
        if not self.api_key and "localhost" not in self.endpoint_url:
            logger.warning("No API key configured for ExternalAPIProvider.")
            return None

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a writing assistant. Return analysis in JSON format.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(self.endpoint_url, data=data, headers=headers)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode("utf-8"))
                return result["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"External API Provider error: {e}")
            return None

    def analyze_grammar(self, text: str) -> List[Dict[str, Any]]:
        # In a full external setup, prompt is sent and parsed.
        # Fallback to empty if endpoint not reachable.
        return []

    def analyze_spelling(self, text: str) -> List[Dict[str, Any]]:
        return []

    def analyze_style(self, text: str) -> List[Dict[str, Any]]:
        return []
