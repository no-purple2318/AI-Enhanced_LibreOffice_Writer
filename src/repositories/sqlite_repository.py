"""Optional SQLite persistence repository for storing analysis history and suggestion logs."""

import os
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional

from src.models.analysis_result import AnalysisResult
from src.models.document import Document
from src.models.quality_score import QualityScore
from src.models.suggestion import Suggestion, SuggestionStatus, SuggestionType
from src.utils.logging import get_logger

logger = get_logger("ai_writer.repository")


class SQLiteRepository:
    """Manages optional persistent storage of document analysis results and audit logs."""

    def __init__(self, db_path: str = "ai_writer_history.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        """Create database tables per Section 43 data model."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.executescript("""
                    CREATE TABLE IF NOT EXISTS documents (
                        document_id TEXT PRIMARY KEY,
                        file_name TEXT,
                        file_path TEXT,
                        file_type TEXT,
                        created_at TEXT,
                        last_modified_at TEXT
                    );

                    CREATE TABLE IF NOT EXISTS analysis_results (
                        result_id TEXT PRIMARY KEY,
                        document_id TEXT,
                        analyzed_at TEXT,
                        overall_score REAL,
                        writing_score REAL,
                        consistency_score REAL,
                        formatting_score REAL,
                        readability_score REAL,
                        privacy_score REAL,
                        FOREIGN KEY(document_id) REFERENCES documents(document_id)
                    );

                    CREATE TABLE IF NOT EXISTS suggestions (
                        suggestion_id TEXT PRIMARY KEY,
                        result_id TEXT,
                        type TEXT,
                        category TEXT,
                        message TEXT,
                        original_text TEXT,
                        suggested_text TEXT,
                        position TEXT,
                        severity TEXT,
                        status TEXT,
                        created_at TEXT,
                        FOREIGN KEY(result_id) REFERENCES analysis_results(result_id)
                    );

                    CREATE TABLE IF NOT EXISTS suggestion_logs (
                        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        suggestion_id TEXT,
                        action TEXT,
                        action_at TEXT
                    );
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize SQLite repository: {e}")

    def save_analysis(self, result: AnalysisResult, document: Document) -> bool:
        """Persist document snapshot and analysis result."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                # Insert / replace document
                cursor.execute("""
                    INSERT OR REPLACE INTO documents (
                        document_id, file_name, file_path, file_type, created_at, last_modified_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    document.documentId,
                    document.fileName,
                    document.filePath,
                    document.fileType,
                    document.createdAt.isoformat(),
                    document.lastModifiedAt.isoformat(),
                ))

                # Insert analysis result
                qs = result.qualityScore
                cursor.execute("""
                    INSERT OR REPLACE INTO analysis_results (
                        result_id, document_id, analyzed_at, overall_score,
                        writing_score, consistency_score, formatting_score,
                        readability_score, privacy_score
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    result.resultId,
                    document.documentId,
                    result.analyzedAt.isoformat(),
                    qs.overallScore,
                    qs.writingScore,
                    qs.consistencyScore,
                    qs.formattingScore,
                    qs.readabilityScore,
                    qs.privacyScore,
                ))

                # Insert suggestions
                for s in result.suggestions:
                    cursor.execute("""
                        INSERT OR REPLACE INTO suggestions (
                            suggestion_id, result_id, type, category, message,
                            original_text, suggested_text, position, severity, status, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        s.suggestionId,
                        result.resultId,
                        s.type.value,
                        s.category,
                        s.message,
                        s.originalText,
                        s.suggestedText,
                        s.position,
                        s.severity.value,
                        s.status.value,
                        s.createdAt.isoformat(),
                    ))

                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error saving analysis result to SQLite: {e}")
            return False

    def log_suggestion_action(self, suggestion_id: str, action: str) -> None:
        """Record suggestion user action (accept, reject, ignore, apply) into audit log."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO suggestion_logs (suggestion_id, action, action_at)
                    VALUES (?, ?, ?)
                """, (suggestion_id, action, datetime.utcnow().isoformat()))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging suggestion action: {e}")

    def get_history_by_document(self, document_id: str) -> List[Dict[str, Any]]:
        """Retrieve previous analysis sessions for a document."""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM analysis_results WHERE document_id = ? ORDER BY analyzed_at DESC
                """, (document_id,))
                rows = cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception as e:
            logger.error(f"Error retrieving history for document {document_id}: {e}")
            return []
