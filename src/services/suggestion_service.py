"""SuggestionService managing suggestion lifecycle and non-destructive modification protocol."""

from typing import Optional, Tuple

from src.integration.uno_cursor_adapter import UNOCursorAdapter
from src.models.document import Document
from src.models.suggestion import Suggestion, SuggestionStatus
from src.utils.logging import get_logger

logger = get_logger("ai_writer.suggestion_service")


class SuggestionService:
    """Provides safe suggestion validation, application, rejection, and ignore workflows."""

    def __init__(self):
        pass

    def validate_suggestion(
        self, suggestion: Suggestion, document: Document
    ) -> Tuple[bool, str]:
        """Verify that the target document range and content are still valid and uncorrupted."""
        if not suggestion or not document:
            return False, "Invalid suggestion or document reference"

        if not suggestion.range:
            return False, "Suggestion has no associated document range"

        # Check paragraph existence
        p = document.get_paragraph(suggestion.range.paragraph_id)
        if not p:
            return False, f"Target paragraph #{suggestion.range.paragraph_id} was removed"

        # Verify paragraph bounds
        p_len = len(p.text)
        if (
            suggestion.range.start_offset < 0
            or suggestion.range.end_offset > p_len
            or suggestion.range.start_offset > suggestion.range.end_offset
        ):
            return (
                False,
                f"Range offsets [{suggestion.range.start_offset}:{suggestion.range.end_offset}] out of bounds for paragraph length ({p_len})",
            )

        # Verify matching target text (if applicable)
        if suggestion.originalText:
            current_slice = p.text[
                suggestion.range.start_offset : suggestion.range.end_offset
            ]
            if current_slice != suggestion.originalText:
                return (
                    False,
                    f"Document content changed since analysis. Expected '{suggestion.originalText}' but found '{current_slice}'",
                )

        return True, "Valid"

    def apply_suggestion(
        self, suggestion: Suggestion, document: Document
    ) -> Tuple[bool, str]:
        """Safely apply an approved suggestion to the document.
        
        If the document changed since analysis, marks suggestion as Stale/Conflicted and aborts.
        """
        if suggestion.status == SuggestionStatus.Applied:
            return True, "Suggestion already applied"

        valid, reason = self.validate_suggestion(suggestion, document)
        if not valid:
            suggestion.mark_stale(reason)
            logger.warning(
                f"Cannot apply suggestion {suggestion.suggestionId[:8]}: {reason}. Marked as Stale/Conflicted."
            )
            return False, reason

        # Accept the suggestion first
        suggestion.accept()

        # If it is a text replacement suggestion
        if suggestion.originalText and suggestion.suggestedText is not None:
            success, apply_reason = UNOCursorAdapter.safe_replace(
                document=document,
                doc_range=suggestion.range,
                expected_original_text=suggestion.originalText,
                replacement_text=suggestion.suggestedText,
            )
            if not success:
                suggestion.mark_stale(apply_reason)
                return False, apply_reason

        # Mark applied
        suggestion.apply()
        logger.info(f"Suggestion {suggestion.suggestionId[:8]} applied successfully.")
        return True, "Applied successfully"

    def reject_suggestion(self, suggestion: Suggestion) -> None:
        """Reject a suggestion without touching the document."""
        if suggestion:
            suggestion.reject()
            logger.info(f"Suggestion {suggestion.suggestionId[:8]} rejected by user.")

    def ignore_suggestion(self, suggestion: Suggestion) -> None:
        """Ignore a suggestion without touching the document."""
        if suggestion:
            suggestion.ignore()
            logger.info(f"Suggestion {suggestion.suggestionId[:8]} ignored by user.")
