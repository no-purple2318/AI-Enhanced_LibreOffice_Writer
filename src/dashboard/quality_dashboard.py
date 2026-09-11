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


# ---------------------------------------------------------------------------
#  Color & Style Helpers
# ---------------------------------------------------------------------------

_SEVERITY_COLORS = {
    "Critical": "#dc3545",
    "High": "#e67e22",
    "Medium": "#f0ad4e",
    "Low": "#5bc0de",
}

_SEVERITY_BG = {
    "Critical": "#fce4e4",
    "High": "#fef3e5",
    "Medium": "#fef9e7",
    "Low": "#eaf6fb",
}

def _score_color(score: float) -> str:
    """Return a color hex based on score range."""
    if score >= 90:
        return "#27ae60"
    elif score >= 70:
        return "#f39c12"
    elif score >= 50:
        return "#e67e22"
    return "#e74c3c"


class InteractiveDashboardWindow:
    """Interactive GUI Assistant Panel (Tkinter / Desktop) for testing and development."""

    def __init__(self, ai_controller: Any, document: Document):
        self.ai_controller = ai_controller
        self.document = document
        self.root: Optional[tk.Tk] = None
        self.result: Optional[AnalysisResult] = None
        self.selected_suggestion: Optional[Suggestion] = None
        self._suggestion_map: Dict[str, Suggestion] = {}

    def launch(self) -> None:
        """Launch the Assistant UI window."""
        if not TKINTER_AVAILABLE:
            logger.warning("Tkinter is not installed on this system. GUI dashboard is unavailable.")
            print("[Warning] Tkinter is not installed. Install with: sudo apt install python3-tk")
            return

        self.root = tk.Tk()
        self.root.title("AI Document Assistant — LibreOffice Writer")
        self.root.geometry("900x780")
        self.root.minsize(750, 600)
        self.root.configure(bg="#f0f2f5")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Header.TLabel", font=("Segoe UI", 15, "bold"), background="#f0f2f5")
        style.configure("Score.TLabel", font=("Segoe UI", 28, "bold"), background="#ffffff")
        style.configure("Cat.TLabel", font=("Segoe UI", 10), background="#ffffff")
        style.configure("CatVal.TLabel", font=("Segoe UI", 10, "bold"), background="#ffffff")
        style.configure("Detail.TLabel", font=("Segoe UI", 10), background="#ffffff", wraplength=400)
        style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=6)
        style.configure("Card.TFrame", background="#ffffff", relief="groove")

        self._build_header()
        self._build_score_panel()
        self._build_issues_panel()
        self._build_detail_panel()
        self._build_action_bar()

        # Run initial analysis
        self._on_analyze()
        self.root.mainloop()

    # ------------------------------------------------------------------
    #  UI Construction
    # ------------------------------------------------------------------

    def _build_header(self) -> None:
        hf = ttk.Frame(self.root, padding=(15, 10))
        hf.pack(fill=tk.X)

        ttk.Label(hf, text="🤖 AI Document Assistant", style="Header.TLabel").pack(side=tk.LEFT)

        btn_frame = ttk.Frame(hf)
        btn_frame.pack(side=tk.RIGHT)

        self.btn_analyze = ttk.Button(btn_frame, text="⚡ Re-Analyze", command=self._on_analyze, style="Action.TButton")
        self.btn_analyze.pack(side=tk.LEFT, padx=4)

        self.btn_report = ttk.Button(btn_frame, text="📄 Export Report", command=self._on_report, style="Action.TButton")
        self.btn_report.pack(side=tk.LEFT, padx=4)

    def _build_score_panel(self) -> None:
        wrapper = ttk.Frame(self.root, padding=(15, 5))
        wrapper.pack(fill=tk.X)

        card = ttk.Frame(wrapper, style="Card.TFrame", padding=15)
        card.pack(fill=tk.X)

        # Overall score (large number)
        left = ttk.Frame(card, style="Card.TFrame")
        left.pack(side=tk.LEFT, padx=(0, 30))

        ttk.Label(left, text="Overall Score", style="Cat.TLabel").pack(anchor=tk.W)
        self.lbl_overall = ttk.Label(left, text="—", style="Score.TLabel")
        self.lbl_overall.pack(anchor=tk.W)
        self.lbl_grade = ttk.Label(left, text="", style="Cat.TLabel")
        self.lbl_grade.pack(anchor=tk.W)

        # Category breakdown with mini bars
        right = ttk.Frame(card, style="Card.TFrame")
        right.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._cat_widgets: Dict[str, Dict[str, Any]] = {}
        categories = [
            ("Writing", "25%"),
            ("Consistency", "20%"),
            ("Formatting", "20%"),
            ("Readability", "20%"),
            ("Privacy", "15%"),
        ]
        for row_idx, (cat, weight) in enumerate(categories):
            ttk.Label(right, text=f"{cat} ({weight})", style="Cat.TLabel").grid(
                row=row_idx, column=0, sticky=tk.W, padx=(0, 10), pady=1
            )
            canvas = tk.Canvas(right, width=200, height=14, bg="#e9ecef",
                               highlightthickness=0, bd=0)
            canvas.grid(row=row_idx, column=1, sticky=tk.W, pady=1)
            val_lbl = ttk.Label(right, text="—", style="CatVal.TLabel")
            val_lbl.grid(row=row_idx, column=2, sticky=tk.W, padx=(8, 0), pady=1)
            self._cat_widgets[cat] = {"canvas": canvas, "label": val_lbl}

    def _build_issues_panel(self) -> None:
        wrapper = ttk.Frame(self.root, padding=(15, 5))
        wrapper.pack(fill=tk.BOTH, expand=True)

        self.issues_label = ttk.Label(wrapper, text="Suggestions & Alerts (0)", font=("Segoe UI", 11, "bold"))
        self.issues_label.pack(anchor=tk.W, pady=(0, 4))

        cols = ("sev", "type", "message", "status")
        self.tree = ttk.Treeview(wrapper, columns=cols, show="headings", selectmode="browse", height=12)
        self.tree.heading("sev", text="Severity")
        self.tree.heading("type", text="Category")
        self.tree.heading("message", text="Issue Description")
        self.tree.heading("status", text="Status")

        self.tree.column("sev", width=80, anchor=tk.CENTER)
        self.tree.column("type", width=110)
        self.tree.column("message", width=480)
        self.tree.column("status", width=90, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(wrapper, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree.bind("<<TreeviewSelect>>", self._on_select_issue)

    def _build_detail_panel(self) -> None:
        wrapper = ttk.Frame(self.root, padding=(15, 5))
        wrapper.pack(fill=tk.X)

        card = ttk.Frame(wrapper, style="Card.TFrame", padding=12)
        card.pack(fill=tk.X)

        ttk.Label(card, text="Issue Details", font=("Segoe UI", 11, "bold"),
                  background="#ffffff").pack(anchor=tk.W)

        self.detail_text = tk.Text(card, height=5, wrap=tk.WORD, font=("Segoe UI", 10),
                                   bg="#ffffff", bd=0, relief=tk.FLAT, state=tk.DISABLED,
                                   padx=8, pady=4)
        self.detail_text.pack(fill=tk.X, pady=(4, 0))

        # Configure tags for highlighting
        self.detail_text.tag_configure("label", font=("Segoe UI", 10, "bold"))
        self.detail_text.tag_configure("original", foreground="#e74c3c",
                                        font=("Segoe UI", 10, "overstrike"))
        self.detail_text.tag_configure("suggested", foreground="#27ae60",
                                        font=("Segoe UI", 10, "bold"))

    def _build_action_bar(self) -> None:
        af = ttk.Frame(self.root, padding=(15, 8))
        af.pack(fill=tk.X)

        self.btn_accept = ttk.Button(af, text="✔ Accept Change", command=self._on_accept,
                                     state=tk.DISABLED, style="Action.TButton")
        self.btn_accept.pack(side=tk.LEFT, padx=4)

        self.btn_reject = ttk.Button(af, text="✖ Reject", command=self._on_reject,
                                     state=tk.DISABLED, style="Action.TButton")
        self.btn_reject.pack(side=tk.LEFT, padx=4)

        self.btn_ignore = ttk.Button(af, text="👁 Ignore", command=self._on_ignore,
                                     state=tk.DISABLED, style="Action.TButton")
        self.btn_ignore.pack(side=tk.LEFT, padx=4)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(af, textvariable=self.status_var, font=("Segoe UI", 9),
                               foreground="#7f8c8d")
        status_bar.pack(side=tk.RIGHT, padx=8)

    # ------------------------------------------------------------------
    #  Event Handlers
    # ------------------------------------------------------------------

    def _on_analyze(self) -> None:
        self.status_var.set("Analyzing...")
        self.root.update_idletasks()
        self.result = self.ai_controller.analyze(self.document)
        self._suggestion_map = {s.suggestionId: s for s in self.result.suggestions}
        self._update_scores()
        self._update_issues()
        self._clear_detail()
        count = len(self.result.suggestions)
        self.status_var.set(f"Analysis complete — {count} issue{'s' if count != 1 else ''} found")

    def _update_scores(self) -> None:
        if not self.result:
            return
        qs = self.result.qualityScore
        overall = qs.overallScore
        color = _score_color(overall)

        self.lbl_overall.config(text=f"{overall:.1f}", foreground=color)

        if overall >= 90:
            grade = "Excellent"
        elif overall >= 75:
            grade = "Good"
        elif overall >= 60:
            grade = "Needs Improvement"
        else:
            grade = "Poor"
        self.lbl_grade.config(text=grade, foreground=color)

        cat_scores = {
            "Writing": qs.writingScore,
            "Consistency": qs.consistencyScore,
            "Formatting": qs.formattingScore,
            "Readability": qs.readabilityScore,
            "Privacy": qs.privacyScore,
        }
        for cat, val in cat_scores.items():
            w = self._cat_widgets[cat]
            c = w["canvas"]
            c.delete("all")
            bar_w = int(val * 2)  # max 200px at score 100
            bar_color = _score_color(val)
            c.create_rectangle(0, 0, bar_w, 14, fill=bar_color, outline="")
            w["label"].config(text=f"{val:.1f}", foreground=bar_color)

    def _update_issues(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        if not self.result:
            self.issues_label.config(text="Suggestions & Alerts (0)")
            return

        self.issues_label.config(text=f"Suggestions & Alerts ({len(self.result.suggestions)})")

        for s in self.result.suggestions:
            desc = s.message
            if s.originalText and s.suggestedText:
                desc = f"'{s.originalText}' → '{s.suggestedText}'"
            sev = s.severity.value
            self.tree.insert(
                "",
                tk.END,
                iid=s.suggestionId,
                values=(sev, s.type.value, desc, s.status.value),
                tags=(sev,),
            )

        # Color-code severity rows
        for sev, color in _SEVERITY_BG.items():
            self.tree.tag_configure(sev, background=color)

    def _clear_detail(self) -> None:
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)
        self.detail_text.insert(tk.END, "Select an issue above to see details.")
        self.detail_text.config(state=tk.DISABLED)
        self.selected_suggestion = None
        self.btn_accept.config(state=tk.DISABLED)
        self.btn_reject.config(state=tk.DISABLED)
        self.btn_ignore.config(state=tk.DISABLED)

    def _on_select_issue(self, event: Any) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        s_id = sel[0]
        s = self._suggestion_map.get(s_id)
        if not s:
            return
        self.selected_suggestion = s

        # Update detail panel
        self.detail_text.config(state=tk.NORMAL)
        self.detail_text.delete("1.0", tk.END)

        self.detail_text.insert(tk.END, "Category: ", "label")
        self.detail_text.insert(tk.END, f"{s.type.value} — {s.category}\n")

        self.detail_text.insert(tk.END, "Severity: ", "label")
        self.detail_text.insert(tk.END, f"{s.severity.value}\n")

        self.detail_text.insert(tk.END, "Message: ", "label")
        self.detail_text.insert(tk.END, f"{s.message}\n")

        if s.originalText:
            self.detail_text.insert(tk.END, "Original: ", "label")
            self.detail_text.insert(tk.END, f"{s.originalText}\n", "original")

        if s.suggestedText:
            self.detail_text.insert(tk.END, "Suggested: ", "label")
            self.detail_text.insert(tk.END, f"{s.suggestedText}\n", "suggested")

        if s.range:
            self.detail_text.insert(tk.END, "Location: ", "label")
            self.detail_text.insert(tk.END, f"Paragraph {s.range.paragraph_id}, "
                                            f"chars {s.range.start_offset}–{s.range.end_offset}\n")

        self.detail_text.config(state=tk.DISABLED)

        # Enable/disable action buttons based on status
        is_active = s.status in (SuggestionStatus.New, SuggestionStatus.Accepted)
        self.btn_accept.config(state=tk.NORMAL if is_active else tk.DISABLED)
        self.btn_reject.config(state=tk.NORMAL if is_active else tk.DISABLED)
        self.btn_ignore.config(state=tk.NORMAL if is_active else tk.DISABLED)

    def _on_accept(self) -> None:
        if not self.selected_suggestion:
            return
        success, reason = self.ai_controller.applySuggestion(
            self.selected_suggestion, self.document
        )
        if success:
            self.status_var.set(f"Applied: {self.selected_suggestion.category}")
        else:
            messagebox.showwarning("Cannot Apply", f"Cannot apply change:\n{reason}")
            self.status_var.set(f"Conflict: {reason}")
        self._update_issues()
        self._clear_detail()

    def _on_reject(self) -> None:
        if not self.selected_suggestion:
            return
        self.ai_controller.rejectSuggestion(self.selected_suggestion)
        self.status_var.set(f"Rejected: {self.selected_suggestion.category}")
        self._update_issues()
        self._clear_detail()

    def _on_ignore(self) -> None:
        if not self.selected_suggestion:
            return
        self.ai_controller.ignoreSuggestion(self.selected_suggestion)
        self.status_var.set(f"Ignored: {self.selected_suggestion.category}")
        self._update_issues()
        self._clear_detail()

    def _on_report(self) -> None:
        if not self.result:
            messagebox.showinfo("No Analysis", "Run analysis first before generating a report.")
            return
        report = self.ai_controller.generateReport(self.result)
        path = report.export(format="html")
        messagebox.showinfo("Report Generated", f"Quality Report exported to:\n{path}")
        self.status_var.set(f"Report saved: {path}")
