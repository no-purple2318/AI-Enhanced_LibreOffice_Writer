"""End-to-End integration tests for full document analysis lifecycle."""

import os
import tempfile
from src.ai.local_provider import LocalRuleBasedProvider
from src.controller.ai_controller import AIController
from src.integration.uno_document_adapter import UNODocumentAdapter
from src.models.suggestion import SuggestionStatus, SuggestionType


def test_end_to_end_full_pipeline():
    controller = AIController(ai_provider=LocalRuleBasedProvider())

    fixture_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "consistency_document.txt",
    )
    with open(fixture_path, "r", encoding="utf-8") as f:
        content = f.read()

    doc = UNODocumentAdapter.from_plain_text(content, fileName="consistency_document.odt")

    # 1. Analyze Document
    result = controller.analyze(doc)
    assert result is not None
    assert result.qualityScore.overallScore > 0.0
    assert len(result.suggestions) > 0

    # 2. Review and Apply a suggestion
    terminology_suggs = [
        s for s in result.suggestions if s.type == SuggestionType.Consistency and s.category == "Terminology"
    ]
    if terminology_suggs:
        s = terminology_suggs[0]
        success, _ = controller.applySuggestion(s, doc)
        assert success
        assert s.status == SuggestionStatus.Applied

    # 3. Generate and Export Report
    with tempfile.TemporaryDirectory() as tmp_dir:
        report = controller.generateReport(result)
        md_path = os.path.join(tmp_dir, "final_report.md")
        html_path = os.path.join(tmp_dir, "final_report.html")

        report.export(md_path, format="markdown")
        report.export(html_path, format="html")

        assert os.path.exists(md_path)
        assert os.path.exists(html_path)
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()
        assert "Document Quality Report" in md_content


def test_end_to_end_binary_odt_analysis():
    controller = AIController(ai_provider=LocalRuleBasedProvider())
    odt_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "fixtures",
        "consistency_document.odt",
    )
    if os.path.exists(odt_path):
        doc = UNODocumentAdapter.from_odt_file(odt_path)
        assert doc is not None
        assert len(doc.paragraphs) > 0

        result = controller.analyze(doc)
        assert result.qualityScore.overallScore > 0.0
        assert len(result.suggestions) > 0

