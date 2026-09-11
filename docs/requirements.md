# Requirements & Traceability Matrix

## 1. Functional Requirements

| Req ID | Description | Primary Component | Verification Status |
| :--- | :--- | :--- | :--- |
| **FR-01** | Analyze active LibreOffice Writer document via menu or command. | `AIController`, `UNODocumentAdapter` | ✅ Verified |
| **FR-02** | Detect grammar problems and generate actionable suggestions. | `WritingAssistant` | ✅ Verified |
| **FR-03** | Detect spelling errors against dictionary and typo patterns. | `WritingAssistant` | ✅ Verified |
| **FR-04** | Identify wordy phrases and stylistic improvements. | `WritingAssistant` | ✅ Verified |
| **FR-05** | Detect named entity discrepancies using advisory warnings. | `ConsistencyAnalyzer` | ✅ Verified |
| **FR-06** | Detect terminology variations (e.g. acronyms vs full forms). | `ConsistencyAnalyzer` | ✅ Verified |
| **FR-07** | Detect inconsistent date and number formats. | `ConsistencyAnalyzer` | ✅ Verified |
| **FR-08** | Perform semantic role-based font consistency analysis. | `FormattingEngine` | ✅ Verified |
| **FR-09** | Inspect heading hierarchy and detect skipped levels (e.g. H1 to H3). | `FormattingEngine` | ✅ Verified |
| **FR-10** | Calculate Flesch Reading Ease and detect sentence/vocabulary complexity. | `ReadabilityModule` | ✅ Verified |
| **FR-11** | Detect emails, phone numbers, and personal identifiers (SSN). | `SensitiveInfoDetector` | ✅ Verified |
| **FR-12** | Aggregate findings and compute deterministic quality scores (Writing 25%, Consistency 20%, Formatting 20%, Readability 20%, Privacy 15%). | `QualityService` | ✅ Verified |
| **FR-13** | Allow user to Accept, Reject, or Ignore individual suggestions. | `SuggestionService` | ✅ Verified |
| **FR-14** | Execute safe two-phase replacement, refusing stale edits if text changed. | `SuggestionService`, `UNOCursorAdapter` | ✅ Verified |
| **FR-15** | Generate and export comprehensive Quality Reports in Markdown, HTML, and TXT. | `ReportService`, `Report` | ✅ Verified |

---

## 2. Non-Functional Requirements

- **NFR-01 (Safety)**: Zero silent modifications. Every document change requires explicit user initiation.
- **NFR-02 (Privacy)**: Local processing by default. No document content logged or transmitted externally without explicit user configuration.
- **NFR-03 (Performance)**: Analysis completes in under 5.0 seconds for documents up to 10 pages (~6,500 words). Tested: **0.11s** on synthetic 10-page text.
- **NFR-04 (Resilience)**: Failure in one module does not interrupt the execution of other modules.
- **NFR-05 (Cross-Platform)**: Supports Linux, Windows, and macOS with platform-independent path handling.

