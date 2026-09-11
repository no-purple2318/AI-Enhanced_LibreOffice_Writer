#!/usr/bin/env python3
"""CLI and Standalone Runner for AI-Enhanced LibreOffice Writer Assistant."""

import argparse
import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ai.local_provider import LocalRuleBasedProvider
from src.ai.mock_provider import MockProvider
from src.controller.ai_controller import AIController
from src.dashboard.quality_dashboard import InteractiveDashboardWindow
from src.integration.libreoffice_connection import LibreOfficeConnection
from src.integration.uno_document_adapter import UNODocumentAdapter
from src.utils.config import Config
from src.utils.logging import setup_logger


def main():
    parser = argparse.ArgumentParser(
        description="AI-Enhanced LibreOffice Writer - Intelligent Document Assistance System"
    )
    parser.add_argument(
        "--connect",
        action="store_true",
        help="Connect to a running LibreOffice instance via PyUNO socket (port 2002)",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Analyze a local text or .odt sample file directly",
    )
    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Disable the Interactive Assistant Dashboard GUI (terminal output only)",
    )
    parser.add_argument(
        "--export-report",
        type=str,
        choices=["markdown", "html", "text"],
        default=None,
        help="Export quality report in specified format",
    )
    parser.add_argument(
        "--mock-ai",
        action="store_true",
        help="Use Mock AI Provider instead of local NLP engine",
    )

    args = parser.parse_args()
    logger = setup_logger(level="INFO")

    config = Config()
    ai_provider = MockProvider() if args.mock_ai else LocalRuleBasedProvider()
    controller = AIController(config=config, ai_provider=ai_provider)

    doc = None

    if args.connect:
        logger.info("Attempting connection to LibreOffice instance...")
        conn = LibreOfficeConnection(
            host=config.get("connection.host", "localhost"),
            port=config.get("connection.port", 2002),
        )
        if conn.connect():
            x_doc = conn.get_current_document()
            if x_doc:
                doc = UNODocumentAdapter.to_domain_document(x_doc)
                logger.info(f"Attached to active Writer document: {doc.fileName}")
            else:
                logger.warning("Connected to LibreOffice, but no active Writer document is currently open.")
                sys.exit(1)
        else:
            logger.error("Failed to connect to LibreOffice. Ensure it was started with listening socket.")
            sys.exit(1)

    elif args.file:
        if not os.path.exists(args.file):
            logger.error(f"File not found: {args.file}")
            sys.exit(1)
        if args.file.lower().endswith(".odt"):
            doc = UNODocumentAdapter.from_odt_file(args.file)
            if not doc:
                logger.error(f"Failed to parse ODT file: {args.file}")
                sys.exit(1)
        else:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
            doc = UNODocumentAdapter.from_plain_text(content, fileName=os.path.basename(args.file))
        logger.info(f"Loaded document fixture: {doc.fileName} ({len(doc.paragraphs)} paragraphs)")

    else:
        # Default sample text demonstrating issues
        sample_text = """# Project Overview

This are a example document demonstrating the AI-Enhanced LibreOffice Writer system.
We definately need to recieve approval from Jon Smith before the release.
John Smith will review the AI model and the artificial intelligence model architecture.

## System Details

In order to facilitate high performance, 10 pages were reviewed while ten pages remain.
The contract was signed on 12/04/2026 and later updated on 2026-04-12.
For inquiries, contact admin@example.com or call +1-555-019-2834.
Confidential SSN: 000-12-3456.
"""
        doc = UNODocumentAdapter.from_plain_text(sample_text, fileName="DemoDocument.odt")
        logger.info(f"Using default rich sample document: {doc.fileName}")

    result = controller.analyze(doc)

    if args.no_gui:
        # Print summary to console only
        summary = result.getSummary()
        qs = result.qualityScore
        print("\n" + "=" * 60)
        print("  AI-Enhanced LibreOffice Writer - Analysis Result")
        print("=" * 60)
        print(f"  Document:        {result.fileName}")
        print(f"  Overall Score:   {qs.overallScore:.1f} / 100")
        print(f"  Writing Score:   {qs.writingScore:.1f} / 100")
        print(f"  Consistency:     {qs.consistencyScore:.1f} / 100")
        print(f"  Formatting:      {qs.formattingScore:.1f} / 100")
        print(f"  Readability:     {qs.readabilityScore:.1f} / 100")
        print(f"  Privacy Score:   {qs.privacyScore:.1f} / 100")
        print(f"  Total Issues:    {len(result.suggestions)}")
        print("-" * 60)
        for idx, s in enumerate(result.suggestions, 1):
            print(f"  [{idx}] [{s.severity.value:8}] {s.type.value:12} | {s.category:16} | {s.message}")
        print("=" * 60 + "\n")
    else:
        # Launch Interactive Dashboard GUI (default)
        logger.info("Opening Assistant Dashboard UI...")
        dashboard_window = InteractiveDashboardWindow(controller, doc)
        dashboard_window.launch()

    if args.export_report:
        report = controller.generateReport(result)
        out_path = report.export(format=args.export_report)
        print(f"Report successfully exported to: {out_path}")


if __name__ == "__main__":
    main()

