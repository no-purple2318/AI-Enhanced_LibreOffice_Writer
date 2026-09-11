# AI-Enhanced LibreOffice Writer

[![Tests](https://img.shields.io/badge/tests-37%20passed-brightgreen.svg)](#running-tests)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](#prerequisites)
[![LibreOffice](https://img.shields.io/badge/LibreOffice-7.0+-orange.svg)](#prerequisites)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE.txt)

> **Golden Principle: AI Assists, User Decides**  
> The system analyzes, detects issues, calculates quality metrics, and recommends actionable improvements. It **NEVER** silently modifies, deletes, reformats, or transmits document content without explicit user approval.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Core Features](#core-features)
  - [1. Writing Assistant](#1-writing-assistant)
  - [2. Consistency Analyzer](#2-consistency-analyzer)
  - [3. Formatting Engine](#3-formatting-engine)
  - [4. Readability Module](#4-readability-module)
  - [5. Sensitive Information Detector](#5-sensitive-information-detector)
- [Quality Scoring System](#quality-scoring-system)
- [System Architecture](#system-architecture)
- [Prerequisites](#prerequisites)
- [Installation & Setup](#installation--setup)
- [Installing the .oxt Extension](#installing-the-oxt-extension)
  - [Method 1: Command-Line (unopkg)](#method-1-command-line-unopkg)
  - [Method 2: Graphical User Interface (GUI)](#method-2-graphical-user-interface-gui)
- [Running the CLI & Standalone Assistant](#running-the-cli--standalone-assistant)
- [Workflow Guide](#workflow-guide)
- [Suggestion Lifecycle & Conflict Protection](#suggestion-lifecycle--conflict-protection)
- [Report Generation & Export](#report-generation--export)
- [AI Provider Configuration](#ai-provider-configuration)
- [Running Tests](#running-tests)
- [Security & Privacy Guarantees](#security--privacy-guarantees)
- [Troubleshooting](#troubleshooting)
- [Known Limitations](#known-limitations)
- [License](#license)

---

## Project Overview

**AI-Enhanced LibreOffice Writer** is a production-ready, intelligent document analysis and editing assistance suite built specifically for LibreOffice Writer. Built entirely on Python 3.10+ and native PyUNO bindings without requiring heavy third-party dependencies, it equips authors, editors, and technical writers with real-time quality audits, stylistic polish, layout consistency checks, and sensitive data protection.

Unlike aggressive auto-correct tools or opaque cloud-dependent services, AI-Enhanced LibreOffice Writer keeps all document data strictly local by default, highlights recommendations directly in Writer, and enforces an immutable two-phase validation barrier that refuses to apply suggestions if document content has drifted or been modified.

---

## Core Features

The engine orchestrates five specialized analysis modules under a fault-tolerant supervisor. If any single module fails, the remaining modules continue uninterrupted.

### 1. Writing Assistant
- **Grammar Inspection**: Catches subject-verb agreement mismatches, irregular verb forms, missing articles, and repeated words.
- **Spelling Verification**: Identifies common spelling mistakes, typographical transpositions, and orthographic errors against an extensible dictionary.
- **Style Optimization**: Recommends conciseness improvements, eliminates wordy padding (e.g., *"in order to"* &rarr; *"to"*, *"due to the fact that"* &rarr; *"because"*), and identifies passive voice formulations.
- **Pluggable AI Backend**: Seamlessly transitions between offline rule-based heuristics, test mocks, and external LLM REST endpoints.

### 2. Consistency Analyzer
- **Named Entity Matching**: Employs fuzzy string similarity (Gestalt Pattern Matching) to detect slight name variations across the text (e.g., *"Jon Smith"* vs. *"John Smith"*).
- **Terminology Harmonization**: Detects competing technical terminology, acronym usage, and spelling variations (e.g., *"AI model"* vs. *"artificial intelligence model"*, *"front-end"* vs. *"frontend"*).
- **Date & Number Consistency**: Identifies clashing date notations (e.g., ISO `2026-04-12` alongside slash format `12/04/2026`) and mixed number conventions (e.g., numerals *"10 pages"* vs. spelled-out words *"ten pages"* in the same context).

### 3. Formatting Engine
- **Semantic Font Consistency**: Groups document paragraphs by their semantic role (`Heading 1`, `Heading 2`, `Standard`, `Body Text`) and flags rogue font family overrides or inconsistent font sizes.
- **Heading Hierarchy Auditing**: Enforces logical document structure and flags skipped heading levels (e.g., leaping directly from `H1` to `H3` without an intermediate `H2`).
- **Layout & Alignment**: Inspects paragraph alignment consistency across related semantic styles to ensure uniform margins and visual rhythm.

### 4. Readability Module
- **Flesch Reading Ease**: Computes exact Flesch scores based on word counts, sentence lengths, and syllable density.
- **Sentence Complexity**: Flags run-on sentences exceeding configured word thresholds (default: >30 words) that impair comprehension.
- **Vocabulary Complexity**: Flags overly complex or bureaucratic jargon and offers accessible plain-English alternatives (e.g., *"utilization"* &rarr; *"use"*, *"facilitate"* &rarr; *"help"*).

### 5. Sensitive Information Detector
- **Email Detection**: Scans for email addresses to prevent unintended information disclosure prior to public dissemination.
- **Phone Numbers**: Identifies international E.164 numbers, US phone formats, and formatted telephone strings.
- **Personal Identifiers (PII)**: Flags Social Security Numbers (`XXX-XX-XXXX`), passport numbers, and national identification formats with high and critical severities.

---

## Quality Scoring System

Every analysis produces a deterministic 0–100 quality rating across each dimension and a unified overall document score:

$$\text{Overall Score} = 0.25 \times \text{Writing} + 0.20 \times \text{Consistency} + 0.20 \times \text{Formatting} + 0.20 \times \text{Readability} + 0.15 \times \text{Privacy}$$

### Dimension Weights

| Dimension | Weight | Primary Factors Evaluated |
| :--- | :---: | :--- |
| **Writing** | **25%** | Grammar violations, spelling mistakes, style and wordiness penalties. |
| **Consistency** | **20%** | Name spelling discrepancies, competing terminology, mixed dates/numbers. |
| **Formatting** | **20%** | Rogue fonts within semantic styles, skipped heading levels, alignment bugs. |
| **Readability** | **20%** | Flesch Reading Ease baseline combined with run-on sentence deductions. |
| **Privacy** | **15%** | PII presence (SSNs, emails, phone numbers, national IDs). |

### Severity Deductions

Category penalties scale according to the severity of detected issues:

- **Critical**: `-20.0` points (e.g., unredacted Social Security Numbers, severe structure breaks)
- **High**: `-10.0` points (e.g., passport/national IDs, skipped heading levels)
- **Medium**: `-5.0` points (e.g., grammar errors, spelling mistakes, inconsistent terminology)
- **Low**: `-2.0` points (e.g., minor stylistic wordiness, advisory date format variances)

*Note: For large documents, category penalties are scaled relative to standard 500-word reference units to ensure fair scoring across varying document lengths.*

---

## System Architecture

The system is structured in five clean, decoupled layers adhering to the single-responsibility principle:

```
+-------------------------------------------------------------------------------+
| Layer 1: LibreOffice Integration (src/integration/)                          |
|  - libreoffice_connection.py   (Socket / Pipe PyUNO desktop bridge)           |
|  - uno_document_adapter.py     (UNO TextDocument & ODT Zip -> Domain Models)  |
|  - uno_cursor_adapter.py       (Safe range selection & atomic text replace)   |
|  - sidebar_controller.py       (Event dispatcher between UI and Controller)   |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Layer 2: Application Controller & Services (src/controller/ & src/services/)   |
|  - ai_controller.py            (Analysis coordinator & suggestion dispatcher) |
|  - quality_service.py          (Deterministic multi-factor score calculator)  |
|  - suggestion_service.py       (Non-destructive validator & conflict checker) |
|  - report_service.py           (Report generator for Markdown, HTML, and TXT) |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Layer 3: Document Parser & Domain Models (src/parser/ & src/models/)          |
|  - document_parser.py          (Text, structural, and formatting extractors)  |
|  - document.py                 (Document, Paragraph, Heading, Formatting)     |
|  - document_range.py           (Paragraph index & character offset spans)     |
|  - document_revision.py        (Content hashing & drift detection snapshots)  |
|  - suggestion.py               (Suggestion, Type, Severity, Lifecycle Status) |
|  - quality_score.py            (Overall and dimensional score structures)     |
|  - report.py                   (Quality report domain model)                  |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Layer 4: Analysis Modules (src/analysis/)                                     |
|  - analysis_module.py          (Base class with fault-tolerant contract)      |
|  - writing_assistant.py        (Grammar, spelling, and style analysis)        |
|  - consistency_analyzer.py     (Names, terminology, dates, numbers)           |
|  - formatting_engine.py        (Semantic font, heading, layout checks)        |
|  - readability_module.py       (Flesch score, sentence & word complexity)     |
|  - sensitive_info_detector.py  (Emails, phone numbers, PII identifiers)       |
+-------------------------------------------------------------------------------+
                                      |
                                      v
+-------------------------------------------------------------------------------+
| Layer 5: AI Provider Abstraction (src/ai/)                                    |
|  - ai_model.py                 (AIModel abstract base class)                  |
|  - ai_provider.py              (AIProvider interface)                         |
|  - local_provider.py           (Offline rule-based NLP & heuristic provider)  |
|  - mock_provider.py            (Deterministic mock provider for testing)      |
|  - external_provider.py        (Pluggable REST/HTTPS LLM provider)            |
+-------------------------------------------------------------------------------+
```

---

## Prerequisites

- **Operating System**: Linux (Ubuntu 20.04+, Debian 11+, Fedora 36+), macOS (11+), or Windows (10/11).
- **Python**: Version **3.10** or higher.
- **LibreOffice**: Version **7.0** or higher (with Writer installed).
- **PyUNO**: The Python-UNO bridge bundled with LibreOffice (on Debian/Ubuntu: `sudo apt install python3-uno`).
- **Dependencies**: Standard library only! Zero third-party Python packages required.

---

## Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/ai-libreoffice/writer-assistant.git
   cd "writer-assistant"
   ```

2. **Verify Python & PyUNO Installation**:
   ```bash
   python3 -c "import sys; print(sys.version)"
   python3 -c "import uno; print('PyUNO successfully detected!')"
   ```
   *(If `import uno` fails, ensure your environment uses LibreOffice's internal Python or install your distribution's `python3-uno` package.)*

3. **Verify Project Health via Test Suite**:
   ```bash
   python3 scripts/run_tests.py
   ```

---

## Installing the .oxt Extension

The extension can be compiled into a `.oxt` package and installed directly into LibreOffice.

### Build the Package
```bash
chmod +x scripts/build_extension.sh
./scripts/build_extension.sh
```
This generates `dist/ai_writer_assistant.oxt`.

### Method 1: Command-Line (unopkg)
You can install or update the extension via LibreOffice's `unopkg` utility:
```bash
unopkg add -f dist/ai_writer_assistant.oxt
```
To verify installation:
```bash
unopkg list | grep org.libreoffice.ai.assistant
```

### Method 2: Graphical User Interface (GUI)
1. Launch **LibreOffice Writer**.
2. Navigate to **Tools** &rarr; **Extension Manager...** (or press `Ctrl+Alt+E`).
3. Click the **Add...** button.
4. Browse to the project repository and select `dist/ai_writer_assistant.oxt`.
5. Accept the MIT License agreement when prompted.
6. Restart LibreOffice.
7. You will now see the **AI Assistant** top menu and the toolbar icon.

---

## Running the CLI & Standalone Assistant

The `scripts/run_assistant.py` script provides a full-featured CLI for headless inspection, CI/CD integration, and direct desktop attachment.

```bash
python3 scripts/run_assistant.py [OPTIONS]
```

### Supported CLI Flags

| Flag | Argument | Description |
| :--- | :--- | :--- |
| `--file` | `<path>` | Analyze a local `.odt` document or plain-text file directly. |
| `--connect` | *(flag)* | Attach to a live LibreOffice Writer instance over PyUNO socket (port 2002). |
| `--export-report` | `markdown \| html \| text` | Automatically generate and export an audit report in the specified format. |
| `--mock-ai` | *(flag)* | Use the deterministic `MockProvider` instead of the local NLP engine. |
| `--gui` | *(flag)* | Launch the standalone Assistant Dashboard window. |

### CLI Usage Examples

- **Analyze a sample file and print console diagnostic summary**:
  ```bash
  python3 scripts/run_assistant.py --file tests/fixtures/consistency_document.odt
  ```

- **Analyze an active document in a running LibreOffice instance**:
  ```bash
  python3 scripts/run_assistant.py --connect
  ```

- **Analyze a file and export a Markdown report**:
  ```bash
  python3 scripts/run_assistant.py --file document.odt --export-report markdown
  ```

- **Run in test mode with mock AI provider**:
  ```bash
  python3 scripts/run_assistant.py --mock-ai --export-report text
  ```

---

## Workflow Guide

```
+-------------------+      +--------------------+      +--------------------+
| 1. Open Document  | ---> | 2. Trigger Audit   | ---> | 3. Review Findings |
| (Writer or File)  |      | (Menu / Toolbar)   |      | (Scores & Issues)  |
+-------------------+      +--------------------+      +--------------------+
                                                                  |
                                                                  v
+-------------------+      +--------------------+      +--------------------+
| 6. Export Report  | <--- | 5. Execute Action  | <--- | 4. Navigate Target |
| (MD / HTML / TXT) |      | (Accept/Reject/Ign)|      | (Highlight in Doc) |
+-------------------+      +--------------------+      +--------------------+
```

1. **Open Document**: Author or load your document in LibreOffice Writer.
2. **Trigger Audit**: Click **AI Assistant** &rarr; **⚡ Analyze Document** or run the CLI.
3. **Review Findings**: Inspect the overall score and the breakdown across Writing, Consistency, Formatting, Readability, and Privacy.
4. **Navigate to Issue**: Click on any suggestion in the list to automatically jump the cursor to and highlight the problematic passage in Writer.
5. **Take Action**:
   - **Accept**: Applies the recommended change safely after confirming text integrity.
   - **Reject**: Dismisses the recommendation for this session.
   - **Ignore**: Dismisses the recommendation without altering document scores.
6. **Export Report**: Export an audit trail to Markdown, HTML, or plain text for review.

---

## Suggestion Lifecycle & Conflict Protection

To guarantee the **Golden Principle**, every suggestion transitions through an explicit state machine:

```
                  +--------+
                  |  New   |
                  +--------+
                  /   |    \
        Accept   /    |     \  Ignore / Reject
                v     |      v
     +------------+   |   +--------------------+
     |  Accepted  |   |   | Rejected / Ignored |
     +------------+   |   +--------------------+
            |         |
      Apply |         | Text modified since analysis
            v         v
      +---------+  +--------------------+
      | Applied |  |  Stale/Conflicted  |
      +---------+  +--------------------+
```

### Two-Phase Conflict Protection Protocol
1. **Pre-condition Check**: When the user clicks **Accept**, `SuggestionService.validate_suggestion()` checks:
   - Does the paragraph still exist?
   - Do the character start and end offsets lie within current paragraph boundaries?
   - Does the live text slice in Writer **exactly match** the `originalText` recorded during analysis?
2. **Safe Execution**: If and only if all checks pass, `UNOCursorAdapter.safe_replace()` applies the replacement string via `XTextCursor`.
3. **Drift Protection**: If the author edited the passage after the analysis ran, the suggestion is immediately flagged as `Stale/Conflicted`. **The edit is aborted**, and the user is alerted to re-run analysis.

---

## Report Generation & Export

The system features built-in report formatting with `ReportService`:

- **Markdown (`.md`)**: GitHub-flavored markdown with summary tables, module breakdowns, and actionable resolution logs.
- **HTML (`.html`)**: Self-contained styled HTML documents featuring responsive CSS, visual quality score cards, and color-coded severity badges.
- **Plain Text (`.txt`)**: Clean ASCII-formatted summaries ideal for command-line piping and terminal viewing.

Reports can be exported programmatically or via CLI (`--export-report markdown`).

---

## AI Provider Configuration

Configuration is managed via `config/default_config.json`. You can switch providers or adjust penalty parameters without touching code:

```json
{
    "aiProvider": "local",
    "model": "rule-based-nlp-v1",
    "analysisTimeout": 30,
    "enableGrammar": true,
    "enableSpelling": true,
    "enableStyle": true,
    "enableConsistency": true,
    "enableFormatting": true,
    "enableReadability": true,
    "enablePrivacyDetection": true,
    "privacyMode": true,
    "qualityWeights": {
        "writing": 0.25,
        "consistency": 0.20,
        "formatting": 0.20,
        "readability": 0.20,
        "privacy": 0.15
    },
    "severityDeductions": {
        "critical": 20.0,
        "high": 10.0,
        "medium": 5.0,
        "low": 2.0
    },
    "connection": {
        "host": "localhost",
        "port": 2002,
        "pipeName": "uno_ai_pipe",
        "connectionType": "socket"
    }
}
```

### Supported Providers
- `"local"`: **LocalRuleBasedProvider** (Default). Pure Python offline NLP heuristics. Zero data leaves your computer.
- `"mock"`: **MockProvider**. Deterministic responses designed for unit testing and CI pipelines.
- `"external"`: **ExternalAPIProvider**. Pluggable REST endpoint for cloud or self-hosted LLMs.

---

## Running Tests

The test suite includes **37 comprehensive test cases** spanning unit tests, end-to-end integration flows, and high-volume performance benchmarks:

```bash
python3 scripts/run_tests.py
```

### Expected Output:
```text
============================================================
Tests run: 37
Errors: 0
Failures: 0
Time: 0.205s
============================================================
```

### Test Scope
- `tests/unit/`: Tests for each of the 5 analysis modules, quality score algorithms, document range math, SQLite repository persistence, and safety boundary edge cases.
- `tests/integration/`: End-to-end analysis of binary `.odt` documents using real zip extraction and domain model conversion.
- `tests/performance/`: Stress test analyzing synthetic 10-page documents (~6,500 words) in **< 0.15 seconds** (well within the 5.0s requirement).

---

## Security & Privacy Guarantees

1. **Local-First Processing**: In default mode, all document parsing, NLP analysis, and metrics calculations execute strictly within your local machine.
2. **Zero Content Logging**: Log files record only metadata (issue IDs, timestamps, document word counts). Sensitive document text is sanitized.
3. **No Automatic Telemetry**: No tracking, usage beacons, or third-party analytical pings are bundled.
4. **Explicit Action Required**: As defined by our Golden Principle, zero modifications to document text can ever occur without user interaction.

---

## Troubleshooting

| Issue | Likely Cause | Resolution |
| :--- | :--- | :--- |
| `ImportError: No module named 'uno'` | Python cannot locate the LibreOffice PyUNO bindings. | On Ubuntu/Debian, run `sudo apt install python3-uno`. On Windows/macOS, use the `python.bin` bundled inside LibreOffice's `program/` directory. |
| `Connection refused (port 2002)` | LibreOffice is not running with an open listening socket. | Start LibreOffice with: `soffice "--accept=socket,host=localhost,port=2002;urp;" --writer` |
| `unopkg: command not found` | LibreOffice binaries are not in system `PATH`. | Add `/usr/lib/libreoffice/program` (Linux) or `/Applications/LibreOffice.app/Contents/MacOS` (macOS) to your `PATH`. |
| Suggestion marked `Stale/Conflicted` | The document text was edited after the last analysis ran. | Click **Analyze Document** again to refresh the analysis against the latest document snapshot. |
| Menu item does not appear in Writer | LibreOffice was not restarted after installing `.oxt`. | Completely close all LibreOffice windows (including quickstarters) and launch Writer again. |

---

## Known Limitations

- **Complex Table Cells**: Semantic formatting audits currently evaluate body paragraphs and headings; table cell alignment inspection is limited.
- **Embedded OLE Objects**: Images, math formulas, and embedded spreadsheets are skipped during text readability audits.
- **Language Coverage**: The rule-based NLP heuristics in `LocalRuleBasedProvider` are optimized for English. Support for additional languages is planned for future releases.

---

## License

This project is licensed under the **MIT License**. See the [LICENSE.txt](LICENSE.txt) file for details.
