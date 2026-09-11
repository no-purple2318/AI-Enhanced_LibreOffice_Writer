# API Reference: AI-Enhanced LibreOffice Writer

## `src.controller.AIController`

The central orchestrator that coordinates all analysis modules and services.

### Constructor
```python
AIController(config: Config = None, ai_provider: AIProvider = None)
```

### Methods

| Method | Parameters | Returns | Description |
| :--- | :--- | :--- | :--- |
| `analyze(document)` | `document: Document` | `AnalysisResult` | Runs all 5 analysis modules, catches per-module errors, calculates QualityScore, and returns the aggregate result. |
| `getSuggestions(status)` | `status: Optional[SuggestionStatus]` | `List[Suggestion]` | Returns suggestions from the latest analysis, optionally filtered by status. |
| `applySuggestion(suggestion, document)` | `suggestion: Suggestion`, `document: Document` | `Tuple[bool, str]` | Safely validates and applies an accepted change. Returns `(success, reason)`. |
| `rejectSuggestion(suggestion)` | `suggestion: Suggestion` | `None` | Sets status to `Rejected` without altering document. |
| `ignoreSuggestion(suggestion)` | `suggestion: Suggestion` | `None` | Sets status to `Ignored` without altering document. |
| `navigateToIssue(suggestion, document)` | `suggestion: Suggestion`, `document: Document` | `bool` | Selects and highlights the target range in Writer. |
| `generateReport(result)` | `result: Optional[AnalysisResult]` | `Report` | Returns a formatted quality audit report. |

---

## `src.models.Suggestion`

Represents a single actionable finding from analysis.

| Field | Type | Description |
| :--- | :--- | :--- |
| `suggestionId` | `str` | Unique identifier (UUID). |
| `type` | `SuggestionType` | Enum: `Grammar`, `Spelling`, `Style`, `Consistency`, `Formatting`, `Readability`, `Privacy`. |
| `category` | `str` | Sub-category (e.g. `Names`, `Email`, `Sentence Complexity`). |
| `message` | `str` | Explanation presented to user. |
| `originalText` | `str` | Text slice to replace. |
| `suggestedText` | `str` | Proposed text replacement. |
| `range` | `DocumentRange` | Target paragraph and character offset bounds. |
| `severity` | `Severity` | Enum: `Low`, `Medium`, `High`, `Critical`. |
| `status` | `SuggestionStatus` | Enum: `New`, `Accepted`, `Applied`, `Rejected`, `Ignored`, `StaleConflicted`. |

### Status Transitions
- `accept()` → `New` → `Accepted`
- `apply()` → `Accepted` → `Applied`
- `reject()` → `New` → `Rejected`
- `ignore()` → `New` → `Ignored`
- `mark_stale(reason)` → Any → `StaleConflicted` (blocks further apply)

---

## `src.models.DocumentRange`

Precise location targeting within a document.

| Field | Type | Description |
| :--- | :--- | :--- |
| `paragraph_id` | `int` | Index of target paragraph. |
| `start_offset` | `int` | Start character offset within paragraph. |
| `end_offset` | `int` | End character offset within paragraph. |
| `length` | `int` | Computed property: `end_offset - start_offset`. |

---

## `src.models.DocumentRevision`

Snapshot hashing for drift detection.

| Method | Description |
| :--- | :--- |
| `create_from_paragraphs(doc_id, paragraph_texts)` | Creates revision with SHA-256 hashes per paragraph. |
| `is_paragraph_valid(paragraph_id, current_text)` | Returns `True` if current text matches the stored hash. |

---

## `src.services.QualityService`

Deterministic multi-factor scoring engine.

```python
calculate_scores(
    suggestions: List[Suggestion],
    document: Document,
    flesch_reading_ease: float
) -> QualityScore
```

**Formula:**
$$\text{Overall} = 0.25 \times \text{Writing} + 0.20 \times \text{Consistency} + 0.20 \times \text{Formatting} + 0.20 \times \text{Readability} + 0.15 \times \text{Privacy}$$

**Severity Penalty Weights:** Critical = 20.0, High = 10.0, Medium = 5.0, Low = 2.0

---

## `src.services.SuggestionService`

Safe non-destructive suggestion application.

| Method | Returns | Description |
| :--- | :--- | :--- |
| `validate_suggestion(suggestion, document)` | `Tuple[bool, str]` | Verifies range bounds and expected text integrity. |
| `apply_suggestion(suggestion, document)` | `Tuple[bool, str]` | Atomically updates document text or marks `StaleConflicted`. |

