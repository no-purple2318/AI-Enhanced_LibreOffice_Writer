"""AIController coordinating document parsing, module execution, quality calculation, and safe suggestion application."""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.ai.ai_provider import AIProvider
from src.ai.local_provider import LocalRuleBasedProvider
from src.analysis.consistency_analyzer import ConsistencyAnalyzer
from src.analysis.formatting_engine import FormattingEngine
from src.analysis.readability_module import ReadabilityModule
from src.analysis.sensitive_info_detector import SensitiveInfoDetector
from src.analysis.writing_assistant import WritingAssistant
from src.integration.uno_cursor_adapter import UNOCursorAdapter
from src.models.analysis_result import AnalysisResult
from src.models.document import Document
from src.models.report import Report
from src.models.suggestion import Suggestion, SuggestionStatus
from src.parser.document_parser import DocumentParser
from src.services.quality_service import QualityService
from src.services.report_service import ReportService
from src.services.suggestion_service import SuggestionService
from src.utils.config import Config
from src.utils.logging import get_logger

logger = get_logger("ai_writer.controller")


class AIController:
    """Central controller coordinating document analysis and suggestion lifecycle."""

    def __init__(
        self,
        controllerId: Optional[str] = None,
        config: Optional[Config] = None,
        ai_provider: Optional[AIProvider] = None,
    ):
        self.controllerId: str = controllerId or str(uuid.uuid4())
        self.config: Config = config or Config()
        self.ai_provider: AIProvider = ai_provider or LocalRuleBasedProvider()

        # Instantiate parser, services, and modules
        self.parser = DocumentParser()
        self.quality_service = QualityService(self.config)
        self.suggestion_service = SuggestionService()
        self.report_service = ReportService()

        # The 5 major analysis modules
        self.writing_assistant = WritingAssistant(ai_provider=self.ai_provider)
        self.consistency_analyzer = ConsistencyAnalyzer()
        self.formatting_engine = FormattingEngine()
        self.readability_module = ReadabilityModule()
        self.sensitive_info_detector = SensitiveInfoDetector()

        self._last_result: Optional[AnalysisResult] = None
        self._current_document: Optional[Document] = None

    def analyze(self, document: Document) -> AnalysisResult:
        """Execute complete document analysis pipeline across all 5 intelligent modules.
        
        Guarantees fault-tolerance: if a module fails, it records the error and continues.
        """
        logger.info(f"Analysis started for document: {document.fileName} (ID: {document.documentId[:8]})")
        start_time = time.time()
        self._current_document = document

        # Ensure document revision is fresh
        document.create_revision()

        all_suggestions: List[Suggestion] = []
        module_times: Dict[str, float] = {}
        module_errors: Dict[str, str] = {}

        # 1. Writing Assistant
        if self.config.get("enableGrammar", True) or self.config.get("enableSpelling", True) or self.config.get("enableStyle", True):
            t0 = time.time()
            try:
                w_suggs = self.writing_assistant.analyze(document)
                all_suggestions.extend(w_suggs)
            except Exception as e:
                logger.error(f"WritingAssistant failed: {e}", exc_info=True)
                module_errors["WritingAssistant"] = str(e)
            finally:
                module_times["WritingAssistant"] = round(time.time() - t0, 4)

        # 2. Consistency Analyzer
        if self.config.get("enableConsistency", True):
            t0 = time.time()
            try:
                c_suggs = self.consistency_analyzer.analyze(document)
                all_suggestions.extend(c_suggs)
            except Exception as e:
                logger.error(f"ConsistencyAnalyzer failed: {e}", exc_info=True)
                module_errors["ConsistencyAnalyzer"] = str(e)
            finally:
                module_times["ConsistencyAnalyzer"] = round(time.time() - t0, 4)

        # 3. Formatting Engine
        if self.config.get("enableFormatting", True):
            t0 = time.time()
            try:
                f_suggs = self.formatting_engine.analyze(document)
                all_suggestions.extend(f_suggs)
            except Exception as e:
                logger.error(f"FormattingEngine failed: {e}", exc_info=True)
                module_errors["FormattingEngine"] = str(e)
            finally:
                module_times["FormattingEngine"] = round(time.time() - t0, 4)

        # 4. Readability Module
        flesch_score = 100.0
        if self.config.get("enableReadability", True):
            t0 = time.time()
            try:
                r_suggs = self.readability_module.analyze(document)
                all_suggestions.extend(r_suggs)
                flesch_score = self.readability_module._last_flesch_score
            except Exception as e:
                logger.error(f"ReadabilityModule failed: {e}", exc_info=True)
                module_errors["ReadabilityModule"] = str(e)
            finally:
                module_times["ReadabilityModule"] = round(time.time() - t0, 4)

        # 5. Sensitive Information Detector
        if self.config.get("enablePrivacyDetection", True):
            t0 = time.time()
            try:
                p_suggs = self.sensitive_info_detector.analyze(document)
                all_suggestions.extend(p_suggs)
            except Exception as e:
                logger.error(f"SensitiveInfoDetector failed: {e}", exc_info=True)
                module_errors["SensitiveInfoDetector"] = str(e)
            finally:
                module_times["SensitiveInfoDetector"] = round(time.time() - t0, 4)

        # Calculate Quality Scores
        quality_score = self.quality_service.calculate_scores(
            suggestions=all_suggestions,
            document=document,
            flesch_reading_ease=flesch_score,
        )

        total_elapsed = round(time.time() - start_time, 4)
        logger.info(
            f"Analysis completed in {total_elapsed}s. Found {len(all_suggestions)} issues. Overall score: {quality_score.overallScore:.1f}"
        )

        result = AnalysisResult(
            documentId=document.documentId,
            fileName=document.fileName,
            analyzedAt=datetime.utcnow(),
            suggestions=all_suggestions,
            qualityScore=quality_score,
            moduleExecutionTimes=module_times,
            moduleErrors=module_errors,
            wordCount=len(document.getText().split()),
            paragraphCount=len(document.paragraphs),
        )
        self._last_result = result
        return result

    def getSuggestions(self, status: Optional[SuggestionStatus] = None) -> List[Suggestion]:
        """Return suggestions from the last analysis."""
        if not self._last_result:
            return []
        return self._last_result.getSuggestions(status=status)

    def applySuggestion(
        self, suggestion: Suggestion, document: Optional[Document] = None
    ) -> Tuple[bool, str]:
        """Apply an approved suggestion to the document.
        
        MUST require explicit user initiation. Will NEVER silently modify document.
        """
        doc = document or self._current_document
        if not doc:
            return False, "No active document found to apply suggestion"

        success, reason = self.suggestion_service.apply_suggestion(suggestion, doc)
        if success and self._last_result:
            # Re-evaluate quality scores dynamically
            self._last_result.qualityScore = self.quality_service.calculate_scores(
                suggestions=[s for s in self._last_result.suggestions if s.status not in (SuggestionStatus.Applied, SuggestionStatus.Rejected, SuggestionStatus.Ignored)],
                document=doc,
                flesch_reading_ease=self.readability_module._last_flesch_score,
            )
        return success, reason

    def rejectSuggestion(self, suggestion: Suggestion) -> None:
        """Reject a suggestion without touching document content."""
        self.suggestion_service.reject_suggestion(suggestion)

    def ignoreSuggestion(self, suggestion: Suggestion) -> None:
        """Ignore a suggestion without touching document content."""
        self.suggestion_service.ignore_suggestion(suggestion)

    def navigateToIssue(self, suggestion: Suggestion, document: Optional[Document] = None) -> bool:
        """Move cursor in LibreOffice Writer to highlight the issue."""
        doc = document or self._current_document
        if not doc or not suggestion.range:
            return False
        return UNOCursorAdapter.select_range(doc, suggestion.range)

    def generateReport(self, result: Optional[AnalysisResult] = None) -> Report:
        """Generate a complete quality report."""
        target_result = result or self._last_result
        if not target_result:
            raise ValueError("No analysis result available to generate report")
        return self.report_service.generate_report(target_result)
