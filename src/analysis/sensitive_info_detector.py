"""Sensitive Information Detector module detecting emails, phone numbers, and personal IDs."""

import re
from typing import Any, Dict, List, Optional

from src.analysis.analysis_module import AnalysisModule
from src.models.document import Document
from src.models.document_range import DocumentRange
from src.models.suggestion import (
    Severity,
    Suggestion,
    SuggestionStatus,
    SuggestionType,
)


class SensitiveInfoDetector(AnalysisModule):
    """Scans document for sensitive PII data before sharing or exporting."""

    # Regex patterns for MVP detection
    EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    
    # Phone numbers (US, International E.164, and common formatted variations)
    PHONE_PATTERNS = [
        r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        r"\b\+?\d{1,4}[-.\s]?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}\b",
    ]

    # Personal Identifiers (SSN: XXX-XX-XXXX, National ID / PAN / Passport patterns)
    IDENTIFIER_PATTERNS = [
        (r"\b\d{3}-\d{2}-\d{4}\b", "Social Security Number (SSN)", Severity.Critical),
        (r"\b[A-Z]{1,2}\d{6,8}[A-Z]?\b", "Passport / National ID Number", Severity.High),
        (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "National Identification / UID Pattern", Severity.Critical),
    ]

    def __init__(self, moduleId: Optional[str] = None):
        super().__init__(moduleId=moduleId, moduleName="SensitiveInfoDetector")

    def detectEmails(self, document: Document) -> List[Suggestion]:
        """Detect email addresses in document paragraphs."""
        suggestions = []
        for p in document.paragraphs:
            for match in re.finditer(self.EMAIL_PATTERN, p.text):
                email = match.group(0)
                s = Suggestion(
                    type=SuggestionType.Privacy,
                    category="Email",
                    message=f"Email address detected: '{email}'. Verify permission before sharing document publicly.",
                    originalText=email,
                    suggestedText="[REDACTED_EMAIL]",
                    range=DocumentRange(
                        paragraph_id=p.id,
                        start_offset=match.start(),
                        end_offset=match.end(),
                    ),
                    position=f"Paragraph {p.id + 1}",
                    severity=Severity.High,
                    status=SuggestionStatus.New,
                )
                suggestions.append(s)
        return suggestions

    def detectPhoneNumbers(self, document: Document) -> List[Suggestion]:
        """Detect telephone numbers in document paragraphs."""
        suggestions = []
        for p in document.paragraphs:
            for pattern in self.PHONE_PATTERNS:
                for match in re.finditer(pattern, p.text):
                    phone = match.group(0)
                    # Filter out short digit sequences or years like 2026
                    digits_only = re.sub(r"\D", "", phone)
                    if len(digits_only) < 7 or len(digits_only) > 15:
                        continue
                    s = Suggestion(
                        type=SuggestionType.Privacy,
                        category="Phone",
                        message=f"Phone number detected: '{phone}'. Ensure recipient is authorized to view this contact information.",
                        originalText=phone,
                        suggestedText="[REDACTED_PHONE]",
                        range=DocumentRange(
                            paragraph_id=p.id,
                            start_offset=match.start(),
                            end_offset=match.end(),
                        ),
                        position=f"Paragraph {p.id + 1}",
                        severity=Severity.High,
                        status=SuggestionStatus.New,
                    )
                    suggestions.append(s)
        return suggestions

    def detectIdentifiers(self, document: Document) -> List[Suggestion]:
        """Detect personal identification numbers (SSN, national IDs)."""
        suggestions = []
        for p in document.paragraphs:
            for pattern, id_name, severity in self.IDENTIFIER_PATTERNS:
                for match in re.finditer(pattern, p.text):
                    ident = match.group(0)
                    s = Suggestion(
                        type=SuggestionType.Privacy,
                        category="Personal Identifier",
                        message=f"{id_name} detected: '{ident}'. Highly sensitive personal information.",
                        originalText=ident,
                        suggestedText="[REDACTED_ID]",
                        range=DocumentRange(
                            paragraph_id=p.id,
                            start_offset=match.start(),
                            end_offset=match.end(),
                        ),
                        position=f"Paragraph {p.id + 1}",
                        severity=severity,
                        status=SuggestionStatus.New,
                    )
                    suggestions.append(s)
        return suggestions

    def generatePrivacyWarnings(self, document: Document) -> List[Suggestion]:
        """Generate privacy warning alerts."""
        return self.analyze(document)

    def analyze(self, document: Document) -> List[Suggestion]:
        """Execute full sensitive information detection."""
        if not document:
            return []

        suggestions: List[Suggestion] = []
        suggestions.extend(self.detectEmails(document))
        suggestions.extend(self.detectPhoneNumbers(document))
        suggestions.extend(self.detectIdentifiers(document))

        for s in suggestions:
            s.revision = document.current_revision

        return suggestions
