"""
Settings Screen Module - About, License, Contact, and Preferences
Author: Smaine Chellat
Institution: University Constantine 1, Geological Department, Algeria
"""
import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from datetime import datetime


class SettingsScreen(tk.Frame):
    """Settings screen with Read-me/License, About/Contact, and Preferences"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.parent = parent  # ✅ FIX: Use parent for clipboard access
        self.app = app
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_frame = tk.Frame(self, bg='#2c3e50', height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        title_label = tk.Label(title_frame, text="GranuloGraph - Settings",
                             font=('Arial', 18, 'bold'), bg='#2c3e50', fg='white')
        title_label.pack(side=tk.LEFT, padx=20)
        
        # Home button
        home_btn = tk.Button(title_frame, text="🏠 Home",
                           command=self.app.show_home_screen,
                           bg='#34495e', fg='white', font=('Arial', 10))
        home_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Main content with notebook tabs
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tab 1: Preferences [NEW - Calculation Basis Setting]
        prefs_frame = ttk.Frame(notebook)
        notebook.add(prefs_frame, text="⚙ Preferences")
        self.setup_preferences_tab(prefs_frame)
        
        # Tab 2: Read-me & License
        readme_frame = ttk.Frame(notebook)
        notebook.add(readme_frame, text="📖 Read-me & License")
        self.setup_readme_tab(readme_frame)
        
        # Tab 3: About & Contact
        about_frame = ttk.Frame(notebook)
        notebook.add(about_frame, text="👤 About & Contact")
        self.setup_about_tab(about_frame)
    
    def setup_preferences_tab(self, parent):
        """Setup the Preferences tab with calculation basis setting"""
        # Create scrollable frame
        canvas = tk.Canvas(parent, bg='white')
        scrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # === Default Calculation Basis ===
        basis_frame = tk.LabelFrame(scrollable_frame, text="🔬 Default Calculation Method",
                                   font=('Arial', 11, 'bold'), bg='white',
                                   padx=15, pady=10)
        basis_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(basis_frame, text="Select default method for new analyses:",
                font=('Arial', 10), bg='white', justify=tk.LEFT, wraplength=450).pack(anchor=tk.W, pady=(0, 10))
        
        # Radio buttons for calculation basis
        self.basis_var = tk.StringVar(value=self.app.config.get_calculation_basis())
        
        basis_options = [
            ("RECOVERED", "🔬 Recovered Weight (ASTM D6913)\n    • For research, journals, sedimentology stats\n    • Ensures cumulative curve spans 0–100%"),
            ("INITIAL", "🏗️ Initial Weight (NF P 94-056 / ISO)\n    • For geotechnical reports, engineering projects\n    • Standard for Algerian/French standards")
        ]
        
        for value, text in basis_options:
            frame = tk.Frame(basis_frame, bg='white')
            frame.pack(fill=tk.X, pady=5)
            
            radio = tk.Radiobutton(frame, variable=self.basis_var, value=value,
                                  command=self._save_basis_preference,
                                  bg='white', activebackground='white')
            radio.pack(side=tk.LEFT, padx=(0, 10))
            
            label = tk.Label(frame, text=text, font=('Arial', 9),
                            bg='white', justify=tk.LEFT, wraplength=400)
            label.pack(side=tk.LEFT)
        
        # === Appearance Preferences ===
        appearance_frame = tk.LabelFrame(scrollable_frame, text="🎨 Appearance",
                                        font=('Arial', 11, 'bold'), bg='white',
                                        padx=15, pady=10)
        appearance_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Font size
        font_frame = tk.Frame(appearance_frame, bg='white')
        font_frame.pack(fill=tk.X, pady=5)
        tk.Label(font_frame, text="Font Size:", font=('Arial', 10),
                bg='white', width=12, anchor='w').pack(side=tk.LEFT)
        
        self.font_size_var = tk.IntVar(value=self.app.config.get('appearance.font_size', 10))
        font_scale = ttk.Scale(font_frame, from_=8, to=14, orient=tk.HORIZONTAL,
                              variable=self.font_size_var, command=self._save_font_size)
        font_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)
        tk.Label(font_frame, textvariable=self.font_size_var,
                font=('Arial', 10), bg='white', width=3).pack(side=tk.LEFT)
        
        # Show grid toggle
        grid_frame = tk.Frame(appearance_frame, bg='white')
        grid_frame.pack(fill=tk.X, pady=5)
        
        self.show_grid_var = tk.BooleanVar(value=self.app.config.get('appearance.show_grid', True))
        grid_check = tk.Checkbutton(grid_frame, text="Show grid lines on graphs",
                                   variable=self.show_grid_var, command=self._save_grid_preference,
                                   bg='white', activebackground='white', font=('Arial', 10))
        grid_check.pack(anchor=tk.W)
        
        # === Export Preferences ===
        export_frame = tk.LabelFrame(scrollable_frame, text="💾 Export Settings",
                                    font=('Arial', 11, 'bold'), bg='white',
                                    padx=15, pady=10)
        export_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Graph DPI
        dpi_frame = tk.Frame(export_frame, bg='white')
        dpi_frame.pack(fill=tk.X, pady=5)
        tk.Label(dpi_frame, text="Graph Export DPI:", font=('Arial', 10),
                bg='white', width=15, anchor='w').pack(side=tk.LEFT)
        
        self.dpi_var = tk.IntVar(value=self.app.config.get('export.graph_dpi', 300))
        dpi_combo = ttk.Combobox(dpi_frame, textvariable=self.dpi_var,
                                values=[150, 200, 300, 600], state="readonly", width=10)
        dpi_combo.pack(side=tk.LEFT, padx=10)
        dpi_combo.bind('<<ComboboxSelected>>', self._save_dpi_preference)
        tk.Label(dpi_frame, text="(higher = better quality, larger file)",
                font=('Arial', 9), bg='white', fg='#7f8c8d').pack(side=tk.LEFT)
        
        # Decimal places
        decimal_frame = tk.Frame(export_frame, bg='white')
        decimal_frame.pack(fill=tk.X, pady=5)
        tk.Label(decimal_frame, text="Decimal Places:", font=('Arial', 10),
                bg='white', width=15, anchor='w').pack(side=tk.LEFT)
        
        self.decimal_var = tk.IntVar(value=self.app.config.get('export.decimal_places', 4))
        decimal_spin = tk.Spinbox(decimal_frame, from_=2, to=6, width=5,
                                 textvariable=self.decimal_var,
                                 command=self._save_decimal_preference)
        decimal_spin.pack(side=tk.LEFT, padx=10)
        
        # === Reset to Defaults ===
        reset_frame = tk.Frame(scrollable_frame, bg='white')
        reset_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Button(reset_frame, text="🔄 Reset All Preferences to Defaults",
                 command=self._reset_preferences,
                 bg='#e74c3c', fg='white', font=('Arial', 10),
                 padx=15, pady=5).pack()
        
        # Status message
        self.pref_status = tk.Label(scrollable_frame, text="✓ Preferences saved",
                                   font=('Arial', 9, 'italic'), bg='white', fg='#27ae60')
        self.pref_status.pack(pady=(0, 20))
    
    def _save_basis_preference(self):
        """Save calculation basis preference"""
        basis = self.basis_var.get()
        self.app.config.set_calculation_basis(basis)
        self._show_pref_saved()
        
        # Update home screen if it exists
        if hasattr(self.app, 'home') and self.app.home:
            self.app.home.calc_basis_var.set(basis.lower())
    
    def _save_font_size(self, value):
        """Save font size preference"""
        self.app.config.set('appearance.font_size', int(float(value)))
        self._show_pref_saved()
    
    def _save_grid_preference(self):
        """Save grid visibility preference"""
        self.app.config.set('appearance.show_grid', self.show_grid_var.get())
        self._show_pref_saved()
    
    def _save_dpi_preference(self, event=None):
        """Save graph DPI preference"""
        self.app.config.set('export.graph_dpi', self.dpi_var.get())
        self._show_pref_saved()
    
    def _save_decimal_preference(self):
        """Save decimal places preference"""
        self.app.config.set('export.decimal_places', self.decimal_var.get())
        self._show_pref_saved()
    
    def _reset_preferences(self):
        """Reset all preferences to defaults"""
        if messagebox.askyesno("Reset Preferences", 
                              "Reset all preferences to default values?"):
            self.app.config.config = self.app.config.default_config()
            self.app.config.save_config()
            
            # Update UI variables
            self.basis_var.set("RECOVERED")
            self.font_size_var.set(10)
            self.show_grid_var.set(True)
            self.dpi_var.set(300)
            self.decimal_var.set(4)
            
            self.pref_status.config(text="✓ Preferences reset to defaults", fg='#27ae60')
            messagebox.showinfo("Reset Complete", "All preferences have been reset.")
    
    def _show_pref_saved(self):
        """Show temporary 'saved' message"""
        self.pref_status.config(text="✓ Preference saved", fg='#27ae60')
        self.after(2000, lambda: self.pref_status.config(text=""))
    
    def setup_readme_tab(self, parent):
        """Setup the Read-me and License tab with author information"""
        # Create text widget with scrollbar
        text_frame = tk.Frame(parent)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text = tk.Text(text_frame, wrap=tk.WORD, font=('Arial', 11),
                      bg='white', fg='black')
        scrollbar = tk.Scrollbar(text_frame, command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Insert readme content
        readme_content = f"""
GRANULOGRAPH - README
{'='*60}
VERSION: 1.0
DATE: {datetime.now().strftime('%B %Y')}
DOI: https://doi.org/10.5281/zenodo.19109947  

AUTHOR:
{'='*60}
• Name: Smaine Chellat
• Email: smaine.chellat@gmail.com
• ORCID: https://orcid.org/0000-0003-4103-0436  
• Affiliation: University Constantine 1, Geological Department, Algeria
• Research Fields: Sedimentology • Environmental Geology • XRD/XRF Analysis

DESCRIPTION:
{'='*60}
GranuloGraph is a comprehensive granulometry analysis application
designed for sedimentologists, engineering geologists, and civil
engineers. It provides tools for sieve analysis, statistical
parameters calculation, and data visualization using Folk & Ward (1957) methodology.

FEATURES:
{'='*60}
• Data Entry: Interactive spreadsheet-like interface for sieve data
• Multiple Series: Compare up to 10 samples simultaneously
• Statistical Parameters: Folk & Ward (1957) calculations
  - Graphic Mean (Mz)
  - Inclusive Graphic Standard Deviation (Sorting)
  - Skewness (Sk)
  - Kurtosis (KG)
• Geotechnical Indices:
  - Uniformity Coefficient (Cu)
  - Curvature Coefficient (Cc)
  - Fineness Modulus (FM) - BS EN 12620
• Percentiles: 5%, 16%, 25%, 50%, 75%, 84%, 95%
• Visualization:
  - Cumulative curves (semi-log)
  - Frequency curves
  - Wentworth classification bands
  - Correlation plots (Friedman, 1967; Passega, 1969)
• Export: Graphs (PNG, JPG, TIFF, PDF) and Results (CSV, Excel)

INSTALLATION:
{'='*60}
1. Install Python 3.11 or higher from python.org
2. Install dependencies: pip install -r requirements.txt
3. Run: python main.py
4. Or build executable: run build_exe.bat

USAGE:
{'='*60}
1. Enter initial sample weight
2. Enter sieve diameters and retained weights (at least 10 sieves)
3. Select calculation basis:
   • 🔬 Recovered Weight (ASTM): Research, journals, sedimentology
   • 🏗️ Initial Weight (NF/ISO): Geotechnical reports, engineering
4. Click "Validate Data" to check for errors
5. Click "Display Graph" to visualize cumulative curve
6. Use right panel for statistical analysis
7. Export results as needed

REFERENCES:
{'='*60}
• Folk, R.L. and Ward, W.C. (1957) - Statistical parameters
• Wentworth, C.K. (1922) - Grain size classification
• Friedman, G.M. (1967) - Dynamic processes
• BS EN 12620 - Aggregates for concrete
• Passega & Byramjee (1969) - C-M diagram

LICENSE:
{'='*60}
MIT License - See LICENSE file for details

CONTACT:
{'='*60}
For questions, collaboration, or bug reports:

• Name: Smaine Chellat
• Email: smaine.chellat@gmail.com
• Department: Geological Department
• Institution: University Constantine 1
• Address: Constantine, Algeria
• ORCID: https://orcid.org/0000-0003-4103-0436  
• Zenodo DOI: https://doi.org/10.5281/zenodo.19109947  

CITATION:
{'='*60}
If you use GranuloGraph in your research, please cite:

Chellat, S. (2026). GranuloGraph: A granulometry analysis 
application for sedimentology and engineering geology 
[Computer software]. Zenodo. 
https://doi.org/10.5281/zenodo.19109947  

© 2026 Smaine Chellat, University Constantine 1. All Rights Reserved.
"""
        text.insert('1.0', readme_content)
        text.config(state=tk.DISABLED)
    
    def setup_about_tab(self, parent):
        """Setup the About and Contact tab with author information"""
        # Create scrollable frame
        canvas = tk.Canvas(parent, bg='white')
        scrollbar = tk.Scrollbar(parent, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # === AUTHOR HEADER ===
        header_frame = tk.Frame(scrollable_frame, bg='#2c3e50')
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(header_frame, text="GranuloGraph",
                font=('Arial', 24, 'bold'), bg='#2c3e50', fg='white').pack(pady=(20, 5))
        tk.Label(header_frame, text="v1.0 • March 2026",
                font=('Arial', 12), bg='#2c3e50', fg='#bdc3c7').pack()
        
        # === AUTHOR INFORMATION ===
        author_frame = tk.LabelFrame(scrollable_frame, text="👤 Author",
                                    font=('Arial', 12, 'bold'), bg='white',
                                    padx=15, pady=10)
        author_frame.pack(fill=tk.X, padx=20, pady=10)
        
        author_info = [
            ("Name:", "Smaine Chellat"),
            ("Email:", "smaine.chellat@gmail.com"),
            ("ORCID:", "https://orcid.org/0000-0003-4103-0436"),
            ("Affiliation:", "University Constantine 1"),
            ("Department:", "Geological Department"),
            ("Location:", "Constantine, Algeria"),
            ("Research Fields:", "Sedimentology • Environmental Geology • XRD/XRF Analysis")
        ]
        
        for label, value in author_info:
            frame = tk.Frame(author_frame, bg='white')
            frame.pack(fill=tk.X, pady=2)
            tk.Label(frame, text=label, font=('Arial', 10, 'bold'),
                    bg='white', width=15, anchor='w').pack(side=tk.LEFT)
            tk.Label(frame, text=value, font=('Arial', 10),
                    bg='white', anchor='w').pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # === DOI BADGE ===
        doi_frame = tk.Frame(scrollable_frame, bg='#ecf0f1')
        doi_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(doi_frame, text="📄 Zenodo DOI:",
                font=('Arial', 11, 'bold'), bg='#ecf0f1').pack(anchor=tk.W)
        
        doi_link = tk.Label(doi_frame, 
                           text="https://doi.org/10.5281/zenodo.19109947",
                           font=('Arial', 10), bg='#ecf0f1', fg='#3498db',
                           cursor="hand2")
        doi_link.pack(anchor=tk.W, pady=(5, 0))
        doi_link.bind("<Button-1>", lambda e: webbrowser.open_new(
            "https://doi.org/10.5281/zenodo.19109947"))
        
        # === DESCRIPTION ===
        desc_frame = tk.LabelFrame(scrollable_frame, text="📖 About GranuloGraph",
                                  font=('Arial', 12, 'bold'), bg='white',
                                  padx=15, pady=10)
        desc_frame.pack(fill=tk.X, padx=20, pady=10)
        
        desc_text = """GranuloGraph is a comprehensive granulometry analysis application 
designed for sedimentologists, engineering geologists, and civil engineers. 

Key capabilities:
• Folk & Ward (1957) statistical parameter calculations
• Geotechnical indices (Cu, Cc, Fineness Modulus) per BS EN 12620
• Interactive cumulative and frequency distribution curves
• Wentworth (1922) grain size classification visualization
• Friedman (1967) and Passega (1969) scientific diagrams
• Multi-format data import/export (CSV, Excel, PNG, PDF)

Developed for academic research and professional applications in 
sedimentology and environmental geology."""
        
        tk.Label(desc_frame, text=desc_text, font=('Arial', 10),
                bg='white', justify=tk.LEFT, wraplength=500).pack(pady=10)
        
        # === FEATURES ===
        features_frame = tk.LabelFrame(scrollable_frame, text="✨ Key Features",
                                      font=('Arial', 12, 'bold'), bg='white',
                                      padx=15, pady=10)
        features_frame.pack(fill=tk.X, padx=20, pady=10)
        
        features = [
            "✓ Folk & Ward (1957) statistical parameters",
            "✓ Geotechnical indices with engineering notes",
            "✓ Interactive cumulative and frequency curves",
            "✓ Wentworth grain size classification bands",
            "✓ Friedman (1967) beach/river discrimination diagrams",
            "✓ Passega (1969) C-M transportation mechanism diagrams",
            "✓ Multi-sample comparison and correlation analysis",
            "✓ Export to PNG, CSV, Excel, and PDF formats",
            "✓ Windows executable (no Python installation required)",
            "✓ Offline operation (no internet connection needed)"
        ]
        
        for feature in features:
            tk.Label(features_frame, text=feature,
                    font=('Arial', 10), bg='white', anchor=tk.W).pack(
                        fill=tk.X, pady=1)
        
        # === REFERENCES ===
        refs_frame = tk.LabelFrame(scrollable_frame, text="📚 Scientific References",
                                  font=('Arial', 12, 'bold'), bg='white',
                                  padx=15, pady=10)
        refs_frame.pack(fill=tk.X, padx=20, pady=10)
        
        references = [
            "Folk, R.L. & Ward, W.C. (1957). Brazos River bar: a study in the "
            "significance of grain size parameters. J. Sed. Petrol., 27, 3-27.",
            
            "Wentworth, C.K. (1922). A scale of grade and class terms for "
            "clastic sediments. J. Geol., 30, 377-392.",
            
            "Friedman, G.M. (1967). Dynamic processes and statistical parameters "
            "compared for size frequency distribution of beach and river sands. "
            "J. Sed. Petrol., 37, 327-354.",
            
            "Passega, R. & Byramjee, R. (1969). Grain-size image of clastic "
            "deposits. Sedimentology, 13, 233-252.",
            
            "BS EN 12620:2013. Aggregates for concrete. British Standards Institution."
        ]
        
        for ref in references:
            tk.Label(refs_frame, text="• " + ref, font=('Arial', 9),
                    bg='white', justify=tk.LEFT, wraplength=520).pack(
                        anchor=tk.W, pady=3)
        
        # === LICENSE ===
        license_frame = tk.LabelFrame(scrollable_frame, text="⚖️ License",
                                     font=('Arial', 12, 'bold'), bg='white',
                                     padx=15, pady=10)
        license_frame.pack(fill=tk.X, padx=20, pady=10)
        
        license_text = """MIT License © 2026 Smaine Chellat

GranuloGraph is free and open-source software. You may use, copy, modify, 
merge, publish, distribute, sublicense, and/or sell copies of the Software, 
subject to the conditions in the LICENSE file.

When using this software in academic work, please cite the Zenodo DOI:
https://doi.org/10.5281/zenodo.19109947"""
        
        tk.Label(license_frame, text=license_text, font=('Arial', 10),
                bg='white', justify=tk.LEFT, wraplength=520).pack(pady=10)
        
        # View full license button
        tk.Button(license_frame, text="View Full MIT License",
                 command=self.show_license,
                 bg='#3498db', fg='white', font=('Arial', 10),
                 padx=15, pady=5).pack(pady=5)
        
        # === CONTACT ===
        contact_frame = tk.LabelFrame(scrollable_frame, text="📬 Contact & Support",
                                     font=('Arial', 12, 'bold'), bg='white',
                                     padx=15, pady=10)
        contact_frame.pack(fill=tk.X, padx=20, pady=(10, 30))
        
        contact_info = """For questions, bug reports, or collaboration inquiries:

✉️ Email: smaine.chellat@gmail.com
🔗 ORCID: https://orcid.org/0000-0003-4103-0436
📄 DOI: https://doi.org/10.5281/zenodo.19109947
🏛️ Institution: University Constantine 1, Geological Department
📍 Location: Constantine, Algeria

Response time: Typically 1-3 business days.

When reporting issues, please include:
• Python version and operating system
• Error message or unexpected behavior description
• Sample data file (if applicable)"""
        
        tk.Label(contact_frame, text=contact_info, font=('Arial', 10),
                bg='white', justify=tk.LEFT, wraplength=520).pack(pady=10)
        
        # Email link button
        email_btn = tk.Button(contact_frame, text="✉️ Send Email to Author",
                             command=lambda: webbrowser.open_new(
                                 "mailto:smaine.chellat@gmail.com?subject=GranuloGraph%20Inquiry"),
                             bg='#27ae60', fg='white', font=('Arial', 10),
                             padx=15, pady=5)
        email_btn.pack(pady=5)
        
        # === COPYRIGHT ===
        tk.Label(scrollable_frame,
                text="© 2026 Smaine Chellat, University Constantine 1. All Rights Reserved.",
                font=('Arial', 9), bg='white', fg='#7f8c8d').pack(pady=(20, 10))
        
        # === CITATION BOX ===
        citation_frame = tk.Frame(scrollable_frame, bg='#f8f9f9', relief=tk.GROOVE, bd=1)
        citation_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(citation_frame, text="📝 How to Cite GranuloGraph",
                font=('Arial', 11, 'bold'), bg='#f8f9f9').pack(pady=(10, 5))
        
        citation_text = """Chellat, S. (2026). GranuloGraph: A granulometry analysis 
application for sedimentology and engineering geology [Computer software]. 
Zenodo. https://doi.org/10.5281/zenodo.19109947"""
        
        tk.Label(citation_frame, text=citation_text, font=('Courier', 9),
                bg='#f8f9f9', justify=tk.LEFT, wraplength=500).pack(padx=10, pady=5)
        
        # Copy citation button - ✅ FIX: Use self.parent instead of self.root
        def copy_citation():
            self.parent.clipboard_clear()  # ✅ FIX: Was self.root (doesn't exist)
            self.parent.clipboard_append(citation_text)
            messagebox.showinfo("Copied", "Citation copied to clipboard!")
        
        tk.Button(citation_frame, text="📋 Copy Citation",
                 command=copy_citation,
                 bg='#9b59b6', fg='white', font=('Arial', 9),
                 padx=10, pady=3).pack(pady=(0, 10))
    
    def show_license(self):
        """Show full MIT License in a new window"""
        license_window = tk.Toplevel(self)
        license_window.title("MIT License - GranuloGraph")
        license_window.geometry("650x550")
        
        text = tk.Text(license_window, wrap=tk.WORD, padx=15, pady=15,
                      font=('Courier', 9))
        text.pack(fill=tk.BOTH, expand=True)
        
        license_text = """MIT License

Copyright (c) 2026 Smaine Chellat, University Constantine 1, Algeria
ORCID: https://orcid.org/0000-0003-4103-0436
Contact: smaine.chellat@gmail.com

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

---

CITATION REQUIREMENT:
If you use GranuloGraph in academic research or publications, please cite:

Chellat, S. (2026). GranuloGraph: A granulometry analysis application for 
sedimentology and engineering geology [Computer software]. Zenodo. 
https://doi.org/10.5281/zenodo.19109947

---

CONTACT FOR LICENSING QUESTIONS:
Smaine Chellat
Geological Department, University Constantine 1
Constantine, Algeria
Email: smaine.chellat@gmail.com
ORCID: https://orcid.org/0000-0003-4103-0436"""
        
        text.insert('1.0', license_text)
        text.config(state=tk.DISABLED)