"""Local rule-based NLP provider for offline analysis without external API dependencies."""

import re
from typing import Any, Dict, List

from src.ai.ai_provider import AIProvider


class LocalRuleBasedProvider(AIProvider):
    """Local offline provider utilizing heuristic rules and dictionary patterns."""

    # Common grammar rules: (pattern, replacement, message, severity)
    GRAMMAR_RULES = [
        (
            r"\b(This|That|It)\s+are\b",
            lambda m: f"{m.group(1)} is",
            "Subject-verb agreement error. Singular subject requires 'is'.",
            "Medium",
        ),
        (
            r"\b(These|Those|They)\s+is\b",
            lambda m: f"{m.group(1)} are",
            "Subject-verb agreement error. Plural subject requires 'are'.",
            "Medium",
        ),
        (
            r"\ba\s+([aeiouAEIOU]\w+)",
            r"an \1",
            "Indefinite article error: Use 'an' before words starting with vowel sounds.",
            "Medium",
        ),
        (
            r"\ban\s+([^aeiouAEIOU\s]\w+)",
            r"a \1",
            "Indefinite article error: Use 'a' before words starting with consonant sounds.",
            "Medium",
        ),
        (
            r"\b(could|should|would)\s+of\b",
            r"\1 have",
            "Common error: 'of' instead of 'have' (e.g., 'could have').",
            "High",
        ),
        (
            r"\b(\w+)\s+\1\b",
            r"\1",
            "Repeated word detected.",
            "Low",
        ),
        (
            r"\b(more|most)\s+(better|faster|cheaper|stronger|easier)\b",
            r"\2",
            "Double comparative/superlative error.",
            "Medium",
        ),
    ]

    # Spelling dictionary / typo mappings
    COMMON_TYPOS = {
        "teh": "the",
        "recieve": "receive",
        "seperate": "separate",
        "definately": "definitely",
        "untill": "until",
        "occured": "occurred",
        "accomodate": "accommodate",
        "embarass": "embarrass",
        "maintainance": "maintenance",
        "goverment": "government",
        "wierd": "weird",
        "truely": "truly",
        "refering": "referring",
        "existance": "existence",
        "calender": "calendar",
        "neccessary": "necessary",
        "suprise": "surprise",
        "wich": "which",
        "tommorrow": "tomorrow",
        "succesful": "successful",
    }

    # Style improvements
    STYLE_RULES = [
        (
            r"\bin order to\b",
            "to",
            "Wordy phrasing: 'in order to' can be simplified to 'to'.",
            "Low",
        ),
        (
            r"\bat this point in time\b",
            "now",
            "Wordy cliché: 'at this point in time' can be replaced with 'now' or 'currently'.",
            "Low",
        ),
        (
            r"\bdue to the fact that\b",
            "because",
            "Wordy phrase: 'due to the fact that' can be simplified to 'because'.",
            "Low",
        ),
        (
            r"\bhas the ability to\b",
            "can",
            "Wordy phrase: 'has the ability to' can be replaced with 'can'.",
            "Low",
        ),
        (
            r"\butilize\b",
            "use",
            "Style recommendation: 'use' is generally clearer and less pretentious than 'utilize'.",
            "Low",
        ),
        (
            r"\ba large number of\b",
            "many",
            "Wordy phrase: 'a large number of' can be simplified to 'many'.",
            "Low",
        ),
    ]

    def get_provider_name(self) -> str:
        return "LocalRuleBasedProvider (Offline)"

    def analyze_grammar(self, text: str) -> List[Dict[str, Any]]:
        results = []
        for pattern, repl_fn, msg, severity in self.GRAMMAR_RULES:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                orig = match.group(0)
                if callable(repl_fn):
                    repl = repl_fn(match)
                else:
                    repl = match.expand(repl_fn)
                results.append({
                    "original": orig,
                    "replacement": repl,
                    "message": msg,
                    "severity": severity,
                    "start": match.start(),
                    "end": match.end(),
                })
        return results

    def analyze_spelling(self, text: str) -> List[Dict[str, Any]]:
        results = []
        words = re.finditer(r"\b[A-Za-z]+\b", text)
        for match in words:
            w = match.group(0)
            w_lower = w.lower()
            if w_lower in self.COMMON_TYPOS:
                correct = self.COMMON_TYPOS[w_lower]
                if w.isupper():
                    correct = correct.upper()
                elif w[0].isupper():
                    correct = correct.capitalize()
                results.append({
                    "original": w,
                    "replacement": correct,
                    "message": f"Possible spelling error: '{w}'. Did you mean '{correct}'?",
                    "severity": "Low",
                    "start": match.start(),
                    "end": match.end(),
                })
        return results

    def analyze_style(self, text: str) -> List[Dict[str, Any]]:
        results = []
        for pattern, repl, msg, severity in self.STYLE_RULES:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                orig = match.group(0)
                results.append({
                    "original": orig,
                    "replacement": repl,
                    "message": msg,
                    "severity": severity,
                    "start": match.start(),
                    "end": match.end(),
                })
        return results
