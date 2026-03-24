#!/usr/bin/env python3
"""
GranuloGraph - Granulometry Analysis Software for Windows
Author: Smaine Chellat
Institution: University Constantine 1, Geological Department, Algeria
Version: 1.0
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.patches as patches
from matplotlib.path import Path
import csv
from typing import List, Tuple, Dict, Optional
import warnings
warnings.filterwarnings('ignore')

# Import custom modules
from home_screen import HomeScreen
from graph_screen import GraphScreen
from settings_screen import SettingsScreen
from calculations import GranuloCalculator
from utils import DataValidator, FileHandler, ConfigManager


class GranuloGraph:
    """Main Application Class"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("GranuloGraph - Granulometry Analysis Software")
        self.root.geometry("1200x800")
        
        # Set application icon (if available)
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass
        
        # Initialize configuration
        self.config = ConfigManager()
        
        # Initialize data storage
        self.current_data = None
        self.multiple_series = []  # ✅ Store additional series
        self.initial_weight = None
        self.use_recovered_weight = True  # ✅ Default to ASTM
        
        # Create menu bar
        self.create_menu()
        
        # Show home screen initially
        self.show_home_screen()
        
        # Center window on screen
        self.center_window()
        
    def create_menu(self):
        """Create application menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Session", command=self.new_session)
        file_menu.add_command(label="Open Data", command=self.open_data_dialog)
        file_menu.add_command(label="Save Data", command=self.save_data_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Export Graph", command=self.export_graph)
        file_menu.add_command(label="Export Results", command=self.export_results)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Home", command=self.show_home_screen)
        view_menu.add_command(label="Graph", command=self.show_graph_screen)
        view_menu.add_command(label="Settings", command=self.show_settings_screen)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Calculate Parameters", command=self.calculate_parameters)
        tools_menu.add_command(label="Compare Series", command=self.compare_series)
        tools_menu.add_separator()
        tools_menu.add_command(label="Preferences", command=self.show_settings_screen)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="Documentation", command=self.show_documentation)
        help_menu.add_command(label="About", command=self.show_about)
        
    def center_window(self):
        """Center window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def show_home_screen(self):
        """Display home screen"""
        self.clear_screen()
        self.home = HomeScreen(self.root, self)
        self.home.pack(fill=tk.BOTH, expand=True)
        
    def show_graph_screen(self):
        """Display graph screen"""
        if self.current_data is None and not self.multiple_series:
            messagebox.showwarning("No Data", "Please enter or load data first!")
            return
        
        # ✅ Retrieve calculation basis from HomeScreen if available
        if hasattr(self, 'home') and self.home:
            self.use_recovered_weight = self.home.get_calculation_basis()
        
        self.clear_screen()
        self.graph = GraphScreen(self.root, self, self.current_data, self.multiple_series)
        self.graph.pack(fill=tk.BOTH, expand=True)
        
    def show_settings_screen(self):
        """Display settings screen"""
        self.clear_screen()
        self.settings = SettingsScreen(self.root, self)
        self.settings.pack(fill=tk.BOTH, expand=True)
        
    def clear_screen(self):
        """Clear current screen"""
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Menu):
                continue
            widget.destroy()
            
    def new_session(self):
        """Start new analysis session"""
        result = messagebox.askyesno("New Session", "Clear all current data?")
        if result:
            self.current_data = None
            self.multiple_series = []
            self.initial_weight = None
            self.use_recovered_weight = True  # Reset to default (ASTM)
            self.show_home_screen()
            
    def open_data_dialog(self):
        """Open file dialog to load data"""
        from tkinter import filedialog
        filename = filedialog.askopenfilename(
            title="Select data file",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx *.xls"),
                      ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            try:
                data, weight = FileHandler.load_data(filename)
                self.current_data = data
                self.initial_weight = weight
                self.use_recovered_weight = True  # Reset to default (ASTM) on new load
                messagebox.showinfo("Success", f"Loaded {len(data)} sieves from {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load file: {str(e)}")
                
    def save_data_dialog(self):
        """Save current data to file"""
        if self.current_data is None:
            messagebox.showwarning("No Data", "No data to save!")
            return
        
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            title="Save data as",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        if filename:
            try:
                FileHandler.save_data(filename, self.current_data, self.initial_weight)
                messagebox.showinfo("Success", f"Data saved to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
                
    def export_graph(self):
        """Export current graph as image"""
        if not hasattr(self, 'graph') or not self.graph:
            messagebox.showwarning("No Graph", "No graph to export!")
            return
        
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            title="Export graph as",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"),
                      ("TIFF files", "*.tiff"), ("PDF files", "*.pdf")]
        )
        if filename:
            try:
                self.graph.export_graph(filename)
                messagebox.showinfo("Success", f"Graph exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
                
    def export_results(self):
        """Export calculation results"""
        if self.current_data is None:
            messagebox.showwarning("No Data", "No results to export!")
            return
        
        from tkinter import filedialog
        filename = filedialog.asksaveasfilename(
            title="Export results as",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        if filename:
            try:
                # Calculate with selected basis
                calculator = GranuloCalculator(
                    self.current_data, 
                    self.initial_weight,
                    use_recovered_weight=self.use_recovered_weight
                )
                results = calculator.get_all_parameters()
                FileHandler.export_results(filename, results)
                messagebox.showinfo("Success", f"Results exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")
                
    def calculate_parameters(self):
        """Calculate and display sedimentological parameters"""
        if self.current_data is None:
            messagebox.showwarning("No Data", "Please enter data first!")
            return
        
        # Calculate with selected basis
        calculator = GranuloCalculator(
            self.current_data, 
            self.initial_weight,
            use_recovered_weight=self.use_recovered_weight
        )
        params = calculator.get_all_parameters()
        
        # Display results in a new window
        self.show_parameters_window(params)
        
    def show_parameters_window(self, params):
        """Display parameters in a new window"""
        window = tk.Toplevel(self.root)
        window.title("Sedimentological Parameters")
        window.geometry("650x550")  # Slightly wider for basis label
        
        # Add calculation basis indicator at top
        basis_text = "🔬 ASTM (Recovered Weight)" if self.use_recovered_weight else "🏗️ NF/ISO (Initial Weight)"
        basis_label = tk.Label(
            window, 
            text=f"📋 Calculation Basis: {basis_text}",
            font=('Arial', 10, 'bold'),
            bg='#e8f4f8',
            fg='#2c3e50',
            pady=5,
            relief=tk.FLAT
        )
        basis_label.pack(fill=tk.X, padx=10)
        
        # Create notebook for tabs
        notebook = ttk.Notebook(window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sedimentological parameters tab
        sed_frame = ttk.Frame(notebook)
        notebook.add(sed_frame, text="Sedimentological")
        
        # Create treeview for parameters
        tree = ttk.Treeview(sed_frame, columns=('Value', 'Classification'), show='tree headings')
        tree.heading('#0', text='Parameter')
        tree.heading('Value', text='Value')
        tree.heading('Classification', text='Classification')
        tree.column('#0', width=200)
        tree.column('Value', width=150)
        tree.column('Classification', width=200)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(sed_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert parameters
        sed_params = ['mode_mm', 'mean_phi', 'median_phi', 'sorting', 'skewness', 'kurtosis']
        sed_labels = ['Mode', 'Graphic Mean', 'Median', 'Sorting (σI)', 'Skewness (Sk)', 'Kurtosis (KG)']
        for param, label in zip(sed_params, sed_labels):
            if param in params:
                value = params[param]
                class_val = params.get(f'{param.replace("_mm", "").replace("_phi", "")}_class', '')
                tree.insert('', tk.END, text=label,
                          values=(f"{value:.3f}" if isinstance(value, (int, float)) else str(value), class_val))
        
        # Geotechnical parameters tab
        geo_frame = ttk.Frame(notebook)
        notebook.add(geo_frame, text="Geotechnical")
        
        geo_tree = ttk.Treeview(geo_frame, columns=('Value', 'Classification'), show='tree headings')
        geo_tree.heading('#0', text='Parameter')
        geo_tree.heading('Value', text='Value')
        geo_tree.heading('Classification', text='Classification')
        
        geo_scrollbar = ttk.Scrollbar(geo_frame, orient=tk.VERTICAL, command=geo_tree.yview)
        geo_tree.configure(yscrollcommand=geo_scrollbar.set)
        
        geo_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        geo_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert geotechnical parameters
        geo_params = ['Cu', 'Cc', 'FM']
        geo_labels = ['Uniformity Coeff. (Cu)', 'Curvature Coeff. (Cc)', 'Fineness Modulus (FM)']
        for param, label in zip(geo_params, geo_labels):
            if param in params:
                value = params[param]
                class_val = params.get(f'{param}_class', '')
                geo_tree.insert('', tk.END, text=label,
                              values=(f"{value:.3f}" if isinstance(value, (int, float)) else str(value), class_val))
        
        # Percentiles tab
        perc_frame = ttk.Frame(notebook)
        notebook.add(perc_frame, text="Percentiles")
        
        perc_tree = ttk.Treeview(perc_frame, columns=('Diameter (mm)', 'Phi (φ)'), show='tree headings')
        perc_tree.heading('#0', text='Percentile')
        perc_tree.heading('Diameter (mm)', text='Diameter (mm)')
        perc_tree.heading('Phi (φ)', text='Phi (φ)')
        
        perc_scrollbar = ttk.Scrollbar(perc_frame, orient=tk.VERTICAL, command=perc_tree.yview)
        perc_tree.configure(yscrollcommand=perc_scrollbar.set)
        
        perc_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        perc_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert percentiles
        percentiles = [5, 10, 16, 25, 30, 50, 60, 70, 75, 84, 90, 95]
        for p in percentiles:
            d_key = f'D{p}'
            phi_key = f'phi{p}'
            if d_key in params and phi_key in params:
                perc_tree.insert('', tk.END, text=f"{p}%",
                               values=(f"{params[d_key]:.4f}", f"{params[phi_key]:.3f}"))
        
        # Add recovery info at bottom
        recovery_frame = tk.Frame(window, bg='#f9f9f9', relief=tk.SUNKEN, bd=1)
        recovery_frame.pack(fill=tk.X, padx=10, pady=5)
        
        recovery_text = (
            f"Initial Weight: {params.get('initial_weight', 0):.3f} g  |  "
            f"Recovered: {params.get('recovered_weight', 0):.3f} g  |  "
            f"Recovery: {params.get('recovery_pct', 0):.1f}%"
        )
        tk.Label(recovery_frame, text=recovery_text, font=('Arial', 9),
                bg='#f9f9f9', fg='#555').pack(pady=3)
        
        if params.get('recovery_warning'):
            tk.Label(recovery_frame, text="⚠️ Low recovery may affect D5/D95 accuracy",
                    font=('Arial', 9, 'italic'), bg='#f9f9f9', fg='#e74c3c').pack()
        
    def compare_series(self):
        """Compare multiple data series"""
        if len(self.multiple_series) < 2:
            messagebox.showwarning("Insufficient Data", "Need at least 2 series to compare!")
            return
        
        self.show_graph_screen()
        
    def show_documentation(self):
        """Show documentation window"""
        window = tk.Toplevel(self.root)
        window.title("Documentation")
        window.geometry("650x450")
        
        text = tk.Text(window, wrap=tk.WORD, padx=10, pady=10, font=('Arial', 10))
        text.pack(fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(window, orient=tk.VERTICAL, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        documentation = """
GRANULOGRAPH - Granulometry Analysis Software
=============================================

Version: 1.0
Author: Smaine Chellat
Institution: University Constantine 1, Geological Department, Algeria

FEATURES:
---------
1. Data Entry: Enter sieve diameters and retained weights
2. Dual Calculation Methods:
   • Recovered Weight (ASTM D6913) - For research & journals
   • Initial Weight (NF P 94-056 / ISO) - For geotechnical reports
3. Statistical Calculations: Folk & Ward (1957) parameters
4. Geotechnical Indices: Cu, Cc, Fineness Modulus
5. Interactive Graphs: Cumulative and frequency curves
6. Export Options: Graphs and results with method metadata

USAGE:
------
1. Enter initial sample weight
2. Enter sieve data (at least 10 rows required)
3. Select calculation basis:
   • 🔬 ASTM: Research, papers, sedimentology stats
   • 🏗️ NF/ISO: Engineering, geotechnical reports
4. Click "Display Graph" to visualize
5. Use cursor to read values from curve
6. Calculate statistical parameters
7. Export results as needed

CALCULATION METHODS:
-------------------
🔬 Recovered Weight (ASTM D6913):
   • Percentages based on total recovered mass
   • Ensures cumulative curve spans exactly 0-100%
   • Recommended for Folk & Ward statistical analysis
   • Standard for international journals

🏗️ Initial Weight (NF P 94-056 / ISO 17892-4):
   • Percentages based on initial dry mass
   • Standard for Algerian/French engineering reports
   • Compatible with local geotechnical standards
   • Use when reporting to engineering bureaus

REFERENCES:
-----------
• Folk, R.L. and Ward, W.C. (1957) - Brazos River bar study
• Wentworth, C.K. (1922) - Grain size classification
• ASTM D6913 - Standard test methods for particle-size analysis
• ISO 17892-4 - Geotechnical investigation and testing
• NF P 94-056 - French standard for soil analysis
• BS EN 12620 - Aggregates for concrete

© 2025 Smaine Chellat, University Constantine 1 - All Rights Reserved
"""
        
        text.insert('1.0', documentation)
        text.config(state=tk.DISABLED)
        
    def show_about(self):
        """Show about window"""
        about_text = """
GranuloGraph v1.0
=================

A comprehensive granulometry analysis application
for sedimentology and engineering geology.

Features:
✓ Sieve analysis calculations
✓ Folk & Ward (1957) statistical parameters
✓ Geotechnical indices (Cu, Cc, FM)
✓ Interactive cumulative and frequency curves
✓ Wentworth grain-size classification
✓ Dual calculation methods (ASTM / NF-ISO)
✓ Export capabilities (CSV, Excel, PNG, PDF)

Created for:
• University Constantine 1
• Geological Department, Algeria
• Sedimentology & Environmental Research Lab

Standards Supported:
• ASTM D6913, D2487, C136
• ISO 17892-4
• NF P 94-056 (French/Algerian)
• BS EN 12620

© 2026 Smaine Chellat All Rights Reserved
"""
        messagebox.showinfo("About GranuloGraph", about_text)
        
    def run(self):
        """Run the application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = GranuloGraph()
    app.run()