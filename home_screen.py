"""
Home Screen Module - Data Entry Interface

FIXED VERSION (v3.0):
  2. Provenance comboboxes are now perfectly aligned with their data columns.
     Every cell (header label, Entry, Combobox) is wrapped in a fixed-pixel
     Frame (pack_propagate(False)), so the header row, the provenance row and
     every data row share the exact same column grid.
  3. ToolTip rewritten: HOVER-ONLY and never forced above other applications.
     The tooltip appears only while the cursor rests on its widget and is
     destroyed the moment the cursor leaves (widget, tooltip window or the
     whole app losing focus), so it can no longer linger above other windows
     such as Word or a browser. Still clamped to the screen edges (tooltips
     of the right-hand columns are no longer off-screen) and safe against
     widget destruction.
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import pandas as pd
import os
import csv
from typing import List, Tuple, Optional, Union
from calculations import is_pan_label, normalize_pan_label, PAN_LABELS

# Unified export engine: full-window HD/4K capture (better than screenshots)
from export_utils import prompt_export_screen

ENVIRONMENTS = [
    "--- Select ---",
    "Unknown",
    "Crushed / Quarry",
    "Natural - Unconfirmed",
    "Continental - Alluvial fans",
    "Continental - Fluvial",
    "Continental - Lacustrine",
    "Continental - Aeolian",
    "Continental - Glacial",
    "Continental - Paludal",
    "Transitional - Deltas",
    "Transitional - Beaches",
    "Transitional - Lagoons",
    "Transitional - Tidal flats",
    "Transitional - Estuaries",
    "Marine - Continental shelf",
    "Marine - Organic reefs",
    "Marine - Continental slope",
    "Marine - Abyssal plain"
]

ENV_DESCRIPTIONS = {
    "--- Select ---": "Please select a provenance for this sample.",
    "Unknown": "Provenance is not known.\n(Will be plotted with a grey 'X' marker).",
    "Crushed / Quarry": "Anthropogenic material (crushed rock).\n(Excluded from Friedman and Passega diagrams).",
    "Natural - Unconfirmed": "Appears natural but field provenance is unverified.\n(Plotted with a grey 'X' marker).",
    "Continental - Alluvial fans": "Cone-shaped deposits of coarse, poorly sorted gravel and sand where steep mountain streams suddenly flatten out onto a valley floor.",
    "Continental - Fluvial": "Meandering and braided rivers transport and deposit gravel, sand, and silt across channels, point bars, and surrounding floodplains.",
    "Continental - Lacustrine": "Calm freshwater bodies trap fine-grained mud, silt, and organic matter in their centers, while coarser sands settle near the shorelines.",
    "Continental - Aeolian": "Wind sorts and transports fine sand into large cross-bedded dunes and carries silt away as dust.",
    "Continental - Glacial": "Moving ice grinds rock into unsorted mixtures of clay, sand, and boulders, leaving behind moraines and outwash plains.",
    "Continental - Paludal": "Stagnant, oxygen-poor wetlands (swamps and marshes) accumulate thick layers of plant debris.",
    "Transitional - Deltas": "Fan-shaped accumulations of sand, silt, and mud build outward where sediment-laden rivers enter a standing body of water.",
    "Transitional - Beaches": "Constant wave action washes away fine mud, leaving behind well-sorted quartz or carbonate sands along the coast.",
    "Transitional - Lagoons": "Shallow, quiet bodies of water separated from the open ocean by barrier islands or reefs collect fine mud, silt, and evaporite minerals.",
    "Transitional - Tidal flats": "Low-lying coastal zones regularly flooded and exposed by tides accumulate alternating layers of fine mud and sand.",
    "Transitional - Estuaries": "Drowned river valleys where freshwater mixes with seawater trap fine-grained silts and clays.",
    "Marine - Continental shelf": "Sunlight penetrates these relatively shallow waters, supporting abundant marine life and accumulating sands, muds, and carbonate shells.",
    "Marine - Organic reefs": "Wave-resistant structures built by corals, sponges, and algae thrive in warm, clear, shallow tropical waters.",
    "Marine - Continental slope": "Underwater gravity flows called turbidity currents carry sand and mud down the steep edge of the continent.",
    "Marine - Abyssal plain": "The flat, deep ocean floor far from land slowly collects microscopic shells (oozes) and windblown clay particles."
}

# ----------------------------------------------------------------------------------
# Column grid: ONE source of truth for the width of every column, in PIXELS.
# Header labels, data Entries and provenance Comboboxes are all stretched to fill
# these fixed cells, so the three rows can never drift apart again.
# ----------------------------------------------------------------------------------
CELL_WIDTHS = {0: 200, 1: 165}      # sieve diameter column, first weight column
DEFAULT_CELL_WIDTH = 120            # every additional sample column
CELL_HEADER_H = 30                  # header cell height
CELL_PROV_H = 48                    # provenance cell height (mini label + combobox)
CELL_DATA_H = 26                    # data entry cell height
DEL_ZONE_W = 48                     # width of the per-row delete-button zone


def cell_width(i: int) -> int:
    return CELL_WIDTHS.get(i, DEFAULT_CELL_WIDTH)


class ToolTip:
    """Reliable HOVER-ONLY tooltip.

    Behaviour (v2.2):
      - appears only while the cursor rests on the widget (after `delay` ms)
      - destroyed as soon as the cursor leaves the widget, the tooltip window
        itself, or the app window loses focus -> it can never linger above
        other applications (Word, browser, ...)
      - NOT "-topmost": a lifted transient Toplevel is still above every
        window of this own application, which is all a tooltip needs; forcing
        topmost made it cover unrelated programs
      - position clamped to the screen (no more tooltips lost off the
        right/bottom edge for the columns on the right side of the table)
      - real requested size measured before positioning (update_idletasks)
      - pending callbacks cancelled when the widget is destroyed (no TclError
        after the provenance row is rebuilt)
    """

    def __init__(self, widget, text: str = "", delay: int = 400):
        self.widget, self.text, self.delay = widget, text, delay
        self.tooltip, self._after_id = None, None
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")
        widget.bind("<FocusOut>", self._on_leave, add="+")   # alt-tab / click on another app
        widget.bind("<Destroy>", self._on_destroy, add="+")

    def _on_enter(self, event=None):
        self.schedule()

    def _on_leave(self, event=None):
        self.unschedule()
        self.hide()

    def _on_destroy(self, event=None):
        if event.widget is self.widget:
            self.unschedule()
            self.hide()

    def schedule(self):
        self.unschedule()
        try:
            self._after_id = self.widget.after(self.delay, self.show)
        except tk.TclError:
            self._after_id = None

    def unschedule(self):
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def show(self):
        self._after_id = None
        if self.tooltip or not self.text:
            return
        try:
            self.widget.update_idletasks()
        except tk.TclError:
            return
        self.tooltip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        # NO "-topmost": the tooltip must never float above OTHER applications.
        # A lifted transient of this app is above every window of this app,
        # which is all a tooltip needs; when the user switches to Word or a
        # browser, that program simply covers it.
        try:
            tw.transient(self.widget.winfo_toplevel())
        except tk.TclError:
            pass
        # Safety nets: if the cursor lands on the tooltip itself and then
        # leaves (towards another application), the tooltip must not linger.
        tw.bind("<Leave>", lambda e: self.hide(), add="+")
        tw.bind("<ButtonPress>", lambda e: self.hide(), add="+")
        tk.Label(tw, text=self.text, justify=tk.LEFT, background="#ffffe0",
                 relief=tk.SOLID, borderwidth=1, font=("Arial", 9),
                 padx=8, pady=4, wraplength=380).pack(ipadx=1)
        tw.update_idletasks()
        sw, sh = self.widget.winfo_screenwidth(), self.widget.winfo_screenheight()
        w_req, h_req = tw.winfo_reqwidth(), tw.winfo_reqheight()
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        if x + w_req > sw - 8:                       # clamp right edge
            x = max(8, sw - w_req - 8)
        if x < 8:
            x = 8
        if y + h_req > sh - 8:                       # clamp bottom edge -> flip above
            y = max(8, self.widget.winfo_rooty() - h_req - 6)
        tw.wm_geometry(f"+{x}+{y}")
        tw.lift()

    def hide(self):
        if self.tooltip is not None:
            try:
                self.tooltip.destroy()
            except tk.TclError:
                pass
            self.tooltip = None

    def configure(self, text: str):
        self.text = text
        if self.tooltip is not None:                 # visible right now -> refresh
            self.hide()
            self.show()


class HomeScreen(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.parent, self.app = parent, app
        self.data_rows, self.num_columns = [], 2
        self.canvas, self.headers_frame, self.types_frame = None, None, None
        self.calc_basis_var = tk.StringVar(value="recovered")
        self.basis_tooltip = None
        self.type_vars = []
        self.setup_ui()

    def setup_ui(self):
        title_frame = tk.Frame(self, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X); title_frame.pack_propagate(False)
        settings_btn = tk.Button(title_frame, text="⚙ Settings", command=self.app.show_settings_screen, bg='#34495e', fg='white', font=('Arial', 11), padx=15, pady=2, relief=tk.FLAT, cursor="hand2")
        settings_btn.pack(side=tk.RIGHT, padx=20)
        tk.Label(title_frame, text="GranuloGraph - Data Entry", font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white').pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        content_frame = tk.Frame(self); content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        left_panel = tk.Frame(content_frame, relief=tk.GROOVE, bd=2); left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        weight_frame = tk.Frame(left_panel, bg='#ecf0f1', height=50); weight_frame.pack(fill=tk.X, padx=5, pady=5); weight_frame.pack_propagate(False)
        tk.Label(weight_frame, text="Initial Sample Weight (g):", font=('Arial', 11, 'bold'), bg='#ecf0f1').pack(side=tk.LEFT, padx=5)
        self.weight_var = tk.StringVar(value="100.0")
        tk.Entry(weight_frame, textvariable=self.weight_var, font=('Arial', 11), width=15).pack(side=tk.LEFT, padx=5)
        tk.Label(weight_frame, text="(g)", font=('Arial', 10), bg='#ecf0f1').pack(side=tk.LEFT)

        basis_frame = tk.Frame(left_panel, bg='#ecf0f1', height=70); basis_frame.pack(fill=tk.X, padx=5, pady=5); basis_frame.pack_propagate(False)
        tk.Label(basis_frame, text="Calculation Basis:", font=('Arial', 11, 'bold'), bg='#ecf0f1').pack(side=tk.LEFT, padx=5)
        self.basis_combo = ttk.Combobox(basis_frame, textvariable=self.calc_basis_var, values=["recovered", "initial"], state="readonly", width=18, font=('Arial', 10))
        self.basis_combo.pack(side=tk.LEFT, padx=5); self._update_basis_tooltip()
        tk.Label(basis_frame, text="▼", font=('Arial', 8), bg='#ecf0f1').pack(side=tk.LEFT)
        self.basis_indicator = tk.Label(basis_frame, text="🔬 ASTM (Research)", font=('Arial', 9, 'italic'), bg='#ecf0f1', fg='#27ae60')
        self.basis_indicator.pack(side=tk.LEFT, padx=10); self.calc_basis_var.trace_add("write", self._on_basis_change)

        table_frame = tk.Frame(left_panel); table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        table_container = tk.Frame(table_frame); table_container.pack(fill=tk.BOTH, expand=True)

        # scrollbars are created first so the header zone can reserve EXACTLY the
        # same width for the vertical scrollbar => identical viewport widths =>
        # pixel-perfect header/data sync at every scroll position
        self.xscrollbar = tk.Scrollbar(table_container, orient=tk.HORIZONTAL)
        scrollbar = tk.Scrollbar(table_container, orient=tk.VERTICAL)
        sb_w = scrollbar.winfo_reqwidth()

        # ---- frozen header zone: scrolls horizontally in sync with the data ----
        header_zone = tk.Frame(table_container)
        header_zone.pack(side=tk.TOP, fill=tk.X)
        self.header_spacer = tk.Frame(header_zone, width=sb_w)
        self.header_spacer.pack(side=tk.RIGHT)
        self.header_canvas = tk.Canvas(header_zone, highlightthickness=0, borderwidth=0,
                                       height=CELL_HEADER_H + CELL_PROV_H + 8)
        self.header_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.header_inner = tk.Frame(self.header_canvas)
        self.header_canvas.create_window((0, 0), window=self.header_inner, anchor="nw")
        self.header_inner.bind("<Configure>", lambda e: self.header_canvas.configure(scrollregion=self.header_canvas.bbox("all")))
        self.headers_frame = tk.Frame(self.header_inner); self.headers_frame.pack(fill=tk.X)
        self.types_frame = tk.Frame(self.header_inner, bg='#f8f9f9'); self.types_frame.pack(fill=tk.X, pady=(2, 5))
        self._update_table_headers(self.headers_frame)

        # ---- data zone: vertical AND horizontal scrolling (no more squeezed columns) ----
        self.xscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # highlightthickness=0 so the data area starts at the exact same x as the header zone
        self.canvas = tk.Canvas(table_container, highlightthickness=0, borderwidth=0,
                                xscrollcommand=self._sync_header_x)
        self.scrollable_frame = tk.Frame(self.canvas)
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.canvas.yview)
        self.xscrollbar.config(command=self.canvas.xview)
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel); self.canvas.bind_all("<Button-4>", self._on_mousewheel); self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        for i in range(10): self.add_data_row(i)

        button_frame = tk.Frame(left_panel); button_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Button(button_frame, text="➕ Add Row", command=self.add_row, bg='#27ae60', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="➖ Remove Last Row", command=self.remove_row, bg='#e74c3c', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="➕ Add Column", command=self.add_column, bg='#3498db', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="➖ Delete Last Column", command=self.delete_last_column, bg='#9b59b6', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=2)

        right_panel = tk.Frame(content_frame, width=320, relief=tk.GROOVE, bd=2, bg='#f8f9f9')
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0)); right_panel.pack_propagate(False)
        canvas_right = tk.Canvas(right_panel, bg='#f8f9f9', highlightthickness=0); scrollbar_right = tk.Scrollbar(right_panel, orient=tk.VERTICAL, command=canvas_right.yview)
        scrollable_right = tk.Frame(canvas_right, bg='#f8f9f9')
        scrollable_right.bind("<Configure>", lambda e: canvas_right.configure(scrollregion=canvas_right.bbox("all")))
        canvas_right.create_window((0, 0), window=scrollable_right, anchor="nw")
        canvas_right.configure(yscrollcommand=scrollbar_right.set); canvas_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); scrollbar_right.pack(side=tk.RIGHT, fill=tk.Y)

        def _on_right_mousewheel(event):
            if canvas_right.winfo_exists(): canvas_right.yview_scroll(int(-1*(event.delta/120)), "units")
        # entering the right panel re-targets the global wheel; LEAVING now RESTORES the
        # main table wheel instead of unbinding it completely (bug fix)
        canvas_right.bind("<Enter>", lambda e: canvas_right.bind_all("<MouseWheel>", _on_right_mousewheel))
        canvas_right.bind("<Leave>", lambda e: self._restore_main_wheel())

        file_frame = tk.Frame(scrollable_right, bg='#f8f9f9'); file_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        tk.Label(file_frame, text="File Operations", font=('Arial', 12, 'bold'), bg='#f8f9f9', fg='#2c3e50').pack(pady=(0, 5))
        tk.Button(file_frame, text="📂 Import CSV/Excel/TXT", command=self.import_data, bg='#3498db', fg='white', font=('Arial', 10), cursor="hand2").pack(fill=tk.X, pady=2)
        tk.Button(file_frame, text="💾 Save as CSV", command=self.save_data, bg='#f39c12', fg='white', font=('Arial', 10), cursor="hand2").pack(fill=tk.X, pady=2)

        info_frame = tk.Frame(scrollable_right, bg='#fffacd', relief=tk.SOLID, bd=1); info_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Label(info_frame, text="📋 Calculation Methods", font=('Arial', 10, 'bold'), bg='#fffacd', fg='#2c3e50').pack(pady=3)
        info_text = "🔬 Recovered Weight (ASTM):\n   • Research & Journals\n   • Folk & Ward statistics\n   • Ensures 0–100% curve\n\n🏗️ Initial Weight (NF/ISO):\n   • Geotechnical reports\n   • Algerian/French standards\n   • Engineering projects\n\n📌 ASTM D6913 Limits:\n   • Max sieving loss allowed: 0.5%\n   • Type 'Pan' in Diameter"
        tk.Label(info_frame, text=info_text, justify=tk.LEFT, font=('Arial', 8), bg='#fffacd', fg='#34495e').pack(padx=8, pady=5)

        valid_frame = tk.Frame(scrollable_right, bg='#f8f9f9'); valid_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Label(valid_frame, text="Validation", font=('Arial', 12, 'bold'), bg='#f8f9f9', fg='#2c3e50').pack(pady=(5, 2))
        self.valid_label = tk.Label(valid_frame, text="⏳ Ready to validate", font=('Arial', 9), bg='#f8f9f9', fg='#7f8c8d', wraplength=280, justify=tk.CENTER)
        self.valid_label.pack(pady=(0, 10), fill=tk.X)
        tk.Button(valid_frame, text="✓ Validate Data", command=self.validate_data, bg='#27ae60', fg='white', font=('Arial', 11, 'bold'), cursor="hand2").pack(fill=tk.X, pady=2)
        tk.Button(scrollable_right, text="📊 Display Graph", command=self.go_to_graph, bg='#8e44ad', fg='white', font=('Arial', 12, 'bold'), cursor="hand2").pack(fill=tk.X, padx=10, pady=(15, 5))
        tk.Button(scrollable_right, text="🖥 Save Home Screen (HD/4K)", command=self.save_home_screen, bg='#16a085', fg='white', font=('Arial', 10, 'bold'), cursor="hand2").pack(fill=tk.X, padx=10, pady=(0, 15))

        help_frame = tk.LabelFrame(scrollable_right, text="Instructions", font=('Arial', 9, 'bold'), bg='#f8f9f9', fg='#7f8c8d'); help_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        help_text = "• Enter at least 4 sieves + Pan\n• Diameters in descending order\n• Use comma or point for decimals\n• Type 'Pan' or 'Bottom' in Diameter\n• Select calculation basis first\n• CSV format: diameter,weight\n• European: diameter;weight (31,5)"
        tk.Label(help_frame, text=help_text, justify=tk.LEFT, anchor="nw", font=('Arial', 9), bg='#f8f9f9', fg='#34495e', wraplength=280).pack(padx=10, pady=10, fill=tk.X)

    def _sync_header_x(self, first, last):
        """Keep the frozen header/provenance rows glued to the data columns
        while the data area is scrolled horizontally."""
        self.xscrollbar.set(first, last)
        try:
            self.header_canvas.xview_moveto(first)
        except tk.TclError:
            pass

    def _restore_main_wheel(self):
        """Re-bind the main table wheel after the right panel stole it."""
        if not self.canvas:
            return
        try:
            self.canvas.unbind_all("<MouseWheel>")
            self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
            self.canvas.bind_all("<Button-4>", self._on_mousewheel)
            self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        except tk.TclError:
            pass

    def show_env_info(self):
        win = tk.Toplevel(self)
        win.title("Provenance Environment Guide")
        win.geometry("600x650")
        win.configure(bg='white')

        text = tk.Text(win, wrap=tk.WORD, font=('Arial', 10), bg='white', padx=15, pady=15)
        scrollbar = tk.Scrollbar(win, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text.tag_configure("title", font=('Arial', 14, 'bold'), foreground='#2c3e50')
        text.tag_configure("env_name", font=('Arial', 11, 'bold'), foreground='#3498db')

        text.insert(tk.END, "📖 Provenance Environment Guide\n", "title")
        text.insert(tk.END, "="*60 + "\n\n")

        for env in ENVIRONMENTS:
            if env == "--- Select ---": continue
            desc = ENV_DESCRIPTIONS.get(env, "No description available.")
            text.insert(tk.END, f"🔹 {env}\n", "env_name")
            text.insert(tk.END, f"{desc}\n\n")

        text.config(state=tk.DISABLED)

    def _make_cell(self, parent, i: int, height: int) -> tk.Frame:
        """Fixed-width cell: the single source of truth for the column geometry."""
        cell = tk.Frame(parent, width=cell_width(i), height=height)
        cell.pack(side=tk.LEFT, padx=1)
        cell.pack_propagate(False)          # keep the frame at exactly the target size
        return cell

    def _update_table_headers(self, parent):
        # ---- header row: every label stretched inside its fixed cell ----
        for widget in parent.winfo_children(): widget.destroy()
        for i in range(self.num_columns):
            if i == 0: header_text = "Sieve Diameter (mm or Pan)"
            elif i == 1: header_text = "Retained Weight (g)"
            else: header_text = f"Column {i+1}"
            cell = self._make_cell(parent, i, CELL_HEADER_H)
            tk.Label(cell, text=header_text, bg='#3498db', fg='white',
                     font=('Arial', 10, 'bold')).pack(fill=tk.BOTH, expand=True)

        # ---- provenance row: same fixed cells, combobox stretched to 100% width ----
        for widget in self.types_frame.winfo_children(): widget.destroy()
        self.type_vars = []
        for i in range(self.num_columns):
            cell = self._make_cell(self.types_frame, i, CELL_PROV_H)
            inner = tk.Frame(cell, bg='#f8f9f9')
            inner.pack(fill=tk.BOTH, expand=True)
            if i == 0:
                tk.Label(inner, text="", bg='#f8f9f9').pack(fill=tk.BOTH, expand=True)
                self.type_vars.append(None)
            else:
                tk.Label(inner, text=f"Sample {i}", font=('Arial', 7), fg='#7f8c8d', bg='#f8f9f9').pack(anchor='w')
                var = tk.StringVar(value="--- Select ---")
                # NO width= parameter: the combobox stretches to the exact cell width
                combo = ttk.Combobox(inner, textvariable=var, values=ENVIRONMENTS, state="readonly")
                combo.pack(fill=tk.X, expand=True)

                tooltip = ToolTip(combo, f"--- Select ---\n\n{ENV_DESCRIPTIONS['--- Select ---']}")

                def _on_selected(event=None, t=tooltip, c=combo):
                    env = c.get()
                    # Update the text only: the tooltip is shown by HOVERING
                    # over the combobox, never pushed after a selection (the
                    # old forced show() used to linger above other windows
                    # such as Word or the browser).
                    t.configure(f"{env}\n\n{ENV_DESCRIPTIONS.get(env, 'No description available.')}")

                combo.bind("<<ComboboxSelected>>", _on_selected)
                self.type_vars.append(var)

        # trailing spacer matching the delete-button zone, so the header stays glued
        # to the data columns even when scrolled fully to the right
        for zone_parent, zone_h in ((parent, CELL_HEADER_H), (self.types_frame, CELL_PROV_H)):
            spacer = tk.Frame(zone_parent, width=DEL_ZONE_W, height=zone_h)
            spacer.pack(side=tk.LEFT)
            spacer.pack_propagate(False)

    def _on_basis_change(self, *args):
        self._update_basis_tooltip()
        if self.calc_basis_var.get() == "recovered": self.basis_indicator.config(text="🔬 ASTM (Research)", fg='#27ae60')
        else: self.basis_indicator.config(text="🏗️ NF/ISO (Geotechnical)", fg='#e67e22')

    def _update_basis_tooltip(self):
        if self.calc_basis_var.get() == "recovered": tooltip_text = "🔬 Recovered Weight (ASTM D6913)\n\n• For: Research, Papers\n• Percentages based on total recovered mass\n• Ensures cumulative curve spans 0–100%\n• Recommended for Folk & Ward statistics"
        else: tooltip_text = "🏗️ Initial Weight (NF P 94-056 / ISO 17892-4)\n\n• For: Engineering, Geotechnical Reports\n• Percentages based on initial dry mass\n• Standard for Algerian/French standards"
        if self.basis_tooltip: self.basis_tooltip.configure(tooltip_text)
        else: self.basis_tooltip = ToolTip(self.basis_combo, tooltip_text)

    def _on_mousewheel(self, event):
        if self.canvas is None: return
        try:
            if event.num == 5 or event.delta == -120: self.canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta == 120: self.canvas.yview_scroll(-1, "units")
        except tk.TclError: pass

    def destroy(self):
        try:
            if self.canvas: self.canvas.unbind_all("<MouseWheel>"); self.canvas.unbind_all("<Button-4>"); self.canvas.unbind_all("<Button-5>")
        except: pass
        super().destroy()

    def add_data_row(self, row_num: int, values: List[str] = None):
        row_frame = tk.Frame(self.scrollable_frame); row_frame.pack(fill=tk.X, pady=1)
        if values is None: values = [""] * self.num_columns
        entry_vars, cells = [], []
        for i in range(max(self.num_columns, len(values))):
            cell = self._make_cell(row_frame, i, CELL_DATA_H)
            var = tk.StringVar(value=values[i] if i < len(values) else "")
            tk.Entry(cell, textvariable=var).pack(fill=tk.BOTH, expand=True)
            entry_vars.append(var); cells.append(cell)
        del_btn = tk.Button(row_frame, text="✖", command=lambda: self.delete_row(row_frame), bg='#e74c3c', fg='white', width=2)
        del_btn.pack(side=tk.LEFT, padx=1)
        self.data_rows.append({'frame': row_frame, 'entry_vars': entry_vars, 'cells': cells, 'del_btn': del_btn})

    def add_row(self): self.add_data_row(len(self.data_rows))

    def remove_row(self):
        if len(self.data_rows) > 10:
            row = self.data_rows.pop(); row['frame'].destroy()
        else: messagebox.showwarning("Cannot Remove", "Minimum 10 rows required!")

    def delete_row(self, row_frame):
        if len(self.data_rows) <= 10: messagebox.showwarning("Cannot Delete", "Minimum 10 rows required!"); return
        for i, row in enumerate(self.data_rows):
            if row['frame'] == row_frame: self.data_rows.pop(i); row_frame.destroy(); break

    def add_column(self):
        self.num_columns += 1
        if self.headers_frame: self._update_table_headers(self.headers_frame)
        for row in self.data_rows:
            cell = self._make_cell(row['frame'], self.num_columns - 1, CELL_DATA_H)
            cell.pack(side=tk.LEFT, padx=1, before=row['del_btn'])   # re-slot BEFORE the ✖ button
            var = tk.StringVar(value="")
            tk.Entry(cell, textvariable=var).pack(fill=tk.BOTH, expand=True)
            row['entry_vars'].append(var); row['cells'].append(cell)
        messagebox.showinfo("Column Added", f"Column {self.num_columns} added successfully!")

    def delete_last_column(self):
        if self.num_columns <= 2: messagebox.showwarning("Cannot Delete", "Minimum 2 columns required!"); return
        for row in self.data_rows:
            if row['cells']:
                row['cells'].pop().destroy()      # removes the cell frame and its Entry
                if row['entry_vars']: row['entry_vars'].pop()
        self.num_columns -= 1
        if self.headers_frame: self._update_table_headers(self.headers_frame)
        messagebox.showinfo("Column Deleted", f"Column {self.num_columns + 1} deleted successfully!")

    def get_data(self) -> Tuple[List[Tuple[Union[float, str], float]], float]:
        all_series, initial_weight = self.get_all_series_data()
        return (all_series[0], initial_weight) if all_series else ([], initial_weight)

    def get_all_series_data(self) -> Tuple[List[List[Tuple[Union[float, str], float]]], float]:
        if not self.data_rows: return [], 100.0
        try: initial_weight = float(self.weight_var.get().replace(",", "."))
        except ValueError: initial_weight = 100.0
        num_data_cols = self.num_columns - 1
        if num_data_cols < 1: return [], initial_weight
        all_series = []
        series_types = []
        for col_idx in range(1, self.num_columns):
            series = []
            for row in self.data_rows:
                if len(row["entry_vars"]) <= col_idx: continue
                dia_raw = row["entry_vars"][0].get().strip(); wt_raw = row["entry_vars"][col_idx].get().strip()
                if not dia_raw or not wt_raw: continue
                try: weight = float(wt_raw.replace(",", "."))
                except ValueError: continue
                if weight < 0: continue
                if is_pan_label(dia_raw): series.append((normalize_pan_label(dia_raw), weight)); continue
                try: diameter = float(dia_raw.replace(",", "."))
                except ValueError: continue
                if diameter > 0: series.append((diameter, weight))
            if series:
                all_series.append(series)
                var = self.type_vars[col_idx] if col_idx < len(self.type_vars) else None
                series_types.append(var.get() if var else "--- Select ---")

        self.app.sample_types = series_types
        return all_series, initial_weight

    def get_calculation_basis(self) -> bool: return self.calc_basis_var.get() == "recovered"

    def validate_data(self) -> bool:
        all_series, initial_weight = self.get_all_series_data()
        if not all_series: self.valid_label.config(text="❌ No valid data found", fg='red'); return False

        # 1. MANDATORY PROVENANCE CHECK & ERROR MESSAGE
        for i, stype in enumerate(getattr(self.app, 'sample_types', [])):
            if stype == "--- Select ---":
                self.valid_label.config(text=f"❌ Please select a Provenance for Sample {i+1}", fg='red')
                messagebox.showwarning("Missing Provenance", f"Please select a Provenance for Sample {i+1} before proceeding.")
                return False

        first_series = all_series[0]
        sieve_entries = [(d, w) for d, w in first_series if not isinstance(d, str)]
        pan_entries = [(d, w) for d, w in first_series if isinstance(d, str)]

        if len(sieve_entries) < 4: self.valid_label.config(text="❌ Need at least 4 sieves (plus the pan) per sample", fg='red'); return False
        diameters = [d for d, _ in sieve_entries]
        if diameters != sorted(diameters, reverse=True): self.valid_label.config(text="❌ Sieves must be in descending order", fg='red'); return False
        if initial_weight <= 0: self.valid_label.config(text="❌ Invalid initial weight", fg='red'); return False
        if len(pan_entries) > 1: self.valid_label.config(text="❌ Only one 'Pan'/'Bottom' row per sample is allowed", fg='red'); return False

        total_weight = sum(w for _, w in first_series)
        recovery_pct = total_weight / initial_weight * 100.0
        loss_pct = 100.0 - recovery_pct

        if abs(loss_pct) > 0.5:
            if loss_pct > 0: self.valid_label.config(text=f"⚠️ Sieving loss {loss_pct:.2f}% > 0.5% (ASTM D6913)", fg='orange')
            else: self.valid_label.config(text=f"⚠️ Total weight > initial by {abs(loss_pct):.2f}%", fg='orange')
        else:
            method = "ASTM (Research)" if self.get_calculation_basis() else "NF/ISO (Geotech)"
            num_samples = len(all_series); pan_note = " · pan ✓" if pan_entries else ""
            self.valid_label.config(text=f"✅ Validated — {method}\n({num_samples} sample{'s' if num_samples > 1 else ''}){pan_note}", fg='green')

        self.app.current_data = first_series
        self.app.multiple_series = all_series[1:] if len(all_series) > 1 else []
        self.app.initial_weight = initial_weight
        self.app.use_recovered_weight = self.get_calculation_basis()
        return True

    def go_to_graph(self, force: bool = False):
        if self.validate_data():
            method = "ASTM (Recovered Weight)" if self.get_calculation_basis() else "NF/ISO (Initial Weight)"
            if force or messagebox.askokcancel("Confirm Calculation", f"Proceed with {method} method?\n\n• Research/Journals: Use ASTM\n• Geotechnical Reports: Use NF/ISO"):
                self.app.show_graph_screen(force=True)

    def save_home_screen(self):
        """Capture the whole Home Screen window (menu bar, data grid and side
        panel) in HD / Full HD / 2K / 4K - much better than a manual screenshot
        (Windows PrintWindow API, Pillow fallback elsewhere)."""
        saved = prompt_export_screen(self.winfo_toplevel(), parent=self,
                                     suggested_name="GranuloGraph_home_screen")
        if saved:
            messagebox.showinfo("Export Successful", f"Home screen image saved to:\n{saved}", parent=self)

    def import_data(self):
        filename = filedialog.askopenfilename(
            title="Select data file",
            filetypes=[("All Supported Files", "*.csv *.xlsx *.xls *.txt"), ("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("Text files", "*.txt"), ("All files", "*.*")])
        if not filename: return
        try:
            df = None
            if filename.endswith('.csv'):
                try: df = pd.read_csv(filename, header=None)
                except:
                    try: df = pd.read_csv(filename, header=None, sep=';', decimal=',', thousands=' ', skipinitialspace=True)
                    except: df = pd.read_csv(filename, header=None, sep='\t')
            elif filename.endswith(('.xlsx', '.xls')): df = pd.read_excel(filename, header=None)
            elif filename.endswith('.txt'):
                try: df = pd.read_csv(filename, header=None, sep='\t')
                except:
                    try: df = pd.read_csv(filename, header=None, sep=';', decimal=',', thousands=' ', skipinitialspace=True)
                    except: df = pd.read_csv(filename, header=None)

            for row in self.data_rows: row['frame'].destroy()
            self.data_rows.clear()
            self.num_columns = max(2, len(df.columns))
            if self.headers_frame: self._update_table_headers(self.headers_frame)

            for i, row in df.iterrows():
                values = []
                for val in row:
                    if pd.isna(val): values.append("")
                    elif isinstance(val, str): values.append(normalize_pan_label(val.strip()))
                    else: values.append(str(val).strip())
                self.add_data_row(i, values)

            if len(df.columns) >= 3:
                try:
                    third = df.iloc[:, 2].dropna().unique()
                    if len(third) == 1 and not is_pan_label(third[0]):
                        self.weight_var.set(str(float(str(third[0]).strip().replace(",", "."))))
                except: pass

            messagebox.showinfo("Success", f"Imported {len(df)} rows from {os.path.basename(filename)}")
        except Exception as e: messagebox.showerror("Import Error", f"Failed to import file: {str(e)}")

    def save_data(self):
        data, initial_weight = self.get_data()
        if not data: messagebox.showwarning("No Data", "No data to save!"); return
        filename = filedialog.asksaveasfilename(title="Save data as", defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])
        if not filename: return
        try:
            basis = "RECOVERED" if self.get_calculation_basis() else "INITIAL"
            def _fmt(v): return v if isinstance(v, str) else (f"{v:.4f}" if abs(v) < 0.01 else f"{v:.2f}")
            if filename.endswith('.csv'):
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Diameter_mm', 'Weight_g', 'Initial_Weight_g', 'Calculation_Basis'])
                    for d, w in data: writer.writerow([_fmt(d), f"{w:.2f}", f"{initial_weight:.2f}", basis])
            else:
                df = pd.DataFrame([(_fmt(d), f"{w:.2f}") for d, w in data], columns=['Diameter_mm', 'Weight_g'])
                df['Initial_Weight_g'] = f"{initial_weight:.2f}"
                df['Calculation_Basis'] = basis
                df.to_excel(filename, index=False)
            messagebox.showinfo("Success", f"Data saved to {os.path.basename(filename)}")
        except Exception as e: messagebox.showerror("Save Error", f"Failed to save file: {str(e)}")
