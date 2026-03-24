"""
Graph Screen Module - Visualization and Analysis
Complete implementation with ISO 14688-1:2017 classification
Author: Smaine Chellat
Institution: University Constantine 1, Geological Department, Algeria
"""
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
from typing import List, Tuple, Dict, Optional
import math
from scipy import interpolate
from calculations import GranuloCalculator
import csv


class GraphScreen(tk.Frame):
    """Graph screen for data visualization and analysis"""
    
    def __init__(self, parent, app, data=None, multiple_series=None):
        super().__init__(parent)
        self.parent = parent
        self.app = app
        self.data = data
        self.multiple_series = multiple_series or []
        
        # Graph state
        self.show_frequency = False
        self.current_cursor_x = None
        self.current_cursor_y = None
        self.current_series_index = 0
        self.freq_ax = None
        self.last_correlation_fig = None  # Store last correlation figure for export
        
        # Color palette for multiple series
        self.colors = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12',
                      '#9b59b6', '#1abc9c', '#e67e22', '#34495e']
        
        # ISO 14688-1:2017 grain size classification boundaries
        self.iso_boundaries = [
            0.002, 0.0063, 0.02, 0.063, 0.2, 0.63,
            2.0, 6.3, 20.0, 63.0, 200.0, 630.0
        ]
        
        self.setup_ui()
        if self.data or self.multiple_series:
            self.plot_data()
    
    def setup_ui(self):
        """Setup the complete user interface"""
        # Top toolbar
        toolbar = tk.Frame(self, bg='#2c3e50', height=40)
        toolbar.pack(fill=tk.X)
        
        tk.Button(toolbar, text="🏠 Home", command=self.app.show_home_screen,
                 bg='#34495e', fg='white', font=('Arial', 10), padx=10).pack(side=tk.LEFT, padx=5, pady=5)
        tk.Button(toolbar, text="⚙ Settings", command=self.app.show_settings_screen,
                 bg='#34495e', fg='white', font=('Arial', 10), padx=10).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Series selector if multiple series
        if len(self.multiple_series) > 0 or self.data:
            tk.Label(toolbar, text="Series:", bg='#2c3e50', fg='white',
                    font=('Arial', 10)).pack(side=tk.LEFT, padx=(20,5))
            self.series_var = tk.StringVar(value="Sample 1")
            all_samples = ["Sample 1"] + [f"Sample {i+2}" for i in range(len(self.multiple_series))]
            series_menu = ttk.Combobox(toolbar, textvariable=self.series_var,
                                      values=all_samples, state="readonly", width=15)
            series_menu.pack(side=tk.LEFT, padx=5)
            series_menu.bind('<<ComboboxSelected>>', self.on_series_change)
        
        # Main content area with left graph and right control panels
        content = tk.Frame(self)
        content.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Graph (70% width)
        left_panel = tk.Frame(content, width=700)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Create matplotlib figure with improved layout
        self.fig = Figure(figsize=(10, 7), dpi=100, facecolor='white')
        self.ax = self.fig.add_subplot(111)
        self.fig.subplots_adjust(left=0.1, right=0.9, top=0.88, bottom=0.12)
        
        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, left_panel)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Navigation toolbar
        toolbar_frame = tk.Frame(left_panel)
        toolbar_frame.pack(fill=tk.X)
        self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        self.toolbar.update()
        
        # Connect mouse motion event for cursor tracking
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        
        # Toggle frequency curve button
        toggle_frame = tk.Frame(left_panel)
        toggle_frame.pack(fill=tk.X, pady=5)
        self.toggle_btn = tk.Button(toggle_frame, text="📈 Show Frequency Curves",
                                   command=self.toggle_frequency,
                                   bg='#3498db', fg='white', font=('Arial', 10), padx=10)
        self.toggle_btn.pack(side=tk.LEFT, padx=5)
        
        # Right panel - Controls and Analysis (30% width)
        right_panel = tk.Frame(content, width=350, relief=tk.GROOVE, bd=2, bg='#f8f9f9')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH)
        right_panel.pack_propagate(False)
        
        # Create scrollable right panel
        canvas_right = tk.Canvas(right_panel, bg='#f8f9f9', highlightthickness=0)
        scrollbar_right = tk.Scrollbar(right_panel, orient=tk.VERTICAL, command=canvas_right.yview)
        scrollable_frame = tk.Frame(canvas_right, bg='#f8f9f9')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas_right.configure(scrollregion=canvas_right.bbox("all"))
        )
        
        canvas_right.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas_right.configure(yscrollcommand=scrollbar_right.set)
        
        canvas_right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_right.pack(side=tk.RIGHT, fill=tk.Y)
        
        # === Cursor Position Display ===
        cursor_frame = tk.LabelFrame(scrollable_frame, text="📌 Cursor Position",
                                    font=('Arial', 11, 'bold'), bg='#f8f9f9',
                                    padx=10, pady=10)
        cursor_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.cursor_x_var = tk.StringVar(value="Diameter: -- mm")
        self.cursor_y_var = tk.StringVar(value="Passing: -- %")
        
        tk.Label(cursor_frame, textvariable=self.cursor_x_var,
                bg='#f8f9f9', font=('Arial', 10)).pack(anchor=tk.W, pady=2)
        tk.Label(cursor_frame, textvariable=self.cursor_y_var,
                bg='#f8f9f9', font=('Arial', 10)).pack(anchor=tk.W, pady=2)
        
        # === Percentile Projection with Series Selection ===
        proj_frame = tk.LabelFrame(scrollable_frame, text="🎯 Project Value",
                                  font=('Arial', 11, 'bold'), bg='#f8f9f9',
                                  padx=10, pady=10)
        proj_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Series selector for project value
        if len(self.multiple_series) > 0 or self.data:
            proj_sample_frame = tk.Frame(proj_frame, bg='#f8f9f9')
            proj_sample_frame.pack(fill=tk.X, pady=2)
            
            tk.Label(proj_sample_frame, text="Sample:",
                    bg='#f8f9f9', font=('Arial', 10)).pack(side=tk.LEFT, padx=(0,5))
            
            self.proj_sample_var = tk.StringVar(value="Sample 1")
            all_samples = ["Sample 1"] + [f"Sample {i+2}" for i in range(len(self.multiple_series))]
            proj_sample_menu = ttk.Combobox(proj_sample_frame, textvariable=self.proj_sample_var,
                                           values=all_samples, state="readonly", width=12)
            proj_sample_menu.pack(side=tk.LEFT)
            proj_sample_menu.bind('<<ComboboxSelected>>', self.on_proj_sample_change)
        
        tk.Label(proj_frame, text="Enter percentile (%):",
                bg='#f8f9f9', font=('Arial', 10)).pack(anchor=tk.W)
        
        entry_frame = tk.Frame(proj_frame, bg='#f8f9f9')
        entry_frame.pack(fill=tk.X, pady=5)
        
        self.proj_entry = tk.Entry(entry_frame, width=15, font=('Arial', 10))
        self.proj_entry.pack(side=tk.LEFT, padx=(0,5))
        self.proj_entry.bind('<KeyRelease>', self.project_percentile)
        
        tk.Label(entry_frame, text="%", bg='#f8f9f9',
                font=('Arial', 10)).pack(side=tk.LEFT)
        
        self.proj_result = tk.Label(proj_frame, text="→ -- mm",
                                   bg='#f8f9f9', font=('Arial', 11, 'bold'),
                                   fg='#27ae60')
        self.proj_result.pack(anchor=tk.W, pady=5)
        
        # === Quick Percentiles Display with Vertical Scrollbar ===
        quick_frame = tk.LabelFrame(scrollable_frame, text="📊 Key Percentiles",
                                   font=('Arial', 11, 'bold'), bg='#f8f9f9',
                                   padx=10, pady=10)
        quick_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Fixed height container for percentiles
        quick_container = tk.Frame(quick_frame, bg='white', height=150)
        quick_container.pack(fill=tk.BOTH, expand=True)
        quick_container.pack_propagate(False)
        
        # LEFT: Vertical scrollbar for percentiles navigation
        quick_v_scrollbar = ttk.Scrollbar(quick_container, orient=tk.VERTICAL)
        quick_v_scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        
        # CENTER: Canvas for scrollable percentiles
        quick_canvas = tk.Canvas(quick_container, bg='white', highlightthickness=0,
                                yscrollcommand=quick_v_scrollbar.set)
        quick_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Link scrollbar to canvas
        quick_v_scrollbar.config(command=quick_canvas.yview)
        
        # RIGHT: Horizontal scrollbar
        quick_h_scrollbar = ttk.Scrollbar(quick_container, orient=tk.HORIZONTAL,
                                         command=quick_canvas.xview)
        quick_h_scrollbar.pack(side=tk.LEFT, fill=tk.X)
        
        quick_canvas.config(xscrollcommand=quick_h_scrollbar.set)
        
        # Frame inside canvas for percentiles content
        quick_scrollable_frame = tk.Frame(quick_canvas, bg='white')
        quick_canvas.create_window((0, 0), window=quick_scrollable_frame, anchor="nw")
        
        # Bind configure event to update scrollregion
        quick_scrollable_frame.bind(
            "<Configure>",
            lambda e: quick_canvas.configure(scrollregion=quick_canvas.bbox("all"))
        )
        
        # Bind mouse wheel for easy scrolling
        def _on_quick_percentiles_mousewheel(event):
            if quick_canvas.winfo_exists():
                quick_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        quick_canvas.bind("<Enter>", lambda e: quick_canvas.bind_all("<MouseWheel>", _on_quick_percentiles_mousewheel))
        quick_canvas.bind("<Leave>", lambda e: quick_canvas.unbind_all("<MouseWheel>"))
        
        # Show percentiles for ALL samples
        self.quick_text_widgets = {}
        self.update_quick_percentiles_all_samples(quick_scrollable_frame)
        
        # === Action Buttons ===
        btn_frame = tk.LabelFrame(scrollable_frame, text="⚡ Analysis Tools",
                                 font=('Arial', 11, 'bold'), bg='#f8f9f9',
                                 padx=10, pady=10)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        buttons = [
            ("📊 Sedimentological Parameters", self.show_sedimentological, '#8e44ad'),
            ("⚙ Geotechnical Parameters", self.show_geotechnical, '#27ae60'),
            ("🔄 Correlation Graphs", self.show_correlation, '#e67e22'),
            ("📈 Friedman (1967) Plots", self.show_friedman_plots, '#3498db'),
            ("📉 Passega C-M Diagram", self.show_passega_diagram, '#9b59b6'),
        ]
        
        for text, command, color in buttons:
            tk.Button(btn_frame, text=text, command=command,
                     bg=color, fg='white', font=('Arial', 10),
                     width=30, pady=3).pack(pady=2)
        
        # === Consolidated Export Button with Dropdown ===
        export_frame = tk.LabelFrame(scrollable_frame, text="💾 Export",
                                    font=('Arial', 11, 'bold'), bg='#f8f9f9',
                                    padx=10, pady=10)
        export_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Main export button
        self.export_btn = tk.Button(export_frame, text="📥 Export",
                                   command=self.show_export_menu,
                                   bg='#3498db', fg='white', font=('Arial', 10, 'bold'),
                                   width=30, pady=5)
        self.export_btn.pack(pady=2)
        
        # Export dropdown menu
        self.export_menu = tk.Menu(export_frame, tearoff=0, bg='white',
                                  font=('Arial', 10))
        self.export_menu.add_command(label="📊 Main Graph as PNG", command=self.export_main_graph)
        self.export_menu.add_command(label="📁 Results as CSV", command=lambda: self.app.export_results())
        self.export_menu.add_command(label="📄 Report as PDF", command=self.export_pdf_report)
        self.export_menu.add_separator()
        self.export_menu.add_command(label="📥 Export All Parameters", command=self.export_all_parameters)
        self.export_menu.add_separator()
        self.export_menu.add_command(label="📈 Export Friedman Plots", command=self.export_friedman_plots)
        self.export_menu.add_command(label="📉 Export Passega Diagram", command=self.export_passega_diagram)
        self.export_menu.add_separator()
        self.export_menu.add_command(label="📊 Export Correlation Graph", command=self.export_correlation_graph)
    
    def show_export_menu(self):
        """Display export dropdown menu"""
        x = self.export_btn.winfo_rootx()
        y = self.export_btn.winfo_rooty() + self.export_btn.winfo_height()
        
        try:
            self.export_menu.post(x, y)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to show export menu: {str(e)}")
    
    def export_main_graph(self):
        """Export main graph as PNG"""
        filename = filedialog.asksaveasfilename(
            title="Export Main Graph",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"),
                      ("JPEG files", "*.jpg"), ("TIFF files", "*.tiff")]
        )
        if filename:
            try:
                dpi = 300 if filename.endswith('.png') else 150
                self.fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')
                messagebox.showinfo("Export Successful", f"Main graph exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def export_correlation_graph(self):
        """Export the correlation graph"""
        # Check if correlation graph was shown before
        if self.last_correlation_fig is None:
            messagebox.showwarning("No Correlation Graph", 
                                   "Please open the Correlation Graph window first before exporting.")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Correlation Graph",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf"),
                      ("JPEG files", "*.jpg"), ("TIFF files", "*.tiff")]
        )
        if filename:
            try:
                dpi = 300 if filename.endswith('.png') else 150
                self.last_correlation_fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')
                messagebox.showinfo("Export Successful", f"Correlation graph exported to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export: {str(e)}")
    
    def get_smooth_curve(self, diameters, percentages, num_points=500):
        """
        Generate smooth curve using interpolation
        Preserves all sieve size classes, handles duplicates by grouping
        """
        try:
            x = np.array(diameters, dtype=float)
            y = np.array(percentages, dtype=float)
            
            # Remove invalid values
            valid_mask = np.isfinite(x) & (x > 0) & np.isfinite(y)
            x = x[valid_mask]
            y = y[valid_mask]
            
            if len(x) < 3:
                sort_idx = np.argsort(x)[::-1]
                return x[sort_idx], y[sort_idx]
            
            # Sort in ascending order for interpolation
            sort_idx = np.argsort(x)
            x_asc = x[sort_idx]
            y_asc = y[sort_idx]
            
            # Group duplicate x-values by averaging y-values
            unique_x = []
            unique_y = []
            i = 0
            while i < len(x_asc):
                j = i
                x_val = x_asc[i]
                y_sum = y_asc[i]
                count = 1
                
                while j + 1 < len(x_asc) and abs(x_asc[j + 1] - x_val) < 1e-9:
                    j += 1
                    y_sum += y_asc[j]
                    count += 1
                
                unique_x.append(x_val)
                unique_y.append(y_sum / count)
                i = j + 1
            
            x_asc = np.array(unique_x)
            y_asc = np.array(unique_y)
            
            if len(x_asc) < 3:
                x_desc = x_asc[::-1]
                y_desc = y_asc[::-1]
                return x_desc, y_desc
            
            # Convert to log space
            log_x = np.log10(x_asc)
            log_x_fine = np.linspace(log_x.min(), log_x.max(), num_points)
            x_fine_asc = 10 ** log_x_fine
            
            # Create spline interpolation
            try:
                spline = interpolate.CubicSpline(log_x, y_asc, bc_type='natural', extrapolate=False)
                y_fine_asc = spline(log_x_fine)
            except:
                # Fallback to linear interpolation
                spline = interpolate.interp1d(log_x, y_asc, kind='linear', 
                                              bounds_error=False, fill_value=(y_asc[0], y_asc[-1]))
                y_fine_asc = spline(log_x_fine)
            
            # Ensure values are within bounds
            y_fine_asc = np.clip(y_fine_asc, 0, 100)
            
            # Ensure monotonic non-decreasing
            for i in range(1, len(y_fine_asc)):
                if y_fine_asc[i] < y_fine_asc[i-1]:
                    y_fine_asc[i] = y_fine_asc[i-1]
            
            # Return in descending order for plotting (coarse to fine)
            x_fine_desc = x_fine_asc[::-1]
            y_fine_desc = y_fine_asc[::-1]
            
            return x_fine_desc, y_fine_desc
            
        except Exception as e:
            print(f"Smoothing error: {e}")
            sort_idx = np.argsort(diameters)[::-1]
            return np.array(diameters)[sort_idx], np.array(percentages)[sort_idx]
    
    def calculate_frequency_curve(self, diameters_desc, passing_desc):
        """
        Calculate frequency curve (percentage retained on each sieve)
        """
        try:
            frequencies = []
            freq_diameters = []
            
            for i in range(len(diameters_desc) - 1):
                d1 = diameters_desc[i]
                d2 = diameters_desc[i + 1]
                p1 = passing_desc[i]
                p2 = passing_desc[i + 1]
                
                # Percentage retained in this interval
                retained = p1 - p2
                
                if retained > 0 and d1 > 0 and d2 > 0:
                    # Geometric mean diameter
                    mean_diameter = np.sqrt(d1 * d2)
                    frequencies.append(retained)
                    freq_diameters.append(mean_diameter)
            
            freq_diameters = np.array(freq_diameters)
            frequencies = np.array(frequencies)
            
            # Normalize to sum to 100%
            total = np.sum(frequencies)
            if total > 0:
                frequencies = (frequencies / total) * 100
            
            return freq_diameters, frequencies
            
        except Exception as e:
            print(f"Error calculating frequency curve: {e}")
            return np.array([]), np.array([])
    
    def plot_data(self):
        """Plot the granulometry curves with all enhancements"""
        try:
            self.ax.clear()
            
            # Remove frequency axis if it exists
            if hasattr(self, 'freq_ax') and self.freq_ax is not None:
                self.freq_ax.remove()
                self.freq_ax = None
            
            has_data = False
            
            # Configure axes
            self.ax.set_xscale('log')
            self.ax.set_xlim(1000, 0.0001)
            self.ax.set_ylim(-2, 102)
            self.ax.invert_xaxis()
            
            # Labels
            self.ax.set_xlabel('Grain Size (mm) - Logarithmic Scale', fontsize=12)
            self.ax.set_ylabel('Cumulative Percentage Passing (%)', fontsize=12)
            self.ax.set_title('Grain Size Distribution Curve', fontsize=14, fontweight='bold')
            self.ax.grid(True, alpha=0.3, linestyle='--')
            
            # Add ISO classification
            self.add_iso_classification()
            self.add_grain_size_classes()
            
            # Create frequency axis if needed
            if self.show_frequency:
                self.freq_ax = self.ax.twinx()
                self.freq_ax.set_ylabel('Frequency / Retained (%)', fontsize=12, color='gray')
                self.freq_ax.tick_params(axis='y', labelcolor='gray')
                self.freq_ax.set_ylim(0, 100)
            
            # Plot data series
            if self.data and len(self.data) > 0:
                self.plot_series_smooth(self.data, 'Sample 1', self.colors[0], 0)
                has_data = True
            
            for i, series in enumerate(self.multiple_series):
                if series and len(series) > 0:
                    color = self.colors[(i + 1) % len(self.colors)]
                    self.plot_series_smooth(series, f'Sample {i+2}', color, i+1)
                    has_data = True
            
            if not has_data:
                self.ax.text(0.5, 0.5, 'No data to display',
                            transform=self.ax.transAxes,
                            ha='center', va='center', fontsize=14,
                            bbox=dict(boxstyle='round', facecolor='yellow', alpha=0.5))
            
            if len(self.multiple_series) > 0 or (self.data and len(self.multiple_series) > 0):
                self.ax.legend(loc='lower left', fontsize=9)
            
            # Add reference lines for percentiles
            for p in [16, 50, 84]:
                self.ax.axhline(y=p, color='gray', linestyle=':', alpha=0.5, linewidth=0.5)
            
            self.fig.canvas.draw_idle()
            self.canvas.draw()
            
        except Exception as e:
            print(f"Error in plot_data: {e}")
            import traceback
            traceback.print_exc()
    
    def plot_series_smooth(self, data, label, color, index):
        """
        Plot a single data series with smoothed cumulative and frequency curves
        Preserves all original data points
        """
        try:
            if not data or len(data) == 0:
                return
            
            diameters = [d for d, _ in data]
            
            # Get cumulative passing percentages
            use_recovered = getattr(self.app, 'use_recovered_weight', True)
            calculator = GranuloCalculator(data, self.app.initial_weight,
                                          use_recovered_weight=use_recovered)
            passing = calculator.cumulative_passing
            
            # Sort original data in descending order for plotting (coarse to fine)
            sorted_indices = np.argsort(diameters)[::-1]
            diameters_desc = np.array(diameters)[sorted_indices]
            passing_desc = np.array(passing)[sorted_indices]
            
            # Plot original data points (markers only)
            self.ax.plot(diameters_desc, passing_desc, 'o', color=color,
                        markersize=5, markeredgecolor='white', 
                        markeredgewidth=1, alpha=0.7, zorder=3)
            
            # Plot smoothed cumulative curve
            if len(diameters) >= 3:
                smooth_diam, smooth_passing = self.get_smooth_curve(diameters, passing)
                self.ax.plot(smooth_diam, smooth_passing, '-', color=color,
                            label=label, linewidth=2.5, zorder=2)
            else:
                # If not enough points for smoothing, connect the points
                self.ax.plot(diameters_desc, passing_desc, '-', color=color,
                            label=label, linewidth=2, zorder=2)
            
            # Frequency curve calculation and plotting
            if self.show_frequency and self.freq_ax is not None:
                freq_diameters, frequencies = self.calculate_frequency_curve(diameters_desc, passing_desc)
                
                if len(freq_diameters) > 0 and len(frequencies) > 0:
                    # Sort frequency data in descending order
                    freq_sort_idx = np.argsort(freq_diameters)[::-1]
                    freq_diam_desc = freq_diameters[freq_sort_idx]
                    freq_desc = frequencies[freq_sort_idx]
                    
                    # Smooth frequency curve if enough points
                    if len(freq_diam_desc) >= 3:
                        try:
                            # Need ascending order for interpolation
                            freq_sort_asc = np.argsort(freq_diam_desc)
                            freq_diam_asc = freq_diam_desc[freq_sort_asc]
                            freq_asc = freq_desc[freq_sort_asc]
                            
                            log_freq = np.log10(freq_diam_asc)
                            log_freq_fine = np.linspace(log_freq.min(), log_freq.max(), 200)
                            freq_diam_fine_asc = 10 ** log_freq_fine
                            
                            freq_spline = interpolate.CubicSpline(log_freq, freq_asc,
                                                                 bc_type='natural', extrapolate=False)
                            freq_smooth_asc = freq_spline(log_freq_fine)
                            freq_smooth_asc = np.clip(freq_smooth_asc, 0, None)
                            
                            # Convert back to descending for plotting
                            freq_diam_fine_desc = freq_diam_fine_asc[::-1]
                            freq_smooth_desc = freq_smooth_asc[::-1]
                            
                            self.freq_ax.plot(freq_diam_fine_desc, freq_smooth_desc, '--', color=color,
                                            alpha=0.7, linewidth=1.5, 
                                            label=f'{label} (freq)', zorder=1)
                        except:
                            # Fallback to raw data
                            self.freq_ax.plot(freq_diam_desc, freq_desc, '--s', color=color,
                                            alpha=0.5, linewidth=1.5, markersize=3,
                                            label=f'{label} (freq)', zorder=1)
                    else:
                        # Plot raw frequency data
                        self.freq_ax.plot(freq_diam_desc, freq_desc, '--s', color=color,
                                        alpha=0.5, linewidth=1.5, markersize=3,
                                        label=f'{label} (freq)', zorder=1)
                    
                    # Update frequency axis limits
                    if len(frequencies) > 0:
                        max_freq = max(frequencies)
                        self.freq_ax.set_ylim(0, max(100, max_freq * 1.2))
            
        except Exception as e:
            print(f"Error in plot_series_smooth for {label}: {e}")
            import traceback
            traceback.print_exc()
    
    def add_iso_classification(self):
        """Add ISO 14688-1:2017 grain size classification boundaries"""
        main_boundaries = [
            (0.002, 'Clay/Silt'),
            (0.063, 'Silt/Sand'),
            (2.0, 'Sand/Gravel'),
            (63.0, 'Gravel/Cobble'),
            (200.0, 'Cobble/Boulder')
        ]
        
        for boundary, label in main_boundaries:
            self.ax.axvline(x=boundary, color='gray', linestyle='-',
                            linewidth=2.5, alpha=0.7, zorder=5)
        
        iso_values = [0.002, 0.0063, 0.02, 0.063, 0.2, 0.63, 2.0, 6.3, 20.0, 63.0, 200.0, 630.0]
        
        for value in iso_values:
            self.ax.axvline(x=value, color='black', linestyle='--',
                           linewidth=0.5, alpha=0.4, zorder=4)
            self.ax.text(value, -1.5, f'{value:g}',
                        rotation=90, fontsize=7, ha='center', va='top',
                        color='black', alpha=0.6)
    
    def add_grain_size_classes(self):
        """Add grain size classes at top"""
        secax = self.ax.secondary_xaxis('top')
        secax.set_xlabel('Grain Size Classes (ISO 14688-1:2017)', fontsize=11)
        
        positions = [
            ('Clay', 0.001), ('Silt', 0.02), ('Sand', 0.5),
            ('Gravel', 20), ('Cobbles', 100), ('Boulders', 500)
        ]
        
        for name, pos in positions:
            self.ax.text(pos, 1.02, name, transform=self.ax.get_xaxis_transform(),
                        ha='center', va='bottom', fontsize=9, fontweight='bold',
                        rotation=0, bbox=dict(boxstyle="round,pad=0.3",
                                 facecolor='white', alpha=0.8))
    
    def update_quick_percentiles_all_samples(self, parent):
        """Update percentiles display for ALL samples with scrollbar"""
        for widget in parent.winfo_children():
            widget.destroy()
        
        all_series = []
        if self.data:
            all_series.append(('Sample 1', self.data))
        for i, series in enumerate(self.multiple_series):
            all_series.append((f'Sample {i+2}', series))
        
        if not all_series:
            return
        
        use_recovered = getattr(self.app, 'use_recovered_weight', True)
        
        for sample_name, series in all_series:
            sample_frame = tk.Frame(parent, bg='white')
            sample_frame.pack(fill=tk.X, padx=5, pady=3)
            
            header_label = tk.Label(sample_frame, text=sample_name,
                                   font=('Arial', 9, 'bold'), bg='#3498db',
                                   fg='white', padx=10, pady=2)
            header_label.pack(fill=tk.X)
            
            text_widget = tk.Text(sample_frame, height=8, width=45,
                                 font=('Courier', 8), bg='white')
            text_widget.pack(fill=tk.X, padx=2, pady=2)
            
            calculator = GranuloCalculator(series, self.app.initial_weight,
                                          use_recovered_weight=use_recovered)
            params = calculator.get_all_percentiles()
            
            text = "Pct | Diameter(mm) | Phi(φ)\n"
            text += "-" * 35 + "\n"
            percentiles = [5, 10, 16, 25, 30, 50, 60, 70, 75, 84, 90, 95]
            for p in percentiles:
                mm = params.get(f'D{p}', 0)
                phi = params.get(f'phi{p}', 0)
                if not math.isnan(mm) and mm > 0 and not math.isnan(phi):
                    text += f"{p:3.0f}%| {mm:12.4f} | {phi:6.3f}\n"
                else:
                    text += f"{p:3.0f}%|     --      |  --\n"
            
            text_widget.insert('1.0', text)
            text_widget.config(state=tk.DISABLED)
            
            self.quick_text_widgets[sample_name] = text_widget
    
    def toggle_frequency(self):
        """Toggle frequency curve display"""
        self.show_frequency = not self.show_frequency
        if self.show_frequency:
            self.toggle_btn.config(text="📉 Hide Frequency Curves", bg='#e74c3c')
        else:
            self.toggle_btn.config(text="📈 Show Frequency Curves", bg='#3498db')
        self.plot_data()
    
    def on_mouse_move(self, event):
        """Handle mouse movement on graph for cursor tracking"""
        if event.inaxes == self.ax:
            x, y = event.xdata, event.ydata
            if x is not None and y is not None and 0 <= y <= 100:
                self.cursor_x_var.set(f"Diameter: {x:.6f} mm")
                self.cursor_y_var.set(f"Passing: {y:.2f} %")
    
    def on_series_change(self, event=None):
        """Handle series selection change"""
        self.plot_data()
    
    def on_proj_sample_change(self, event=None):
        """Handle project value sample selection change"""
        self.project_percentile()
    
    def project_percentile(self, event=None):
        """Project percentile value for selected sample"""
        try:
            pct = float(self.proj_entry.get())
            if 0 <= pct <= 100:
                selected_sample = self.proj_sample_var.get()
                
                if selected_sample == "Sample 1":
                    series_data = self.data
                else:
                    sample_idx = int(selected_sample.split()[1]) - 2
                    if 0 <= sample_idx < len(self.multiple_series):
                        series_data = self.multiple_series[sample_idx]
                    else:
                        series_data = self.data
                
                if series_data:
                    use_recovered = getattr(self.app, 'use_recovered_weight', True)
                    calculator = GranuloCalculator(series_data, self.app.initial_weight,
                                                  use_recovered_weight=use_recovered)
                    diameter = calculator.get_percentile_diameter(pct)
                    if not math.isnan(diameter) and diameter > 0:
                        self.proj_result.config(text=f"→ {diameter:.6f} mm")
                    else:
                        self.proj_result.config(text="→ Outside range")
                else:
                    self.proj_result.config(text="→ No data")
            else:
                self.proj_result.config(text="→ Invalid (0-100)")
        except ValueError:
            self.proj_result.config(text="→ Enter number")
    
    def show_sedimentological(self):
        """Show sedimentological parameters for ALL samples"""
        all_series = []
        if self.data:
            all_series.append(('Sample 1', self.data))
        for i, series in enumerate(self.multiple_series):
            all_series.append((f'Sample {i+2}', series))
        
        if not all_series:
            messagebox.showwarning("No Data", "No data available")
            return
        
        use_recovered = getattr(self.app, 'use_recovered_weight', True)
        
        win = tk.Toplevel(self)
        win.title("Sedimentological Parameters - Folk & Ward (1957)")
        win.geometry("700x750")
        win.configure(bg='white')
        
        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for sample_name, series in all_series:
            calculator = GranuloCalculator(series, self.app.initial_weight,
                                          use_recovered_weight=use_recovered)
            params = calculator.get_all_parameters()
            
            frame = tk.Frame(notebook, bg='white')
            notebook.add(frame, text=sample_name)
            
            text = tk.Text(frame, wrap=tk.WORD, font=('Courier', 11),
                          bg='white', fg='#2c3e50', padx=10, pady=10)
            scrollbar = tk.Scrollbar(frame, command=text.yview)
            text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            report = f"""
{'='*60}
SEDIMENTOLOGICAL PARAMETERS (Folk & Ward, 1957)
{'='*60}
{'─'*60}
CALCULATION BASIS:
{'─'*60}
Method: {'ASTM D6913 (Recovered Weight)' if use_recovered else 'NF P 94-056 / ISO (Initial Weight)'}
{'─'*60}
PERCENTILES:
{'─'*60}
5%:     {params.get('D5', 0):8.6f} mm    (φ = {params.get('phi5', 0):6.3f})
10%:     {params.get('D10', 0):8.6f} mm    (φ = {params.get('phi10', 0):6.3f})
16%:     {params.get('D16', 0):8.6f} mm    (φ = {params.get('phi16', 0):6.3f})
25%:     {params.get('D25', 0):8.6f} mm    (φ = {params.get('phi25', 0):6.3f})
30%:     {params.get('D30', 0):8.6f} mm    (φ = {params.get('phi30', 0):6.3f})
50%:     {params.get('D50', 0):8.6f} mm    (φ = {params.get('phi50', 0):6.3f})
60%:     {params.get('D60', 0):8.6f} mm    (φ = {params.get('phi60', 0):6.3f})
70%:     {params.get('D70', 0):8.6f} mm    (φ = {params.get('phi70', 0):6.3f})
75%:     {params.get('D75', 0):8.6f} mm    (φ = {params.get('phi75', 0):6.3f})
84%:     {params.get('D84', 0):8.6f} mm    (φ = {params.get('phi84', 0):6.3f})
90%:     {params.get('D90', 0):8.6f} mm    (φ = {params.get('phi90', 0):6.3f})
95%:     {params.get('D95', 0):8.6f} mm    (φ = {params.get('phi95', 0):6.3f})
{'─'*60}
CENTRAL TENDENCY:
{'─'*60}
Mode:            {params.get('mode_mm', 0):8.6f} mm
Modality:        {params.get('modality', 'unknown')}
Graphic Mean:    {params.get('mean_mm', 0):8.6f} mm  (φ = {params.get('mean_phi', 0):6.3f})
Median:          {params.get('median_mm', 0):8.6f} mm  (φ = {params.get('median_phi', 0):6.3f})
{'─'*60}
SORTING: σI = {params.get('sorting', 0):6.3f} → {params.get('sorting_class', 'unknown')}
SKEWNESS: Sk = {params.get('skewness', 0):6.3f} → {params.get('skewness_class', 'unknown')}
KURTOSIS: KG = {params.get('kurtosis', 0):6.3f} → {params.get('kurtosis_class', 'unknown')}
{'─'*60}
QUALITY CONTROL:
Initial: {self.app.initial_weight:.2f}g | Recovered: {calculator.recovered_weight:.2f}g | Recovery: {params.get('recovery_pct', 0):.2f}%
{'='*60}
"""
            text.insert('1.0', report)
            text.config(state=tk.DISABLED)
    
    def show_geotechnical(self):
        """Show geotechnical parameters for ALL samples"""
        all_series = []
        if self.data:
            all_series.append(('Sample 1', self.data))
        for i, series in enumerate(self.multiple_series):
            all_series.append((f'Sample {i+2}', series))
        
        if not all_series:
            messagebox.showwarning("No Data", "No data available")
            return
        
        use_recovered = getattr(self.app, 'use_recovered_weight', True)
        
        win = tk.Toplevel(self)
        win.title("Geotechnical Parameters")
        win.geometry("700x700")
        win.configure(bg='white')
        
        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for sample_name, series in all_series:
            calculator = GranuloCalculator(series, self.app.initial_weight,
                                          use_recovered_weight=use_recovered)
            params = calculator.get_all_parameters()
            
            frame = tk.Frame(notebook, bg='white')
            notebook.add(frame, text=sample_name)
            
            text = tk.Text(frame, wrap=tk.WORD, font=('Courier', 11),
                          bg='white', fg='#2c3e50', padx=10, pady=10)
            scrollbar = tk.Scrollbar(frame, command=text.yview)
            text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            fm_class_full = params.get('FM_class', 'unknown')
            fm_main = fm_class_full.split(' - ')[0] if ' - ' in fm_class_full else fm_class_full
            
            report = f"""
{'='*60}
GEOTECHNICAL PARAMETERS
{'='*60}
Method: {'ASTM D6913' if use_recovered else 'NF P 94-056 / ISO'}
{'─'*60}
Cu = D60/D10 = {params.get('Cu', 0):.3f} → {params.get('Cu_class', 'unknown')}
Cc = (D30)²/(D10×D60) = {params.get('Cc', 0):.3f} → {params.get('Cc_class', 'unknown')}
FM = {params.get('FM', 0):.3f} → {fm_main}
{'─'*60}
INTERPRETATION:
• Cu > 6: Well-graded | Cu 4-6: Medium | Cu < 4: Poorly graded
• 1 < Cc < 3: Well-graded (IDEAL for construction)
• FM 2.6-2.9: HIGH-QUALITY CONCRETE (PREFERRED)
{'='*60}
"""
            text.insert('1.0', report)
            text.config(state=tk.DISABLED)
    
    def show_correlation(self):
        """Show correlation graphs for multiple samples"""
        all_series = []
        if self.data:
            all_series.append(self.data)
        all_series.extend(self.multiple_series)
        
        if len(all_series) < 2:
            messagebox.showwarning("Insufficient Data", "Need at least 2 samples")
            return
        
        win = tk.Toplevel(self)
        win.title("Correlation Analysis")
        win.geometry("900x700")
        
        fig = Figure(figsize=(12, 9), dpi=100)
        self.last_correlation_fig = fig  # Store for export
        use_recovered = getattr(self.app, 'use_recovered_weight', True)
        
        all_params = []
        sample_names = []
        for i, series in enumerate(all_series):
            calc = GranuloCalculator(series, self.app.initial_weight,
                                    use_recovered_weight=use_recovered)
            params = calc.get_all_parameters()
            all_params.append(params)
            sample_names.append(f"Sample {i+1}")
        
        skewness = [p.get('skewness', 0) for p in all_params]
        kurtosis = [p.get('kurtosis', 0) for p in all_params]
        sorting = [p.get('sorting', 0) for p in all_params]
        mean_phi = [p.get('mean_phi', 0) for p in all_params]
        fm = [p.get('FM', 0) for p in all_params]
        
        ax1 = fig.add_subplot(221)
        ax1.scatter(skewness, kurtosis, c=range(len(skewness)), cmap='viridis', s=100, alpha=0.7)
        ax1.set_xlabel('Skewness (Sk)')
        ax1.set_ylabel('Kurtosis (KG)')
        ax1.set_title('Skewness vs Kurtosis')
        ax1.grid(True, alpha=0.3)
        
        ax2 = fig.add_subplot(222)
        ax2.scatter(mean_phi, sorting, c=range(len(mean_phi)), cmap='plasma', s=100, alpha=0.7)
        ax2.set_xlabel('Mean Grain Size (φ)')
        ax2.set_ylabel('Sorting (σI)')
        ax2.set_title('Mean vs Sorting')
        ax2.grid(True, alpha=0.3)
        ax2.invert_xaxis()
        
        ax3 = fig.add_subplot(223)
        ax3.scatter([p.get('mean_mm', 0) for p in all_params], fm, c='green', s=100, alpha=0.7)
        ax3.set_xlabel('Mean Grain Size (mm)')
        ax3.set_ylabel('Fineness Modulus')
        ax3.set_title('Mean vs FM')
        ax3.set_xscale('log')
        ax3.grid(True, alpha=0.3)
        
        ax4 = fig.add_subplot(224)
        param_matrix = np.array([skewness, kurtosis, sorting, mean_phi, fm])
        corr_matrix = np.corrcoef(param_matrix)
        im = ax4.imshow(corr_matrix, cmap='RdBu', vmin=-1, vmax=1, aspect='auto')
        ax4.set_xticks(range(5))
        ax4.set_yticks(range(5))
        ax4.set_xticklabels(['Skew', 'Kurt', 'Sort', 'Mean φ', 'FM'], rotation=45, ha='right')
        ax4.set_yticklabels(['Skew', 'Kurt', 'Sort', 'Mean φ', 'FM'])
        ax4.set_title('Correlation Matrix')
        plt.colorbar(im, ax=ax4, fraction=0.046, pad=0.04)
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, win)
        toolbar.update()
    
    def show_friedman_plots(self):
        """Show Friedman (1967) discrimination diagrams"""
        all_series = []
        if self.data:
            all_series.append(self.data)
        all_series.extend(self.multiple_series)
        
        if len(all_series) < 1:
            messagebox.showwarning("No Data", "Need at least 1 sample")
            return
        
        win = tk.Toplevel(self)
        win.title("Friedman (1967) Discrimination Diagrams")
        win.geometry("1100x900")
        
        fig = Figure(figsize=(14, 10), dpi=100)
        fig.suptitle('Friedman (1967) Environmental Discrimination Diagrams',
                    fontsize=14, fontweight='bold', y=0.995)
        
        use_recovered = getattr(self.app, 'use_recovered_weight', True)
        
        all_params = []
        sample_names = []
        for i, series in enumerate(all_series):
            calc = GranuloCalculator(series, self.app.initial_weight,
                                    use_recovered_weight=use_recovered)
            params = calc.get_all_parameters()
            all_params.append(params)
            sample_names.append(f"S{i+1}")
        
        skewness = [p.get('skewness', 0) for p in all_params]
        kurtosis = [p.get('kurtosis', 0) for p in all_params]
        sorting = [p.get('sorting', 0) for p in all_params]
        mean_phi = [p.get('mean_phi', 0) for p in all_params]
        
        colors = [self.colors[i % len(self.colors)] for i in range(len(all_params))]
        
        ax1 = fig.add_subplot(221)
        beach1 = plt.Rectangle((-0.6, 0.8), 0.9, 0.8, alpha=0.15, color='blue', label='Beach')
        river1 = plt.Rectangle((0.0, 0.9), 0.6, 1.2, alpha=0.15, color='green', label='River')
        ax1.add_patch(beach1)
        ax1.add_patch(river1)
        for i, (sk, kg) in enumerate(zip(skewness, kurtosis)):
            ax1.scatter(sk, kg, c=[colors[i]], s=80, alpha=0.8, edgecolors='black')
            ax1.annotate(sample_names[i], (sk, kg), fontsize=8, xytext=(6, 6), textcoords='offset points')
        ax1.set_xlabel('Skewness (Sk)')
        ax1.set_ylabel('Kurtosis (KG)')
        ax1.set_title('① Skewness vs Kurtosis')
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(-0.7, 0.7)
        ax1.set_ylim(0.5, 2.5)
        ax1.legend(loc='lower right', fontsize=8)
        
        ax2 = fig.add_subplot(222)
        beach2 = plt.Rectangle((-0.6, 0.2), 0.9, 0.6, alpha=0.15, color='blue')
        river2 = plt.Rectangle((0.0, 0.5), 0.6, 1.5, alpha=0.15, color='green')
        ax2.add_patch(beach2)
        ax2.add_patch(river2)
        for i, (sk, so) in enumerate(zip(skewness, sorting)):
            ax2.scatter(sk, so, c=[colors[i]], s=80, alpha=0.8, edgecolors='black')
            ax2.annotate(sample_names[i], (sk, so), fontsize=8, xytext=(6, 6), textcoords='offset points')
        ax2.set_xlabel('Skewness (Sk)')
        ax2.set_ylabel('Sorting (σI)')
        ax2.set_title('② Skewness vs Sorting')
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(-0.7, 0.7)
        ax2.set_ylim(0, 2.5)
        
        ax3 = fig.add_subplot(223)
        beach3 = plt.Rectangle((-0.6, -1.0), 0.9, 2.5, alpha=0.15, color='blue')
        river3 = plt.Rectangle((0.0, 0.5), 0.6, 2.0, alpha=0.15, color='green')
        ax3.add_patch(beach3)
        ax3.add_patch(river3)
        for i, (sk, mz) in enumerate(zip(skewness, mean_phi)):
            ax3.scatter(sk, mz, c=[colors[i]], s=80, alpha=0.8, edgecolors='black')
            ax3.annotate(sample_names[i], (sk, mz), fontsize=8, xytext=(6, 6), textcoords='offset points')
        ax3.set_xlabel('Skewness (Sk)')
        ax3.set_ylabel('Mean Grain Size (Mz, φ)')
        ax3.set_title('③ Skewness vs Mean Grain Size')
        ax3.grid(True, alpha=0.3)
        ax3.set_xlim(-0.7, 0.7)
        ax3.set_ylim(3.5, -1.5)
        
        ax4 = fig.add_subplot(224)
        beach4 = plt.Rectangle((-1.5, 0.2), 3.0, 0.6, alpha=0.15, color='blue')
        river4 = plt.Rectangle((0.0, 0.5), 2.5, 1.5, alpha=0.15, color='green')
        ax4.add_patch(beach4)
        ax4.add_patch(river4)
        for i, (mz, so) in enumerate(zip(mean_phi, sorting)):
            ax4.scatter(mz, so, c=[colors[i]], s=80, alpha=0.8, edgecolors='black')
            ax4.annotate(sample_names[i], (mz, so), fontsize=8, xytext=(6, 6), textcoords='offset points')
        ax4.set_xlabel('Mean Grain Size (Mz, φ)')
        ax4.set_ylabel('Sorting (σI)')
        ax4.set_title('④ Mean Grain Size vs Sorting')
        ax4.grid(True, alpha=0.3)
        ax4.set_xlim(3.5, -1.5)
        ax4.set_ylim(0, 2.5)
        
        fig.tight_layout(rect=[0, 0.02, 1, 0.96])
        
        fig.text(0.5, 0.005,
                 "Beach sands: negative skew, better sorting (σI < 1.0) | River sands: positive skew, poorer sorting (σI > 1.0)",
                 ha='center', fontsize=9, style='italic',
                 bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9))
        
        canvas = FigureCanvasTkAgg(fig, win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, win)
        toolbar.update()
        
        export_btn = tk.Button(win, text="💾 Export Friedman Diagrams",
                              command=lambda: self._export_friedman(fig),
                              bg='#3498db', fg='white', font=('Arial', 9))
        export_btn.pack(pady=5)
    
    def _export_friedman(self, fig):
        """Export Friedman diagrams"""
        filename = filedialog.asksaveasfilename(
            title="Export Friedman Diagrams",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")]
        )
        if filename:
            try:
                dpi = 300 if filename.endswith('.png') else 150
                fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')
                messagebox.showinfo("Export Successful", f"Saved to:\n{filename}")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed: {str(e)}")
    
    def show_passega_diagram(self):
        """Show Passega C-M diagram"""
        all_series = []
        if self.data:
            all_series.append(self.data)
        all_series.extend(self.multiple_series)
        
        if len(all_series) < 1:
            messagebox.showwarning("No Data", "Need at least 1 sample")
            return
        
        win = tk.Toplevel(self)
        win.title("Passega C-M Diagram (1969)")
        win.geometry("800x700")
        
        fig = Figure(figsize=(10, 8), dpi=100)
        ax = fig.add_subplot(111)
        
        use_recovered = getattr(self.app, 'use_recovered_weight', True)
        
        c_values = []
        m_values = []
        sample_names = []
        
        for i, series in enumerate(all_series):
            try:
                calc = GranuloCalculator(series, self.app.initial_weight,
                                        use_recovered_weight=use_recovered)
                c = calc.get_percentile_diameter(1)
                m = calc.get_percentile_diameter(50)
                
                if (c is not None and m is not None and
                     not math.isnan(c) and not math.isnan(m) and
                    c > 0 and m > 0 and c < 1000 and m < 1000):
                    c_values.append(c)
                    m_values.append(m)
                    sample_names.append(f"S{i+1}")
            except Exception as e:
                print(f"Error: {e}")
                continue
        
        if not c_values or not m_values:
            messagebox.showwarning("No Valid Data", "Could not calculate C and M values")
            return
        
        ax.scatter(m_values, c_values, c=range(len(c_values)), cmap='viridis', s=150, alpha=0.7, edgecolors='black')
        ax.set_xlabel('M - Median (mm)')
        ax.set_ylabel('C - 1st Percentile (mm)')
        ax.set_title('Passega C-M Diagram')
        ax.set_xscale('log')
        ax.set_yscale('log')
        
        ax.axhspan(0.1, 0.5, xmin=0, xmax=0.3, alpha=0.2, color='blue', label='I - Suspension')
        ax.axhspan(0.5, 10, xmin=0.1, xmax=0.8, alpha=0.2, color='green', label='II - Saltation')
        ax.axhspan(10, 1000, xmin=0.5, xmax=1, alpha=0.2, color='red', label='III - Rolling')
        
        max_val = max(max(c_values), max(m_values))
        min_val = min(min(c_values), min(m_values))
        ax.plot([min_val, max_val], [min_val, max_val], 'k--', alpha=0.5, label='C = M')
        
        for i, name in enumerate(sample_names):
            ax.annotate(name, (m_values[i], c_values[i]), fontsize=10, xytext=(5,5), textcoords='offset points')
        
        ax.grid(True, alpha=0.3, which='both')
        ax.legend(loc='upper left')
        
        fig.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        toolbar = NavigationToolbar2Tk(canvas, win)
        toolbar.update()
    
    def export_all_parameters(self):
        """Export all parameters to CSV"""
        all_series = []
        if self.data:
            all_series.append(('Sample 1', self.data))
        for i, series in enumerate(self.multiple_series):
            all_series.append((f'Sample {i+2}', series))
        
        if not all_series:
            messagebox.showwarning("No Data", "No data to export")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export All Parameters",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")]
        )
        if not filename:
            return
        
        try:
            use_recovered = getattr(self.app, 'use_recovered_weight', True)
            
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Sample', 'Parameter', 'Value', 'Classification'])
                
                for sample_name, series in all_series:
                    calculator = GranuloCalculator(series, self.app.initial_weight,
                                                  use_recovered_weight=use_recovered)
                    params = calculator.get_all_parameters()
                    
                    writer.writerow([sample_name, 'Calculation Basis',
                                    'ASTM' if use_recovered else 'NF/ISO', ''])
                    
                    for p in [5, 10, 16, 25, 30, 50, 60, 70, 75, 84, 90, 95]:
                        writer.writerow([sample_name, f'D{p} (mm)', params.get(f'D{p}', ''), ''])
                        writer.writerow([sample_name, f'φ{p}', params.get(f'phi{p}', ''), ''])
                    
                    writer.writerow([sample_name, 'Mode (mm)', params.get('mode_mm', ''), ''])
                    writer.writerow([sample_name, 'Mean (mm)', params.get('mean_mm', ''), ''])
                    writer.writerow([sample_name, 'Median (mm)', params.get('median_mm', ''), ''])
                    writer.writerow([sample_name, 'Sorting (σI)', params.get('sorting', ''), params.get('sorting_class', '')])
                    writer.writerow([sample_name, 'Skewness', params.get('skewness', ''), params.get('skewness_class', '')])
                    writer.writerow([sample_name, 'Kurtosis', params.get('kurtosis', ''), params.get('kurtosis_class', '')])
                    writer.writerow([sample_name, 'Cu', params.get('Cu', ''), params.get('Cu_class', '')])
                    writer.writerow([sample_name, 'Cc', params.get('Cc', ''), params.get('Cc_class', '')])
                    writer.writerow([sample_name, 'FM', params.get('FM', ''), params.get('FM_class', '')])
                    writer.writerow([])
            
            messagebox.showinfo("Export Successful", f"All parameters exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed: {str(e)}")
    
    def export_friedman_plots(self):
        """Export Friedman plots"""
        all_series = []
        if self.data:
            all_series.append(self.data)
        all_series.extend(self.multiple_series)
        
        if len(all_series) < 1:
            messagebox.showwarning("No Data", "Need at least 1 sample")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Friedman Plots",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")]
        )
        if not filename:
            return
        
        try:
            use_recovered = getattr(self.app, 'use_recovered_weight', True)
            
            all_params = []
            for series in all_series:
                calc = GranuloCalculator(series, self.app.initial_weight,
                                        use_recovered_weight=use_recovered)
                all_params.append(calc.get_all_parameters())
            
            skewness = [p.get('skewness', 0) for p in all_params]
            kurtosis = [p.get('kurtosis', 0) for p in all_params]
            sorting = [p.get('sorting', 0) for p in all_params]
            mean_phi = [p.get('mean_phi', 0) for p in all_params]
            
            fig = Figure(figsize=(14, 10), dpi=100)
            fig.suptitle('Friedman (1967) Diagrams', fontsize=14, fontweight='bold')
            
            ax1 = fig.add_subplot(221)
            ax1.scatter(skewness, kurtosis, c='blue', s=100, alpha=0.7)
            ax1.set_xlabel('Skewness (Sk)')
            ax1.set_ylabel('Kurtosis (KG)')
            ax1.set_title('① Skewness vs Kurtosis')
            ax1.grid(True, alpha=0.3)
            
            ax2 = fig.add_subplot(222)
            ax2.scatter(skewness, sorting, c='green', s=100, alpha=0.7)
            ax2.set_xlabel('Skewness (Sk)')
            ax2.set_ylabel('Sorting (σI)')
            ax2.set_title('② Skewness vs Sorting')
            ax2.grid(True, alpha=0.3)
            
            ax3 = fig.add_subplot(223)
            ax3.scatter(skewness, mean_phi, c='red', s=100, alpha=0.7)
            ax3.set_xlabel('Skewness (Sk)')
            ax3.set_ylabel('Mean (φ)')
            ax3.set_title('③ Skewness vs Mean')
            ax3.grid(True, alpha=0.3)
            ax3.invert_yaxis()
            
            ax4 = fig.add_subplot(224)
            ax4.scatter(mean_phi, sorting, c='purple', s=100, alpha=0.7)
            ax4.set_xlabel('Mean (φ)')
            ax4.set_ylabel('Sorting (σI)')
            ax4.set_title('④ Mean vs Sorting')
            ax4.grid(True, alpha=0.3)
            ax4.invert_xaxis()
            
            fig.tight_layout()
            
            dpi = 300 if filename.endswith('.png') else 150
            fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')
            messagebox.showinfo("Export Successful", f"Friedman plots exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed: {str(e)}")
    
    def export_passega_diagram(self):
        """Export Passega diagram"""
        all_series = []
        if self.data:
            all_series.append(self.data)
        all_series.extend(self.multiple_series)
        
        if len(all_series) < 1:
            messagebox.showwarning("No Data", "Need at least 1 sample")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export Passega Diagram",
            defaultextension=".png",
            filetypes=[("PNG files", "*.png"), ("PDF files", "*.pdf")]
        )
        if not filename:
            return
        
        try:
            use_recovered = getattr(self.app, 'use_recovered_weight', True)
            
            c_values = []
            m_values = []
            for series in all_series:
                calc = GranuloCalculator(series, self.app.initial_weight,
                                        use_recovered_weight=use_recovered)
                c = calc.get_percentile_diameter(1)
                m = calc.get_percentile_diameter(50)
                if c > 0 and m > 0:
                    c_values.append(c)
                    m_values.append(m)
            
            if not c_values or not m_values:
                messagebox.showwarning("No Valid Data", "Could not calculate C and M")
                return
            
            fig = Figure(figsize=(10, 8), dpi=100)
            ax = fig.add_subplot(111)
            
            ax.scatter(m_values, c_values, c='blue', s=150, alpha=0.7, edgecolors='black')
            ax.set_xlabel('M - Median (mm)')
            ax.set_ylabel('C - 1st Percentile (mm)')
            ax.set_title('Passega C-M Diagram')
            ax.set_xscale('log')
            ax.set_yscale('log')
            ax.grid(True, alpha=0.3)
            
            fig.tight_layout()
            
            dpi = 300 if filename.endswith('.png') else 150
            fig.savefig(filename, dpi=dpi, bbox_inches='tight', facecolor='white')
            messagebox.showinfo("Export Successful", f"Passega diagram exported to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed: {str(e)}")
    
    def export_pdf_report(self):
        """Export PDF report"""
        if not self.data:
            messagebox.showwarning("No Data", "No data to export")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Save PDF Report",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")]
        )
        if not filename:
            return
        
        messagebox.showinfo("Export", f"PDF report would be saved to:\n{filename}")