"""Mock AI Provider for deterministic offline testing and edge-case simulation."""

from typing import Any, Dict, List, Optional

from src.ai.ai_provider import AIProvider


class MockProvider(AIProvider):
    """Deterministic mock provider with configurable responses and failure triggers."""

    def __init__(self, should_fail: bool = False, custom_suggestions: Optional[List[Dict[str, Any]]] = None):
        self.should_fail = should_fail
        self.custom_suggestions = custom_suggestions or []

    def get_provider_name(self) -> str:
        return "MockAIProvider"

    def analyze_grammar(self, text: str) -> List[Dict[str, Any]]:
        if self.should_fail:
            raise RuntimeError("Simulated AI Provider Failure in Grammar analysis")
        results = []
        if "This are" in text:
            results.append({
                "original": "This are",
                "replacement": "This is",
                "message": "Subject-verb agreement error. Use 'This is'.",
                "severity": "Medium",
            })
        if "They is" in text:
            results.append({
                "original": "They is",
                "replacement": "They are",
                "message": "Subject-verb agreement error. Use 'They are'.",
                "severity": "Medium",
            })
        return results

    def analyze_spelling(self, text: str) -> List[Dict[str, Any]]:
        if self.should_fail:
            raise RuntimeError("Simulated AI Provider Failure in Spelling analysis")
        results = []
        words_map = {
            "teh": "the",
            "definately": "definitely",
            "recieve": "receive",
            "seperate": "separate",
            "occured": "occurred",
        }
        for wrong, correct in words_map.items():
            if wrong in text:
                results.append({
                    "original": wrong,
                    "replacement": correct,
                    "message": f"Possible spelling mistake: '{wrong}' -> '{correct}'.",
                    "severity": "Low",
                })
        return results

    def analyze_style(self, text: str) -> List[Dict[str, Any]]:
        if self.should_fail:
            raise RuntimeError("Simulated AI Provider Failure in Style analysis")
        results = []
        if "in order to" in text:
            results.append({
                "original": "in order to",
                "replacement": "to",
                "message": "Wordy phrase. Consider simplifying 'in order to' to 'to'.",
                "severity": "Low",
            })
        if "at this point in time" in text:
            results.append({
                "original": "at this point in time",
                "replacement": "now",
                "message": "Cliché/Wordy phrase. Replace with 'now' or 'currently'.",
                "severity": "Low",
            })
        return results
