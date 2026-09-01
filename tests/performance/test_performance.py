"""Performance tests benchmarking document analysis execution times."""

import time
from src.ai.local_provider import LocalRuleBasedProvider
from src.controller.ai_controller import AIController
from src.integration.uno_document_adapter import UNODocumentAdapter


def test_performance_10_page_document():
    controller = AIController(ai_provider=LocalRuleBasedProvider())

    base_para = (
        "In order to facilitate the development of the system, John Smith reviewed the AI model. "
        "We definately need to recieve the report on 12/04/2026. "
        "Contact info: support.team@company.org or 555-019-2834. "
        "There are 10 pages in the appendix and ten pages in the introduction. "
    )
    paragraphs = [f"## Section {i}\n" + (base_para * 3) for i in range(50)]
    full_text = "\n\n".join(paragraphs)

    doc = UNODocumentAdapter.from_plain_text(full_text, fileName="TenPageDoc.odt")
    word_count = len(doc.getText().split())
    assert word_count >= 3000

    start_time = time.time()
    result = controller.analyze(doc)
    elapsed = time.time() - start_time

    print(f"\n[Performance] Analyzed {word_count} words in {elapsed:.4f}s")
    assert elapsed < 5.0, f"Analysis took {elapsed:.2f}s, exceeding 5.0s performance target"
    assert result.qualityScore.overallScore > 0.0

