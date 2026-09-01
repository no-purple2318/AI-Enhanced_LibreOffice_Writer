"""Writing Assistant module for detecting grammar, spelling, and style problems."""

import re
from typing import List, Optional

from src.ai.ai_provider import AIProvider
from src.ai.local_provider import LocalRuleBasedProvider
from src.analysis.analysis_module import AnalysisModule
from src.models.document import Document, Paragraph
from src.models.document_range import DocumentRange
from src.models.suggestion import (
    Severity,
    Suggestion,
    SuggestionStatus,
    SuggestionType,
)


class WritingAssistant(AnalysisModule):
    """Detects grammar issues, spelling mistakes, and style improvements."""

    def __init__(
        self,
        moduleId: Optional[str] = None,
        ai_provider: Optional[AIProvider] = None,
    ):
        super().__init__(
            moduleId=moduleId,
            moduleName="WritingAssistant",
            ai_provider=ai_provider or LocalRuleBasedProvider(),
        )

    def checkGrammar(self, text: str, paragraph_id: int = 0) -> List[Suggestion]:
        """Detect grammar anomalies in text using AI/Rule provider."""
        suggestions = []
        if not text or not self.ai_provider:
            return suggestions

        raw_issues = self.ai_provider.analyze_grammar(text)
        for issue in raw_issues:
            orig = issue["original"]
            repl = issue["replacement"]
            msg = issue["message"]
            sev = Severity(issue.get("severity", "Medium"))

            start = issue.get("start")
            end = issue.get("end")
            if start is None or end is None:
                match = re.search(re.escape(orig), text)
                if match:
                    start = match.start()
                    end = match.end()
                else:
                    start, end = 0, len(orig)

            s = Suggestion(
                type=SuggestionType.Grammar,
                category="Grammar",
                message=msg,
                originalText=orig,
                suggestedText=repl,
                range=DocumentRange(
                    paragraph_id=paragraph_id,
                    start_offset=start,
                    end_offset=end,
                ),
                position=f"Paragraph {paragraph_id + 1} (chars {start}-{end})",
                severity=sev,
                status=SuggestionStatus.New,
            )
            suggestions.append(s)
        return suggestions

    def checkSpelling(self, text: str, paragraph_id: int = 0) -> List[Suggestion]:
        """Detect spelling errors in text."""
        suggestions = []
        if not text or not self.ai_provider:
            return suggestions

        raw_issues = self.ai_provider.analyze_spelling(text)
        for issue in raw_issues:
            orig = issue["original"]
            repl = issue["replacement"]
            msg = issue["message"]
            sev = Severity(issue.get("severity", "Low"))

            start = issue.get("start")
            end = issue.get("end")
            if start is None or end is None:
                match = re.search(re.escape(orig), text)
                if match:
                    start = match.start()
                    end = match.end()
                else:
                    start, end = 0, len(orig)

            s = Suggestion(
                type=SuggestionType.Spelling,
                category="Spelling",
                message=msg,
                originalText=orig,
                suggestedText=repl,
                range=DocumentRange(
                    paragraph_id=paragraph_id,
                    start_offset=start,
                    end_offset=end,
                ),
                position=f"Paragraph {paragraph_id + 1} (chars {start}-{end})",
                severity=sev,
                status=SuggestionStatus.New,
            )
            suggestions.append(s)
        return suggestions

    def generateStyleSuggestions(self, text: str, paragraph_id: int = 0) -> List[Suggestion]:
        """Generate style and clarity suggestions."""
        suggestions = []
        if not text or not self.ai_provider:
            return suggestions

        raw_issues = self.ai_provider.analyze_style(text)
        for issue in raw_issues:
            orig = issue["original"]
            repl = issue["replacement"]
            msg = issue["message"]
            sev = Severity(issue.get("severity", "Low"))

            start = issue.get("start")
            end = issue.get("end")
            if start is None or end is None:
                match = re.search(re.escape(orig), text)
                if match:
                    start = match.start()
                    end = match.end()
                else:
                    start, end = 0, len(orig)

            s = Suggestion(
                type=SuggestionType.Style,
                category="Style",
                message=msg,
                originalText=orig,
                suggestedText=repl,
                range=DocumentRange(
                    paragraph_id=paragraph_id,
                    start_offset=start,
                    end_offset=end,
                ),
                position=f"Paragraph {paragraph_id + 1} (chars {start}-{end})",
                severity=sev,
                status=SuggestionStatus.New,
            )
            suggestions.append(s)
        return suggestions

    def analyze(self, document: Document) -> List[Suggestion]:
        """Analyze full document across all paragraphs."""
        all_suggestions = []
        if not document:
            return all_suggestions

        for p in document.paragraphs:
            if not p.text.strip():
                continue
            all_suggestions.extend(self.checkGrammar(p.text, paragraph_id=p.id))
            all_suggestions.extend(self.checkSpelling(p.text, paragraph_id=p.id))
            all_suggestions.extend(self.generateStyleSuggestions(p.text, paragraph_id=p.id))

        # Assign document revision reference
        for s in all_suggestions:
            s.revision = document.current_revision

        return all_suggestions
