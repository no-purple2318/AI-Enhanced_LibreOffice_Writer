"""Adapter for LibreOffice cursor selection and safe text replacement."""

from typing import Any, Optional, Tuple

from src.models.document import Document
from src.models.document_range import DocumentRange
from src.utils.logging import get_logger

logger = get_logger("ai_writer.cursor_adapter")


class UNOCursorAdapter:
    """Manages cursor positioning, issue selection, and safe text replacement via UNO."""

    @classmethod
    def select_range(cls, document: Document, doc_range: DocumentRange) -> bool:
        """Move Writer cursor / selection to highlight the affected document range."""
        if not document or not doc_range:
            return False

        if not document.uno_component:
            logger.info(f"Mock selecting range in document: {doc_range}")
            return True

        try:
            x_doc = document.uno_component
            x_text = x_doc.getText()
            p = document.get_paragraph(doc_range.paragraph_id)
            if not p or not p.uno_paragraph_ref:
                return False

            cursor = x_text.createTextCursorByRange(p.uno_paragraph_ref.getStart())
            cursor.goRight(doc_range.start_offset, False)
            cursor.goRight(doc_range.length, True)

            # Assign selection to current controller/frame
            controller = x_doc.getCurrentController()
            if controller:
                controller.select(cursor)
            return True

        except Exception as e:
            logger.error(f"Failed to move cursor to range {doc_range}: {e}")
            return False

    @classmethod
    def safe_replace(
        cls,
        document: Document,
        doc_range: DocumentRange,
        expected_original_text: str,
        replacement_text: str,
    ) -> Tuple[bool, str]:
        """Safely replace text at range only if the current document slice strictly matches originalText.
        
        Returns (success, reason_if_failed).
        """
        if not document or not doc_range:
            return False, "Invalid document or range reference"

        p = document.get_paragraph(doc_range.paragraph_id)
        if not p:
            return False, f"Target paragraph #{doc_range.paragraph_id} does not exist"

        # If live UNO component is attached
        if document.uno_component and p.uno_paragraph_ref:
            try:
                elem = p.uno_paragraph_ref
                current_p_text = elem.getString()

                # Verify bounds
                if (
                    doc_range.start_offset < 0
                    or doc_range.end_offset > len(current_p_text)
                    or doc_range.start_offset > doc_range.end_offset
                ):
                    return False, "Target range offsets are out of bounds for current paragraph"

                current_slice = current_p_text[doc_range.start_offset : doc_range.end_offset]
                if expected_original_text and current_slice != expected_original_text:
                    return (
                        False,
                        f"Document text has changed. Expected '{expected_original_text}' but found '{current_slice}'",
                    )

                x_text = document.uno_component.getText()
                cursor = x_text.createTextCursorByRange(elem.getStart())
                cursor.goRight(doc_range.start_offset, False)
                cursor.goRight(doc_range.length, True)
                cursor.setString(replacement_text)

                # Update in-memory representation
                new_p_text = (
                    current_p_text[: doc_range.start_offset]
                    + replacement_text
                    + current_p_text[doc_range.end_offset :]
                )
                p.text = new_p_text
                document.create_revision()
                logger.info(
                    f"Successfully applied text replacement in paragraph {p.id}: '{expected_original_text}' -> '{replacement_text}'"
                )
                return True, "Success"

            except Exception as e:
                logger.error(f"Error applying UNO text replacement: {e}")
                return False, f"UNO error: {e}"

        # Fallback / Simulated in-memory replacement (for test harness)
        current_p_text = p.text
        if (
            doc_range.start_offset < 0
            or doc_range.end_offset > len(current_p_text)
            or doc_range.start_offset > doc_range.end_offset
        ):
            return False, "Target range offsets are out of bounds"

        current_slice = current_p_text[doc_range.start_offset : doc_range.end_offset]
        if expected_original_text and current_slice != expected_original_text:
            return (
                False,
                f"Document text has changed. Expected '{expected_original_text}' but found '{current_slice}'",
            )

        new_p_text = (
            current_p_text[: doc_range.start_offset]
            + replacement_text
            + current_p_text[doc_range.end_offset :]
        )
        p.text = new_p_text
        document.create_revision()
        return True, "Success"
