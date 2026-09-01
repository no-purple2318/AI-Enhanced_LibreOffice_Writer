"""Quality Dashboard component rendering scores, issue lists, and user action controls."""

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
    TKINTER_AVAILABLE = True
except ImportError:
    tk = None
    messagebox = None
    ttk = None
    TKINTER_AVAILABLE = False
from typing import Any, Callable, Dict, List, Optional

from src.models.analysis_result import AnalysisResult
from src.models.document import Document
from src.models.quality_score import QualityScore
from src.models.suggestion import (
    Severity,
    Suggestion,
    SuggestionStatus,
    SuggestionType,
)
from src.utils.logging import get_logger

logger = get_logger("ai_writer.dashboard")


class QualityDashboard:
    """Document Quality Dashboard managing visualization of scores, issues, and user interactions."""

    def __init__(self, sidebar_controller: Any = None):
        self.sidebar_controller = sidebar_controller
        self.current_result: Optional[AnalysisResult] = None
        self.current_document: Optional[Document] = None
        self.selected_suggestion: Optional[Suggestion] = None

    def displayScore(self, score: QualityScore) -> Dict[str, Any]:
        """Format and return dashboard score representation."""
        return {
            "overall": score.overallScore,
            "writing": score.writingScore,
            "consistency": score.consistencyScore,
            "formatting": score.formattingScore,
            "readability": score.readabilityScore,
            "privacy": score.privacyScore,
        }

    def displayIssues(
        self, suggestions: List[Suggestion]
    ) -> List[Dict[str, Any]]:
        """Format and return list of issues for UI display."""
        return [
            {
                "id": s.suggestionId,
                "type": s.type.value,
                "category": s.category,
                "severity": s.severity.value,
                "message": s.message,
                "original": s.originalText,
                "suggested": s.suggestedText,
                "position": s.position,
                "status": s.status.value,
            }
            for s in suggestions
        ]

    def navigateToIssue(self, suggestion: Suggestion) -> bool:
        """Trigger navigation/selection to the issue's location in LibreOffice Writer."""
        if not self.sidebar_controller or not self.current_document:
            return False
        return self.sidebar_controller.on_suggestion_clicked(
            suggestion.suggestionId, self.current_document
        )

    def refresh(self) -> None:
        """Refresh dashboard state."""
        if self.sidebar_controller and self.sidebar_controller.current_result:
            self.current_result = self.sidebar_controller.current_result


class InteractiveDashboardWindow:
    """Interactive GUI Assistant Panel (Tkinter / Desktop) for testing and development."""

    def __init__(self, ai_controller: Any, document: Document):
        self.ai_controller = ai_controller
        self.document = document
        self.root: Optional[tk.Tk] = None
        self.result: Optional[AnalysisResult] = None
        self.selected_suggestion: Optional[Suggestion] = None

    def launch(self) -> None:
        """Launch the Assistant UI window."""
        if not TKINTER_AVAILABLE:
            logger.warning("Tkinter is not installed on this system. GUI dashboard is unavailable.")
            print("[Warning] Tkinter is not installed. Use CLI or LibreOffice UNO integration.")
            return

        self.root = tk.Tk()
        self.root.title("AI Document Assistant - LibreOffice Writer")
        self.root.geometry("680x750")
        self.root.configure(bg="#f8f9fa")

        # Top Header & Analyze Button
        header_frame = ttk.Frame(self.root, padding=10)
        header_frame.pack(fill=tk.X)

        title_lbl = ttk.Label(
            header_frame,
            text="AI Document Assistant",
            font=("Helvetica", 14, "bold"),
        )
        title_lbl.pack(side=tk.LEFT)

        self.btn_analyze = ttk.Button(
            header_frame, text="⚡ Analyze Document", command=self._on_analyze
        )
        self.btn_analyze.pack(side=tk.RIGHT)

        # Score Overview Frame
        self.score_frame = ttk.LabelFrame(self.root, text="Quality Overview", padding=10)
        self.score_frame.pack(fill=tk.X, padx=10, pady=5)

        self.lbl_overall = ttk.Label(
            self.score_frame, text="Overall Score: -- / 100", font=("Helvetica", 12, "bold")
        )
        self.lbl_overall.pack(anchor=tk.W)

        self.category_labels: Dict[str, ttk.Label] = {}
        cats = ["Writing", "Consistency", "Formatting", "Readability", "Privacy"]
        cat_subframe = ttk.Frame(self.score_frame)
        cat_subframe.pack(fill=tk.X, pady=5)
        for idx, cat in enumerate(cats):
            lbl = ttk.Label(cat_subframe, text=f"{cat}: --", font=("Helvetica", 9))
            lbl.grid(row=0, column=idx, padx=5, sticky=tk.W)
            self.category_labels[cat] = lbl

        # Issues Treeview
        issues_frame = ttk.LabelFrame(self.root, text="Detected Suggestions & Alerts", padding=10)
        issues_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        cols = ("Severity", "Category", "Problem / Suggestion", "Status")
        self.tree = ttk.Treeview(issues_frame, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("Severity", text="Severity")
        self.tree.heading("Category", text="Category")
        self.tree.heading("Problem / Suggestion", text="Problem / Suggestion")
        self.tree.heading("Status", text="Status")

        self.tree.column("Severity", width=75, anchor=tk.CENTER)
        self.tree.column("Category", width=110)
        self.tree.column("Problem / Suggestion", width=340)
        self.tree.column("Status", width=85, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(issues_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select_issue)

        # Action Buttons Frame
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill=tk.X)

        self.btn_accept = ttk.Button(action_frame, text="✔ Accept", command=self._on_accept, state=tk.DISABLED)
        self.btn_accept.pack(side=tk.LEFT, padx=5)

        self.btn_reject = ttk.Button(action_frame, text="✖ Reject", command=self._on_reject, state=tk.DISABLED)
        self.btn_reject.pack(side=tk.LEFT, padx=5)

        self.btn_ignore = ttk.Button(action_frame, text="👁 Ignore", command=self._on_ignore, state=tk.DISABLED)
        self.btn_ignore.pack(side=tk.LEFT, padx=5)

        self.btn_report = ttk.Button(action_frame, text="📄 Generate Report", command=self._on_report)
        self.btn_report.pack(side=tk.RIGHT, padx=5)

        # Run initial analysis
        self._on_analyze()
        self.root.mainloop()

    def _on_analyze(self) -> None:
        self.result = self.ai_controller.analyze(self.document)
        self._update_display()

    def _update_display(self) -> None:
        if not self.result:
            return

        qs = self.result.qualityScore
        self.lbl_overall.config(text=f"Overall Score: {qs.overallScore:.1f} / 100")
        self.category_labels["Writing"].config(text=f"Writing: {qs.writingScore:.1f}")
        self.category_labels["Consistency"].config(text=f"Consistency: {qs.consistencyScore:.1f}")
        self.category_labels["Formatting"].config(text=f"Formatting: {qs.formattingScore:.1f}")
        self.category_labels["Readability"].config(text=f"Readability: {qs.readabilityScore:.1f}")
        self.category_labels["Privacy"].config(text=f"Privacy: {qs.privacyScore:.1f}")

        # Clear and repopulate tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        for s in self.result.suggestions:
            desc = s.message
            if s.originalText and s.suggestedText:
                desc = f"'{s.originalText}' -> '{s.suggestedText}' ({s.message})"
            self.tree.insert(
                "",
                tk.END,
                iid=s.suggestionId,
                values=(s.severity.value, s.type.value, desc, s.status.value),
            )

    def _on_select_issue(self, event: Any) -> None:
        sel = self.tree.selection()
        if not sel or not self.result:
            return
        s_id = sel[0]
        for s in self.result.suggestions:
            if s.suggestionId == s_id:
                self.selected_suggestion = s
                break

        if self.selected_suggestion:
            # Highlight issue in Writer
            self.ai_controller.navigateToIssue(self.selected_suggestion, self.document)
            is_active = self.selected_suggestion.status in (
                SuggestionStatus.New,
                SuggestionStatus.Accepted,
            )
            self.btn_accept.config(state=tk.NORMAL if is_active else tk.DISABLED)
            self.btn_reject.config(state=tk.NORMAL if is_active else tk.DISABLED)
            self.btn_ignore.config(state=tk.NORMAL if is_active else tk.DISABLED)

    def _on_accept(self) -> None:
        if not self.selected_suggestion:
            return
        success, reason = self.ai_controller.applySuggestion(
            self.selected_suggestion, self.document
        )
        if not success:
            messagebox.showwarning("Conflict / Cannot Apply", f"Cannot apply: {reason}")
        self._update_display()

    def _on_reject(self) -> None:
        if not self.selected_suggestion:
            return
        self.ai_controller.rejectSuggestion(self.selected_suggestion)
        self._update_display()

    def _on_ignore(self) -> None:
        if not self.selected_suggestion:
            return
        self.ai_controller.ignoreSuggestion(self.selected_suggestion)
        self._update_display()

    def _on_report(self) -> None:
        if not self.result:
            return
        report = self.ai_controller.generateReport(self.result)
        path = report.export(format="markdown")
        messagebox.showinfo("Report Generated", f"Quality Report exported to:\n{path}")
