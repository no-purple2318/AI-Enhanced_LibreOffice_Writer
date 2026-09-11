# User Guide: AI-Enhanced LibreOffice Writer

## What It Does

The AI Document Assistant analyzes your LibreOffice Writer documents for:
- **Grammar & Spelling** errors and **style** improvements
- **Name & terminology inconsistencies** (e.g. "Jon Smith" vs "John Smith")
- **Formatting problems** (inconsistent fonts, skipped heading levels)
- **Readability** issues (overly complex sentences, difficult vocabulary)
- **Privacy risks** (exposed emails, phone numbers, Social Security Numbers)

It calculates an **Overall Quality Score** (0–100) and presents actionable suggestions.

> **Important:** The assistant **never** changes your document without your explicit approval.

---

## Quick Start

### Option A: Using the Extension in LibreOffice
1. Install the extension (`dist/ai_writer_assistant.oxt`) via **Tools → Extension Manager → Add**.
2. Restart LibreOffice Writer.
3. Open any document.
4. Click **AI Assistant → ⚡ Analyze Document** from the menu bar.
5. Review your quality score and the list of findings.

### Option B: Using the Command Line
```bash
# Analyze any .odt or .txt file
python3 scripts/run_assistant.py --file your_document.odt

# Generate an HTML quality report
python3 scripts/run_assistant.py --file your_document.odt --export-report html
```

---

## Understanding Your Score

| Category | Weight | What It Measures |
| :--- | :---: | :--- |
| Writing | 25% | Grammar, spelling, and style |
| Consistency | 20% | Names, terminology, date/number formats |
| Formatting | 20% | Font consistency, heading hierarchy, layout |
| Readability | 20% | Sentence complexity, vocabulary difficulty |
| Privacy | 15% | Exposed personal information |

---

## Working with Suggestions

Each issue found is presented as a suggestion with a severity level:

| Action | What Happens |
| :--- | :--- |
| **Accept ✔** | Safely replaces the text. If you edited the document since analysis, the system detects the conflict and alerts you instead of corrupting your text. |
| **Reject ✖** | Dismisses the suggestion. Your document is not changed. |
| **Ignore 👁** | Hides the suggestion for this session. Your document is not changed. |

---

## Generating Reports

Click **📄 Generate Quality Report** or use the CLI:
```bash
python3 scripts/run_assistant.py --file document.odt --export-report html
```

Reports include: document metadata, score breakdown, severity summary, privacy alerts, and a complete findings table.

