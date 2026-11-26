#!/usr/bin/env python3
"""
GranuloGraph - Granulometry Analysis Software for Windows
"""
import sys
import os
import warnings
warnings.filterwarnings('ignore')
sys.setrecursionlimit(10000)

def resource_path(relative_path):
    try: base_path = sys._MEIPASS
    except AttributeError: base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.patches as patches
from matplotlib.path import Path

import csv
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import List, Tuple, Dict, Optional

import numpy as np
import pandas as pd

try:
    from home_screen import HomeScreen
    from graph_screen import GraphScreen
    from calculations import GranuloCalculator
    from utils import (DataValidator, FileHandler, ConfigManager,
                       UnitConverter, StatisticsHelper, ReportGenerator)
except ImportError as e:
    print(f"Error importing custom modules: {e}")
    sys.exit(1)

# Unified export engine: every format (PNG/JPEG/TIFF/WebP/GIF/PDF/SVG/EPS/AI/
# DXF/DWG/CRD/CDR/WP/WPG) and every resolution (96-600 DPI, HD -> 4K UHD).
try:
    import export_utils
except ImportError as e:
    print(f"Error importing export_utils.py (unified export engine): {e}\n"
          f"Place export_utils.py next to main.py.")
    sys.exit(1)

# settings_screen.py is optional: the menu degrades gracefully when it is absent
try:
    from settings_screen import SettingsScreen
except ImportError:
    SettingsScreen = None


class GranuloGraph:
    def __init__(self):
        sys.excepthook = self.global_exception_handler
        self.root = tk.Tk()
        self.root.title("GranuloGraph - Granulometry Analysis Software")
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        win_width = min(1200, int(screen_width * 0.90))
        win_height = min(800, int(screen_height * 0.90))
        self.root.geometry(f"{win_width}x{win_height}")
        self.root.minsize(1024, 700)
        
        try:
            icon_path = resource_path('icon.ico')
            if os.path.exists(icon_path): self.root.iconbitmap(default=icon_path)
        except Exception: pass
            
        self.config = ConfigManager()
        self.current_data = None
        self.multiple_series = []
        self.initial_weight = None
        # Default calculation basis from preferences (RECOVERED = ASTM, INITIAL = NF/ISO)
        self.use_recovered_weight = self.config.get_calculation_basis() != 'INITIAL'
        self.sample_types = []
        
        self.create_menu()
        self.show_home_screen()
        self.center_window()
    
    def global_exception_handler(self, exc_type, exc_value, exc_traceback):
        import traceback
        error_msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        try: messagebox.showerror("Critical Error", f"An unexpected error occurred:\n\n{exc_value}\n\nDetails logged to error.log")
        except: pass
        try:
            with open('error.log', 'w') as f: f.write(error_msg)
        except: pass
        sys.exit(1)
    
    def create_menu(self):
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Session", command=self.new_session)
        file_menu.add_command(label="Open Data", command=self.open_data_dialog)
        file_menu.add_command(label="Save Data", command=self.save_data_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Export Graph", command=self.export_graph)
        file_menu.add_command(label="Export Results", command=self.export_results)
        file_menu.add_command(label="Export Text Report", command=self.export_text_report)
        file_menu.add_separator()
        file_menu.add_command(label="Save Current Screen (HD/4K)", command=self.save_current_screen)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Home", command=self.show_home_screen)
        view_menu.add_command(label="Graph", command=self.show_graph_screen)
        view_menu.add_command(label="Settings", command=self.show_settings_screen)
        
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Calculate Parameters", command=self.calculate_parameters)
        tools_menu.add_command(label="Compare Series", command=self.compare_series)
        tools_menu.add_separator()
        tools_menu.add_command(label="Preferences", command=self.show_settings_screen)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def show_home_screen(self):
        self.clear_screen()
        self.home = HomeScreen(self.root, self)
        self.home.pack(fill=tk.BOTH, expand=True)
    
    def show_graph_screen(self, force=False):
        # PREVENTS BYPASSING VALIDATION FROM THE MENU
        if not force and hasattr(self, 'home') and self.home.winfo_exists():
            self.home.go_to_graph()
            return
            
        if self.current_data is None and not self.multiple_series:
            messagebox.showwarning("No Data", "Please enter or load data first!")
            return
        if hasattr(self, 'home') and self.home:
            self.use_recovered_weight = self.home.get_calculation_basis()
        self.clear_screen()
        self.graph = GraphScreen(self.root, self, self.current_data, self.multiple_series)
        self.graph.pack(fill=tk.BOTH, expand=True)
    
    def show_settings_screen(self):
        if SettingsScreen is None:
            messagebox.showinfo("Settings", "settings_screen.py is not present in this installation - the preferences screen is unavailable.\nDefaults can still be edited in granulograph_config.json.")
            return
        self.clear_screen()
        self.settings = SettingsScreen(self.root, self)
        self.settings.pack(fill=tk.BOTH, expand=True)
    
    def clear_screen(self):
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Menu): continue
            widget.destroy()
    
    def new_session(self):
        if messagebox.askyesno("New Session", "Clear all current data?"):
            self.current_data = None
            self.multiple_series = []
            self.initial_weight = None
            self.use_recovered_weight = self.config.get_calculation_basis() != 'INITIAL'
            self.sample_types = []
            self.show_home_screen()
    
    def open_data_dialog(self):
        filename = filedialog.askopenfilename(
            title="Select data file",
            filetypes=[("All Supported Files", "*.csv *.xlsx *.xls *.txt *.grl"), ("GranuloGraph Data Files", "*.grl"), ("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"), ("Text files", "*.txt"), ("All files", "*.*")])
        if filename:
            try:
                # utils.FileHandler.load_data returns (data, initial_weight, calculation_basis)
                if filename.lower().endswith('.grl'):
                    data, weight, basis = FileHandler.load_csv(filename)  # .grl = GranuloGraph data file (text/CSV format)
                else:
                    data, weight, basis = FileHandler.load_data(filename)
                self.current_data = data
                self.initial_weight = weight
                self.use_recovered_weight = (basis != 'INITIAL')
                basis_label = ("ASTM D6913 (Recovered Weight)" if self.use_recovered_weight
                               else "NF P94-056 / ISO 17892-4 (Initial Weight)")
                messagebox.showinfo("Success", f"Loaded {len(data)} sieves from {os.path.basename(filename)}\n\nCalculation basis read from file: {basis_label}")
            except Exception as e: messagebox.showerror("Error", f"Failed to load file: {str(e)}")
    
    def save_data_dialog(self):
        if self.current_data is None: messagebox.showwarning("No Data", "No data to save!"); return
        filename = filedialog.asksaveasfilename(title="Save data as", defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])
        if filename:
            try:
                basis = "RECOVERED" if self.use_recovered_weight else "INITIAL"
                if self.initial_weight is None:
                    self.initial_weight = float(self.config.get('analysis.default_initial_weight', 100.0))
                # utils.FileHandler API: save_csv / save_excel carry the calculation-basis metadata
                if filename.lower().endswith('.xlsx'):
                    FileHandler.save_excel(filename, self.current_data, self.initial_weight, calculation_basis=basis)
                else:
                    FileHandler.save_csv(filename, self.current_data, self.initial_weight, calculation_basis=basis)
                messagebox.showinfo("Success", f"Data saved to {filename}\nCalculation basis: {basis}")
            except Exception as e: messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def export_text_report(self):
        """Save a formatted plain-text analysis report (utils.ReportGenerator)."""
        if self.current_data is None: messagebox.showwarning("No Data", "Please load or enter data first!"); return
        filename = filedialog.asksaveasfilename(title="Save text report as", defaultextension=".txt", filetypes=[("Text files", "*.txt")])
        if not filename: return
        try:
            calculator = GranuloCalculator(self.current_data, self.initial_weight, use_recovered_weight=self.use_recovered_weight)
            results = calculator.get_all_parameters()
            basis = "RECOVERED" if self.use_recovered_weight else "INITIAL"
            ReportGenerator.save_text_report(filename, results, calculation_basis=basis)
            messagebox.showinfo("Success", f"Text report saved to {filename}")
        except Exception as e: messagebox.showerror("Error", f"Failed to export report: {str(e)}")

    def save_current_screen(self):
        """Capture the whole application window (menu bar + current screen) in
        HD / Full HD / 2K / 4K - better than a manual screenshot (Windows
        PrintWindow API, Pillow fallback elsewhere)."""
        try:
            saved = export_utils.prompt_export_screen(self.root, parent=self.root,
                                                      suggested_name="GranuloGraph_screen")
            if saved:
                messagebox.showinfo("Success", f"Screen image saved to {saved}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to capture screen: {str(e)}")

    def export_graph(self):
        """Export the main graph through the unified export engine: every
        format (PNG/JPEG/TIFF/WebP/GIF/PDF/SVG/EPS/AI/DXF/DWG/CRD/CDR/WP/WPG)
        and every resolution (96-600 DPI, HD -> 4K UHD)."""
        if not hasattr(self, 'graph') or not self.graph: messagebox.showwarning("No Graph", "No graph to export!"); return
        saved = export_utils.prompt_export_figure(self.graph.fig, parent=self.root,
                                                  suggested_name="GranuloGraph_main_graph")
        if saved:
            messagebox.showinfo("Success", f"Graph exported to {saved}")
    
    def export_results(self):
        if self.current_data is None: messagebox.showwarning("No Data", "No results to export!"); return
        filename = filedialog.asksaveasfilename(title="Export results as", defaultextension=".csv", filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")])
        if filename:
            try:
                calculator = GranuloCalculator(self.current_data, self.initial_weight, use_recovered_weight=self.use_recovered_weight)
                results = calculator.get_all_parameters()
                basis = "RECOVERED" if self.use_recovered_weight else "INITIAL"
                FileHandler.export_results(filename, results, calculation_basis=basis)
                messagebox.showinfo("Success", f"Results exported to {filename}")
            except Exception as e: messagebox.showerror("Error", f"Failed to export: {str(e)}")
    
    def calculate_parameters(self):
        if self.current_data is None: messagebox.showwarning("No Data", "Please enter data first!"); return
        calculator = GranuloCalculator(self.current_data, self.initial_weight, use_recovered_weight=self.use_recovered_weight)
        params = calculator.get_all_parameters()
        self.show_parameters_window(params)
    
    def show_parameters_window(self, params):
        window = tk.Toplevel(self.root)
        window.title("Sedimentological Parameters")
        window.geometry("650x550")
        basis_text = "🔬 ASTM (Recovered Weight)" if self.use_recovered_weight else "🏗️ NF/ISO (Initial Weight)"
        tk.Label(window, text=f"📋 Calculation Basis: {basis_text}", font=('Arial', 10, 'bold'), bg='#e8f4f8', fg='#2c3e50', pady=5, relief=tk.FLAT).pack(fill=tk.X, padx=10)
        notebook = ttk.Notebook(window); notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        sed_frame = ttk.Frame(notebook); notebook.add(sed_frame, text="Sedimentological")
        tree = ttk.Treeview(sed_frame, columns=('Value', 'Classification'), show='tree headings')
        tree.heading('#0', text='Parameter'); tree.heading('Value', text='Value'); tree.heading('Classification', text='Classification')
        tree.column('#0', width=200); tree.column('Value', width=150); tree.column('Classification', width=200)
        scrollbar = ttk.Scrollbar(sed_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        for param, label in zip(['mode_mm', 'mean_phi', 'median_phi', 'sorting', 'skewness', 'kurtosis'], ['Mode', 'Graphic Mean', 'Median', 'Sorting (σI)', 'Skewness (Sk)', 'Kurtosis (KG)']):
            if param in params:
                value = params[param]
                class_val = params.get(f'{param.replace("_mm", "").replace("_phi", "")}_class', '')
                tree.insert('', tk.END, text=label, values=(f"{value:.3f}" if isinstance(value, (int, float)) else str(value), class_val))
        
        geo_frame = ttk.Frame(notebook); notebook.add(geo_frame, text="Geotechnical")
        geo_tree = ttk.Treeview(geo_frame, columns=('Value', 'Classification'), show='tree headings')
        geo_tree.heading('#0', text='Parameter'); geo_tree.heading('Value', text='Value'); geo_tree.heading('Classification', text='Classification')
        geo_scrollbar = ttk.Scrollbar(geo_frame, orient=tk.VERTICAL, command=geo_tree.yview)
        geo_tree.configure(yscrollcommand=geo_scrollbar.set)
        geo_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); geo_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        for param, label in zip(['Cu', 'Cc', 'FM'], ['Uniformity Coeff. (Cu)', 'Curvature Coeff. (Cc)', 'Fineness Modulus (FM)']):
            if param in params:
                value = params[param]
                class_val = params.get(f'{param}_class', '')
                geo_tree.insert('', tk.END, text=label, values=(f"{value:.3f}" if isinstance(value, (int, float)) else str(value), class_val))
        
        perc_frame = ttk.Frame(notebook); notebook.add(perc_frame, text="Percentiles")
        perc_tree = ttk.Treeview(perc_frame, columns=('Diameter (mm)', 'Phi (φ)'), show='tree headings')
        perc_tree.heading('#0', text='Percentile'); perc_tree.heading('Diameter (mm)', text='Diameter (mm)'); perc_tree.heading('Phi (φ)', text='Phi (φ)')
        perc_scrollbar = ttk.Scrollbar(perc_frame, orient=tk.VERTICAL, command=perc_tree.yview)
        perc_tree.configure(yscrollcommand=perc_scrollbar.set)
        perc_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); perc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        for p in [5, 10, 16, 25, 30, 50, 60, 70, 75, 84, 90, 95]:
            d_key, phi_key = f'D{p}', f'phi{p}'
            if d_key in params and phi_key in params:
                perc_tree.insert('', tk.END, text=f"{p}%", values=(f"{params[d_key]:.4f}", f"{params[phi_key]:.3f}"))
        
        recovery_frame = tk.Frame(window, bg='#f9f9f9', relief=tk.SUNKEN, bd=1); recovery_frame.pack(fill=tk.X, padx=10, pady=5)
        recovery_text = f"Initial Weight: {params.get('initial_weight', 0):.3f} g  |  Recovered: {params.get('recovered_weight', 0):.3f} g  |  Recovery: {params.get('recovery_pct', 0):.1f}%"
        tk.Label(recovery_frame, text=recovery_text, font=('Arial', 9), bg='#f9f9f9', fg='#555').pack(pady=3)
        if params.get('recovery_warning'):
            tk.Label(recovery_frame, text="⚠️ Sieving loss exceeds 0.5% (ASTM D6913 limit)", font=('Arial', 9, 'italic'), bg='#f9f9f9', fg='#e74c3c').pack()
    
    def compare_series(self):
        if len(self.multiple_series) < 2: messagebox.showwarning("Insufficient Data", "Need at least 2 series to compare!"); return
        self.show_graph_screen()
    
    def show_documentation(self):
        window = tk.Toplevel(self.root); window.title("Documentation"); window.geometry("650x450")
        text = tk.Text(window, wrap=tk.WORD, padx=10, pady=10, font=('Arial', 10))
        scrollbar = ttk.Scrollbar(window, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True); scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        documentation = ("GRANULOGRAPH - Granulometry Analysis Software\n"
                         "Version: 3.0\n\n"
                         "Author: Smaine Chellat\n"
                         "Institution: University Constantine 1 - Geological Department, Algeria\n"
                         "Email: smaine.chellat@gmail.com\n"
                         "ORCID: 0000-0003-4103-0436\n\n"
                         "Standards: ASTM D6913 / NF P94-056 / ISO 17892-4 / ISO 14688-1:2017\n"
                         "Statistics: Folk & Ward (1957)\n\n"
                         "Full documentation: see README.md installed with the application.\n\n"
                         "DOI: https://doi.org/10.5281/zenodo.24550453\n\n"
                         "Released under the MIT License - see LICENSE.txt")
        text.insert('1.0', documentation); text.config(state=tk.DISABLED)
    
    def show_about(self):
        messagebox.showinfo("About GranuloGraph",
                            "GranuloGraph v3.0\n\n"
                            "A comprehensive granulometry analysis application\n"
                            "for sedimentology and engineering geology.\n\n"
                            "Author: Smaine Chellat - University Constantine 1\n"
                            "DOI: https://doi.org/10.5281/zenodo.24550453\n\n"
                            "Released under the MIT License (see LICENSE.txt)")
    
    def run(self):
        try: self.root.mainloop()
        except Exception as e:
            messagebox.showerror("Fatal Error", f"Application crashed: {str(e)}")
            raise

if __name__ == "__main__":
    try:
        app = GranuloGraph()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
