"""Document Consistency Analyzer module for names, terminology, dates, and numbers."""

import difflib
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from src.analysis.analysis_module import AnalysisModule
from src.models.document import Document
from src.models.document_range import DocumentRange
from src.models.suggestion import (
    Severity,
    Suggestion,
    SuggestionStatus,
    SuggestionType,
)


class ConsistencyAnalyzer(AnalysisModule):
    """Detects name variations, terminology discrepancies, and inconsistent date/number formatting."""

    # Common terminology variant pairs: { canonical_or_preferred: [variants] }
    KNOWN_VARIANTS = {
        "AI model": ["artificial intelligence model", "ai-model"],
        "e-mail": ["email", "e mail"],
        "front-end": ["frontend", "front end"],
        "back-end": ["backend", "back end"],
        "open-source": ["open source", "opensource"],
        "dataset": ["data set", "data-set"],
        "multi-threaded": ["multithreaded", "multi threaded"],
        "real-time": ["realtime", "real time"],
        "plug-in": ["plugin", "plug in"],
        "sub-system": ["subsystem", "sub system"],
    }

    # Number words mapping for comparison (e.g. "10 pages" vs "ten pages")
    NUMBER_WORDS = {
        "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
        "6": "six", "7": "seven", "8": "eight", "9": "nine", "10": "ten",
        "11": "eleven", "12": "twelve", "20": "twenty", "50": "fifty", "100": "hundred",
    }

    def __init__(self, moduleId: Optional[str] = None):
        super().__init__(moduleId=moduleId, moduleName="ConsistencyAnalyzer")
        self._last_report: Dict[str, Any] = {}

    def checkNames(self, document: Document) -> List[Suggestion]:
        """Detect possible entity/name spelling inconsistencies with advisory warnings."""
        suggestions = []
        full_text = document.getText()

        # Extract multi-word capitalized named candidates (e.g. "John Smith", "Jon Smith")
        name_pattern = r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\b"
        all_matches: List[Tuple[str, int, int]] = []  # (name, para_id, offset)

        for p in document.paragraphs:
            for m in re.finditer(name_pattern, p.text):
                all_matches.append((m.group(0), p.id, m.start()))

        unique_names = list({m[0] for m in all_matches})

        # Compare pairs for fuzzy similarity
        reported_pairs: Set[Tuple[str, str]] = set()
        for i in range(len(unique_names)):
            for j in range(i + 1, len(unique_names)):
                n1, n2 = unique_names[i], unique_names[j]
                # If similarity is high (> 0.8) and not identical
                similarity = difflib.SequenceMatcher(None, n1.lower(), n2.lower()).ratio()
                if 0.75 <= similarity < 1.0:
                    pair_key = tuple(sorted([n1, n2]))
                    if pair_key in reported_pairs:
                        continue
                    reported_pairs.add(pair_key)

                    # Find occurrences of the less frequent one or both
                    for name_str, p_id, offset in all_matches:
                        if name_str in (n1, n2):
                            other = n2 if name_str == n1 else n1
                            s = Suggestion(
                                type=SuggestionType.Consistency,
                                category="Names",
                                message=f"Possible name inconsistency detected: '{name_str}' vs '{other}'.",
                                originalText=name_str,
                                suggestedText=other,
                                range=DocumentRange(
                                    paragraph_id=p_id,
                                    start_offset=offset,
                                    end_offset=offset + len(name_str),
                                ),
                                position=f"Paragraph {p_id + 1}",
                                severity=Severity.Medium,
                                status=SuggestionStatus.New,
                            )
                            suggestions.append(s)
        return suggestions

    def checkTerminology(self, document: Document) -> List[Suggestion]:
        """Detect inconsistent terminology usages across paragraphs."""
        suggestions = []
        full_text = document.getText().lower()

        for canonical, variants in self.KNOWN_VARIANTS.items():
            all_forms = [canonical.lower()] + [v.lower() for v in variants]
            found_forms = {f for f in all_forms if f in full_text}

            # If more than one variant appears in the same document
            if len(found_forms) > 1:
                dominant_form = max(found_forms, key=lambda f: full_text.count(f))
                for p in document.paragraphs:
                    for form in found_forms:
                        if form != dominant_form:
                            for m in re.finditer(re.escape(form), p.text, flags=re.IGNORECASE):
                                orig = m.group(0)
                                s = Suggestion(
                                    type=SuggestionType.Consistency,
                                    category="Terminology",
                                    message=f"Inconsistent terminology: Document uses both '{orig}' and '{dominant_form}'. Consider standardizing.",
                                    originalText=orig,
                                    suggestedText=dominant_form,
                                    range=DocumentRange(
                                        paragraph_id=p.id,
                                        start_offset=m.start(),
                                        end_offset=m.end(),
                                    ),
                                    position=f"Paragraph {p.id + 1}",
                                    severity=Severity.High,
                                    status=SuggestionStatus.New,
                                )
                                suggestions.append(s)
        return suggestions

    def validateDatesAndNumbers(self, document: Document) -> List[Suggestion]:
        """Validate date formatting patterns and numerical expressions."""
        suggestions = []

        # Date format detection: DD/MM/YYYY vs MM/DD/YYYY vs YYYY-MM-DD
        iso_date_pattern = r"\b\d{4}-\d{2}-\d{2}\b"
        slash_date_pattern = r"\b\d{1,2}/\d{1,2}/\d{4}\b"
        word_date_pattern = r"\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},\s+\d{4}\b"

        iso_count = 0
        slash_count = 0
        word_count = 0

        for p in document.paragraphs:
            iso_count += len(re.findall(iso_date_pattern, p.text))
            slash_count += len(re.findall(slash_date_pattern, p.text))
            word_count += len(re.findall(word_date_pattern, p.text, flags=re.IGNORECASE))

        formats_found = sum(1 for c in [iso_count, slash_count, word_count] if c > 0)
        if formats_found > 1:
            for p in document.paragraphs:
                for m in re.finditer(slash_date_pattern, p.text):
                    s = Suggestion(
                        type=SuggestionType.Consistency,
                        category="Dates",
                        message="Inconsistent date formatting: Multiple date styles detected (numeric slash vs ISO / spelled). Consider standardizing on a single format.",
                        originalText=m.group(0),
                        suggestedText="",
                        range=DocumentRange(
                            paragraph_id=p.id,
                            start_offset=m.start(),
                            end_offset=m.end(),
                        ),
                        position=f"Paragraph {p.id + 1}",
                        severity=Severity.Medium,
                        status=SuggestionStatus.New,
                    )
                    suggestions.append(s)

        # Number expression check (e.g. "10 pages" vs "ten pages")
        for num_digit, num_word in self.NUMBER_WORDS.items():
            pattern_digit = rf"\b{num_digit}\s+([a-z]+)\b"
            pattern_word = rf"\b{num_word}\s+([a-z]+)\b"

            nouns_with_digit: Set[str] = set()
            nouns_with_word: Set[str] = set()

            for p in document.paragraphs:
                for m in re.finditer(pattern_digit, p.text, flags=re.IGNORECASE):
                    nouns_with_digit.add(m.group(1).lower())
                for m in re.finditer(pattern_word, p.text, flags=re.IGNORECASE):
                    nouns_with_word.add(m.group(1).lower())

            clashing_nouns = nouns_with_digit.intersection(nouns_with_word)
            if clashing_nouns:
                for noun in clashing_nouns:
                    for p in document.paragraphs:
                        for m in re.finditer(rf"\b{num_word}\s+{noun}\b", p.text, flags=re.IGNORECASE):
                            s = Suggestion(
                                type=SuggestionType.Consistency,
                                category="Numbers",
                                message=f"Inconsistent number style: Document uses both '{num_digit} {noun}' and '{num_word} {noun}'.",
                                originalText=m.group(0),
                                suggestedText=f"{num_digit} {noun}",
                                range=DocumentRange(
                                    paragraph_id=p.id,
                                    start_offset=m.start(),
                                    end_offset=m.end(),
                                ),
                                position=f"Paragraph {p.id + 1}",
                                severity=Severity.Low,
                                status=SuggestionStatus.New,
                            )
                            suggestions.append(s)

        return suggestions

    def generateConsistencyReport(self) -> Dict[str, Any]:
        """Generate structured summary of consistency analysis."""
        return self._last_report

    def analyze(self, document: Document) -> List[Suggestion]:
        """Perform comprehensive consistency analysis."""
        if not document:
            return []

        suggestions: List[Suggestion] = []
        name_issues = self.checkNames(document)
        term_issues = self.checkTerminology(document)
        date_num_issues = self.validateDatesAndNumbers(document)

        suggestions.extend(name_issues)
        suggestions.extend(term_issues)
        suggestions.extend(date_num_issues)

        for s in suggestions:
            s.revision = document.current_revision

        self._last_report = {
            "name_issues_count": len(name_issues),
            "terminology_issues_count": len(term_issues),
            "date_number_issues_count": len(date_num_issues),
            "total": len(suggestions),
        }
        return suggestions
