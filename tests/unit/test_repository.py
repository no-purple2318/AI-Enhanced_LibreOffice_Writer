"""Unit tests for SQLiteRepository persistence."""

import os
import tempfile
from src.integration.uno_document_adapter import UNODocumentAdapter
from src.models.analysis_result import AnalysisResult
from src.models.quality_score import QualityScore
from src.models.suggestion import Severity, Suggestion, SuggestionStatus, SuggestionType
from src.repositories.sqlite_repository import SQLiteRepository


def test_sqlite_repository_save_and_retrieve():
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_history.db")
        repo = SQLiteRepository(db_path=db_path)

        doc = UNODocumentAdapter.from_plain_text("Sample document text.", fileName="PersistDoc.odt")
        res = AnalysisResult(
            documentId=doc.documentId,
            fileName=doc.fileName,
            suggestions=[
                Suggestion(
                    type=SuggestionType.Grammar,
                    category="Grammar",
                    message="Sample issue",
                    originalText="Sample",
                    suggestedText="Example",
                    severity=Severity.Low,
                    status=SuggestionStatus.New,
                )
            ],
            qualityScore=QualityScore(overallScore=95.0),
        )

        # Save analysis
        saved = repo.save_analysis(res, doc)
        assert saved

        # Retrieve history
        history = repo.get_history_by_document(doc.documentId)
        assert len(history) == 1
        assert history[0]["overall_score"] == 95.0

        # Log action
        repo.log_suggestion_action(res.suggestions[0].suggestionId, "Accepted")
