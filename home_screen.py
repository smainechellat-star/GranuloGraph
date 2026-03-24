"""
Home Screen Module - Data Entry Interface
Author: Smaine Chellat
Institution: University Constantine 1, Geological Department, Algeria
"""
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from tkinter import filedialog
import os
import csv
from typing import List, Tuple, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Simple Tooltip Class (No external dependencies)
# ═══════════════════════════════════════════════════════════════════════════════

class ToolTip:
    """
    Create a tooltip for a given widget.
    Displays text when mouse hovers over the widget.
    """
    def __init__(self, widget, text: str, delay: int = 500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip = None
        self.id = None
        
        # Bind events
        widget.bind("<Enter>", self._on_enter, "+")
        widget.bind("<Leave>", self._on_leave, "+")
        widget.bind("<ButtonPress>", self._on_leave, "+")
    
    def _on_enter(self, event=None):
        """Schedule tooltip display after delay"""
        self._schedule()
    
    def _on_leave(self, event=None):
        """Hide tooltip immediately"""
        self._unschedule()
        self._hide_tooltip()
    
    def _schedule(self):
        """Schedule tooltip to appear after delay"""
        self._unschedule()
        self.id = self.widget.after(self.delay, self._show_tooltip)
    
    def _unschedule(self):
        """Cancel scheduled tooltip display"""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
    
    def _show_tooltip(self):
        """Create and display the tooltip window"""
        if self.tooltip or not self.text:
            return
        
        # Get widget position
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        # Style the tooltip
        label = tk.Label(
            self.tooltip,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            font=("Arial", 9),
            padx=8,
            pady=4,
            wraplength=280
        )
        label.pack(ipadx=1)
    
    def _hide_tooltip(self):
        """Destroy the tooltip window"""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
    
    def configure(self, text: str):
        """Update tooltip text"""
        self.text = text
        # If tooltip is currently showing, update it
        if self.tooltip:
            self._hide_tooltip()
            self._show_tooltip()


# ═══════════════════════════════════════════════════════════════════════════════
# Main Home Screen Class
# ═══════════════════════════════════════════════════════════════════════════════

class HomeScreen(tk.Frame):
    """Home screen for data entry with calculation basis selection"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.data_rows = []
        self.num_columns = 2  # Default: Diameter and Weight
        self.canvas = None
        self.headers_frame = None  # ✅ Store reference to headers frame
        self.calc_basis_var = tk.StringVar(value="recovered")  # Default: ASTM
        self.basis_tooltip = None
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_frame = tk.Frame(self, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="GranuloGraph - Data Entry",
                             font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white')
        title_label.pack(expand=True)
        
        # Settings button at top right
        settings_btn = tk.Button(title_frame, text="⚙ Settings",
                               command=self.app.show_settings_screen,
                               bg='#34495e', fg='white', font=('Arial', 10))
        settings_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Main content area
        content_frame = tk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # ── Left panel - Input section ────────────────────────────────────────
        left_panel = tk.Frame(content_frame, relief=tk.GROOVE, bd=2)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Initial weight input
        weight_frame = tk.Frame(left_panel, bg='#ecf0f1', height=50)
        weight_frame.pack(fill=tk.X, padx=5, pady=5)
        weight_frame.pack_propagate(False)
        
        tk.Label(weight_frame, text="Initial Sample Weight (g):",
                font=('Arial', 11, 'bold'), bg='#ecf0f1').pack(side=tk.LEFT, padx=5)
        
        self.weight_var = tk.StringVar(value="100.0")
        weight_entry = tk.Entry(weight_frame, textvariable=self.weight_var,
                              font=('Arial', 11), width=15)
        weight_entry.pack(side=tk.LEFT, padx=5)
        tk.Label(weight_frame, text="(g)", font=('Arial', 10), bg='#ecf0f1').pack(side=tk.LEFT)
        
        # ── Calculation Basis Selector ───────────────────────────────────────
        basis_frame = tk.Frame(left_panel, bg='#ecf0f1', height=70)
        basis_frame.pack(fill=tk.X, padx=5, pady=5)
        basis_frame.pack_propagate(False)
        
        tk.Label(basis_frame, text="Calculation Basis:",
                font=('Arial', 11, 'bold'), bg='#ecf0f1').pack(side=tk.LEFT, padx=5)
        
        # Dropdown for calculation method
        self.basis_combo = ttk.Combobox(
            basis_frame,
            textvariable=self.calc_basis_var,
            values=["recovered", "initial"],
            state="readonly",
            width=18,
            font=('Arial', 10)
        )
        self.basis_combo.pack(side=tk.LEFT, padx=5)
        
        # Create tooltip with dynamic content
        self._update_basis_tooltip()
        
        # Labels for each option
        tk.Label(basis_frame, text="▼", font=('Arial', 8), bg='#ecf0f1').pack(side=tk.LEFT)
        
        # Display current selection indicator
        self.basis_indicator = tk.Label(
            basis_frame,
            text="🔬 ASTM (Research)",
            font=('Arial', 9, 'italic'),
            bg='#ecf0f1',
            fg='#27ae60'
        )
        self.basis_indicator.pack(side=tk.LEFT, padx=10)
        
        # Update tooltip and indicator when selection changes
        self.calc_basis_var.trace_add("write", self._on_basis_change)
        
        # ── Data entry table ─────────────────────────────────────────────────
        table_frame = tk.Frame(left_panel)
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Table headers frame ✅ Store reference
        self.headers_frame = tk.Frame(table_frame)
        self.headers_frame.pack(fill=tk.X)
        
        # Create dynamic headers based on number of columns
        self._update_table_headers(self.headers_frame)
        
        # Scrollable table body
        table_container = tk.Frame(table_frame)
        table_container.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(table_container)
        scrollbar = tk.Scrollbar(table_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Mouse wheel binding
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", self._on_mousewheel)
        self.canvas.bind_all("<Button-5>", self._on_mousewheel)
        
        # Create initial 10 rows
        for i in range(10):
            self.add_data_row(i)
        
        # Buttons for table management
        button_frame = tk.Frame(left_panel)
        button_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(button_frame, text="➕ Add Row", command=self.add_row,
                 bg='#27ae60', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="➖ Remove Last Row", command=self.remove_row,
                 bg='#e74c3c', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="➕ Add Column", command=self.add_column,
                 bg='#3498db', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=2)
        tk.Button(button_frame, text="➖ Delete Last Column", command=self.delete_last_column,
                 bg='#9b59b6', fg='white', font=('Arial', 10)).pack(side=tk.LEFT, padx=2)
        
        # ── Right panel - Controls ───────────────────────────────────────────
        right_panel = tk.Frame(content_frame, width=280, relief=tk.GROOVE, bd=2)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_panel.pack_propagate(False)
        
        # File operations
        file_frame = tk.Frame(right_panel, bg='#ecf0f1')
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(file_frame, text="File Operations", font=('Arial', 12, 'bold'),
                bg='#ecf0f1').pack(pady=5)
        
        tk.Button(file_frame, text="📂 Import CSV/Excel", command=self.import_data,
                 bg='#3498db', fg='white', font=('Arial', 10), width=25).pack(pady=2)
        tk.Button(file_frame, text="💾 Save as CSV", command=self.save_data,
                 bg='#f39c12', fg='white', font=('Arial', 10), width=25).pack(pady=2)
        
        # Calculation Basis Info Box
        info_frame = tk.Frame(right_panel, bg='#fffacd', relief=tk.SOLID, bd=1)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(info_frame, text="📋 Calculation Methods",
                font=('Arial', 10, 'bold'), bg='#fffacd', fg='#2c3e50').pack(pady=3)
        
        info_text = (
            "🔬 Recovered Weight (ASTM):\n"
            "   • Research & Journals\n"
            "   • Folk & Ward statistics\n"
            "   • Ensures 0–100% curve\n\n"
            "🏗️ Initial Weight (NF/ISO):\n"
            "   • Geotechnical reports\n"
            "   • Algerian/French standards\n"
            "   • Engineering projects"
        )
        tk.Label(info_frame, text=info_text, justify=tk.LEFT,
                font=('Arial', 8), bg='#fffacd', fg='#34495e').pack(padx=8, pady=2)
        
        # Validation section
        valid_frame = tk.Frame(right_panel, bg='#ecf0f1')
        valid_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(valid_frame, text="Validation", font=('Arial', 12, 'bold'),
                bg='#ecf0f1').pack(pady=5)
        
        self.valid_label = tk.Label(valid_frame, text="⏳ Ready to validate",
                                   font=('Arial', 10), bg='#ecf0f1')
        self.valid_label.pack(pady=2)
        
        tk.Button(valid_frame, text="✓ Validate Data", command=self.validate_data,
                 bg='#27ae60', fg='white', font=('Arial', 10), width=25).pack(pady=2)
        
        # Graph button
        tk.Button(right_panel, text="📊 Display Graph", command=self.go_to_graph,
                 bg='#8e44ad', fg='white', font=('Arial', 12, 'bold'), height=2).pack(
                 fill=tk.X, padx=5, pady=10)
        
        # Help text
        help_frame = tk.Frame(right_panel, bg='#ecf0f1')
        help_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        help_text = """
Instructions:
• Enter at least 10 rows of data
• Sieve diameters in descending order
• Use comma (,) or point (.) for decimals
• Select calculation basis before plotting
• Import CSV format: diameter,weight
• European CSV: diameter;weight (e.g., 31,5;600,10)
• Multi-column CSV: diameter,weight,extra_column
"""
        tk.Label(help_frame, text=help_text, justify=tk.LEFT,
                font=('Arial', 9), bg='#ecf0f1').pack(padx=5, pady=5)
    
    def _update_table_headers(self, parent):
        """Update table headers based on number of columns"""
        # Clear existing headers
        for widget in parent.winfo_children():
            widget.destroy()
        
        # Create headers
        for i in range(self.num_columns):
            if i == 0:
                header_text = "Sieve Diameter (mm)"
                width = 20
            elif i == 1:
                header_text = "Retained Weight (g)"
                width = 20
            else:
                header_text = f"Column {i+1}"
                width = 15
            
            label = tk.Label(parent, text=header_text, width=width, bg='#3498db',
                            fg='white', font=('Arial', 10, 'bold'))
            label.pack(side=tk.LEFT, padx=1)
    
    def _on_basis_change(self, *args):
        """Update tooltip and indicator when basis selection changes"""
        self._update_basis_tooltip()
        
        # Update indicator label
        if self.calc_basis_var.get() == "recovered":
            self.basis_indicator.config(text="🔬 ASTM (Research)", fg='#27ae60')
        else:
            self.basis_indicator.config(text="🏗️ NF/ISO (Geotechnical)", fg='#e67e22')
    
    def _update_basis_tooltip(self):
        """Create/update tooltip with correct content for selected option"""
        if self.calc_basis_var.get() == "recovered":
            tooltip_text = (
                "🔬 Recovered Weight (ASTM D6913)\n\n"
                "• For: Research, Papers, Sedimentology Stats\n"
                "• Percentages based on total recovered mass\n"
                "• Ensures cumulative curve spans 0–100%\n"
                "• Recommended for Folk & Ward statistics\n"
                "• Use when submitting to international journals"
            )
        else:
            tooltip_text = (
                "🏗️ Initial Weight (NF P 94-056 / ISO 17892-4)\n\n"
                "• For: Engineering, Geotechnical Reports\n"
                "• Percentages based on initial dry mass\n"
                "• Standard for Algerian/French standards\n"
                "• Use for local bureau submissions\n"
                "• Compatible with NF P 94-056 requirements"
            )
        
        # Destroy old tooltip and create new one
        if self.basis_tooltip:
            self.basis_tooltip.configure(tooltip_text)
        else:
            self.basis_tooltip = ToolTip(self.basis_combo, tooltip_text)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        if self.canvas is None:
            return
        try:
            if event.num == 5 or event.delta == -120:
                self.canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta == 120:
                self.canvas.yview_scroll(-1, "units")
        except tk.TclError:
            try:
                self.canvas.unbind_all("<MouseWheel>")
                self.canvas.unbind_all("<Button-4>")
                self.canvas.unbind_all("<Button-5>")
            except:
                pass
    
    def destroy(self):
        """Clean up mouse wheel bindings when screen is destroyed"""
        try:
            if self.canvas:
                self.canvas.unbind_all("<MouseWheel>")
                self.canvas.unbind_all("<Button-4>")
                self.canvas.unbind_all("<Button-5>")
            if self.headers_frame:
                for widget in self.headers_frame.winfo_children():
                    widget.destroy()
        except:
            pass
        super().destroy()
    
    def add_data_row(self, row_num: int, values: List[str] = None):
        """Add a new data entry row"""
        row_frame = tk.Frame(self.scrollable_frame)
        row_frame.pack(fill=tk.X, pady=1)
        
        if values is None:
            values = [""] * self.num_columns
        
        # Create entry widgets for each column
        entry_vars = []
        for i in range(max(self.num_columns, len(values))):  # ✅ Handle imported columns
            var = tk.StringVar(value=values[i] if i < len(values) else "")
            entry = tk.Entry(row_frame, textvariable=var, width=20 if i < 2 else 15)
            entry.pack(side=tk.LEFT, padx=1)
            entry_vars.append(var)
        
        # Delete button
        del_btn = tk.Button(row_frame, text="✖", command=lambda: self.delete_row(row_frame),
                           bg='#e74c3c', fg='white', width=2)
        del_btn.pack(side=tk.LEFT, padx=1)
        
        # Store references
        self.data_rows.append({
            'frame': row_frame,
            'entry_vars': entry_vars
        })
    
    def add_row(self):
        """Add a new empty row"""
        self.add_data_row(len(self.data_rows))
    
    def remove_row(self):
        """Remove the last row"""
        if len(self.data_rows) > 10:
            row = self.data_rows.pop()
            row['frame'].destroy()
        else:
            messagebox.showwarning("Cannot Remove", "Minimum 10 rows required!")
    
    def delete_row(self, row_frame):
        """Delete a specific row"""
        if len(self.data_rows) <= 10:
            messagebox.showwarning("Cannot Delete", "Minimum 10 rows required!")
            return
        for i, row in enumerate(self.data_rows):
            if row['frame'] == row_frame:
                self.data_rows.pop(i)
                row_frame.destroy()
                break
    
    def add_column(self):
        """Add a new column to the table"""
        self.num_columns += 1
        
        # Update headers ✅ Using stored reference
        if self.headers_frame:
            self._update_table_headers(self.headers_frame)
        
        # Add entry widget to each existing row
        for row in self.data_rows:
            var = tk.StringVar(value="")
            entry = tk.Entry(row['frame'], textvariable=var, width=15)
            entry.pack(side=tk.LEFT, padx=1)
            row['entry_vars'].append(var)
        
        messagebox.showinfo("Column Added", f"Column {self.num_columns} added successfully!")
    
    def delete_last_column(self):
        """Delete the last column from the table"""
        if self.num_columns <= 2:
            messagebox.showwarning("Cannot Delete", "Minimum 2 columns required (Diameter and Weight)!")
            return
        
        # Remove last entry from each row
        for row in self.data_rows:
            if len(row['entry_vars']) > 0:
                row['entry_vars'].pop()
                # Destroy the last widget (should be the entry)
                widgets = row['frame'].winfo_children()
                if len(widgets) > 1:  # Keep the delete button
                    widgets[-2].destroy()  # Second to last is the entry
        
        self.num_columns -= 1
        
        # Update headers ✅ Using stored reference
        if self.headers_frame:
            self._update_table_headers(self.headers_frame)
        
        messagebox.showinfo("Column Deleted", f"Column {self.num_columns + 1} deleted successfully!")
    
    def get_data(self) -> Tuple[List[Tuple[float, float]], float]:
        """Get data from entry fields (first 2 columns only - for backward compatibility)"""
        all_series, initial_weight = self.get_all_series_data()
        if all_series:
            return all_series[0], initial_weight  # Return first series
        return [], initial_weight
    
    def get_all_series_data(self) -> Tuple[List[List[Tuple[float, float]]], float]:
        """
        Get data from ALL columns as multiple series
        Returns: (list of series, initial_weight)
        Each series is a list of (diameter, weight) tuples
        """
        if not self.data_rows:
            return [], 100.0
        
        # Get initial weight
        try:
            initial_weight = float(self.weight_var.get().replace(',', '.'))
        except ValueError:
            initial_weight = 100.0
        
        # Determine number of data columns (excluding diameter column)
        num_data_cols = self.num_columns - 1  # First column is diameter
        
        if num_data_cols < 1:
            return [], initial_weight
        
        # Extract series for each data column
        all_series = []
        
        for col_idx in range(1, self.num_columns):  # Skip column 0 (diameter)
            series = []
            for row in self.data_rows:
                if len(row['entry_vars']) > col_idx:
                    dia_str = row['entry_vars'][0].get().strip()  # Diameter from column 0
                    wt_str = row['entry_vars'][col_idx].get().strip()  # Weight from column col_idx
                    
                    if not dia_str or not wt_str:
                        continue
                    
                    dia_str = dia_str.replace(',', '.')
                    wt_str = wt_str.replace(',', '.')
                    
                    try:
                        diameter = float(dia_str)
                        weight = float(wt_str)
                        if diameter > 0 and weight >= 0:
                            series.append((diameter, weight))
                    except ValueError:
                        continue
            
            # Only add non-empty series
            if series:
                all_series.append(series)
        
        return all_series, initial_weight
    
    def get_calculation_basis(self) -> bool:
        """
        Get the selected calculation basis.
        Returns True for recovered weight (ASTM), False for initial weight (NF/ISO).
        """
        return self.calc_basis_var.get() == "recovered"
    
    def validate_data(self) -> bool:
        """Validate entered data and extract all series"""
        # Get ALL series from home screen
        all_series, initial_weight = self.get_all_series_data()
        
        if not all_series:
            self.valid_label.config(text="❌ No valid data found", fg='red')
            return False
        
        # Use first series for validation
        first_series = all_series[0]
        
        if len(first_series) < 10:
            self.valid_label.config(text="❌ Need at least 10 rows of data", fg='red')
            return False
        
        diameters = [d for d, _ in first_series]
        if diameters != sorted(diameters, reverse=True):
            self.valid_label.config(text="❌ Sieves must be in descending order", fg='red')
            return False
        
        if initial_weight <= 0:
            self.valid_label.config(text="❌ Invalid initial weight", fg='red')
            return False
        
        total_weight = sum(w for _, w in first_series)
        recovery_pct = (total_weight / initial_weight) * 100 if initial_weight > 0 else 0
        
        if total_weight > initial_weight * 1.05:
            self.valid_label.config(text="⚠️ Total > initial weight (possible error)", fg='orange')
        elif recovery_pct < 90:
            basis = "Recovered" if self.get_calculation_basis() else "Initial"
            self.valid_label.config(
                text=f"⚠️ Low recovery ({recovery_pct:.1f}%) - {basis} method",
                fg='orange'
            )
        else:
            method = "ASTM (Research)" if self.get_calculation_basis() else "NF/ISO (Geotech)"
            num_samples = len(all_series)
            self.valid_label.config(
                text=f"✅ Validated - {method} ({num_samples} sample{'s' if num_samples > 1 else ''})",
                fg='green'
            )
        
        # Store ALL series in app
        self.app.current_data = first_series  # Keep first series for backward compatibility
        self.app.multiple_series = all_series[1:] if len(all_series) > 1 else []  # Additional series
        self.app.initial_weight = initial_weight
        self.app.use_recovered_weight = self.get_calculation_basis()
        
        return True
    
    def go_to_graph(self):
        """Navigate to graph screen"""
        if self.validate_data():
            method = "ASTM (Recovered Weight)" if self.get_calculation_basis() else "NF/ISO (Initial Weight)"
            if messagebox.askokcancel(
                "Confirm Calculation",
                f"Proceed with {method} method?\n\n"
                f"• Research/Journals: Use ASTM\n"
                f"• Geotechnical Reports: Use NF/ISO"
            ):
                self.app.show_graph_screen()
    
    def import_data(self):
        """Import data from CSV/Excel file with support for European format and multi-column"""
        filename = filedialog.askopenfilename(
            title="Select data file",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"),
                      ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if not filename:
            return
        try:
            # Try different formats
            df = None
            format_used = ""
            
            if filename.endswith('.csv'):
                # Try standard CSV first (comma delimiter)
                try:
                    df = pd.read_csv(filename, header=None)
                    format_used = "Standard CSV (comma delimiter)"
                except:
                    # Try European format (semicolon delimiter, comma decimal)
                    try:
                        df = pd.read_csv(filename, header=None, sep=';', decimal=',', thousands=' ', skipinitialspace=True)
                        format_used = "European CSV (semicolon delimiter, comma decimal)"
                    except:
                        # Try tab-separated
                        df = pd.read_csv(filename, header=None, sep='\t')
                        format_used = "Tab-separated CSV"
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(filename, header=None)
                format_used = "Excel file"
            else:
                # Try auto-detect for .txt files
                try:
                    df = pd.read_csv(filename, header=None, sep=';', decimal=',', thousands=' ', skipinitialspace=True)
                    format_used = "European format"
                except:
                    df = pd.read_csv(filename, header=None, sep='\t')
                    format_used = "Tab-separated format"
            
            print(f"✓ Imported using: {format_used}")
            print(f"✓ Detected {len(df.columns)} columns and {len(df)} rows")
            
            # Clear existing rows
            for row in self.data_rows:
                row['frame'].destroy()
            self.data_rows.clear()
            
            # ✅ FIX: Update num_columns based on imported data (minimum 2)
            self.num_columns = max(2, len(df.columns))
            
            # ✅ Update headers using stored reference
            if self.headers_frame:
                self._update_table_headers(self.headers_frame)
            
            # Add new rows from file
            for i, row in df.iterrows():
                values = [str(val).strip() if pd.notna(val) else "" for val in row]
                self.add_data_row(i, values)
            
            # Try to read initial weight from third column if available
            if len(df.columns) >= 3:
                try:
                    # Check if all values in column 3 are the same (likely initial weight)
                    third_col_values = df.iloc[:, 2].dropna().unique()
                    if len(third_col_values) == 1:
                        weight_str = str(third_col_values[0]).strip().replace(',', '.')
                        weight = float(weight_str)
                        self.weight_var.set(str(weight))
                        print(f"✓ Extracted initial weight: {weight} g from column 3")
                except Exception as e:
                    print(f"Note: Could not extract initial weight from column 3: {e}")
            
            messagebox.showinfo("Success", f"Imported {len(df)} rows from {os.path.basename(filename)}\nFormat: {format_used}\nColumns: {self.num_columns}")
            
        except Exception as e:
            messagebox.showerror(
                "Import Error", 
                f"Failed to import file: {str(e)}\n\n"
                f"Supported formats:\n"
                f"• 2 columns: diameter,weight (e.g., 2.0,3.0)\n"
                f"• 3+ columns: diameter,weight,extra (e.g., 2.0,3.0,100.0)\n"
                f"• European CSV: diameter;weight (e.g., 31,5;600,10)\n"
                f"• Excel: .xlsx, .xls"
            )
    
    def save_data(self):
        """Save data to CSV file"""
        data, initial_weight = self.get_data()
        
        if not data:
            messagebox.showwarning("No Data", "No data to save!")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save data as",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        if not filename:
            return
        try:
            if filename.endswith('.csv'):
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Diameter_mm', 'Weight_g', 'Initial_Weight_g', 'Calculation_Basis'])
                    basis = "RECOVERED" if self.get_calculation_basis() else "INITIAL"
                    for d, w in data:
                        writer.writerow([d, w, initial_weight, basis])
            else:
                df = pd.DataFrame(data, columns=['Diameter_mm', 'Weight_g'])
                df['Initial_Weight_g'] = initial_weight
                df['Calculation_Basis'] = "RECOVERED" if self.get_calculation_basis() else "INITIAL"
                df.to_excel(filename, index=False)
            
            messagebox.showinfo("Success", f"Data saved to {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save file: {str(e)}")