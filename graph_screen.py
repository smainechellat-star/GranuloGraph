"""
Graph Screen Module - Visualization and Analysis
Complete implementation with ISO 14688-1:2017 classification
Author: Smaine Chellat
Institution: University Constantine 1, Geological Department, Algeria
Version: 2.0
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import pandas as pd
import math
from typing import List, Tuple, Dict, Optional
from calculations import GranuloCalculator, normalize_pan_label
import csv

def fmt_num(x, decimals: int = 2, sig_figs: int = 3) -> str:
    if x is None: return "—"
    try: x = float(x)
    except (TypeError, ValueError): return str(x)
    if not math.isfinite(x): return "—"
    if x == 0: return f"{x:.{decimals}f}"
    magnitude = int(math.floor(math.log10(abs(x))))
    needed = max(decimals, sig_figs - magnitude - 1)
    return f"{x:.{needed}f}"


class GraphScreen(tk.Frame):
    def __init__(self, parent, app, data=None, multiple_series=None):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.data = data
        self.multiple_series = multiple_series or []
        self.show_frequency = False
        self.curve_visible = []   # per-sample visibility of the main cumulative curves
        self.freq_visible = []    # per-sample visibility of the frequency curves
        self.current_cursor_x = None
        self.current_cursor_y = None
        self.current_series_index = 0
        self.freq_ax = None
        self.last_correlation_fig = None
        self.colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
        self.iso_boundaries = [0.002, 0.0063, 0.02, 0.063, 0.2, 0.63, 2.0, 6.3, 20.0, 63.0, 200.0, 630.0]
        self.setup_ui()
        if self.data or self.multiple_series:
            self.plot_data()

    def setup_ui(self):
        toolbar = tk.Frame(self, bg='#2c3e50', height=40)
        toolbar.pack(fill=tk.X)
        tk.Button(toolbar, text="🏠 Home", command=self.app.show_home_screen, bg='#34495e', fg='white', font=('Arial', 10), padx=10).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="⚙ Settings", command=self.app.show_settings_screen, bg='#34495e', fg='white', font=('Arial', 10), padx=10).pack(side=tk.LEFT, padx=5, pady=5)

        if len(self.multiple_series) > 0 or self.data:
            tk.Label(toolbar, text="Series:", bg='#2c3e50', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=(20, 5))
            self.series_var = tk.StringVar(value="Sample 1")
            all_samples = ["Sample 1"] + [f"Sample {i+2}" for i in range(len(self.multiple_series))]
            series_menu = ttk.Combobox(toolbar, textvariable=self.series_var, values=all_samples, state="readonly", width=15)
            series_menu.pack(side=tk.LEFT, padx=5)
            series_menu.bind('<<ComboboxSelected>>', self.on_series_change)
            self.curves_btn = tk.Button(toolbar, text='☑ Curves', bg='#16a085', fg='white', font=('Arial', 10), padx=8,
                                        command=lambda: self._open_visibility_panel('curve_visible', 'Select Curves to Display', self.curves_btn,
                                        hint='Show or hide each sample curve on the main graph.'))
            self.curves_btn.pack(side=tk.LEFT, padx=(5, 10))
            # ── Classification Standard: Classes checkboxes (ISO / ASTM) ──
            tk.Frame(toolbar, width=1, height=22, bg='#566573').pack(side=tk.LEFT, padx=10)
            self.classes_lbl = tk.Label(toolbar, text='Classes (bands):', bg='#2c3e50', fg='white',
                                        font=('Segoe UI', 9, 'bold'))
            self.classes_lbl.pack(side=tk.LEFT, padx=(0, 5))
            # Classes (bands) defaults follow the calculation basis chosen
            # on the Home screen: recovered weight -> ASTM D6913 bands
            # checked; initial weight -> NF P94-056 / ISO 17892-4 bands
            # checked. main.show_graph_screen() re-reads the basis and
            # rebuilds this screen, so the default re-syncs on every open.
            _basis_astm = bool(getattr(self.app, 'use_recovered_weight', True))
            self.show_iso_var = tk.BooleanVar(value=not _basis_astm)
            self.show_astm_var = tk.BooleanVar(value=_basis_astm)
            self.chk_iso = tk.Checkbutton(toolbar, text='ISO', variable=self.show_iso_var,
                                          command=self.on_standard_toggle, bg='#2980b9', fg='white',
                                          selectcolor='#1f618d', activebackground='#2471a3',
                                          activeforeground='white', font=('Segoe UI', 9, 'bold'),
                                          indicatoron=True, padx=8, pady=3, relief='flat', cursor='hand2')
            self.chk_iso.pack(side=tk.LEFT, padx=3)
            self.chk_astm = tk.Checkbutton(toolbar, text='ASTM', variable=self.show_astm_var,
                                           command=self.on_standard_toggle, bg='#d35400', fg='white',
                                           selectcolor='#a04000', activebackground='#ba4a00',
                                           activeforeground='white', font=('Segoe UI', 9, 'bold'),
                                           indicatoron=True, padx=8, pady=3, relief='flat', cursor='hand2')
            self.chk_astm.pack(side=tk.LEFT, padx=3)
            self._attach_tooltip(self.classes_lbl,
                                 'These checkboxes only toggle the classification BANDS (ISO 14688-1 / '
                                 'ASTM D2487) drawn above the graph. They never add, remove or split curves: '
                                 'a sample always keeps the same cumulative and frequency curve. To choose '
                                 'which samples are drawn, use the \u2611 Curves button (cumulative) and the '
                                 '\u2611 Frequency Curves button (frequency).')
            self._attach_tooltip(self.chk_iso,
                                 'ISO 14688-1:2017 classes: Clay < 0.002 | Silt 0.002\u20130.063 | '
                                 'Sand 0.063\u20132 | Gravel 2\u201363 | Cobbles 63\u2013200 | '
                                 'Boulders > 200 mm.\nShows or hides the blue-grey band above the graph '
                                 '(the curves themselves are not affected).')
            self._attach_tooltip(self.chk_astm,
                                 'ASTM D2487 (USCS) classes: Fines < 0.075 (#200) | Sand 0.075\u20134.75 '
                                 '(#4) | Gravel 4.75\u201375 (3 in.) | Cobbles / Boulders > 75 mm.\n'
                                 'Shows or hides the orange band and the dashed ASTM boundary lines '
                                 '(the curves themselves are not affected).')
            # ── Calculation-basis comparison: dotted curve of the other basis ──
            tk.Frame(toolbar, width=1, height=22, bg='#566573').pack(side=tk.LEFT, padx=10)
            self.compare_bases_var = tk.BooleanVar(value=False)
            self.chk_compare = tk.Checkbutton(toolbar, text='⚖ Compare bases', variable=self.compare_bases_var,
                                              command=self.on_compare_toggle, bg='#2c3e50', fg='white',
                                              selectcolor='#46627f', activebackground='#34495e',
                                              activeforeground='white', font=('Segoe UI', 9, 'bold'),
                                              indicatoron=True, padx=8, pady=3, relief='flat', cursor='hand2')
            self.chk_compare.pack(side=tk.LEFT, padx=3)
            self._attach_tooltip(self.chk_compare,
                                 'Solid curve = active calculation basis (Home Screen). The dotted curve '
                                 '(same colour) is the SAME sample recomputed with the other basis: ASTM D6913 '
                                 'recovered weight vs NF P94-056/ISO initial weight. The horizontal gap '
                                 'between the two curves shows how much the mass normalization shifts the '
                                 'percentiles (no gap = 100% recovery). The ISO/ASTM Classes checkboxes '
                                 'never shift curves: they only re-zone them.')

        content = tk.Frame(self)
        content.pack(fill=tk.BOTH, expand=True)
        
        left_panel = tk.Frame(content) 
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(8, 6), dpi=100, facecolor='white')
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.1, right=0.85, top=0.88, bottom=0.12)
        self.canvas = FigureCanvasTkAgg(self.fig, left_panel)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar_frame = tk.Frame(left_panel)
        toolbar_frame.pack(fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        toggle_frame = tk.Frame(left_panel)
        toggle_frame.pack(fill=tk.X, pady=5)
        self.toggle_btn = tk.Button(toggle_frame, text="📈 Display Frequency Curves", command=self.toggle_frequency, bg='#3498db', fg='white', font=('Arial', 10), padx=10)
        self.toggle_btn.pack(side=tk.LEFT, padx=5)
        self.freq_select_btn = tk.Button(toggle_frame, text='☑ Frequency Curves', bg='#8e44ad', fg='white', font=('Arial', 10), padx=10,
                                         command=lambda: self._open_visibility_panel('freq_visible', 'Select Frequency Curves to Display', self.freq_select_btn,
                                         hint='Applies to the frequency curves (press "📈 Display Frequency Curves" to show them).'))
        self.freq_select_btn.pack(side=tk.LEFT, padx=5)

        right_panel = tk.Frame(content, width=320, relief=tk.GROOVE, bd=2, bg='#f8f9f9')
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_panel.pack_propagate(False)
        
        canvas_right = tk.Canvas(right_panel, bg='#f8f9f9', highlightthickness=0)
        scrollbar_right = tk.Scrollbar(right_panel, orient=tk.VERTICAL, command=canvas_right.yview)
        scrollable_frame = tk.Frame(canvas_right, bg='#f8f9f9')
        scrollable_frame.bind("<Configure>", lambda e: canvas_right.configure(scrollregion=canvas_right.bbox("all")))
        canvas_right.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_right.configure(yscrollcommand=scrollbar_right.set)
        canvas_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_right.pack(side=tk.RIGHT, fill=tk.Y)

        cursor_frame = tk.LabelFrame(scrollable_frame, text="📌 Cursor Position", font=('Arial', 11, 'bold'), bg='#f8f9f9', padx=10, pady=10)
        cursor_frame.pack(fill=tk.X, padx=5, pady=5)
        self.cursor_x_var = tk.StringVar(value="Diameter: -- mm")
        self.cursor_y_var = tk.StringVar(value="Passing: -- %")
        tk.Label(cursor_frame, textvariable=self.cursor_x_var, bg='#f8f9f9', font=('Arial', 10)).pack(anchor=tk.W, pady=2)
        tk.Label(cursor_frame, textvariable=self.cursor_y_var, bg='#f8f9f9', font=('Arial', 10)).pack(anchor=tk.W, pady=2)

        proj_frame = tk.LabelFrame(scrollable_frame, text="🎯 Project Value", font=('Arial', 11, 'bold'), bg='#f8f9f9', padx=10, pady=10)
        proj_frame.pack(fill=tk.X, padx=5, pady=5)
        if len(self.multiple_series) > 0 or self.data:
            proj_sample_frame = tk.Frame(proj_frame, bg='#f8f9f9')
            proj_sample_frame.pack(fill=tk.X, pady=2)
            tk.Label(proj_sample_frame, text="Sample:", bg='#f8f9f9', font=('Arial', 10)).pack(side=tk.LEFT, padx=(0, 5))
            self.proj_sample_var = tk.StringVar(value="Sample 1")
            all_samples = ["Sample 1"] + [f"Sample {i+2}" for i in range(len(self.multiple_series))]
            proj_sample_menu = ttk.Combobox(proj_sample_frame, textvariable=self.proj_sample_var, values=all_samples, state="readonly", width=12)
            proj_sample_menu.pack(side=tk.LEFT)
            proj_sample_menu.bind('<<ComboboxSelected>>', self.on_proj_sample_change)
        tk.Label(proj_frame, text="Enter percentile (%):", bg='#f8f9f9', font=('Arial', 10)).pack(anchor=tk.W)
        entry_frame = tk.Frame(proj_frame, bg='#f8f9f9')
        entry_frame.pack(fill=tk.X, pady=5)
        self.proj_entry = tk.Entry(entry_frame, width=15, font=('Arial', 10))
        self.proj_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.proj_entry.bind('<KeyRelease>', self.project_percentile)
        tk.Label(entry_frame, text="%", bg='#f8f9f9', font=('Arial', 10)).pack(side=tk.LEFT)
        self.proj_result = tk.Label(proj_frame, text="→ -- mm", bg='#f8f9f9', font=('Arial', 11, 'bold'), fg='#27ae60')
        self.proj_result.pack(anchor=tk.W, pady=5)

        quick_frame = tk.LabelFrame(scrollable_frame, text="📊 Key Percentiles", font=('Arial', 11, 'bold'), bg='#f8f9f9', padx=10, pady=10)
        quick_frame.pack(fill=tk.X, padx=5, pady=5)
        quick_container = tk.Frame(quick_frame, bg='white', height=170)
        quick_container.pack(fill=tk.BOTH, expand=True)
        quick_container.pack_propagate(False)
        quick_v_scrollbar = ttk.Scrollbar(quick_container, orient=tk.VERTICAL)
        quick_v_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        quick_canvas = tk.Canvas(quick_container, bg='white', highlightthickness=0, yscrollcommand=quick_v_scrollbar.set)
        quick_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        quick_v_scrollbar.config(command=quick_canvas.yview)
        quick_h_scrollbar = ttk.Scrollbar(quick_container, orient=tk.HORIZONTAL, command=quick_canvas.xview)
        quick_h_scrollbar.pack(side=tk.LEFT, fill=tk.X)
        quick_canvas.config(xscrollcommand=quick_h_scrollbar.set)
        quick_scrollable_frame = tk.Frame(quick_canvas, bg='white')
        quick_canvas.create_window((0, 0), window=quick_scrollable_frame, anchor="nw")
        quick_scrollable_frame.bind("<Configure>", lambda e: quick_canvas.configure(scrollregion=quick_canvas.bbox("all")))

        def _on_quick_percentiles_mousewheel(event):
            if quick_canvas.winfo_exists(): quick_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        quick_canvas.bind("<Enter>", lambda e: quick_canvas.bind_all("<MouseWheel>", _on_quick_percentiles_mousewheel))
        quick_canvas.bind("<Leave>", lambda e: quick_canvas.unbind_all("<MouseWheel>"))
        self.quick_text_widgets = {}
        self.update_quick_percentiles_all_samples(quick_scrollable_frame)

        btn_frame = tk.LabelFrame(scrollable_frame, text="⚡ Analysis Tools", font=('Arial', 11, 'bold'), bg='#f8f9f9', padx=10, pady=10)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        buttons = [
            ("📊 Sedimentological Parameters", self.show_sedimentological, '#8e44ad'),
            ("⚙ Geotechnical Parameters", self.show_geotechnical, '#27ae60'),
            ("🔄 Correlation Graphs", self.show_correlation, '#e67e22'),
            ("📈 Friedman (1967) Plots", self.show_friedman_plots, '#3498db'),
            ("📉 Passega C-M Diagram", self.show_passega_diagram, '#9b59b6'),
            ("🌐 Ternary Diagrams (Folk 1954 / Shepard 1954)", self.show_ternary_diagrams, '#c0392b'),
            ("📊 Distribution Graphs (φ & μm/mm)", self.show_distribution, '#2980b9'),
            ("⚖ Bland-Altman (ISO vs ASTM)", self.show_bland_altman, '#16a085'),
        ]
        for text, command, color in buttons:
            tk.Button(btn_frame, text=text, command=command, bg=color, fg='white', font=('Arial', 10), width=30, pady=3).pack(pady=2)

        export_frame = tk.LabelFrame(scrollable_frame, text="💾 Export", font=('Arial', 11, 'bold'), bg='#f8f9f9', padx=10, pady=10)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        self.export_btn = tk.Button(export_frame, text="📥 Export", command=self.show_export_menu, bg='#3498db', fg='white', font=('Arial', 10, 'bold'), width=30, pady=5)
        self.export_btn.pack(pady=2)
        self.export_menu = tk.Menu(export_frame, tearoff=0, bg='white', font=('Arial', 10))
        self.export_menu.add_command(label="📊 Main Graph as PNG", command=self.export_main_graph)
        self.export_menu.add_command(label="📁 Results as CSV", command=lambda: self.app.export_results())
        self.export_menu.add_command(label="📊 Results as Excel (.xlsx)", command=self.export_results_xlsx)
        self.export_menu.add_command(label="📄 Report as PDF", command=self.export_pdf_report)
        self.export_menu.add_separator()
        self.export_menu.add_command(label="📥 Export All Parameters", command=self.export_all_parameters)
        self.export_menu.add_separator()
        self.export_menu.add_command(label="📈 Export Friedman Plots", command=self.export_friedman_plots)
        self.export_menu.add_command(label="📉 Export Passega Diagram", command=self.export_passega_diagram)
        self.export_menu.add_command(label="🌐 Export Ternary Diagrams (Folk/Shepard)", command=self.export_ternary_diagrams)
        self.export_menu.add_command(label="📊 Export Distribution Graphs (PNG)", command=self.export_distribution_graphs)
        self.export_menu.add_command(label="⚖ Export Bland-Altman Plot", command=self.export_bland_altman)
        self.export_menu.add_separator()
        self.export_menu.add_command(label="📊 Export Correlation Graph", command=self.export_correlation_graph)

    def show_export_menu(self):
        x = self.export_btn.winfo_rootx()
        y = self.export_btn.winfo_rooty() + self.export_btn.winfo_height()
        try: self.export_menu.post(x, y)
        except Exception as e: messagebox.showerror("Error", f"Failed to show export menu: {str(e)}")

    def export_main_graph(self):
        filename = filedialog.asksaveasfilename(title="Export Main Graph", defaultextension=".png", filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("JPEG files", "*.jpg"), ("TIFF files", "*.tiff")])
        if filename:
            try:
                dpi = 300 if filename.endswith('.png') else 150
                self.fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')
                messagebox.showinfo("Export Successful", f"Main graph exported to:\n{filename}")
            except Exception as e: messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
            
    def export_main_graph_direct(self, filename):
        dpi = 300 if filename.endswith('.png') else 150
        self.fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')

    def export_correlation_graph(self):
        if self.last_correlation_fig is None:
            messagebox.showwarning("No Correlation Graph", "Please open the Correlation Graph window first before exporting.")
            return
        filename = filedialog.asksaveasfilename(title="Export Correlation Graph", defaultextension=".png", filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"), ("JPEG files", "*.jpg"), ("TIFF files", "*.tiff")])
        if filename:
            try:
                dpi = 300 if filename.endswith('.png') else 150
                self.last_correlation_fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')
                messagebox.showinfo("Export Successful", f"Correlation graph exported to:\n{filename}")
            except Exception as e: messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def export_results_xlsx(self):
        all_series = []
        if self.data: all_series.append(('Sample 1', self.data))
        for i, series in enumerate(self.multiple_series): all_series.append((f'Sample {i+2}', series))
        if not all_series: messagebox.showwarning("No Data", "No data to export"); return
        filename = filedialog.asksaveasfilename(title="Export Results as Excel", defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if not filename: return
        try:
            use_recovered = getattr(self.app, 'use_recovered_weight', True)
            rows = []
            for sample_name, series in all_series:
                calc = GranuloCalculator(series, self.app.initial_weight, use_recovered_weight=use_recovered)
                params = calc.get_all_parameters()
                row = {"Sample": sample_name}
                row.update(params)
                rows.append(row)
            df = pd.DataFrame(rows)
            col_order = ["Sample", "calculation_basis", "initial_weight", "recovered_weight", "recovery_pct", "D10", "D30", "D60", "mean_mm", "sorting", "skewness", "kurtosis", "Cu", "Cc", "FM",
                         "ISO_Clay_%", "ISO_Silt_%", "ISO_Sand_%", "ISO_Gravel_%", "ISO_Cobbles_%",
                         "ASTM_Fines_%", "ASTM_Sand_%", "ASTM_Gravel_%", "ASTM_Cobbles_%"]
            existing_cols = [c for c in col_order if c in df.columns]
            other_cols = [c for c in df.columns if c not in existing_cols]
            df = df[existing_cols + other_cols]
            df.to_excel(filename, index=False)
            messagebox.showinfo("Export Successful", f"Results exported to:\n{filename}")
        except Exception as e: messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def _standard_mode(self):
        """'ISO' | 'ASTM' | 'BOTH' | 'NONE' from the Classes checkboxes (default: ISO only)."""
        iso_var = getattr(self, 'show_iso_var', True)
        astm_var = getattr(self, 'show_astm_var', False)
        iso = bool(iso_var.get()) if hasattr(iso_var, 'get') else bool(iso_var)
        astm = bool(astm_var.get()) if hasattr(astm_var, 'get') else bool(astm_var)
        if iso and astm: return 'BOTH'
        if astm: return 'ASTM'
        if iso: return 'ISO'
        return 'NONE'

    def on_standard_toggle(self, event=None):
        """Redraw the plot when the ISO / ASTM Classes checkboxes change."""
        self.plot_data()

    def on_compare_toggle(self, event=None):
        """Redraw the plot when the 'Compare bases' checkbox is toggled."""
        self.plot_data()

    def draw_classification_headers(self, ax=None, mode=None):
        """Draw ISO 14688-1 / ASTM D2487 / stacked dual classification header bars
        above the cumulative curve, driven by the Classes checkboxes in the top
        toolbar. Axis convention: log scale, fine-left (0.0001 mm) → coarse-right
        (1000 mm)."""
        import matplotlib.transforms as mtransforms
        if ax is None: ax = self.ax
        if mode is None: mode = self._standard_mode()
        if mode == 'NONE': return
        left, right = ax.get_xlim()
        lo, hi = min(left, right), max(left, right)
        trans = mtransforms.blended_transform_factory(ax.transData, ax.transAxes)

        iso_bins = [(lo, 0.002, 'Clay'), (0.002, 0.063, 'Silt'), (0.063, 2.0, 'Sand'),
                    (2.0, 63.0, 'Gravel'), (63.0, 200.0, 'Cobbles'), (200.0, hi, 'Boulders')]
        astm_bins = [(lo, 0.075, 'Fines (Silt & Clay)'), (0.075, 4.75, 'Sand'),
                     (4.75, 75.0, 'Gravel'), (75.0, hi, 'Cobbles / Boulders')]

        def render_bar(bins, y_bottom, height, bg_color):
            ax.plot([lo, hi], [y_bottom + height, y_bottom + height], color='black',
                    linewidth=0.9, transform=trans, clip_on=False, zorder=6)
            for a, b, label in bins:
                l_cl, r_cl = max(a, lo), min(b, hi)
                if l_cl >= r_cl: continue
                if a > lo:
                    ax.plot([a, a], [y_bottom, y_bottom + height], color='black',
                            linewidth=0.9, transform=trans, clip_on=False, zorder=6)
                x_center = math.sqrt(l_cl * r_cl)      # geometric centre in log space
                ax.text(x_center, y_bottom + height / 2.0, label, transform=trans,
                        ha='center', va='center', fontsize=8, fontweight='bold',
                        bbox=dict(boxstyle='square,pad=0.15', facecolor=bg_color,
                                  edgecolor='none', alpha=0.9),
                        clip_on=False, zorder=7)

        def astm_vlines():
            for v in (0.075, 4.75, 75.0):
                if lo < v < hi:
                    ax.axvline(v, color='#a04000', linestyle='--', linewidth=0.9, alpha=0.6, zorder=4)
                    ax.text(v, -1.5, f'{v:g}', rotation=90, fontsize=7, ha='center', va='top',
                            color='#a04000', alpha=0.8)

        if mode == 'ISO':
            render_bar(iso_bins, 1.0, 0.040, '#eef4f8')
            self.add_iso_classification()
            self._set_fig_title('Grain Size Distribution Curve (ISO 14688-1:2017 Classes)')
        elif mode == 'ASTM':
            render_bar(astm_bins, 1.0, 0.040, '#fdf3e7')
            astm_vlines()
            self._set_fig_title('Grain Size Distribution Curve (ASTM D2487 / USCS Classes)')
        elif mode == 'BOTH':
            render_bar(iso_bins, 1.040, 0.040, '#eef4f8')
            render_bar(astm_bins, 1.0, 0.040, '#fdf3e7')
            self.add_iso_classification()
            astm_vlines()
            ax.text(lo, 1.060, 'ISO', transform=trans, ha='right', va='center', fontsize=7.5,
                    fontweight='bold', color='#1f4e78', clip_on=False)
            ax.text(lo, 1.020, 'ASTM', transform=trans, ha='right', va='center', fontsize=7.5,
                    fontweight='bold', color='#833c0c', clip_on=False)
            self._set_fig_title('Grain Size Distribution Curve (ISO 14688-1 & ASTM D2487)')

    def _set_fig_title(self, text):
        """Draw the graph title as figure-level text in the empty band ABOVE
        the ISO/ASTM class bars (figure-fraction y, so the title scales with
        the window and always stays in the empty space, with the class
        labels kept below it). The previous ax.set_title(pad=...) used a
        fixed point offset and slid into the ISO band on large/maximised
        windows."""
        old = getattr(self, '_fig_title_artist', None)
        if old is not None:
            try: self.fig.texts.remove(old)
            except ValueError: pass
        self._fig_title_artist = self.fig.text(
            0.475, 0.978, text, ha='center', va='center',
            fontsize=13, fontweight='bold', color='#1a1a2e')

    def plot_data(self):
        try:
            self.ax.clear()
            if hasattr(self, 'freq_ax') and self.freq_ax is not None: self.freq_ax.remove(); self.freq_ax = None
            has_data = False
            self.ax.set_xscale('log'); self.ax.set_xlim(1000, 0.0001); self.ax.set_ylim(-2, 102); self.ax.invert_xaxis()
            self.ax.set_xlabel('Grain Size (mm) - Logarithmic Scale', fontsize=12)
            self.ax.set_ylabel('Cumulative Percentage Passing (%)', fontsize=12)
            self._set_fig_title('Grain Size Distribution Curve')   # empty band above the class bars
            self.ax.grid(True, alpha=0.3, linestyle='--')
            self.ax.tick_params(axis='x', labelsize=8)
            self.draw_classification_headers()
            if self.show_frequency:
                self.freq_ax = self.ax.twinx()
                self.freq_ax.set_ylabel(r"f(x) = dF/d(log$_{10}$ d)   [% per log$_{10}$ unit]", fontsize=11, color='gray', labelpad=15)
                self.freq_ax.tick_params(axis='y', labelcolor='gray'); self.freq_ax.set_ylim(0, 100)
            vis = self._visible_flags('curve_visible')
            fvis = self._visible_flags('freq_visible')
            compare_on = bool(self.compare_bases_var.get()) if hasattr(self, 'compare_bases_var') else False
            use_recovered = getattr(self.app, 'use_recovered_weight', True)
            self._alt_drawn = False
            if self.data and len(self.data) > 0 and (vis[0] or (self.show_frequency and fvis[0])):
                self.plot_series_smooth(self.data, 'Sample 1', self.colors[0], 0, show_curve=vis[0], show_freq=fvis[0], show_alt=compare_on)
                if vis[0]: has_data = True
            for i, series in enumerate(self.multiple_series):
                if series and len(series) > 0 and (vis[i + 1] or (self.show_frequency and fvis[i + 1])):
                    color = self.colors[(i + 1) % len(self.colors)]
                    self.plot_series_smooth(series, f'Sample {i+2}', color, i + 1, show_curve=vis[i + 1], show_freq=fvis[i + 1], show_alt=compare_on)
                    if vis[i + 1]: has_data = True
            freq_shown = self.show_frequency and self.freq_ax is not None and len(self.freq_ax.lines) > 0
            if not has_data and not freq_shown:
                any_series = bool(self.data) or any(bool(s) for s in self.multiple_series)
                msg = 'No curve selected\n(use the ☑ Curves / ☑ Frequency Curves buttons)' if any_series else 'No data to display'
                self.ax.text(0.5, 0.5, msg, transform=self.ax.transAxes, ha='center', va='center', fontsize=13, bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
            leg_handles, leg_labels = self.ax.get_legend_handles_labels()
            if compare_on and has_data and getattr(self, '_alt_drawn', False):
                other_tag = 'initial wt (NF P94-056/ISO)' if use_recovered else 'recovered wt (ASTM D6913)'
                leg_handles.append(plt.Line2D([], [], linestyle=':', color='#7f8c8d', linewidth=1.6))
                leg_labels.append(f'dotted = other basis: {other_tag}')
            if (len(self.multiple_series) > 0 or (compare_on and has_data)) and leg_handles:
                self.ax.legend(leg_handles, leg_labels, loc='lower left', fontsize=9)
            for p in [16, 50, 84]: self.ax.axhline(y=p, color='gray', linestyle=':', alpha=0.5, linewidth=0.5)
            self.fig.canvas.draw_idle(); self.canvas.draw()
        except Exception as e:
            print(f"Error in plot_data: {e}")
            import traceback; traceback.print_exc()

    def plot_series_smooth(self, data, label, color, index, show_curve=True, show_freq=True, show_alt=False):
        try:
            if not data or len(data) == 0: return
            if not show_curve and not (self.show_frequency and show_freq): return
            use_recovered = getattr(self.app, 'use_recovered_weight', True)
            calculator = GranuloCalculator(data, self.app.initial_weight, use_recovered_weight=use_recovered)
            if show_curve:
                sieve_d = np.array([d for d, _ in calculator.data], dtype=float)
                sieve_p = np.array(calculator.cumulative_passing, dtype=float)
                order = np.argsort(sieve_d)[::-1]
                d_desc = sieve_d[order]; p_desc = sieve_p[order]
                self.ax.plot(d_desc, p_desc, 'o', color=color, markersize=5, markeredgecolor='white', markeredgewidth=1, alpha=0.7, zorder=3)
                d_smooth, p_smooth = calculator.get_cumulative_curve(num_points=1500)
                if len(d_smooth) >= 2: self.ax.plot(d_smooth, p_smooth, '-', color=color, label=label, linewidth=2.5, zorder=2)
                else: self.ax.plot(d_desc, p_desc, '-', color=color, label=label, linewidth=2, zorder=2)
                if show_alt:
                    # dotted comparison curve: same sample recomputed with the OTHER
                    # calculation basis (ASTM D6913 recovered vs NF P94-056/ISO initial).
                    # Segments where the two bases coincide (gap < 0.2 %) are masked,
                    # so the dotted trace only appears where the shift is real.
                    alt_calc = GranuloCalculator(data, self.app.initial_weight, use_recovered_weight=(not use_recovered))
                    alt_d, alt_p = alt_calc.get_cumulative_curve(num_points=1500)
                    if len(alt_d) >= 2:
                        alt_y = np.array(alt_p, dtype=float)
                        if len(d_smooth) == len(alt_d):
                            gap_arr = np.abs(alt_y - np.asarray(p_smooth, dtype=float))
                            alt_y = np.where(gap_arr >= 0.2, alt_y, np.nan)
                        if np.isfinite(alt_y).any():
                            self.ax.plot(alt_d, alt_y, ':', color=color, linewidth=1.8, alpha=0.95, zorder=3.5)
                            self._alt_drawn = True
            if self.show_frequency and self.freq_ax is not None and show_freq:
                d_freq, f_freq = calculator.get_frequency_curve(num_points=1500)
                if len(d_freq) >= 2:
                    self.freq_ax.plot(d_freq, f_freq, '--', color=color, alpha=0.75, linewidth=1.6, label=f"{label} (freq)", zorder=1)
                    max_f = float(np.nanmax(f_freq)) if len(f_freq) else 0.0
                    if max_f > 0: self.freq_ax.set_ylim(0, max(self.freq_ax.get_ylim()[1], max_f * 1.15))
        except Exception as e:
            print(f"Error in plot_series_smooth for {label}: {e}")
            import traceback; traceback.print_exc()

    def add_iso_classification(self):
        main_boundaries = [(0.002, 'Clay/Silt'), (0.063, 'Silt/Sand'), (2.0, 'Sand/Gravel'), (63.0, 'Gravel/Cobble'), (200.0, 'Cobble/Boulder')]
        for boundary, _label in main_boundaries: self.ax.axvline(x=boundary, color='gray', linestyle='-', linewidth=2.5, alpha=0.7, zorder=5)
        for value in [0.002, 0.0063, 0.02, 0.063, 0.2, 0.63, 2.0, 6.3, 20.0, 63.0, 200.0, 630.0]:
            self.ax.axvline(x=value, color='black', linestyle='--', linewidth=0.5, alpha=0.4, zorder=4)
            self.ax.text(value, -1.5, f'{value:g}', rotation=90, fontsize=7, ha='center', va='top', color='black', alpha=0.6)

    def update_quick_percentiles_all_samples(self, parent):
        for widget in parent.winfo_children(): widget.destroy()
        all_series = []
        if self.data: all_series.append(('Sample 1', self.data))
        for i, series in enumerate(self.multiple_series): all_series.append((f'Sample {i+2}', series))
        if not all_series: return
        use_recovered = getattr(self.app, 'use_recovered_weight', True)
        for sample_name, series in all_series:
            sample_frame = tk.Frame(parent, bg='white')
            sample_frame.pack(fill=tk.X, padx=5, pady=3)
            tk.Label(sample_frame, text=sample_name, font=('Arial', 9, 'bold'), bg='#3498db', fg='white', padx=10, pady=2).pack(fill=tk.X)
            text_widget = tk.Text(sample_frame, height=9, width=45, font=('Courier', 8), bg='white')
            text_widget.pack(fill=tk.X, padx=2, pady=2)
            calculator = GranuloCalculator(series, self.app.initial_weight, use_recovered_weight=use_recovered)
            params = calculator.get_all_percentiles()
            text = "Pct |  Diameter (mm)  |  Phi (φ)\n" + "-" * 38 + "\n"
            for p in [5, 10, 16, 25, 30, 50, 60, 70, 75, 84, 90, 95]:
                mm = params.get(f'D{p}', 0); phi = params.get(f'phi{p}', 0)
                if mm and not math.isnan(mm) and mm > 0 and not math.isnan(phi): text += f"{p:3.0f}%| {fmt_num(mm, 2, 3):>14} | {fmt_num(phi, 3, 3):>7}\n"
                else: text += f"{p:3.0f}%|       —        |    —\n"
            pan = calculator.get_pan_summary()
            if pan["has_pan"]: text += "-" * 38 + "\n" + f"Pan | {fmt_num(pan['pan_weight_g'], 2, 4):>9} g  | " + f"{fmt_num(pan['pan_pct_of_basis'], 2, 3)}% of basis\n"
            text_widget.insert('1.0', text); text_widget.config(state=tk.DISABLED)
            self.quick_text_widgets[sample_name] = text_widget

    def toggle_frequency(self):
        self.show_frequency = not self.show_frequency
        if self.show_frequency: self.toggle_btn.config(text="📉 Hide Frequency Curves", bg='#e74c3c')
        else: self.toggle_btn.config(text="📈 Display Frequency Curves", bg='#3498db')
        self.plot_data()

    def _visible_flags(self, attr):
        """Normalized per-sample visibility flags (index 0 = Sample 1, i+1 = Sample i+2).
        Missing entries default to True (visible)."""
        n = 1 + len(self.multiple_series)
        flags = [bool(f) for f in list(getattr(self, attr, []) or [])]
        if len(flags) < n: flags += [True] * (n - len(flags))
        return flags[:n]

    @staticmethod
    def _attach_tooltip(widget, text):
        """Lightweight hover tooltip (mouse-over hint) for a toolbar widget."""
        state = {'win': None}

        def show(_event=None):
            if state['win'] is not None: return
            try:
                x = widget.winfo_rootx() + 10
                y = widget.winfo_rooty() + widget.winfo_height() + 6
                ty = min(max(8, y), widget.winfo_screenheight() - 120)
                tw = tk.Toplevel(widget)
                tw.wm_overrideredirect(True)
                tw.wm_geometry(f'+{x}+{ty}')
                tk.Label(tw, text=text, justify=tk.LEFT, bg='#fffbe6', fg='#2c3e50',
                         relief=tk.SOLID, borderwidth=1, font=('Segoe UI', 8),
                         wraplength=420, padx=7, pady=5).pack()
                state['win'] = tw
            except Exception:
                state['win'] = None

        def hide(_event=None):
            if state['win'] is not None:
                try: state['win'].destroy()
                except Exception: pass
                state['win'] = None

        widget.bind('<Enter>', show)
        widget.bind('<Leave>', hide)
        widget.bind('<ButtonPress>', hide)
        try: widget.bind('<Destroy>', hide, add='+')
        except Exception: pass

    def _open_visibility_panel(self, attr, title, anchor_widget=None, hint=None):
        """Popup panel with a cross checkbox per sample plus Select All / Deselect All,
        to show or hide individual sample curves. Changes apply instantly."""
        flags = self._visible_flags(attr)
        n = len(flags)
        win = tk.Toplevel(self)
        win.title(title)
        win.resizable(False, False)
        win.withdraw()   # build hidden, position, then show
        main = tk.Frame(win, bg='#f8f9f9', padx=12, pady=10)
        main.pack(fill=tk.BOTH, expand=True)
        tk.Label(main, text="☑ Check / uncheck the samples to display:", bg='#f8f9f9',
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(0, 2))
        if hint:
            tk.Label(main, text=hint, bg='#f8f9f9', fg='#666666',
                     font=('Arial', 8, 'italic'), wraplength=340, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 6))
        list_frame = tk.Frame(main, bg='#f8f9f9')
        list_frame.pack(fill=tk.BOTH, expand=True)

        def apply_changes(_event=None):
            setattr(self, attr, [bool(v.get()) for v in check_vars])
            self.plot_data()

        def select_all(state):
            for v in check_vars: v.set(bool(state))
            apply_changes()

        check_vars = []
        cols = 2 if n > 6 else 1
        for i in range(n):
            var = tk.BooleanVar(value=bool(flags[i]))
            check_vars.append(var)
            row, col = divmod(i, cols)
            tk.Label(list_frame, text='  ', bg=self.colors[i % len(self.colors)], width=2,
                     relief=tk.GROOVE).grid(row=row, column=col * 2, sticky='ew', padx=(10 if col else 4, 2), pady=2)
            tk.Checkbutton(list_frame, text=f'Sample {i+1}', variable=var, command=apply_changes,
                           bg='#f8f9f9', font=('Arial', 10), anchor='w').grid(row=row, column=col * 2 + 1, sticky='w')
        btn_row = tk.Frame(main, bg='#f8f9f9')
        btn_row.pack(fill=tk.X, pady=(10, 0))
        tk.Button(btn_row, text='☑ Select All', command=lambda: select_all(True), bg='#27ae60', fg='white',
                  font=('Arial', 9, 'bold'), padx=8, pady=2).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_row, text='☐ Deselect All', command=lambda: select_all(False), bg='#e67e22', fg='white',
                  font=('Arial', 9, 'bold'), padx=8, pady=2).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_row, text='✕ Close', command=win.destroy, bg='#7f8c8d', fg='white',
                  font=('Arial', 9, 'bold'), padx=8, pady=2).pack(side=tk.RIGHT, padx=3)
        # Position the panel next to its trigger button while keeping it fully on
        # screen: a button at the bottom of the window (e.g. the bottom
        # 'Frequency Curves' selector) would otherwise open the panel below the
        # visible area, making the button look dead.
        try:
            win.update_idletasks()
            sw, sh = win.winfo_screenwidth(), win.winfo_screenheight()
            pw = max(win.winfo_reqwidth(), 140)
            ph = max(win.winfo_reqheight(), 100)
            if anchor_widget is not None:
                bx = anchor_widget.winfo_rootx()
                by = anchor_widget.winfo_rooty()
                bh = max(anchor_widget.winfo_height(), 10)
                x, y = bx, by + bh + 6          # default: just below the button
                if y + ph > sh - 8:             # not enough room below -> flip above
                    y = by - ph - 6
                if y < 8:                       # neither side fits -> clamp inside
                    y = max(8, min(sh - ph - 8, by + bh + 6))
                x = min(max(8, x), max(8, sw - pw - 8))
            else:
                x, y = max(8, (sw - pw) // 2), max(8, (sh - ph) // 2)
            win.geometry(f'+{x}+{y}')
        except Exception:
            pass
        win.transient(self)
        win.deiconify()
        win.lift()
        try: win.focus_set()
        except Exception: pass

    def on_mouse_move(self, event):
        if event.inaxes == self.ax:
            x, y = event.xdata, event.ydata
            if x is not None and y is not None and 0 <= y <= 100:
                self.cursor_x_var.set(f"Diameter: {x:.6f} mm")
                self.cursor_y_var.set(f"Passing: {y:.2f} %")

    def on_series_change(self, event=None): self.plot_data()
    def on_proj_sample_change(self, event=None): self.project_percentile()

    def project_percentile(self, event=None):
        try:
            pct = float(self.proj_entry.get())
            if 0 <= pct <= 100:
                selected_sample = self.proj_sample_var.get()
                if selected_sample == "Sample 1": series_data = self.data
                else:
                    sample_idx = int(selected_sample.split()[1]) - 2
                    series_data = (self.multiple_series[sample_idx] if 0 <= sample_idx < len(self.multiple_series) else self.data)
                if series_data:
                    use_recovered = getattr(self.app, 'use_recovered_weight', True)
                    calculator = GranuloCalculator(series_data, self.app.initial_weight, use_recovered_weight=use_recovered)
                    diameter = calculator.get_percentile_diameter(pct)
                    if not math.isnan(diameter) and diameter > 0: self.proj_result.config(text=f"→ {fmt_num(diameter, 2, 4)} mm")
                    else: self.proj_result.config(text="→ Outside range")
                else: self.proj_result.config(text="→ No data")
            else: self.proj_result.config(text="→ Invalid (0-100)")
        except ValueError: self.proj_result.config(text="→ Enter number")

    def show_sedimentological(self):
        all_series = []
        if self.data: all_series.append(('Sample 1', self.data))
        for i, series in enumerate(self.multiple_series): all_series.append((f'Sample {i+2}', series))
        if not all_series: messagebox.showwarning("No Data", "No data available"); return
        use_recovered = getattr(self.app, 'use_recovered_weight', True)
        win = tk.Toplevel(self)
        win.title("Sedimentological Parameters - Folk & Ward (1957)")
        win.geometry("720x780"); win.configure(bg='white')
        notebook = ttk.Notebook(win); notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for sample_name, series in all_series:
            calculator = GranuloCalculator(series, self.app.initial_weight, use_recovered_weight=use_recovered)
            params = calculator.get_all_parameters()
            frame = tk.Frame(notebook, bg='white'); notebook.add(frame, text=sample_name)
            text = tk.Text(frame, wrap=tk.WORD, font=('Courier', 10), bg='white', fg='#2c3e50', padx=10, pady=10)
            scrollbar = tk.Scrollbar(frame, command=text.yview); text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y); text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sieve_rows = "\n".join(f"{p:>3.0f}%:  {fmt_num(params.get(f'D{p}', 0), 2, 3):>12} mm    (φ = {fmt_num(params.get(f'phi{p}', 0), 3, 3):>7})" for p in (5, 10, 16, 25, 30, 50, 60, 70, 75, 84, 90, 95))
            pan = calculator.get_pan_summary(); pan_block = ""
            if pan["has_pan"]: pan_block = f"{'─'*60}\nPAN (native):\n{'─'*60}\n  Mass              : {fmt_num(pan['pan_weight_g'], 2, 4)} g\n  % of basis        : {fmt_num(pan['pan_pct_of_basis'], 2, 3)} %\n  Finest sieve (ISO): {fmt_num(pan['finest_sieve_mm'], 2, 4)} mm\n  Passing @ finest  : {fmt_num(pan['finest_sieve_passing_pct'], 2, 3)} %\n"
            report = f"\n{'='*60}\nSEDIMENTOLOGICAL PARAMETERS (Folk & Ward, 1957)\n{'='*60}\n{'─'*60}\nCALCULATION BASIS:\n{'─'*60}\nMethod: {'ASTM D6913 (Recovered Weight)' if use_recovered else 'NF P 94-056 / ISO (Initial Weight)'}\n{'─'*60}\nPERCENTILES:\n{'─'*60}\n{sieve_rows}\n{pan_block}{'─'*60}\nCENTRAL TENDENCY:\n{'─'*60}\nMode:            {fmt_num(params.get('mode_mm', 0), 2, 4)} mm\nModality:        {params.get('modality', 'unknown')}\nGraphic Mean:    {fmt_num(params.get('mean_mm', 0), 2, 4)} mm  (φ = {fmt_num(params.get('mean_phi', 0), 3, 3)})\nMedian:          {fmt_num(params.get('median_mm', 0), 2, 4)} mm  (φ = {fmt_num(params.get('median_phi', 0), 3, 3)})\n{'─'*60}\nSORTING: σI = {fmt_num(params.get('sorting', 0), 3, 3)} → {params.get('sorting_class', 'unknown')}\nSKEWNESS: Sk = {fmt_num(params.get('skewness', 0), 3, 3)} → {params.get('skewness_class', 'unknown')}\nKURTOSIS: KG = {fmt_num(params.get('kurtosis', 0), 3, 3)} → {params.get('kurtosis_class', 'unknown')}\n{'─'*60}\nQUALITY CONTROL:\nInitial: {self.app.initial_weight:.2f}g | Recovered: {calculator.recovered_weight:.2f}g | Recovery: {fmt_num(params.get('recovery_pct', 0), 2, 3)}%\n{'='*60}\n"
            text.insert('1.0', report); text.config(state=tk.DISABLED)

    def show_geotechnical(self):
        all_series = []
        if self.data: all_series.append(('Sample 1', self.data))
        for i, series in enumerate(self.multiple_series): all_series.append((f'Sample {i+2}', series))
        if not all_series: messagebox.showwarning("No Data", "No data available"); return
        use_recovered = getattr(self.app, 'use_recovered_weight', True)
        win = tk.Toplevel(self); win.title("Geotechnical Parameters"); win.geometry("700x700"); win.configure(bg='white')
        notebook = ttk.Notebook(win); notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        for sample_name, series in all_series:
            calculator = GranuloCalculator(series, self.app.initial_weight, use_recovered_weight=use_recovered)
            params = calculator.get_all_parameters()
            frame = tk.Frame(notebook, bg='white'); notebook.add(frame, text=sample_name)
            text = tk.Text(frame, wrap=tk.WORD, font=('Courier', 11), bg='white', fg='#2c3e50', padx=10, pady=10)
            scrollbar = tk.Scrollbar(frame, command=text.yview); text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y); text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            fm_class_full = params.get('FM_class', 'unknown'); fm_main = fm_class_full.split(' — ')[0] if ' — ' in fm_class_full else (fm_class_full.split(' - ')[0] if ' - ' in fm_class_full else fm_class_full)
            report = f"\n{'='*60}\nGEOTECHNICAL PARAMETERS\n{'='*60}\nMethod: {'ASTM D6913' if use_recovered else 'NF P 94-056 / ISO'}\n{'─'*60}\nCu = D60/D10 = {fmt_num(params.get('Cu', 0), 2, 3)} → {params.get('Cu_class', 'unknown')}\nCc = (D30)²/(D10×D60) = {fmt_num(params.get('Cc', 0), 3, 3)} → {params.get('Cc_class', 'unknown')}\nFM = {fmt_num(params.get('FM', 0), 2, 3)} → {fm_main}\n{'─'*60}\nINTERPRETATION:\n• Cu > 6: Well-graded | Cu 4-6: Medium | Cu < 4: Poorly graded\n• 1 < Cc < 3: Well-graded (IDEAL for construction)\n• FM 2.6-2.9: HIGH-QUALITY CONCRETE (PREFERRED)\n{'='*60}\n"
            text.insert('1.0', report); text.config(state=tk.DISABLED)

    # ---------- Dual-basis point helpers (ASTM filled / ISO open) ----------
    def _basis_legend_handles(self):
        """Legend proxies: filled circle = ASTM recovered-weight basis,
        open circle = ISO 17892-4 / NF P94-056 initial-weight basis."""
        from matplotlib.lines import Line2D
        return [
            Line2D([0], [0], marker='o', linestyle='None', markersize=9,
                   markerfacecolor='#7f8c8d', markeredgecolor='black', markeredgewidth=1.0,
                   label='ASTM D6913 (filled = recovered weight)'),
            Line2D([0], [0], marker='o', linestyle='None', markersize=9,
                   markerfacecolor='none', markeredgecolor='#7f8c8d', markeredgewidth=2.0,
                   label='ISO 17892-4 / NF P94-056 (open = initial weight)'),
        ]

    def _dual_basis_params(self, series):
        """(params_astm, params_iso): the same sample computed on both
        calculation bases (recovered weight vs initial weight)."""
        p_astm = GranuloCalculator(series, self.app.initial_weight, use_recovered_weight=True).get_all_parameters()
        p_iso = GranuloCalculator(series, self.app.initial_weight, use_recovered_weight=False).get_all_parameters()
        return p_astm, p_iso

    def _plot_dual_point(self, ax, x_astm, y_astm, x_iso, y_iso, color, unknown=False,
                         label=None, connect=True, s=90, lw=1.8):
        """One sample on a bivariate diagram: filled circle = ASTM basis,
        open circle = ISO/NF basis (same colour); a thin gray link between
        the two circles shows the shift caused by the calculation basis."""
        xa, ya, xi, yi = float(x_astm), float(y_astm), float(x_iso), float(y_iso)
        if unknown:
            ax.scatter(xa, ya, s=s, c='#95a5a6', marker='X', alpha=0.85, edgecolors='black', linewidths=1.0, zorder=6)
            ax.scatter(xi, yi, s=s, marker='X', facecolors='none', edgecolors='#7f8c8d', linewidths=lw, alpha=0.85, zorder=6)
        else:
            ax.scatter(xa, ya, s=s, c=[color], alpha=0.85, edgecolors='black', linewidths=0.8, zorder=6)
            ax.scatter(xi, yi, s=s, facecolors='none', edgecolors=[color], linewidths=lw, alpha=0.95, zorder=6)
        if connect and (abs(xa - xi) > 1e-12 or abs(ya - yi) > 1e-12):
            ax.plot([xa, xi], [ya, yi], color='#95a5a6', linewidth=0.9, alpha=0.55, zorder=4)
        if label:
            ax.annotate(label, (xa, ya), fontsize=8, xytext=(6, 6), textcoords='offset points',
                        color=('gray' if unknown else color), fontweight='bold')
    def show_correlation(self):
        all_series = []
        if self.data: all_series.append(self.data)
        all_series.extend(self.multiple_series)
        if len(all_series) < 2: messagebox.showwarning("Insufficient Data", "Need at least 2 samples"); return
        win = tk.Toplevel(self); win.title("Correlation Analysis"); win.geometry("900x700")
        fig = Figure(figsize=(12, 9), dpi=100); self.last_correlation_fig = fig
        use_recovered = getattr(self.app, 'use_recovered_weight', True)
        dual_params = [self._dual_basis_params(s) for s in all_series]   # [(astm, iso), ...]
        cur = [pa if use_recovered else pi for pa, pi in dual_params]    # current Home basis
        skewness = [p.get('skewness', 0) for p in cur]; kurtosis = [p.get('kurtosis', 0) for p in cur]; sorting = [p.get('sorting', 0) for p in cur]; mean_phi = [p.get('mean_phi', 0) for p in cur]; fm = [p.get('FM', 0) for p in cur]
        sample_cols = [plt.cm.viridis(i / max(len(dual_params) - 1, 1)) for i in range(len(dual_params))]
        ax1 = fig.add_subplot(221)
        for i, (pa, pi) in enumerate(dual_params):
            self._plot_dual_point(ax1, pa.get('skewness', 0), pa.get('kurtosis', 0),
                                  pi.get('skewness', 0), pi.get('kurtosis', 0), sample_cols[i])
        ax1.set_xlabel('Skewness (Sk)'); ax1.set_ylabel('Kurtosis (KG)'); ax1.set_title('Skewness vs Kurtosis'); ax1.grid(True, alpha=0.3)
        ax1.legend(handles=self._basis_legend_handles(), loc='best', fontsize=8)
        ax2 = fig.add_subplot(222)
        for i, (pa, pi) in enumerate(dual_params):
            self._plot_dual_point(ax2, pa.get('mean_phi', 0), pa.get('sorting', 0),
                                  pi.get('mean_phi', 0), pi.get('sorting', 0), sample_cols[i])
        ax2.set_xlabel('Mean Grain Size (φ)'); ax2.set_ylabel('Sorting (σI)'); ax2.set_title('Mean vs Sorting'); ax2.grid(True, alpha=0.3); ax2.invert_xaxis()
        ax2.legend(handles=self._basis_legend_handles(), loc='best', fontsize=8)
        ax3 = fig.add_subplot(223)
        for i, (pa, pi) in enumerate(dual_params):
            self._plot_dual_point(ax3, pa.get('mean_mm', 0), pa.get('FM', 0),
                                  pi.get('mean_mm', 0), pi.get('FM', 0), sample_cols[i])
        ax3.set_xlabel('Mean Grain Size (mm)'); ax3.set_ylabel('Fineness Modulus'); ax3.set_title('Mean vs FM'); ax3.set_xscale('log'); ax3.grid(True, alpha=0.3)
        ax3.legend(handles=self._basis_legend_handles(), loc='best', fontsize=8)
        ax4 = fig.add_subplot(224); param_matrix = np.array([skewness, kurtosis, sorting, mean_phi, fm]); corr_matrix = np.corrcoef(param_matrix)
        im = ax4.imshow(corr_matrix, cmap='RdBu', vmin=-1, vmax=1, aspect='auto'); ax4.set_xticks(range(5)); ax4.set_yticks(range(5)); ax4.set_xticklabels(['Skew', 'Kurt', 'Sort', 'Mean φ', 'FM'], rotation=45, ha='right'); ax4.set_yticklabels(['Skew', 'Kurt', 'Sort', 'Mean φ', 'FM']); ax4.set_title('Correlation Matrix'); fig.colorbar(im, ax=ax4, fraction=0.046, pad=0.04)
        fig.tight_layout(rect=[0, 0.045, 1, 1]); fig.text(0.5, 0.008, 'Filled circle = ASTM D6913 (recovered weight)   |   Open circle = ISO 17892-4 / NF P94-056 (initial weight)', ha='center', fontsize=9, style='italic', color='#555555'); canvas = FigureCanvasTkAgg(fig, win); canvas.draw(); canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True); toolbar = NavigationToolbar2Tk(canvas, win); toolbar.update()

    def show_friedman_plots(self):
        all_series = []
        if self.data: all_series.append(self.data)
        all_series.extend(self.multiple_series)
        if len(all_series) < 1: messagebox.showwarning("No Data", "Need at least 1 sample"); return
        
        valid_series, valid_names, valid_types = [], [], []
        excluded_count = 0
        sample_types = getattr(self.app, 'sample_types', [])
        
        for i, series in enumerate(all_series):
            stype = sample_types[i] if i < len(sample_types) else "Unknown"
            if "Crushed" in stype: 
                excluded_count += 1
            else: 
                valid_series.append(series)
                valid_names.append(f"S{i+1}")
                valid_types.append(stype)
                
        if not valid_series:
            messagebox.showwarning("No Valid Data", "All samples are marked as 'Crushed / Quarry'. Environmental discrimination diagrams are disabled for anthropogenic samples.")
            return

        win = tk.Toplevel(self); win.title("Friedman (1967) Discrimination Diagrams"); win.geometry("1100x900")
        fig = Figure(figsize=(14, 10), dpi=100); fig.suptitle('Friedman (1967) Environmental Discrimination Diagrams', fontsize=14, fontweight='bold', y=0.995)
        use_recovered = getattr(self.app, 'use_recovered_weight', True)
        all_params = []
        
        for series in valid_series: 
            calc = GranuloCalculator(series, self.app.initial_weight, use_recovered_weight=use_recovered)
            all_params.append(self._dual_basis_params(series))
            
        colors = [self.colors[i % len(self.colors)] for i in range(len(all_params))]

        def plot_points(ax, x_key, y_key):
            for i in range(len(all_params)):
                pa, pi = all_params[i]
                unknown = valid_types[i] in ["Unknown", "Natural - Unconfirmed"]
                lbl = f"{valid_names[i]} (?)" if unknown else valid_names[i]
                self._plot_dual_point(ax, pa.get(x_key, 0), pa.get(y_key, 0),
                                      pi.get(x_key, 0), pi.get(y_key, 0),
                                      colors[i], unknown=unknown, label=lbl, s=90)

        ax1 = fig.add_subplot(221); ax1.add_patch(plt.Polygon([(-0.7, 0.6), (-0.5, 0.7), (-0.3, 0.8), (-0.2, 0.9), (-0.1, 1.0), (0.0, 1.1), (-0.1, 1.3), (-0.3, 1.4), (-0.5, 1.5), (-0.7, 1.4), (-0.7, 0.6)], alpha=0.15, color='blue', label='Beach sands'))
        ax1.add_patch(plt.Polygon([(0.05, 0.9), (0.1, 1.0), (0.2, 1.1), (0.3, 1.2), (0.4, 1.4), (0.5, 1.6), (0.6, 1.8), (0.7, 2.0), (0.6, 2.2), (0.4, 2.1), (0.2, 1.9), (0.1, 1.6), (0.05, 1.3), (0.05, 0.9)], alpha=0.15, color='green', label='River sands'))
        plot_points(ax1, 'skewness', 'kurtosis')
        ax1.set_xlabel('Skewness (Sk)', fontsize=11); ax1.set_ylabel('Kurtosis (KG)', fontsize=11); ax1.set_title('① Skewness vs Kurtosis', fontsize=12, fontweight='bold'); ax1.grid(True, alpha=0.3); ax1.set_xlim(-0.7, 0.7); ax1.set_ylim(0.5, 2.5)
        from matplotlib.patches import Patch
        zone_handles = [Patch(facecolor='blue', alpha=0.15, label='Beach sands'), Patch(facecolor='green', alpha=0.15, label='River sands')]
        h1, _ = ax1.get_legend_handles_labels(); ax1.legend(handles=zone_handles + self._basis_legend_handles(), loc='lower right', fontsize=8)

        ax2 = fig.add_subplot(222); ax2.add_patch(plt.Polygon([(-0.7, 0.05), (-0.5, 0.1), (-0.3, 0.15), (-0.2, 0.2), (-0.1, 0.25), (0.0, 0.3), (-0.1, 0.4), (-0.3, 0.5), (-0.5, 0.6), (-0.7, 0.5), (-0.7, 0.05)], alpha=0.15, color='blue'))
        ax2.add_patch(plt.Polygon([(0.05, 0.4), (0.1, 0.5), (0.2, 0.6), (0.3, 0.7), (0.4, 0.9), (0.5, 1.2), (0.6, 1.5), (0.7, 1.8), (0.5, 2.0), (0.3, 1.8), (0.1, 1.4), (0.05, 1.0), (0.05, 0.4)], alpha=0.15, color='green'))
        plot_points(ax2, 'skewness', 'sorting')
        ax2.set_xlabel('Skewness (Sk)', fontsize=11); ax2.set_ylabel('Sorting (σI)', fontsize=11); ax2.set_title('② Skewness vs Sorting', fontsize=12, fontweight='bold'); ax2.grid(True, alpha=0.3); ax2.set_xlim(-0.7, 0.7); ax2.set_ylim(0, 2.5); ax2.legend(handles=zone_handles + self._basis_legend_handles(), loc='upper left', fontsize=8)

        ax3 = fig.add_subplot(223); ax3.add_patch(plt.Polygon([(-0.7, 3.5), (-0.5, 3.2), (-0.3, 2.8), (-0.2, 2.5), (-0.1, 2.2), (0.0, 2.0), (-0.1, 1.8), (-0.3, 1.5), (-0.5, 1.2), (-0.7, 1.0), (-0.7, 3.5)], alpha=0.15, color='blue'))
        ax3.add_patch(plt.Polygon([(0.05, 2.0), (0.1, 1.8), (0.2, 1.5), (0.3, 1.2), (0.4, 1.0), (0.5, 0.8), (0.6, 0.5), (0.7, 0.2), (0.5, -0.2), (0.3, -0.5), (0.1, -0.2), (0.05, 0.5), (0.05, 2.0)], alpha=0.15, color='green'))
        plot_points(ax3, 'skewness', 'mean_phi')
        ax3.set_xlabel('Skewness (Sk)', fontsize=11); ax3.set_ylabel('Mean Grain Size (Mz, φ)', fontsize=11); ax3.set_title('③ Skewness vs Mean Grain Size', fontsize=12, fontweight='bold'); ax3.grid(True, alpha=0.3); ax3.set_xlim(-0.7, 0.7); ax3.set_ylim(3.5, -1.5); ax3.legend(handles=zone_handles + self._basis_legend_handles(), loc='upper right', fontsize=8)

        ax4 = fig.add_subplot(224); ax4.add_patch(plt.Polygon([(3.5, 0.05), (3.0, 0.1), (2.5, 0.15), (2.0, 0.2), (1.5, 0.25), (1.0, 0.3), (0.5, 0.35), (0.0, 0.4), (0.0, 0.05), (0.5, 0.05), (1.0, 0.05), (1.5, 0.05), (2.0, 0.05), (2.5, 0.05), (3.0, 0.05), (3.5, 0.05)], alpha=0.15, color='blue'))
        ax4.add_patch(plt.Polygon([(2.5, 0.4), (2.0, 0.5), (1.5, 0.6), (1.0, 0.7), (0.5, 0.9), (0.0, 1.1), (-0.5, 1.3), (-1.0, 1.5), (-1.5, 1.7), (-1.0, 2.0), (-0.5, 1.8), (0.0, 1.6), (0.5, 1.4), (1.0, 1.2), (1.5, 1.0), (2.0, 0.8), (2.5, 0.6)], alpha=0.15, color='green'))
        plot_points(ax4, 'mean_phi', 'sorting')
        ax4.set_xlabel('Mean Grain Size (Mz, φ)', fontsize=11); ax4.set_ylabel('Sorting (σI)', fontsize=11); ax4.set_title('④ Mean Grain Size vs Sorting', fontsize=12, fontweight='bold'); ax4.grid(True, alpha=0.3); ax4.set_xlim(3.5, -1.5); ax4.set_ylim(0, 2.5); ax4.legend(handles=zone_handles + self._basis_legend_handles(), loc='lower right', fontsize=8)

        fig.tight_layout(rect=[0, 0.04, 1, 0.96]); 
        note_text = "Beach sands: negative skew, better sorting | River sands: positive skew, poorer sorting."
        if excluded_count > 0: note_text += f"\n⚠️ {excluded_count} Crushed/Quarry sample(s) excluded."
        note_text += "\n(Gray 'X' markers indicate samples with Unknown/Unconfirmed provenance)"
        note_text += "\nFilled circle = ASTM D6913 (recovered weight) | Open circle = ISO 17892-4 / NF P94-056 (initial weight)"
        fig.text(0.5, 0.01, note_text, ha='center', fontsize=9, style='italic', bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
        
        canvas = FigureCanvasTkAgg(fig, win); canvas.draw(); canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True); toolbar = NavigationToolbar2Tk(canvas, win); toolbar.update()
        tk.Button(win, text="💾 Export Friedman Diagrams", command=lambda: self._export_friedman(fig), bg='#3498db', fg='white', font=('Arial', 9)).pack(pady=5)

    def _export_friedman(self, fig):
        filename = filedialog.asksaveasfilename(title="Export Friedman Diagrams", defaultextension=".png", filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")])
        if filename:
            try:
                dpi = 300 if filename.endswith('.png') else 150
                fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')
                messagebox.showinfo("Export Successful", f"Saved to:\n{filename}")
            except Exception as e: messagebox.showerror("Export Error", f"Failed: {str(e)}")

    def show_passega_diagram(self):
        all_series = []
        if self.data: all_series.append(self.data)
        all_series.extend(self.multiple_series)
        if len(all_series) < 1: messagebox.showwarning("No Data", "Need at least 1 sample"); return
        
        valid_series, valid_types = [], []
        excluded_count = 0
        sample_types = getattr(self.app, 'sample_types', [])
        
        for i, series in enumerate(all_series):
            stype = sample_types[i] if i < len(sample_types) else "Unknown"
            if "Crushed" in stype: 
                excluded_count += 1
            else: 
                valid_series.append(series)
                valid_types.append(stype)
                
        if not valid_series:
            messagebox.showwarning("No Valid Data", "All samples are marked as 'Crushed / Quarry'. Environmental discrimination diagrams are disabled for anthropogenic samples.")
            return

        win = tk.Toplevel(self); win.title("Passega C-M Diagram (1969) - ASTM vs ISO Comparison"); win.geometry("850x750")
        fig = Figure(figsize=(10, 8), dpi=100); ax = fig.add_subplot(111)
        astm_points, iso_points, astm_names, iso_names, astm_types, iso_types = [], [], [], [], [], []
        
        for i, series in enumerate(valid_series):
            sample_name = f"S{i+1}"
            stype = valid_types[i]
            try:
                calc_astm = GranuloCalculator(series, self.app.initial_weight, use_recovered_weight=True)
                c_astm = calc_astm.get_percentile_diameter(1); m_astm = calc_astm.get_percentile_diameter(50)
                if c_astm > 0 and m_astm > 0 and c_astm < 1000 and m_astm < 1000: 
                    astm_points.append((sample_name, m_astm, c_astm)); astm_names.append(sample_name); astm_types.append(stype)
            except: pass
            try:
                calc_iso = GranuloCalculator(series, self.app.initial_weight, use_recovered_weight=False)
                c_iso = calc_iso.get_percentile_diameter(1); m_iso = calc_iso.get_percentile_diameter(50)
                if c_iso > 0 and m_iso > 0 and c_iso < 1000 and m_iso < 1000: 
                    iso_points.append((sample_name, m_iso, c_iso)); iso_names.append(sample_name); iso_types.append(stype)
            except: pass
            
        if not astm_points and not iso_points: messagebox.showwarning("No Valid Data", "Could not calculate C and M values for any sample"); return
        
        ax.axhline(0.5, color='gray', linestyle='--', alpha=0.5, linewidth=1); ax.fill_between([0.001, 100], 0.001, 0.5, alpha=0.1, color='blue'); ax.text(0.05, 0.2, 'I - Suspension', fontsize=10, ha='center', va='center')
        ax.fill_between([0.001, 100], 0.5, 10, alpha=0.1, color='green'); ax.text(0.05, 2, 'II - Saltation', fontsize=10, ha='center', va='center')
        ax.axhline(10, color='gray', linestyle='--', alpha=0.5, linewidth=1); ax.fill_between([0.001, 100], 10, 1000, alpha=0.1, color='red'); ax.text(0.05, 30, 'III - Rolling', fontsize=10, ha='center', va='center')
        x_ref = np.logspace(-3, 3, 100); (cmline,) = ax.plot(x_ref, x_ref, color='black', linestyle=':', alpha=0.7, linewidth=1.5, label='C = M')
        
        if astm_points:
            for i, (name, m, c) in enumerate(astm_points):
                col = self.colors[i % len(self.colors)]
                if astm_types[i] in ["Unknown", "Natural - Unconfirmed"]: ax.scatter(m, c, s=100, color='gray', marker='X', edgecolors='black', linewidth=1.5, zorder=10)
                else: ax.scatter(m, c, s=120, color=col, edgecolors='black', linewidth=1.2, zorder=10)
                ax.annotate(f'{name} (A)', (m, c), xytext=(5, 5), textcoords='offset points', fontsize=8, color=col, fontweight='bold')
        if iso_points:
            for i, (name, m, c) in enumerate(iso_points):
                col = self.colors[i % len(self.colors)]
                if iso_types[i] in ["Unknown", "Natural - Unconfirmed"]: ax.scatter(m, c, s=100, color='gray', marker='X', facecolors='none', edgecolors='#7f8c8d', linewidth=1.5, zorder=10)
                else: ax.scatter(m, c, s=120, facecolors='none', edgecolors=col, linewidth=2.0, zorder=10)
                ax.annotate(f'{name} (I)', (m, c), xytext=(5, -15), textcoords='offset points', fontsize=8, color=col, fontweight='bold')
            
        common_names = set(astm_names) & set(iso_names)
        for name in common_names:
            astm_idx = astm_names.index(name); iso_idx = iso_names.index(name)
            m_astm, c_astm = astm_points[astm_idx][1], astm_points[astm_idx][2]; m_iso, c_iso = iso_points[iso_idx][1], iso_points[iso_idx][2]
            ax.annotate('', xy=(m_iso, c_iso), xytext=(m_astm, c_astm), arrowprops=dict(arrowstyle='->', color='gray', lw=1.5, alpha=0.7, connectionstyle='arc3,rad=0.1'), zorder=5)
            
        ax.set_xlim(0.01, 100); ax.set_ylim(0.001, 100); ax.set_xscale('log'); ax.set_yscale('log')
        ax.set_xlabel('M - Median (D50, mm)', fontsize=12, fontweight='bold'); ax.set_ylabel('C - Coarsest Percentile (mm)', fontsize=12, fontweight='bold')
        ax.set_title('Passega C-M Diagram (Passega & Byramjee, 1969)\nASTM D6913 vs ISO 17892-4 Comparison', fontsize=14, fontweight='bold')
        ax.grid(True, which='both', linestyle=':', alpha=0.3); ax.legend(handles=[cmline] + self._basis_legend_handles(), loc='upper left', fontsize=9)
        
        note_text = ""
        if excluded_count > 0: note_text += f'⚠️ {excluded_count} Crushed/Quarry sample(s) excluded. '
        note_text += "(Gray 'X' = Unknown/Unconfirmed provenance)"
        note_text += "\nFilled circle = ASTM D6913 (recovered weight) | Open circle = ISO 17892-4 / NF P94-056 (initial weight)"
        if note_text: fig.text(0.5, 0.008, note_text, ha='center', va='bottom', fontsize=9, style='italic', color='red')
            
        fig.tight_layout(rect=[0, 0.09, 1, 1]); canvas = FigureCanvasTkAgg(fig, win); canvas.draw(); canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True); toolbar = NavigationToolbar2Tk(canvas, win); toolbar.update()


    # ═════════════════════════════════════════════════════════════════════
    # Ternary classification diagrams — Folk (1954) & Shepard (1954)
    # (ported from Ternary_diagrams.py; fractions from GranuloCalculator.get_size_fractions)
    # ═════════════════════════════════════════════════════════════════════

    def _ternary_xy(self, top, left, right):
        """Barycentric (top, left, right) percentages → Cartesian coordinates."""
        total = top + left + right
        if total <= 0:
            return float("nan"), float("nan")
        t, l, r = top / total, left / total, right / total
        return 0.5 * (2.0 * r + t), (np.sqrt(3) / 2.0) * t

    def _ternary_base(self, ax, top_label, left_label, right_label, title, grid_step=10):
        """Equilateral triangle frame, ticks and internal gridlines."""
        h = np.sqrt(3) / 2.0
        ax.add_patch(plt.Polygon([[0, 0], [1, 0], [0.5, h]], closed=True, fill=False,
                                 edgecolor="black", linewidth=1.5, zorder=5))
        for pct in range(grid_step, 100, grid_step):
            x1, y1 = self._ternary_xy(pct, 100 - pct, 0); x2, y2 = self._ternary_xy(pct, 0, 100 - pct)
            ax.plot([x1, x2], [y1, y2], color="lightgray", linestyle="--", linewidth=0.6, zorder=1)
            x1, y1 = self._ternary_xy(100 - pct, pct, 0); x2, y2 = self._ternary_xy(0, pct, 100 - pct)
            ax.plot([x1, x2], [y1, y2], color="lightgray", linestyle="--", linewidth=0.6, zorder=1)
            x1, y1 = self._ternary_xy(100 - pct, 0, pct); x2, y2 = self._ternary_xy(0, 100 - pct, pct)
            ax.plot([x1, x2], [y1, y2], color="lightgray", linestyle="--", linewidth=0.6, zorder=1)
        ax.text(0.5, h + 0.04, top_label, ha="center", va="bottom", fontsize=11, fontweight="bold")
        ax.text(-0.03, -0.03, left_label, ha="right", va="top", fontsize=11, fontweight="bold")
        ax.text(1.03, -0.03, right_label, ha="left", va="top", fontsize=11, fontweight="bold")
        ax.set_title(title, fontsize=12, fontweight="bold", pad=22)
        ax.set_xlim(-0.15, 1.15); ax.set_ylim(-0.12, h + 0.14)
        ax.set_aspect("equal"); ax.axis("off")

    def _ternary_folk_boundaries(self, ax):
        """Folk (1954) Gravel-Sand-Mud classification lines and field labels."""
        for g in (80, 30, 5, 1):
            x1, y1 = self._ternary_xy(g, 100 - g, 0); x2, y2 = self._ternary_xy(g, 0, 100 - g)
            ax.plot([x1, x2], [y1, y2], color="dimgray", linewidth=1.0, zorder=3)
        for sand_ratio in (90, 50, 10):
            mud_ratio = 100 - sand_ratio
            x_top, y_top = self._ternary_xy(80, 0.2 * sand_ratio, 0.2 * mud_ratio)
            x_bot, y_bot = self._ternary_xy(0, sand_ratio, mud_ratio)
            ax.plot([x_top, x_bot], [y_top, y_bot], color="dimgray", linewidth=1.0, zorder=3)
        fields = [
            (88, 6, 6, "G"), (50, 42, 8, "sG"), (50, 25, 25, "msG"), (50, 8, 42, "mG"),
            (15, 78, 7, "gS"), (15, 42.5, 42.5, "gmS"), (15, 7, 78, "gM"),
            (2.5, 92, 5.5, "(g)S"), (2.5, 48.75, 48.75, "(g)mS"), (2.5, 5.5, 92, "(g)M"),
        ]
        for g, s, m, code in fields:
            fx, fy = self._ternary_xy(g, s, m)
            ax.text(fx, fy, code, ha="center", va="center", fontsize=8,
                    color="darkslategray", zorder=4)

    def _ternary_shepard_boundaries(self, ax):
        """Shepard (1954) Sand-Silt-Clay classification lines and field labels."""
        shepard_lines = [((75, 25, 0), (75, 0, 25)), ((25, 75, 0), (0, 75, 25)),
                         ((25, 0, 75), (0, 25, 75)),
                         ((50, 50, 0), (40, 40, 20)), ((50, 0, 50), (40, 20, 40)),
                         ((0, 50, 50), (20, 40, 40))]
        for p1, p2 in shepard_lines:
            ax.plot(*zip(self._ternary_xy(*p1), self._ternary_xy(*p2)),
                    color="dimgray", linewidth=1.0, zorder=3)
        c_pts = [self._ternary_xy(60, 20, 20), self._ternary_xy(20, 60, 20),
                 self._ternary_xy(20, 20, 60), self._ternary_xy(60, 20, 20)]
        ax.plot([p[0] for p in c_pts], [p[1] for p in c_pts],
                color="dimgray", linewidth=1.0, zorder=3)
        fields = [
            (85, 7.5, 7.5, "Sand"), (7.5, 85, 7.5, "Silt"), (7.5, 7.5, 85, "Clay"),
            (55, 35, 10, "Silty\nSand"), (55, 10, 35, "Clayey\nSand"), (35, 55, 10, "Sandy\nSilt"),
            (10, 55, 35, "Clayey\nSilt"), (35, 10, 55, "Sandy\nClay"), (10, 35, 55, "Silty\nClay"),
            (33.3, 33.3, 33.3, "Sand-Silt-\nClay"),
        ]
        for s, si, c, label in fields:
            fx, fy = self._ternary_xy(s, si, c)
            ax.text(fx, fy, label, ha="center", va="center", fontsize=7.5,
                    color="darkslategray", zorder=4)

    def _build_ternary_figure(self):
        """Build the Folk (1954) + Shepard (1954) ternary figure, or None."""
        all_series = []
        if self.data: all_series.append(('Sample 1', self.data))
        for i, series in enumerate(self.multiple_series): all_series.append((f'Sample {i+2}', series))
        if not all_series:
            messagebox.showwarning("No Data", "No data available"); return None
        use_recovered = getattr(self.app, 'use_recovered_weight', True)
        sample_types = getattr(self.app, 'sample_types', [])
        fig = Figure(figsize=(14, 6.5), dpi=100)
        ax1 = fig.add_subplot(121); ax2 = fig.add_subplot(122)
        self._ternary_base(ax1, "GRAVEL (%)", "SAND (%)", "MUD (%)",
                           "Folk (1954) Gravel–Sand–Mud Diagram")
        self._ternary_folk_boundaries(ax1)
        self._ternary_base(ax2, "SAND (%)", "SILT (%)", "CLAY (%)",
                           "Shepard (1954) Sand–Silt–Clay Diagram")
        self._ternary_shepard_boundaries(ax2)
        plotted = 0
        for i, (sample_name, series) in enumerate(all_series):
            try:
                calc = GranuloCalculator(series, self.app.initial_weight,
                                         use_recovered_weight=use_recovered)
                fr = calc.get_size_fractions()
            except Exception as e:
                print(f"Ternary: cannot compute fractions for {sample_name}: {e}"); continue
            name = f"S{i+1}"
            stype = sample_types[i] if i < len(sample_types) else "Unknown"
            unknown = stype in ["Unknown", "Natural - Unconfirmed"]
            color = "gray" if unknown else self.colors[i % len(self.colors)]
            marker = "X" if unknown else "o"
            mud = fr["silt"] + fr["clay"]
            x, y = self._ternary_xy(fr["gravel"], fr["sand"], mud)
            if math.isfinite(x):
                ax1.scatter(x, y, s=60, color=color, marker=marker,
                            edgecolors="black", linewidth=0.8, zorder=10)
                ax1.annotate(name, (x, y), xytext=(6, 5), textcoords="offset points",
                             fontsize=8, fontweight="bold")
            ssc_total = fr["sand"] + fr["silt"] + fr["clay"]
            if ssc_total > 0:
                x, y = self._ternary_xy(fr["sand"], fr["silt"], fr["clay"])
                if math.isfinite(x):
                    ax2.scatter(x, y, s=60, color=color, marker=marker,
                                edgecolors="black", linewidth=0.8, zorder=10)
                    ax2.annotate(name, (x, y), xytext=(6, 5), textcoords="offset points",
                                 fontsize=8, fontweight="bold")
            plotted += 1
        if plotted == 0:
            messagebox.showwarning("No Valid Data", "Could not compute size fractions for any sample")
            return None
        fig.tight_layout(rect=[0, 0.04, 1, 1])
        fig.text(0.5, 0.005,
                 "Fractions integrated from the PCHIP curve — gravel > 2 mm | sand 0.0625–2 mm | "
                 "silt 0.004–0.0625 mm | clay < 0.004 mm. Shepard renormalizes Sand-Silt-Clay to 100 % "
                 "(gravel excluded). Gray 'X' = Unknown/Unconfirmed provenance.",
                 ha="center", fontsize=8, style="italic", color="#555555")
        return fig

    def show_ternary_diagrams(self):
        """Display the Folk (1954) and Shepard (1954) ternary diagrams."""
        fig = self._build_ternary_figure()
        if fig is None: return
        win = tk.Toplevel(self)
        win.title("Ternary Classification Diagrams - Folk (1954) / Shepard (1954)")
        win.geometry("1250x680")
        canvas = FigureCanvasTkAgg(fig, win); canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, win); toolbar.update()
        tk.Button(win, text="💾 Export Ternary Diagrams", bg='#c0392b', fg='white',
                  font=('Arial', 9),
                  command=lambda: self._export_figure_dialog(fig, "Ternary Diagrams")).pack(pady=5)

    def export_ternary_diagrams(self):
        """Save the ternary diagrams as PNG (300 dpi) or PDF."""
        fig = self._build_ternary_figure()
        if fig is None: return
        self._export_figure_dialog(fig, "Ternary Diagrams")

    def _export_figure_dialog(self, fig, title):
        filename = filedialog.asksaveasfilename(title=f"Export {title}",
            defaultextension=".png", filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")])
        if filename:
            try:
                dpi = 300 if filename.endswith('.png') else 150
                fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')
                messagebox.showinfo("Export Successful", f"Saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed: {str(e)}")


    # ═════════════════════════════════════════════════════════════════════
    # Grain-size distribution graphs — GRADISTAT-style Class Weight (%)
    # φ linear scale + metric (μm) logarithmic scale, all samples overlaid
    # ═════════════════════════════════════════════════════════════════════

    def _sample_class_weights(self, series, use_recovered):
        """Per-sieve class weights (% of active basis) for one sample.
        Pan is anchored half a log-decade below the finest sieve (same
        convention as the PCHIP engine). Returns (diameters_mm coarse→fine,
        class_pct) or None."""
        try:
            calc = GranuloCalculator(series, self.app.initial_weight,
                                     use_recovered_weight=use_recovered)
        except Exception as e:
            print(f"Distribution: cannot compute sample ({e})"); return None
        agg: Dict[float, float] = {}
        for d, w in calc.data:
            agg[d] = agg.get(d, 0.0) + w
        basis = calc.recovered_weight if use_recovered else calc.initial_weight
        diam = sorted(agg.keys(), reverse=True)            # coarse → fine
        pct = [agg[d] * 100.0 / basis for d in diam]
        if calc.has_pan and calc.pan_weight > 0:
            diam = diam + [diam[-1] / math.sqrt(10.0)]     # ½ log-decade anchor
            pct = pct + [calc.pan_weight * 100.0 / basis]
        if len(diam) < 2 or sum(pct) <= 0:
            return None
        return diam, pct

    def _build_distribution_figure(self):
        """GRADISTAT-style distributions: φ (linear) + μm (log) class weights."""
        from scipy.interpolate import PchipInterpolator
        import matplotlib.ticker as ticker
        all_series = []
        if self.data: all_series.append(('Sample 1', self.data))
        for i, series in enumerate(self.multiple_series): all_series.append((f'Sample {i+2}', series))
        if not all_series:
            messagebox.showwarning("No Data", "No data available"); return None
        use_recovered = getattr(self.app, 'use_recovered_weight', True)
        curves = []; gmax = 0.0
        for i, (sample_name, series) in enumerate(all_series):
            res = self._sample_class_weights(series, use_recovered)
            if res is None:
                print(f"Distribution: skipped {sample_name}"); continue
            diam, pct = res
            gmax = max(gmax, max(pct))
            curves.append((sample_name, self.colors[i % len(self.colors)], diam, pct))
        if not curves:
            messagebox.showwarning("No Valid Data",
                                   "Could not compute class weights for any sample")
            return None
        fig = Figure(figsize=(14, 6.0), dpi=100)
        ax1 = fig.add_subplot(121); ax2 = fig.add_subplot(122)
        fig.suptitle("Grain Size Distribution — Class Weight (%)",
                     fontsize=13, fontweight="bold")
        many = len(curves) > 6
        for sample_name, color, diam, pct in curves:
            phi = [-math.log2(d) for d in diam]            # coarse → fine
            mic = [d * 1000.0 for d in diam]               # mm → μm
            # GRAPH 1 — φ linear scale (coarse left → fine right)
            try:
                phi_s = np.linspace(min(phi), max(phi), 300)
                w_s = np.clip(PchipInterpolator(phi, pct)(phi_s), 0, None)
                ax1.plot(phi_s, w_s, "-", color=color, linewidth=2.0,
                         alpha=0.9, label=sample_name)
            except Exception:
                pass
            ax1.plot(phi, pct, "o", color=color, markersize=4,
                     markeredgecolor="black", markeredgewidth=0.5, zorder=6)
            # GRAPH 2 — μm logarithmic scale (fine left → coarse right)
            try:
                order = np.argsort(mic)            # ascending for PCHIP
                mic_a = np.asarray(mic)[order]
                pct_a = np.asarray(pct)[order]
                ld = np.log10(mic_a)
                lds = np.linspace(ld.min(), ld.max(), 300)
                wm = np.clip(PchipInterpolator(ld, pct_a)(lds), 0, None)
                ax2.plot(10.0 ** lds, wm, "-", color=color, linewidth=2.0,
                         alpha=0.9, label=sample_name)
            except Exception:
                pass
            ax2.plot(mic, pct, "o", color=color, markersize=4,
                     markeredgecolor="black", markeredgewidth=0.5, zorder=6)
        # ── GRAPH 1 styling ──
        ax1.set_xlabel("Particle diameter (φ)", fontsize=11, fontweight="bold")
        ax1.set_ylabel("Class weight (%)", fontsize=11, fontweight="bold")
        ax1.set_title("Logarithmic (φ) Scale Distribution", fontsize=11)
        ax1.set_ylim(0, gmax * 1.15)
        ax1.grid(True, which="major", linestyle="-", color="gray", alpha=0.4)
        if ax1.get_legend_handles_labels()[0]:
            ax1.legend(frameon=True, fontsize=7 if many else 9,
                       ncol=2 if many else 1)
        # ── GRAPH 2 styling ──
        ax2.set_xscale("log")
        ax2.xaxis.set_major_formatter(ticker.ScalarFormatter())
        ax2.xaxis.set_minor_formatter(ticker.NullFormatter())
        ax2.set_xlabel("Particle diameter (μm)", fontsize=11, fontweight="bold")
        ax2.set_ylabel("Class weight (%)", fontsize=11, fontweight="bold")
        ax2.set_title("Metric (μm) Log-Scale Distribution", fontsize=11)
        ax2.set_ylim(0, gmax * 1.15)
        ax2.grid(True, which="major", linestyle="-", color="gray", alpha=0.5)
        ax2.grid(True, which="minor", linestyle="-", color="lightgray", alpha=0.5)
        if ax2.get_legend_handles_labels()[0]:
            ax2.legend(frameon=True, fontsize=7 if many else 9,
                       ncol=2 if many else 1)
        basis_txt = ("ASTM D6913 — Recovered Weight" if use_recovered
                     else "NF P 94-056 / ISO 17892-4 — Initial Weight")
        fig.tight_layout(rect=[0, 0.045, 1, 0.93])
        fig.text(0.5, 0.006,
                 "Class weight = partial mass retained per sieve (% of active basis). "
                 "Pan anchored ½ log-decade below the finest sieve. 1 mm = 1000 μm. "
                 f"Basis: {basis_txt}.",
                 ha="center", fontsize=8, style="italic", color="#555555")
        return fig

    def show_distribution(self):
        """Display the GRADISTAT-style distribution graphs (φ / μm)."""
        fig = self._build_distribution_figure()
        if fig is None: return
        win = tk.Toplevel(self)
        win.title("Grain Size Distribution - φ linear / μm logarithmic")
        win.geometry("1350x650")
        canvas = FigureCanvasTkAgg(fig, win); canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, win); toolbar.update()
        tk.Button(win, text="💾 Export Distribution Graphs", bg='#2980b9', fg='white',
                  font=('Arial', 9),
                  command=lambda: self._export_figure_dialog(fig, "Distribution Graphs")).pack(pady=5)

    def export_distribution_graphs(self):
        """Save the distribution graphs (PNG 300 dpi or PDF)."""
        fig = self._build_distribution_figure()
        if fig is None: return
        self._export_figure_dialog(fig, "Distribution Graphs")

    # ═════════════════════════════════════════════════════════════════════
    # Bland-Altman dual-basis comparison — sits alongside the Friedman and
    # Passega C-M diagrams. Difference (ISO - ASTM) vs mean of both bases,
    # for D50 and Folk-Ward sorting σI; mean bias, ±1.96 SD limits of
    # agreement and the zero line are drawn; points are colour-coded by
    # recovery loss 100·(M0 - Mr)/M0 (<2% blue, 2-5% orange, >5% red).
    # ═════════════════════════════════════════════════════════════════════
    def _collect_bland_altman_records(self):
        """One dual-basis record per sample for the Bland-Altman panels:
        recovery loss (%), D50 (φ) and Folk-Ward inclusive graphic sorting
        σI (φ) under both calculation bases (ASTM D6913 recovered weight
        vs ISO 17892-4 / NF P94-056 initial weight)."""
        all_series = []
        if self.data: all_series.append(self.data)
        all_series.extend(self.multiple_series)
        records = []
        for i, series in enumerate(all_series):
            name = f'S{i+1}'
            try:
                p_astm = GranuloCalculator(series, self.app.initial_weight,
                                           use_recovered_weight=True).get_all_parameters()
                p_iso = GranuloCalculator(series, self.app.initial_weight,
                                          use_recovered_weight=False).get_all_parameters()
            except Exception as e:
                print(f"Bland-Altman: cannot compute {name} ({e})"); continue
            records.append({
                'name': name,
                'recovery_loss_pct': max(0.0, 100.0 - float(p_astm.get('recovery_pct', 0.0))),
                'd50_astm_phi': float(p_astm.get('median_phi', 0.0)),
                'd50_iso_phi': float(p_iso.get('median_phi', 0.0)),
                'sort_astm_phi': float(p_astm.get('sorting', 0.0)),
                'sort_iso_phi': float(p_iso.get('sorting', 0.0)),
            })
        return records

    def _render_bland_altman_plot(self, fig, samples_dual_data, label_threshold_bias=True):
        """Two-panel Bland-Altman comparison (ISO vs ASTM):
        a) D50 (median grain size), b) inclusive graphic standard deviation σI.
        Reference lines: zero difference, mean bias and ±1.96 SD limits of
        agreement; points coloured by recovery loss tier
        (<2% blue, 2-5% orange, >5% red)."""
        import matplotlib.patches as mpatches
        fig.clear()
        axes = fig.subplots(2, 1)

        names = [s['name'] for s in samples_dual_data]
        losses = np.array([s['recovery_loss_pct'] for s in samples_dual_data], dtype=float)
        d50_astm = np.array([s['d50_astm_phi'] for s in samples_dual_data], dtype=float)
        d50_iso = np.array([s['d50_iso_phi'] for s in samples_dual_data], dtype=float)
        sort_astm = np.array([s['sort_astm_phi'] for s in samples_dual_data], dtype=float)
        sort_iso = np.array([s['sort_iso_phi'] for s in samples_dual_data], dtype=float)

        colors = []
        for loss in losses:
            if loss < 2.0: colors.append('#1a33ff')        # Recovery Loss < 2 %
            elif loss <= 5.0: colors.append('#ff9900')     # Recovery Loss 2-5 %
            else: colors.append('#ee1111')                 # Recovery Loss > 5 %

        panels = [
            {'ax': axes[0],
             'x': (d50_astm + d50_iso) / 2.0, 'y': d50_iso - d50_astm,
             'title': 'a) Bland-Altman: D50 (Median Grain Size)',
             'xlabel': 'Average D50 (ASTM + ISO) / 2  [φ units]',
             'ylabel': 'Difference (ISO - ASTM)  [φ units]'},
            {'ax': axes[1],
             'x': (sort_astm + sort_iso) / 2.0, 'y': sort_iso - sort_astm,
             'title': 'b) Bland-Altman: Inclusive Graphic Standard Deviation (σI)',
             'xlabel': 'Average Sorting (ASTM + ISO) / 2  [φ units]',
             'ylabel': 'Difference (ISO - ASTM)  [φ units]'},
        ]

        for panel in panels:
            ax = panel['ax']; x = panel['x']; y = panel['y']

            # Bland-Altman exact statistics
            bias = float(np.mean(y))
            sd = float(np.std(y, ddof=1)) if len(y) > 1 else 0.0
            upper_loa = bias + 1.96 * sd
            lower_loa = bias - 1.96 * sd

            # 1. Zero difference line (ideal agreement)
            ax.axhline(0.0, color='#d62728', linestyle=':', linewidth=1.3, zorder=2)
            # 2. Mean bias line
            ax.axhline(bias, color='black', linestyle='-', linewidth=1.4, zorder=3)
            # 3. Upper & Lower 95% Limits of Agreement (±1.96 SD)
            ax.axhline(upper_loa, color='gray', linestyle='--', linewidth=1.2, zorder=2)
            ax.axhline(lower_loa, color='gray', linestyle='--', linewidth=1.2, zorder=2)

            ax.scatter(x, y, c=colors, s=75, edgecolors='black', linewidths=0.8, zorder=4)

            # Annotate samples with the largest magnitude differences
            # (sign-safe: abs(y) > abs(bias) works for + or - bias)
            for i, txt in enumerate(names):
                if not label_threshold_bias or abs(y[i]) > abs(bias):
                    ax.annotate(txt, (x[i], y[i]), xytext=(5, 4), textcoords='offset points',
                                fontsize=8.5, color='#111111', zorder=5)

            # Limits with padding: the y range always includes the zero
            # line; the x range is stretched right to host the line tags
            y_min = min(y.min(), lower_loa, 0.0)
            y_max = max(y.max(), upper_loa, 0.0)
            y_margin = (y_max - y_min) * 0.12 if y_max > y_min else 0.05
            ax.set_ylim(y_min - y_margin, y_max + y_margin)

            x_min, x_max = x.min(), x.max()
            x_span = x_max - x_min if x_max > x_min else 1.0
            ax.set_xlim(x_min - 0.06 * x_span, x_max + 0.18 * x_span)

            # Direct right-edge labels for the 4 horizontal reference lines
            x_label_pos = x_max + 0.03 * x_span
            line_tags = [
                (0.0, 'Zero (0)', '#d62728'),
                (bias, f'Bias ({bias:+.3f})', 'black'),
                (upper_loa, f'+1.96 SD ({upper_loa:+.3f})', 'dimgray'),
                (lower_loa, f'-1.96 SD ({lower_loa:+.3f})', 'dimgray'),
            ]
            # Nudge the tags apart when the four lines run close together
            # (near-zero bias or small SD) so they never overlap; the
            # lines themselves and the printed values stay untouched
            ylo, yhi = ax.get_ylim()
            min_gap = (yhi - ylo) * 0.045
            order = sorted(range(len(line_tags)), key=lambda k: line_tags[k][0])
            disp = [line_tags[k][0] for k in order]
            for a in range(1, len(disp)):
                if disp[a] - disp[a - 1] < min_gap:
                    disp[a] = disp[a - 1] + min_gap
            over = disp[-1] - yhi
            if over > 0:
                disp = [d - over for d in disp]
                for a in range(len(disp) - 2, -1, -1):
                    if disp[a + 1] - disp[a] < min_gap:
                        disp[a] = disp[a + 1] - min_gap
            pos = [0.0] * len(line_tags)
            for rank, k in enumerate(order):
                pos[k] = disp[rank]
            for (_y_val, label_txt, col), y_disp in zip(line_tags, pos):
                ax.text(x_label_pos, y_disp, label_txt, va='center', ha='left',
                        fontsize=7.5, color=col, fontweight='bold', zorder=3)

            ax.set_title(panel['title'], fontsize=11, pad=8)
            ax.set_xlabel(panel['xlabel'], fontsize=9.5)
            ax.set_ylabel(panel['ylabel'], fontsize=9.5)
            ax.minorticks_on()
            ax.tick_params(axis='both', which='both', direction='in', top=True, right=True)
            ax.grid(True, which='major', linestyle=':', color='lightgray', alpha=0.8)

        legend_handles = [
            mpatches.Patch(color='#1a33ff', label='Recovery Loss <2%'),
            mpatches.Patch(color='#ff9900', label='Recovery Loss 2-5%'),
            mpatches.Patch(color='#ee1111', label='Recovery Loss >5%'),
        ]
        axes[1].legend(handles=legend_handles, loc='lower right', frameon=True,
                       facecolor='white', edgecolor='gray', fontsize=8.5)

        fig.suptitle('Bland-Altman Dual-Basis Comparison — ISO 17892-4 / NF P94-056 vs ASTM D6913',
                     fontsize=13, fontweight='bold', y=0.985)
        fig.tight_layout(rect=[0, 0.05, 1, 0.945])
        fig.text(0.5, 0.008,
                 'Difference = ISO (initial weight) - ASTM (recovered weight). '
                 'Colour = recovery loss 100 × (M0 - Mr) / M0. '
                 'A point close to the zero line means both bases agree for that sample.',
                 ha='center', fontsize=8.5, style='italic', color='#555555')

    def show_bland_altman(self):
        """Open the Bland-Altman dual-basis comparison (ISO vs ASTM) in a
        separate window, alongside the Friedman / Passega C-M diagrams."""
        records = self._collect_bland_altman_records()
        if len(records) < 2:
            messagebox.showwarning(
                'Insufficient Samples',
                'Load at least 2 samples with a valid Initial Dry Mass (M0) to '
                'generate a Bland-Altman comparison.')
            return
        fig = Figure(figsize=(10.5, 9.0), dpi=100)
        self._render_bland_altman_plot(fig, records)
        win = tk.Toplevel(self)
        win.title('Bland-Altman Dual-Basis Comparison - ISO vs ASTM')
        win.geometry('1100x950')
        canvas = FigureCanvasTkAgg(fig, win); canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, win); toolbar.update()
        tk.Button(win, text='💾 Export Bland-Altman Plot', bg='#16a085', fg='white',
                  font=('Arial', 9),
                  command=lambda: self._export_figure_dialog(fig, 'Bland-Altman Plot')).pack(pady=5)

    def export_bland_altman(self):
        """Save the Bland-Altman comparison (PNG 300 dpi or PDF)."""
        records = self._collect_bland_altman_records()
        if len(records) < 2:
            messagebox.showwarning(
                'Insufficient Samples',
                'Load at least 2 samples with a valid Initial Dry Mass (M0).')
            return
        fig = Figure(figsize=(10.5, 9.0), dpi=100)
        self._render_bland_altman_plot(fig, records)
        self._export_figure_dialog(fig, 'Bland-Altman Plot')



    def export_all_parameters(self):
        all_series = []
        if self.data: all_series.append(('Sample 1', self.data))
        for i, series in enumerate(self.multiple_series): all_series.append((f'Sample {i+2}', series))
        if not all_series: messagebox.showwarning("No Data", "No data to export"); return
        
        filename = filedialog.asksaveasfilename(
            title="Export All Parameters", defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("Text files", "*.txt")])
        if not filename: return
        
        try:
            use_recovered = getattr(self.app, 'use_recovered_weight', True)
            sample_types = getattr(self.app, 'sample_types', [])
            data_rows = []
            
            for i, (sample_name, series) in enumerate(all_series):
                calculator = GranuloCalculator(series, self.app.initial_weight, use_recovered_weight=use_recovered)
                params = calculator.get_all_parameters()
                stype = sample_types[i] if i < len(sample_types) else "Unknown"
                
                # 1. User Attribution
                data_rows.append([sample_name, 'Declared Sample Type (User)', stype, 'User Input'])
                data_rows.append([sample_name, 'Calculation Basis', 'ASTM' if use_recovered else 'NF/ISO', ''])
                
                # 2. Software Environmental Interpretation
                if "Crushed" in stype:
                    f_env, p_env = "N/A (Crushed aggregate)", "N/A (Crushed aggregate)"
                elif stype in ["Unknown", "Natural - Unconfirmed"]:
                    f_env, p_env = "N/A (Unconfirmed provenance)", "N/A (Unconfirmed provenance)"
                else:
                    # Friedman suggestion
                    skew = params.get('skewness', 0)
                    if skew < -0.1: f_env = "Beach / Coastal (Negative Skew)"
                    elif skew > 0.1: f_env = "Fluvial (River) (Positive Skew)"
                    else: f_env = "Near Symmetrical / Ambiguous"
                    
                    # Passega suggestion (C = D99)
                    c_val = calculator.get_percentile_diameter(99)
                    if c_val < 0.5: p_env = "I - Suspension"
                    elif c_val <= 10.0: p_env = "II - Saltation"
                    else: p_env = "III - Rolling"
                
                data_rows.append([sample_name, "Suggested Environment (Friedman)", f_env, "Software Calculated"])
                data_rows.append([sample_name, "Suggested Mechanism (Passega)", p_env, "Software Calculated"])
                
                # 3. Standard Parameters
                for p in (5, 10, 16, 25, 30, 50, 60, 70, 75, 84, 90, 95):
                    data_rows.append([sample_name, f"D{p} (mm)", fmt_num(params.get(f"D{p}", 0), 2, 4), ""])
                    data_rows.append([sample_name, f"phi{p} (φ)", fmt_num(params.get(f"phi{p}", 0), 3, 4), ""])
                    
                data_rows.append([sample_name, "Mode (mm)", fmt_num(params.get("mode_mm", 0), 2, 4), ""])
                data_rows.append([sample_name, "Mean (mm)", fmt_num(params.get("mean_mm", 0), 2, 4), ""])
                data_rows.append([sample_name, "Mz (φ)", fmt_num(params.get("mean_phi", 0), 3, 4), ""])
                data_rows.append([sample_name, "Median (mm)", fmt_num(params.get("median_mm", 0), 2, 4), ""])
                data_rows.append([sample_name, "Median (φ)", fmt_num(params.get("median_phi", 0), 3, 4), ""])
                
                data_rows.append([sample_name, "Sorting (σI)", fmt_num(params.get("sorting", 0), 3, 3), params.get("sorting_class", "")])
                data_rows.append([sample_name, "Skewness", fmt_num(params.get("skewness", 0), 3, 3), params.get("skewness_class", "")])
                data_rows.append([sample_name, "Kurtosis", fmt_num(params.get("kurtosis", 0), 3, 3), params.get("kurtosis_class", "")])
                data_rows.append([sample_name, "Cu", fmt_num(params.get("Cu", 0), 2, 3), params.get("Cu_class", "")])
                data_rows.append([sample_name, "Cc", fmt_num(params.get("Cc", 0), 3, 3), params.get("Cc_class", "")])
                data_rows.append([sample_name, "FM", fmt_num(params.get("FM", 0), 2, 3), params.get("FM_class", "")])

                # 4. Dual-standard size fractions (ISO 14688-1:2017 / ASTM D2487)
                data_rows.append([sample_name, "ISO 14688-1 Fractions (%)", "", ""])
                data_rows.append([sample_name, "  ISO Clay (< 0.002 mm)", fmt_num(params.get("ISO_Clay_%", 0), 2, 2), ""])
                data_rows.append([sample_name, "  ISO Silt (0.002 - 0.063 mm)", fmt_num(params.get("ISO_Silt_%", 0), 2, 2), ""])
                data_rows.append([sample_name, "  ISO Sand (0.063 - 2 mm)", fmt_num(params.get("ISO_Sand_%", 0), 2, 2), ""])
                data_rows.append([sample_name, "  ISO Gravel (2 - 63 mm)", fmt_num(params.get("ISO_Gravel_%", 0), 2, 2), ""])
                data_rows.append([sample_name, "  ISO Cobbles (> 63 mm)", fmt_num(params.get("ISO_Cobbles_%", 0), 2, 2), ""])
                data_rows.append([sample_name, "ASTM D2487 Fractions (%)", "", ""])
                data_rows.append([sample_name, "  ASTM Fines (< 0.075 mm)", fmt_num(params.get("ASTM_Fines_%", 0), 2, 2), ""])
                data_rows.append([sample_name, "  ASTM Sand (0.075 - 4.75 mm)", fmt_num(params.get("ASTM_Sand_%", 0), 2, 2), ""])
                data_rows.append([sample_name, "  ASTM Gravel (4.75 - 75 mm)", fmt_num(params.get("ASTM_Gravel_%", 0), 2, 2), ""])
                data_rows.append([sample_name, "  ASTM Cobbles (> 75 mm)", fmt_num(params.get("ASTM_Cobbles_%", 0), 2, 2), ""])
                
                pan = calculator.get_pan_summary()
                if pan["has_pan"]:
                    data_rows.append([sample_name, "Pan weight (g)", fmt_num(pan["pan_weight_g"], 2, 4), ""])
                    data_rows.append([sample_name, "Pan % of basis", fmt_num(pan["pan_pct_of_basis"], 2, 3), ""])
                
                data_rows.append(["", "", "", ""])

            if filename.endswith('.csv'):
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Sample', 'Parameter', 'Value', 'Classification'])
                    writer.writerows(data_rows)
            elif filename.endswith('.xlsx'):
                clean_rows = [r for r in data_rows if any(r)]
                df = pd.DataFrame(clean_rows, columns=['Sample', 'Parameter', 'Value', 'Classification'])
                df.to_excel(filename, index=False)
            elif filename.endswith('.txt'):
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Sample\tParameter\tValue\tClassification\n")
                    for row in data_rows:
                        if not any(row): f.write("\n")
                        else: f.write(f"{row[0]}\t{row[1]}\t{row[2]}\t{row[3]}\n")
                            
            messagebox.showinfo("Export Successful", f"All parameters exported to:\n{filename}")
        except Exception as e: 
            messagebox.showerror("Export Error", f"Failed: {str(e)}")

    def export_friedman_plots(self):
        all_series = []
        if self.data: all_series.append(self.data)
        all_series.extend(self.multiple_series)
        if len(all_series) < 1: messagebox.showwarning("No Data", "Need at least 1 sample"); return
        
        valid_series, valid_types, excluded_count = [], [], 0
        sample_types = getattr(self.app, 'sample_types', [])
        
        for i, series in enumerate(all_series):
            stype = sample_types[i] if i < len(sample_types) else "Unknown"
            if "Crushed" in stype: excluded_count += 1
            else:
                valid_series.append(series); valid_types.append(stype)
        if not valid_series: messagebox.showwarning("No Valid Data", "All samples are marked as 'Crushed / Quarry'. Cannot export."); return
        
        filename = filedialog.asksaveasfilename(title="Export Friedman Plots", defaultextension=".png", filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")])
        if not filename: return
        try:
            dual_params = [self._dual_basis_params(s) for s in valid_series]
            fig = Figure(figsize=(14, 10), dpi=100); fig.suptitle('Friedman (1967) Diagrams', fontsize=14, fontweight='bold')
            def _dual_panel(ax, xk, yk, title, xl, yl, invert_y=False, invert_x=False):
                for i, (pa, pi) in enumerate(dual_params):
                    stype = valid_types[i] if i < len(valid_types) else "Unknown"
                    self._plot_dual_point(ax, pa.get(xk, 0), pa.get(yk, 0),
                                          pi.get(xk, 0), pi.get(yk, 0),
                                          self.colors[i % len(self.colors)],
                                          unknown=(stype in ["Unknown", "Natural - Unconfirmed"]),
                                          label=f"S{i+1}")
                ax.set_xlabel(xl, fontsize=11); ax.set_ylabel(yl, fontsize=11); ax.set_title(title, fontsize=12, fontweight='bold'); ax.grid(True, alpha=0.3)
                if invert_y: ax.invert_yaxis()
                if invert_x: ax.invert_xaxis()
                ax.legend(handles=self._basis_legend_handles(), loc='best', fontsize=8)
            _dual_panel(fig.add_subplot(221), 'skewness', 'kurtosis', '① Skewness vs Kurtosis', 'Skewness (Sk)', 'Kurtosis (KG)')
            _dual_panel(fig.add_subplot(222), 'skewness', 'sorting', '② Skewness vs Sorting', 'Skewness (Sk)', 'Sorting (σI)')
            _dual_panel(fig.add_subplot(223), 'skewness', 'mean_phi', '③ Skewness vs Mean', 'Skewness (Sk)', 'Mean Grain Size (Mz, φ)', invert_y=True)
            _dual_panel(fig.add_subplot(224), 'mean_phi', 'sorting', '④ Mean vs Sorting', 'Mean Grain Size (Mz, φ)', 'Sorting (σI)', invert_x=True)
            fig.tight_layout(rect=[0, 0.05, 1, 0.97])
            if excluded_count > 0: fig.text(0.5, 0.01, f"⚠️ {excluded_count} Crushed/Quarry sample(s) excluded.", ha='center', fontsize=9, style='italic', color='red')
            fig.text(0.5, 0.048, 'Filled circle = ASTM D6913 (recovered weight) | Open circle = ISO 17892-4 / NF P94-056 (initial weight)', ha='center', fontsize=9, style='italic', color='#555555')
            dpi = 300 if filename.endswith('.png') else 150; fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')
            messagebox.showinfo("Export Successful", f"Friedman plots exported to:\n{filename}")
        except Exception as e: messagebox.showerror("Export Error", f"Failed: {str(e)}")

    def export_passega_diagram(self):
        all_series = []
        if self.data: all_series.append(self.data)
        all_series.extend(self.multiple_series)
        if len(all_series) < 1: messagebox.showwarning("No Data", "Need at least 1 sample"); return
        
        valid_series, excluded_count = [], 0
        sample_types = getattr(self.app, 'sample_types', [])
        
        for i, series in enumerate(all_series):
            stype = sample_types[i] if i < len(sample_types) else "Unknown"
            if "Crushed" in stype: excluded_count += 1
            else: valid_series.append(series)
                
        if not valid_series: messagebox.showwarning("No Valid Data", "All samples are marked as 'Crushed / Quarry'. Cannot export."); return
        
        filename = filedialog.asksaveasfilename(title="Export Passega Diagram", defaultextension=".png", filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")])
        if not filename: return
        try:
            astm_points, iso_points = [], []
            for i, series in enumerate(valid_series):
                sample_name = f"S{i+1}"
                try:
                    calc_astm = GranuloCalculator(series, self.app.initial_weight, use_recovered_weight=True)
                    c_a = calc_astm.get_percentile_diameter(1); m_a = calc_astm.get_percentile_diameter(50)
                    if c_a > 0 and m_a > 0: astm_points.append((sample_name, m_a, c_a))
                except: pass
                try:
                    calc_iso = GranuloCalculator(series, self.app.initial_weight, use_recovered_weight=False)
                    c_i = calc_iso.get_percentile_diameter(1); m_i = calc_iso.get_percentile_diameter(50)
                    if c_i > 0 and m_i > 0: iso_points.append((sample_name, m_i, c_i))
                except: pass
            if not astm_points and not iso_points: messagebox.showwarning("No Valid Data", "Could not calculate C and M"); return
            fig = Figure(figsize=(10, 8), dpi=100); ax = fig.add_subplot(111)
            ax.fill_between([0.001, 100], 0.001, 0.5, alpha=0.1, color='blue'); ax.fill_between([0.001, 100], 0.5, 10, alpha=0.1, color='green'); ax.fill_between([0.001, 100], 10, 1000, alpha=0.1, color='red')
            (cmline,) = ax.plot(np.logspace(-3, 3, 100), np.logspace(-3, 3, 100), color='black', linestyle=':', alpha=0.7, linewidth=1.5, label='C = M')
            if astm_points:
                for name, m, c in astm_points:
                    ax.scatter(m, c, s=120, color=self.colors[(int(name[1:]) - 1) % len(self.colors)], edgecolors='black', linewidth=1.2, zorder=10)
            if iso_points:
                for name, m, c in iso_points:
                    ax.scatter(m, c, s=120, facecolors='none', edgecolors=self.colors[(int(name[1:]) - 1) % len(self.colors)], linewidth=2.0, zorder=10)
            for name in sorted({p[0] for p in astm_points} & {p[0] for p in iso_points}):
                ma, ca = [(m, c) for n, m, c in astm_points if n == name][0]
                mi, ci = [(m, c) for n, m, c in iso_points if n == name][0]
                ax.plot([ma, mi], [ca, ci], color='#95a5a6', linewidth=1.0, alpha=0.6, zorder=5)
            ax.set_xlim(0.01, 100); ax.set_ylim(0.001, 100); ax.set_xscale('log'); ax.set_yscale('log')
            ax.set_xlabel('M - Median (D50, mm)', fontsize=12, fontweight='bold'); ax.set_ylabel('C - Coarsest Percentile (mm)', fontsize=12, fontweight='bold')
            ax.set_title('Passega C-M Diagram\nASTM D6913 vs ISO 17892-4 Comparison', fontsize=14, fontweight='bold'); ax.grid(True, which='both', linestyle=':', alpha=0.3); ax.legend(handles=[cmline] + self._basis_legend_handles(), loc='upper left', fontsize=9)
            fig.tight_layout(rect=[0, 0.085, 1, 1])
            if excluded_count > 0: fig.text(0.5, 0.048, f"⚠️ {excluded_count} Crushed/Quarry sample(s) excluded.", ha='center', va='bottom', fontsize=9, style='italic', color='red')
            fig.text(0.5, 0.012, 'Filled circle = ASTM D6913 (recovered weight) | Open circle = ISO 17892-4 / NF P94-056 (initial weight)', ha='center', va='bottom', fontsize=9, style='italic', color='#555555')
            dpi = 300 if filename.endswith('.png') else 150; fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')
            messagebox.showinfo("Export Successful", f"Passega diagram exported to:\n{filename}")
        except Exception as e: messagebox.showerror("Export Error", f"Failed: {str(e)}")

    def export_pdf_report(self):
        all_series = []
        if self.data: all_series.append(('Sample 1', self.data))
        for i, series in enumerate(self.multiple_series): all_series.append((f'Sample {i+2}', series))
        if not all_series:
            messagebox.showwarning("No Data", "No data to export"); return
        filename = filedialog.asksaveasfilename(
            title="Save PDF Report", defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")])
        if not filename: return
        try:
            use_recovered = getattr(self.app, 'use_recovered_weight', True)
            n_pages = self._build_pdf_report(filename, all_series, use_recovered)
            messagebox.showinfo("Export Successful",
                                f"PDF report exported to:\n{filename}\n({n_pages} pages: 1 summary + {len(all_series)} sample sheet(s))")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export PDF report: {str(e)}")

    def _build_pdf_report(self, filename, all_series, use_recovered):
        """Generate a real multi-page PDF report:
        page 1 = header + overlay of all cumulative curves,
        then one A4 sheet per sample (curve with D-markers + full parameter block).
        Uses only matplotlib (PdfPages) - no extra dependency."""
        from matplotlib.backends.backend_pdf import PdfPages
        from datetime import datetime
        import textwrap

        iw = getattr(self.app, 'initial_weight', None) or 100.0
        sample_types = getattr(self.app, 'sample_types', [])
        method_label = 'ASTM D6913 (Recovered Weight)' if use_recovered else 'NF P 94-056 / ISO 17892-4 (Initial Weight)'
        created = datetime.now().strftime('%Y-%m-%d %H:%M')

        # --- pre-compute every calculator once ---
        calcs = []
        for idx, (name, series) in enumerate(all_series):
            stype = sample_types[idx] if idx < len(sample_types) else "Unknown"
            calc = GranuloCalculator(series, iw, use_recovered_weight=use_recovered)
            calcs.append({'name': name, 'type': stype, 'calc': calc,
                          'params': calc.get_all_parameters(), 'pan': calc.get_pan_summary()})
        colors = [self.colors[i % len(self.colors)] for i in range(len(calcs))]

        # --- global diameter range for the summary graph ---
        d_all = [d for c in calcs for d, _ in c['calc'].data if d > 0]
        x_lo, x_hi = (min(d_all) * 0.7, max(d_all) * 1.4) if d_all else (0.0001, 1000.0)
        iso_main = [0.002, 0.063, 2.0, 63.0]

        def draw_curve(ax, entry, label, color):
            calc = entry['calc']
            sd = np.array([d for d, _ in calc.data], dtype=float)
            sp = np.array(calc.cumulative_passing, dtype=float)
            if len(sd) == 0 or len(sd) != len(sp):
                return
            order = np.argsort(sd)[::-1]
            ax.plot(sd[order], sp[order], 'o', color=color, markersize=4.5,
                    markeredgecolor='white', markeredgewidth=0.8, alpha=0.85, zorder=3)
            try:
                dsm, psm = calc.get_cumulative_curve(num_points=1000)
                if dsm is not None and len(dsm) >= 2:
                    ax.plot(dsm, psm, '-', color=color, linewidth=2.2, label=label, zorder=2)
                    return
            except Exception:
                pass
            ax.plot(sd[order], sp[order], '-', color=color, linewidth=1.8, label=label, zorder=2)

        n_pages = 0
        with PdfPages(filename) as pdf:
            # ================= PAGE 1 : summary =================
            fig = Figure(figsize=(8.27, 11.69), dpi=100, facecolor='white')
            fig.text(0.5, 0.965, 'GRAIN SIZE DISTRIBUTION REPORT', ha='center', va='top',
                     fontsize=16, fontweight='bold', color='#2c3e50')
            fig.text(0.5, 0.925, f'Generated: {created}', ha='center', va='top', fontsize=9, color='#555555')
            fig.text(0.5, 0.905, f'Calculation basis: {method_label}', ha='center', va='top', fontsize=9, color='#555555')
            fig.text(0.5, 0.885, f'Samples: {len(calcs)}   |   Initial weight: {iw:.2f} g',
                     ha='center', va='top', fontsize=9, color='#555555')
            if len(calcs) <= 8:
                names_line = '   |   '.join(c['name'] for c in calcs)
            else:
                names_line = '\n'.join(textwrap.wrap('   '.join(c['name'] for c in calcs), width=110))
            fig.text(0.5, 0.865, names_line, ha='center', va='top', fontsize=8, color='#34495e')

            ax = fig.add_axes([0.10, 0.07, 0.85, 0.74])
            ax.set_xscale('log'); ax.set_xlim(x_hi, x_lo); ax.set_ylim(-2, 102)
            ax.set_xlabel('Grain Size (mm) - Logarithmic Scale', fontsize=11)
            ax.set_ylabel('Cumulative Percentage Passing (%)', fontsize=11)
            ax.set_title('Grain Size Distribution Curves - All Samples', fontsize=12, fontweight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.tick_params(axis='x', labelsize=8)
            for value in iso_main:
                if x_lo <= value <= x_hi:
                    ax.axvline(x=value, color='gray', linestyle='-', linewidth=1.5, alpha=0.6, zorder=1)
            for entry, color in zip(calcs, colors):
                draw_curve(ax, entry, entry['name'], color)
            if len(calcs) > 1:
                ax.legend(loc='lower left', fontsize=9)
            pdf.savefig(fig, facecolor='white'); n_pages += 1

            # ================= one A4 sheet per sample =================
            for entry, color in zip(calcs, colors):
                fig = Figure(figsize=(8.27, 11.69), dpi=100, facecolor='white')
                fig.text(0.5, 0.965, entry['name'], ha='center', va='top',
                         fontsize=15, fontweight='bold', color='#2c3e50')
                fig.text(0.5, 0.928, f"Declared sample type: {entry['type']}",
                         ha='center', va='top', fontsize=9, color='#555555')
                fig.text(0.5, 0.912, f'Basis: {method_label}',
                         ha='center', va='top', fontsize=9, color='#555555')

                ax = fig.add_axes([0.11, 0.53, 0.84, 0.335])
                ax.set_xscale('log')
                d_here = [d for d, _ in entry['calc'].data if d > 0]
                ax.set_xlim(max(d_here) * 1.4 if d_here else 1000.0,
                            min(d_here) * 0.7 if d_here else 0.0001)
                ax.set_ylim(-2, 102)
                ax.set_xlabel('Grain Size (mm) - Logarithmic Scale', fontsize=10)
                ax.set_ylabel('Cumulative Passing (%)', fontsize=10)
                ax.set_title('Grain Size Distribution Curve', fontsize=11, fontweight='bold')
                ax.grid(True, alpha=0.3, linestyle='--')
                ax.tick_params(axis='x', labelsize=8)
                for value in iso_main:
                    ax.axvline(x=value, color='gray', linestyle='-', linewidth=1.2, alpha=0.5, zorder=1)
                draw_curve(ax, entry, entry['name'], color)
                params = entry['params']
                for p in (10, 30, 50, 60):
                    dval = params.get(f'D{p}', float('nan'))
                    try:
                        if dval and not math.isnan(float(dval)) and float(dval) > 0:
                            ax.plot([dval], [p], 's', color='#c0392b', markersize=6, zorder=6)
                            lim = ax.get_xlim(); dlo, dhi = min(lim), max(lim)
                            near_fine_end = (math.log10(dval) - math.log10(dlo)) < 0.35 * (math.log10(dhi) - math.log10(dlo))
                            if near_fine_end:
                                ax.annotate(f'D{p} = {fmt_num(dval, 2, 3)} mm', (dval, p), xytext=(-6, 6),
                                            textcoords='offset points', fontsize=7.5, ha='right',
                                            color='#c0392b', fontweight='bold')
                            else:
                                ax.annotate(f'D{p} = {fmt_num(dval, 2, 3)} mm', (dval, p), xytext=(6, 6),
                                            textcoords='offset points', fontsize=7.5,
                                            color='#c0392b', fontweight='bold')
                    except (TypeError, ValueError):
                        pass

                # ---- parameter text block ----
                calc = entry['calc']; pan = entry['pan']
                pct_rows = "\n".join(
                    f"  {p:3.0f}%:  {fmt_num(params.get(f'D{p}', 0), 2, 3):>12} mm    (φ = {fmt_num(params.get(f'phi{p}', 0), 3, 3):>8})"
                    for p in (5, 10, 16, 25, 30, 50, 60, 70, 75, 84, 90, 95))
                pan_block = (f"PAN: {fmt_num(pan['pan_weight_g'], 2, 4)} g "
                             f"({fmt_num(pan['pan_pct_of_basis'], 2, 3)} % of basis)\n") if pan.get('has_pan') else ""
                report = (
                    f"{'='*66}\nPERCENTILES\n{'-'*66}\n{pct_rows}\n"
                    f"{pan_block}{'-'*66}\n"
                    f"CENTRAL TENDENCY\n{'-'*66}\n"
                    f"  Mode:            {fmt_num(params.get('mode_mm', 0), 2, 4)} mm    ({params.get('modality', 'unknown')})\n"
                    f"  Graphic mean:    {fmt_num(params.get('mean_mm', 0), 2, 4)} mm    (φ = {fmt_num(params.get('mean_phi', 0), 3, 3)})\n"
                    f"  Median:          {fmt_num(params.get('median_mm', 0), 2, 4)} mm    (φ = {fmt_num(params.get('median_phi', 0), 3, 3)})\n"
                    f"{'-'*66}\n"
                    f"SORTING : σ_I = {fmt_num(params.get('sorting', 0), 3, 3)}  ->  {params.get('sorting_class', 'unknown')}\n"
                    f"SKEWNESS: Sk  = {fmt_num(params.get('skewness', 0), 3, 3)}  ->  {params.get('skewness_class', 'unknown')}\n"
                    f"KURTOSIS: KG  = {fmt_num(params.get('kurtosis', 0), 3, 3)}  ->  {params.get('kurtosis_class', 'unknown')}\n"
                    f"{'-'*66}\n"
                    f"Cu = D60/D10               = {fmt_num(params.get('Cu', 0), 2, 3)}  ->  {params.get('Cu_class', 'unknown')}\n"
                    f"Cc = (D30)²/(D10 × D60)    = {fmt_num(params.get('Cc', 0), 3, 3)}  ->  {params.get('Cc_class', 'unknown')}\n"
                    f"FM (Fineness Modulus)      = {fmt_num(params.get('FM', 0), 2, 3)}  ->  {params.get('FM_class', 'unknown')}\n"
                    f"{'-'*66}\n"
                    f"ISO 14688-1 FRACTIONS (%):  Clay {fmt_num(params.get('ISO_Clay_%', 0), 2, 3)} | Silt {fmt_num(params.get('ISO_Silt_%', 0), 2, 3)} | Sand {fmt_num(params.get('ISO_Sand_%', 0), 2, 3)} | Gravel {fmt_num(params.get('ISO_Gravel_%', 0), 2, 3)} | Cobbles {fmt_num(params.get('ISO_Cobbles_%', 0), 2, 3)}\n"
                    f"ASTM D2487 FRACTIONS (%):   Fines {fmt_num(params.get('ASTM_Fines_%', 0), 2, 3)} | Sand {fmt_num(params.get('ASTM_Sand_%', 0), 2, 3)} | Gravel {fmt_num(params.get('ASTM_Gravel_%', 0), 2, 3)} | Cobbles {fmt_num(params.get('ASTM_Cobbles_%', 0), 2, 3)}\n"
                    f"{'-'*66}\n"
                    f"QC: Initial {iw:.2f} g | Recovered {fmt_num(calc.recovered_weight, 2, 4)} g | "
                    f"Recovery {fmt_num(params.get('recovery_pct', 0), 2, 3)} %\n"
                    f"{'='*66}"
                )
                tax = fig.add_axes([0.04, 0.03, 0.92, 0.46]); tax.axis('off')
                tax.text(0.0, 1.0, report, family='monospace', fontsize=8.0, va='top',
                         ha='left', color='#2c3e50', linespacing=1.28)
                pdf.savefig(fig, facecolor='white'); n_pages += 1

            # ================= PDF metadata =================
            info = pdf.infodict()
            info['Title'] = 'Grain Size Distribution Report'
            info['Author'] = 'Smaine Chellat - University Constantine 1, Geological Department'
            info['Subject'] = f'Sieve analysis - {method_label} - ISO 14688-1:2017 classification'
            info['Keywords'] = 'granulometry, sieve analysis, grain size distribution'
            info['CreationDate'] = datetime.now()
        return n_pages