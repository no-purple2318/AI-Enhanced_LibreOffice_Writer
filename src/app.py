"""
AI Document Analyzer — Complete Overhaul UI
A modern CustomTkinter desktop application for .docx quality analysis.
Features score gauges, tabbed issue views, and severity badges.
"""

import math
import os
import queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from typing import Optional

import customtkinter as ctk

from src.ai.local_provider import LocalRuleBasedProvider
from src.controller.ai_controller import AIController
from src.models.analysis_result import AnalysisResult
from src.models.suggestion import Severity, SuggestionType

# ─── Theme Configuration ────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Colors
COLORS = {
    "bg_dark": "#0F1117",
    "bg_card": "#1A1D27",
    "bg_card_hover": "#22263A",
    "accent_blue": "#3B82F6",
    "accent_green": "#10B981",
    "accent_yellow": "#F59E0B",
    "accent_red": "#EF4444",
    "accent_purple": "#8B5CF6",
    "accent_pink": "#EC4899",
    "text_primary": "#F1F5F9",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "border": "#2D3348",
    "severity_critical": "#DC2626",
    "severity_high": "#F97316",
    "severity_medium": "#EAB308",
    "severity_low": "#22C55E",
}

SEVERITY_COLORS = {
    "Critical": COLORS["severity_critical"],
    "High": COLORS["severity_high"],
    "Medium": COLORS["severity_medium"],
    "Low": COLORS["severity_low"],
}

CATEGORY_ICONS = {
    "Grammar": "G",
    "Spelling": "S",
    "Style": "St",
    "Consistency": "C",
    "Formatting": "F",
    "Readability": "R",
    "Privacy": "P",
}


# ─── Score Gauge Widget ──────────────────────────────────────────────────────
class ScoreGauge(ctk.CTkFrame):
    """A circular score gauge widget that visualizes a 0-100 score."""

    def __init__(self, master, label: str, score: float = 0, size: int = 100, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.label_text = label
        self.score = score
        self.size = size

        self.canvas = tk.Canvas(
            self, width=size, height=size,
            bg=COLORS["bg_card"], highlightthickness=0,
        )
        self.canvas.pack(pady=(5, 2))

        self.label = ctk.CTkLabel(
            self, text=label,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=COLORS["text_secondary"],
        )
        self.label.pack(pady=(0, 5))

        self._draw_gauge(score)

    def _score_color(self, score: float) -> str:
        if score >= 80:
            return COLORS["accent_green"]
        elif score >= 60:
            return COLORS["accent_yellow"]
        elif score >= 40:
            return COLORS["accent_red"]
        return COLORS["severity_critical"]

    def _draw_gauge(self, score: float):
        self.canvas.delete("all")
        cx, cy = self.size // 2, self.size // 2
        r = self.size // 2 - 8
        color = self._score_color(score)

        # Background arc
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=135, extent=270, style="arc",
            outline=COLORS["border"], width=6,
        )
        # Score arc
        extent = (score / 100) * 270
        self.canvas.create_arc(
            cx - r, cy - r, cx + r, cy + r,
            start=135, extent=extent, style="arc",
            outline=color, width=6,
        )
        # Score text
        self.canvas.create_text(
            cx, cy,
            text=f"{score:.0f}",
            fill=color,
            font=("Segoe UI", int(self.size * 0.22), "bold"),
        )

    def update_score(self, score: float):
        self.score = score
        self._draw_gauge(score)


# ─── Issue Card Widget ───────────────────────────────────────────────────────
class IssueCard(ctk.CTkFrame):
    """A card widget displaying a single analysis issue."""

    def __init__(self, master, suggestion, index: int, **kwargs):
        super().__init__(
            master, fg_color=COLORS["bg_card"],
            corner_radius=10, border_width=1,
            border_color=COLORS["border"], **kwargs,
        )
        s = suggestion

        # Top row: severity badge + category
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=12, pady=(10, 4))

        sev_color = SEVERITY_COLORS.get(s.severity.value, COLORS["text_muted"])
        icon = CATEGORY_ICONS.get(s.type.value, "•")

        badge = ctk.CTkLabel(
            top, text=f" {s.severity.value.upper()} ",
            font=ctk.CTkFont(size=10, weight="bold"),
            text_color="#FFFFFF",
            fg_color=sev_color, corner_radius=4,
            width=70, height=22,
        )
        badge.pack(side="left")

        cat_label = ctk.CTkLabel(
            top,
            text=f"  {icon}  {s.type.value} — {s.category}",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        cat_label.pack(side="left", padx=(8, 0))

        # Message
        msg = ctk.CTkLabel(
            self, text=s.message,
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"],
            wraplength=550, justify="left", anchor="w",
        )
        msg.pack(fill="x", padx=12, pady=(2, 4))

        # Original → Suggested
        if s.originalText and s.suggestedText:
            fix_frame = ctk.CTkFrame(self, fg_color="#1E2233", corner_radius=6)
            fix_frame.pack(fill="x", padx=12, pady=(2, 10))

            orig = ctk.CTkLabel(
                fix_frame,
                text=f'  ✗  "{s.originalText}"',
                font=ctk.CTkFont(size=11, family="Courier"),
                text_color=COLORS["accent_red"], anchor="w",
            )
            orig.pack(fill="x", padx=8, pady=(6, 0))

            arrow = ctk.CTkLabel(
                fix_frame, text="  ↓",
                font=ctk.CTkFont(size=11),
                text_color=COLORS["text_muted"], anchor="w",
            )
            arrow.pack(fill="x", padx=8)

            sugg = ctk.CTkLabel(
                fix_frame,
                text=f'  ✓  "{s.suggestedText}"',
                font=ctk.CTkFont(size=11, family="Courier"),
                text_color=COLORS["accent_green"], anchor="w",
            )
            sugg.pack(fill="x", padx=8, pady=(0, 6))


# ─── Stats Bar Widget ────────────────────────────────────────────────────────
class StatCard(ctk.CTkFrame):
    """A small stat display card."""

    def __init__(self, master, title: str, value: str, color: str, **kwargs):
        super().__init__(
            master, fg_color=COLORS["bg_card"],
            corner_radius=10, border_width=1,
            border_color=COLORS["border"], **kwargs,
        )
        self.grid_columnconfigure(0, weight=1)

        val_label = ctk.CTkLabel(
            self, text=value,
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=color,
        )
        val_label.grid(row=0, column=0, padx=15, pady=(12, 0))

        title_label = ctk.CTkLabel(
            self, text=title,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        )
        title_label.grid(row=1, column=0, padx=15, pady=(0, 12))


# ═══════════════════════════════════════════════════════════════════════════════
#  Main Application
# ═══════════════════════════════════════════════════════════════════════════════
class DocxAnalyzerApp(ctk.CTk):
    """Complete overhaul of the AI Document Analyzer with rich visual analytics."""

    def __init__(self):
        super().__init__()

        self.title("AI Document Analyzer")
        self.geometry("1100x750")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg_dark"])

        self.controller: Optional[AIController] = None
        self.current_result: Optional[AnalysisResult] = None
        
        # Thread-safe queue for UI updates to prevent segmentation faults
        self.result_queue = queue.Queue()
        self._check_queue()

        self._build_ui()
        
    def _check_queue(self):
        try:
            msg_type, *data = self.result_queue.get_nowait()
            if msg_type == "success":
                self._show_results(data[0], data[1])
            elif msg_type == "error":
                self._show_error(data[0])
        except queue.Empty:
            pass
        finally:
            self.after(100, self._check_queue)

    # ── Build UI ──────────────────────────────────────────────────────────
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_welcome_screen()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"], corner_radius=0, height=60)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(1, weight=1)

        # Logo / Title
        title = ctk.CTkLabel(
            header, text="AI Document Analyzer",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        title.grid(row=0, column=0, padx=20, pady=15, sticky="w")

        # Right buttons
        btn_frame = ctk.CTkFrame(header, fg_color="transparent")
        btn_frame.grid(row=0, column=2, padx=20, pady=15, sticky="e")

        self.open_btn = ctk.CTkButton(
            btn_frame, text="Open .docx",
            width=120, height=32, corner_radius=8,
            fg_color=COLORS["accent_blue"],
            hover_color="#2563EB",
            text_color="#FFFFFF",
            font=ctk.CTkFont(weight="bold"),
            command=self._open_file,
        )
        self.open_btn.pack(side="left")

    def _build_welcome_screen(self):
        """Show the initial welcome / landing screen."""
        self.welcome_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.welcome_frame.grid(row=1, column=0, sticky="nsew")
        self.welcome_frame.grid_columnconfigure(0, weight=1)
        self.welcome_frame.grid_rowconfigure(0, weight=1)

        center = ctk.CTkFrame(self.welcome_frame, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")

        icon_label = ctk.CTkLabel(
            center, text="",
            font=ctk.CTkFont(size=64),
        )
        icon_label.pack(pady=(0, 10))

        welcome_title = ctk.CTkLabel(
            center, text="Analyze Your Documents with AI",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["text_primary"],
        )
        welcome_title.pack(pady=(0, 8))

        welcome_sub = ctk.CTkLabel(
            center,
            text="Open a .docx file to get grammar, style, consistency,\nreadability, formatting, and privacy analysis in seconds.",
            font=ctk.CTkFont(size=14),
            text_color=COLORS["text_muted"],
            justify="center",
        )
        welcome_sub.pack(pady=(0, 25))

        open_big_btn = ctk.CTkButton(
            center, text="Open .docx File",
            width=220, height=48, corner_radius=12,
            fg_color=COLORS["accent_blue"],
            hover_color="#2563EB",
            font=ctk.CTkFont(size=15, weight="bold"),
            command=self._open_file,
        )
        open_big_btn.pack()

        # Provider status
        provider_text = "Rule-based engine active"

        provider_label = ctk.CTkLabel(
            center, text=provider_text,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
        )
        provider_label.pack(pady=(20, 0))

    # ── File Open & Analysis ──────────────────────────────────────────────
    def _open_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Word Documents", "*.docx")]
        )
        if not filepath:
            return

        # Destroy welcome or previous results
        if hasattr(self, "welcome_frame") and self.welcome_frame.winfo_exists():
            self.welcome_frame.destroy()
        if hasattr(self, "results_frame") and self.results_frame.winfo_exists():
            self.results_frame.destroy()

        # Show loading screen
        self._show_loading(os.path.basename(filepath))

        # Start analysis in background thread
        threading.Thread(
            target=self._run_analysis, args=(filepath,), daemon=True
        ).start()

    def _show_loading(self, filename: str):
        self.loading_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.loading_frame.grid(row=1, column=0, sticky="nsew")
        self.loading_frame.grid_columnconfigure(0, weight=1)
        self.loading_frame.grid_rowconfigure(0, weight=1)

        center = ctk.CTkFrame(self.loading_frame, fg_color="transparent")
        center.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(
            center, text="Analyzing...",
            font=ctk.CTkFont(size=48),
        ).pack(pady=(0, 15))

        ctk.CTkLabel(
            center, text=f"Analyzing {filename}...",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text_primary"],
        ).pack()

        ctk.CTkLabel(
            center,
            text="Running grammar, consistency, formatting, readability, and privacy checks...",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_muted"],
        ).pack(pady=(8, 0))

    def _run_analysis(self, filepath: str):
        try:
            # Build AI provider
            provider = LocalRuleBasedProvider()

            self.controller = AIController(ai_provider=provider)
            doc = self.controller.parser.parse(filepath)
            self.current_result = self.controller.analyze(doc)
            report = self.controller.generateReport(self.current_result)

            self.result_queue.put(("success", self.current_result, report))
        except Exception as e:
            self.result_queue.put(("error", str(e)))

    def _show_error(self, msg: str):
        if hasattr(self, "loading_frame") and self.loading_frame.winfo_exists():
            self.loading_frame.destroy()
        messagebox.showerror("Analysis Error", msg)
        self._build_welcome_screen()

    # ── Results Dashboard ─────────────────────────────────────────────────
    def _show_results(self, result: AnalysisResult, report):
        if hasattr(self, "loading_frame") and self.loading_frame.winfo_exists():
            self.loading_frame.destroy()

        self.results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.results_frame.grid(row=1, column=0, sticky="nsew", padx=15, pady=10)
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(1, weight=1)

        qs = result.qualityScore
        summary = result.getSummary()

        # ── Top Stats Row ─────────────────────────────────────────────
        stats_row = ctk.CTkFrame(self.results_frame, fg_color="transparent")
        stats_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        for i in range(7):
            stats_row.grid_columnconfigure(i, weight=1)

        # Overall Score Gauge (larger)
        overall_gauge = ScoreGauge(stats_row, "Overall", qs.overallScore, size=110)
        overall_gauge.grid(row=0, column=0, padx=5)

        # Category gauges
        gauges_data = [
            ("Writing", qs.writingScore),
            ("Consistency", qs.consistencyScore),
            ("Formatting", qs.formattingScore),
            ("Readability", qs.readabilityScore),
            ("Privacy", qs.privacyScore),
        ]
        for i, (name, score) in enumerate(gauges_data, start=1):
            g = ScoreGauge(stats_row, name, score, size=85)
            g.grid(row=0, column=i, padx=5)

        # Stat cards
        total_issues = len(result.suggestions)
        stat_card = StatCard(
            stats_row, "Issues Found", str(total_issues),
            COLORS["accent_red"] if total_issues > 10 else COLORS["accent_yellow"] if total_issues > 0 else COLORS["accent_green"],
        )
        stat_card.grid(row=0, column=6, padx=5, sticky="ns")

        # ── Tabview for categories ────────────────────────────────────
        tabview = ctk.CTkTabview(
            self.results_frame,
            fg_color=COLORS["bg_card"],
            segmented_button_fg_color=COLORS["bg_dark"],
            segmented_button_selected_color=COLORS["accent_blue"],
            segmented_button_unselected_color=COLORS["bg_card_hover"],
            corner_radius=12,
        )
        tabview.grid(row=1, column=0, sticky="nsew")

        # Add tabs
        all_tab = tabview.add("All Issues")
        report_tab = tabview.add("Full Report")

        # Group issues by category
        categories = {}
        for s in result.suggestions:
            cat = s.type.value
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(s)

        # Add category-specific tabs
        for cat_name in categories:
            tab = tabview.add(f"{CATEGORY_ICONS.get(cat_name, '•')} {cat_name}")
            self._populate_issues_tab(tab, categories[cat_name])

        # Populate "All Issues" tab
        self._populate_issues_tab(all_tab, result.suggestions)

        # Populate "Full Report" tab
        self._populate_report_tab(report_tab, report)

        # Set default tab
        tabview.set("All Issues")

    def _populate_issues_tab(self, tab, suggestions):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(
            tab, fg_color="transparent",
            scrollbar_button_color=COLORS["border"],
            scrollbar_button_hover_color=COLORS["accent_blue"],
        )
        scroll.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        scroll.grid_columnconfigure(0, weight=1)

        if not suggestions:
            ctk.CTkLabel(
                scroll, text="No issues found in this category!",
                font=ctk.CTkFont(size=14),
                text_color=COLORS["accent_green"],
            ).pack(pady=30)
            return

        # Summary bar
        sev_counts = {}
        for s in suggestions:
            key = s.severity.value
            sev_counts[key] = sev_counts.get(key, 0) + 1

        summary_text = f"  {len(suggestions)} issues  |  "
        for sev in ["Critical", "High", "Medium", "Low"]:
            if sev in sev_counts:
                summary_text += f"{sev}: {sev_counts[sev]}  "

        summary_bar = ctk.CTkLabel(
            scroll, text=summary_text,
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_muted"],
            anchor="w",
        )
        summary_bar.grid(row=0, column=0, sticky="w", padx=5, pady=(5, 10))

        for i, s in enumerate(suggestions):
            card = IssueCard(scroll, s, i)
            card.grid(row=i + 1, column=0, sticky="ew", padx=5, pady=3)

    def _populate_report_tab(self, tab, report):
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(0, weight=1)

        textbox = ctk.CTkTextbox(
            tab,
            font=ctk.CTkFont(family="Courier", size=12),
            fg_color=COLORS["bg_dark"],
            text_color=COLORS["text_secondary"],
            scrollbar_button_color=COLORS["border"],
        )
        textbox.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        textbox.insert("1.0", report.content_text)
        textbox.configure(state="disabled")


# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = DocxAnalyzerApp()
    app.mainloop()
