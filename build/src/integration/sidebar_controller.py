"""Sidebar controller managing user interactions and UI state transitions."""

from typing import Any, Callable, Dict, List, Optional

from src.models.analysis_result import AnalysisResult
from src.models.document import Document
from src.models.suggestion import Suggestion, SuggestionStatus
from src.utils.logging import get_logger

logger = get_logger("ai_writer.sidebar_controller")


class SidebarController:
    """Coordinates UI state and user interactions with AIController."""

    def __init__(self, ai_controller: Any):
        self.ai_controller = ai_controller
        self.current_result: Optional[AnalysisResult] = None
        self._listeners: List[Callable[[str, Any], None]] = []

    def add_ui_listener(self, callback: Callable[[str, Any], None]) -> None:
        """Register a callback for UI updates: callback(event_name, data)."""
        self._listeners.append(callback)

    def _notify(self, event_name: str, data: Any = None) -> None:
        for listener in self._listeners:
            try:
                listener(event_name, data)
            except Exception as e:
                logger.error(f"Error in UI listener: {e}")

    def on_analyze_requested(self, document: Document) -> Optional[AnalysisResult]:
        """Trigger document analysis workflow."""
        logger.info(f"Analysis requested for document: {document.fileName}")
        self._notify("analysis_started", {"fileName": document.fileName})
        result = self.ai_controller.analyze(document)
        self.current_result = result
        self._notify("analysis_completed", result)
        return result

    def on_suggestion_clicked(self, suggestion_id: str, document: Document) -> bool:
        """Navigate to and select issue in document."""
        s = self._find_suggestion(suggestion_id)
        if not s or not s.range:
            return False
        return self.ai_controller.navigateToIssue(s, document)

    def on_suggestion_accepted(self, suggestion_id: str, document: Document) -> bool:
        """Accept and safely apply suggestion to document."""
        s = self._find_suggestion(suggestion_id)
        if not s:
            return False
        logger.info(f"User accepted suggestion: {suggestion_id}")
        success, reason = self.ai_controller.applySuggestion(s, document)
        self._notify(
            "suggestion_updated",
            {"suggestion": s, "success": success, "reason": reason},
        )
        return success

    def on_suggestion_rejected(self, suggestion_id: str) -> None:
        """Reject suggestion without touching document."""
        s = self._find_suggestion(suggestion_id)
        if s:
            logger.info(f"User rejected suggestion: {suggestion_id}")
            self.ai_controller.rejectSuggestion(s)
            self._notify("suggestion_updated", {"suggestion": s})

    def on_suggestion_ignored(self, suggestion_id: str) -> None:
        """Ignore suggestion."""
        s = self._find_suggestion(suggestion_id)
        if s:
            logger.info(f"User ignored suggestion: {suggestion_id}")
            self.ai_controller.ignoreSuggestion(s)
            self._notify("suggestion_updated", {"suggestion": s})

    def on_export_report_requested(self, format: str = "markdown", target_path: Optional[str] = None) -> Optional[str]:
        """Export current analysis report to file."""
        if not self.current_result:
            return None
        report = self.ai_controller.generateReport(self.current_result)
        path = report.export(target_path, format=format)
        self._notify("report_exported", {"path": path, "format": format})
        return path

    def _find_suggestion(self, suggestion_id: str) -> Optional[Suggestion]:
        if not self.current_result:
            return None
        for s in self.current_result.suggestions:
            if s.suggestionId == suggestion_id:
                return s
        return None
