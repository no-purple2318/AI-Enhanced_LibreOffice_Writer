# Developer Guide

## Prerequisites

- **Python** 3.10+
- **LibreOffice** 7.0+ with PyUNO:
  ```bash
  sudo apt install libreoffice-script-provider-python python3-uno
  ```

## Project Structure

```
AI-Enhanced LibreOffice Writer/
├── config/default_config.json    # Scoring weights & provider config
├── src/
│   ├── ai/                       # Pluggable AI providers
│   ├── analysis/                 # 5 analysis modules
│   ├── controller/               # AIController orchestrator
│   ├── dashboard/                # Quality dashboard UI
│   ├── integration/              # PyUNO bridge & adapters
│   ├── models/                   # Domain models
│   ├── parser/                   # Document text/structure extractor
│   ├── repositories/             # Optional SQLite persistence
│   └── services/                 # Quality, Suggestion, Report services
├── tests/
│   ├── fixtures/                 # Sample .txt and .odt test documents
│   ├── unit/                     # Unit tests for all modules
│   ├── integration/              # End-to-end pipeline tests
│   └── performance/              # Benchmark tests
├── extension/                    # LibreOffice .oxt extension sources
├── scripts/                      # Build & run scripts
├── dist/                         # Built extension package (.oxt)
└── docs/                         # Documentation
```

## Running Automated Tests

```bash
python3 scripts/run_tests.py
```

Expected: **37 tests passing** in under 1 second.

## Building the Extension (.oxt)

```bash
chmod +x scripts/build_extension.sh
./scripts/build_extension.sh
```

Output: `dist/ai_writer_assistant.oxt`

## Testing with Live LibreOffice

### Method 1: Install Extension via GUI
1. Open LibreOffice Writer.
2. Go to **Tools** → **Extension Manager...**
3. Click **Add**, select `dist/ai_writer_assistant.oxt`.
4. Restart LibreOffice.

### Method 2: Install via Command Line
```bash
unopkg add -f dist/ai_writer_assistant.oxt
```

### Method 3: Live Socket Bridge
```bash
# Terminal 1: Start LibreOffice with listening socket
soffice --writer --accept="socket,host=localhost,port=2002;urp;"

# Terminal 2: Attach the assistant
python3 scripts/run_assistant.py --connect --export-report html
```

## Adding a New Analysis Module

1. Create `src/analysis/your_module.py` extending `AnalysisModule`.
2. Implement `analyze(document: Document) -> List[Suggestion]`.
3. Register it in `src/controller/ai_controller.py`.
4. Add unit tests in `tests/unit/test_your_module.py`.
5. Run `python3 scripts/run_tests.py` to verify.

## Swapping the AI Provider

Edit `config/default_config.json`:
```json
{ "aiProvider": "external", "model": "your-model-name" }
```
Set your API key:
```bash
export AI_WRITER_API_KEY="your-key"
```

