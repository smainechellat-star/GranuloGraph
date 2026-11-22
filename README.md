# GranuloGraph v2.0 - Granulometry Analysis Software

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24435516.svg)](https://doi.org/10.5281/zenodo.24435516)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)

> **A comprehensive granulometry analysis application for sedimentology and engineering geology**

---

## 👤 Author

| Field | Information |
|-------|-------------|
| **Name** | Smaine Chellat |
| **Email** | [smaine.chellat@gmail.com](mailto:smaine.chellat@gmail.com) |
| **ORCID** | [https://orcid.org/0000-0003-4103-0436](https://orcid.org/0000-0003-4103-0436) |
| **Affiliation** | University Constantine 1, Geological Department, Algeria |
| **Research Fields** | Sedimentology • Environmental Geology • XRD/XRF Analysis |

---

## 📖 Overview

**GranuloGraph v2.0** is a desktop application (Python/Tkinter/Matplotlib) designed for sedimentologists, engineering geologists, and civil engineers. It covers the complete sieve-analysis workflow: data entry, automatic validation, statistical parameter calculation (**Folk & Ward, 1957**), geotechnical grading indices, environmental discrimination diagrams, and publication-ready exports.

### 🔬 Dual Calculation Methods

GranuloGraph supports **two calculation bases** to comply with different international standards:

| Method | Standard | Use Case |
|--------|----------|----------|
| **🔬 Recovered Weight** | ASTM D6913 §11.2 | Research papers, journals, sedimentology statistics (ensures a full 0–100 % curve) |
| **🏗️ Initial Weight** | NF P 94-056 / ISO 17892-4 | Geotechnical reports, Algerian/French engineering standards |

> 💡 **Tip**: Select the basis in the **Home Screen** dropdown (the active method is shown live next to it — *🔬 ASTM (Research)* / *🏗️ NF/ISO (Geotech)*) or set a default in **Settings → Preferences**. The choice is confirmed before the graph is drawn and is stamped into every export.

---

## 🎯 Key Features

### 📊 Data Management (Home Screen)
- ✅ Interactive spreadsheet-like data grid (starts with 10 rows, add/remove rows freely)
- ✅ **Multiple samples side by side**: one diameter column + one column per sample (add/delete columns at any time)
- ✅ **Pan support**: type `Pan` or `Bottom` in the diameter field (exactly one pan row per sample)
- ✅ Import: **CSV, Excel (.xlsx/.xls), TXT** — automatically detects `;` separators, decimal commas and thousands spaces (European files such as `31,5` are handled), tabs, and an optional third column holding the initial weight
- ✅ Save data as CSV/Excel with metadata columns (`Diameter_mm`, `Weight_g`, `Initial_Weight_g`, `Calculation_Basis`)
- ✅ Automatic validation with explicit error messages and recovery-percentage quality alerts

### 🧭 Provenance & Environmental Context
- ✅ **Mandatory provenance selection per sample** from 18 environments: Continental (alluvial fans, fluvial, lacustrine, aeolian, glacial, paludal), Transitional (deltas, beaches, lagoons, tidal flats, estuaries) and Marine (shelf, organic reefs, slope, abyssal plain), plus *Unknown*, *Natural – Unconfirmed* and *Crushed / Quarry*
- ✅ Built-in **Provenance Environment Guide** (description window per environment) and per-dropdown tooltips
- ✅ Provenance-aware science: samples marked **Crushed / Quarry** are excluded from Friedman & Passega discrimination (anthropogenic material), and samples with *Unknown / Unconfirmed* provenance are plotted with a grey **X** marker

### 📈 Statistical Calculations (Folk & Ward, 1957)
- ✅ **Central Tendency**: Graphic Mean (Mz), Median, Mode (with parabolic refinement)
- ✅ **Sorting**: Inclusive Graphic Standard Deviation (σI) — *7-class Folk & Ward scale*
- ✅ **Skewness**: Folk & Ward skewness coefficient (Sk) — *5-class interpretation*
- ✅ **Kurtosis**: Graphic Kurtosis (KG) — *6-class Folk & Ward scale*
- ✅ **Percentiles**: D5, D10, D16, D25, D30, D50, D60, D70, D75, D84, D90, D95 (mm & φ) for every sample

### ⚙ Geotechnical Indices (BS EN 12620 / ASTM D2487)
- ✅ **Uniformity Coefficient (Cu)**: D60/D10 with grading classification
- ✅ **Curvature Coefficient (Cc)**: (D30)²/(D10×D60) with well-graded assessment
- ✅ **Fineness Modulus (FM)**: with practical engineering notes for concrete applications (FM 2.6–2.9: high-quality concrete)

### 🎨 Advanced Visualization (Graph Screen)
- ✅ Cumulative curves on a semi-log axis (fine 10⁻⁴ mm on the left → coarse 10³ mm on the right) with classification bands and grain-size class labels on the top axis
- ✅ **Graph title in the empty band**: the *Grain Size Distribution Curve* title is drawn **above the ISO/ASTM class labels** (figure-level position, so it scales with the window and never slides into the header bars on large/maximized windows); the class-type labels (ISO / ASTM bands) stay right below it
- ✅ **Classification Standard selector** — *Classes (bands):* checkboxes (**ISO** blue / **ASTM** orange) in the top toolbar right next to *☑ Curves*. These checkboxes toggle **only the classification bands drawn above the graph** — they never add, remove or split curves: a sample always keeps the same cumulative and frequency curve (the standards differ in class boundaries and in the exported fractions, not in the curve itself). Hover any of them for a tooltip with the exact class limits:
  - ☑ ISO only → single **ISO 14688-1:2017** header bar (Clay | Silt | Sand | Gravel | Cobbles | Boulders)
  - ☑ ASTM only → single **ASTM D2487 / USCS** header bar (Fines | Sand | Gravel | Cobbles) at 0.075 / 4.75 / 75 mm
  - ☑☑ Both → **stacked dual header bars** (ISO on top, ASTM underneath) + dashed ASTM cutoff lines — both standards readable at once
  - ☐☐ None → plain cumulative curve without class bars
- ✅ **Calculation-basis comparison** (*⚖ Compare bases* checkbox in the top toolbar): for every displayed sample, draws an extra **dotted curve in the same colour** recomputed with the *other* calculation basis — **solid = active basis** (Home Screen), **dotted = the other one** (ASTM D6913 recovered weight ↔ NF P94-056/ISO initial weight). The dotted trace appears **only where the two bases actually differ** (segments with a gap < 0.2 % are masked), so a 100 %-recovery sample shows no dotted line at all, and the horizontal/vertical gap between the two curves shows exactly how much mass normalization shifts the percentiles. A legend entry (*dotted = other basis: …*) states the convention. Display-only: exports always use the active basis
- ✅ **Frequency distribution curves** toggle (*📈 Display Frequency Curves*): f(x) = dF/d(log₁₀ d) on a secondary axis
- ✅ Smooth interpolated curves (monotone spline over the sieve points) with distinct colors per sample
- ✅ **Per-sample curve selection** with cross checkboxes: *☑ Curves* (next to the *Series* box, top-right toolbar) and *☑ Frequency Curves* (bottom-left, next to the frequency toggle) open a panel listing every sample — check/uncheck individual samples, or use *☑ Select All / ☐ Deselect All*; the graph redraws instantly and the selection is remembered. The panel always opens **fully on screen** (it flips above the button when the button is near the bottom edge of the window). Display-only: exports and PDF reports always include every sample
- ✅ **Cursor tracking**: real-time diameter / % passing readout in the side panel
- ✅ **Percentile projection tool**: enter any percentage (0–100 %) → get the corresponding diameter for the selected sample
- ✅ **Key Percentiles panel**: P5–P95 table (mm + φ) for every sample at a glance, including the pan summary
- ✅ Full Matplotlib navigation toolbar (zoom, pan, save) with publication-quality output

### 🔬 Scientific Diagrams
- ✅ **Dual-basis convention on every bivariate diagram**: each sample is drawn **twice in the same colour** — **filled circle = ASTM D6913 (recovered weight)** and **open circle = ISO 17892-4 / NF P94-056 (initial weight)** — with a thin grey link between the two circles showing the shift caused by the calculation basis; a legend on every panel spells out the filled/open rule (Unknown/Unconfirmed provenance keeps the grey **X** pair)
- ✅ **Friedman (1967)**: four discrimination diagrams (① Sk–KG, ② Sk–Sorting, ③ Sk–Mz, ④ Mz–Sorting) with beach-sands / river-sands fields and the dual-basis filled/open circles
- ✅ **Passega C-M diagram (Passega & Byramjee, 1969)**: C (1st percentile) vs M (median) with suspension/saltation/rolling provinces — dual-basis plot comparing **ASTM D6913 (filled) vs ISO 17892-4 (open)** positions per sample with linking arrows and `(A)`/`(I)` labels
- ✅ **Ternary classification diagrams** (button right below *Passega C-M Diagram*): side-by-side **Folk (1954) Gravel–Sand–Mud** and **Shepard (1954) Sand–Silt–Clay** diagrams with all classification fields (G, sG, msG, mG, gS, gmS, gM, (g)S… for Folk; Sand, Silty Sand, Clayey Sand, Sandy Silt… for Shepard). Fractions are integrated from the PCHIP curve (gravel > 2 mm · sand 0.0625–2 mm · silt 0.004–0.0625 mm · clay < 0.004 mm); Shepard renormalizes Sand–Silt–Clay to 100 % excluding gravel; provenance-aware markers (grey **X** = Unknown/Unconfirmed, Crushed/Quarry kept for display)
- ✅ **Correlation Graphs**: skewness–kurtosis, mean–sorting, mean–FM scatter plots (each sample = filled ASTM circle + open ISO circle with shift link) + multi-parameter correlation-matrix heatmap
- ✅ **Distribution graphs (GRADISTAT-style)** (button right below *Ternary Diagrams*): per-sieve **Class Weight (%)** in two side-by-side panels — **φ linear scale** (coarse → fine) and **μm logarithmic scale** — all samples overlaid with smooth PCHIP curves through the sieve points; the pan class is anchored ½ log-decade below the finest sieve and the active basis (ASTM recovered / ISO initial weight) is respected
- ✅ **Bland-Altman Dual-Basis Comparison** (button right below *Distribution Graphs*, needs ≥ 2 samples): two stacked panels — **a) D50 (median grain size)** and **b) Folk-Ward Inclusive Graphic Standard Deviation (σI)** — plotting the **difference (ISO − ASTM)** against the **average of the two bases** (both in φ). Each panel draws the **zero line** (red dotted), the **mean bias** (black solid) and the **±1.96 SD limits of agreement** (grey dashed, labeled with their values); points are **colour-coded by recovery loss 100·(M₀ − Mr)/M₀** (< 2 % blue · 2–5 % orange · > 5 % red) with sample names annotated above the bias line and a recovery-loss legend on panel b. A point close to the zero line means both calculation bases agree for that sample — the vertical offset is exactly the shift caused by the recovered-vs-initial mass normalization

### 💾 Export Options (all from the Graph Screen export menu)
- ✅ **Main graph**: PNG (300 DPI), PDF, JPG, TIFF (150 DPI) — also from *File → Export Graph*
- ✅ **Results**: CSV or formatted Excel (.xlsx) including the calculation basis, recovery metadata and the **ISO 14688-1 + ASTM D2487 size-fraction columns (%)**
- ✅ **All Parameters**: one CSV/XLSX/TXT file combining, for every sample: declared provenance, calculation basis, software-suggested environment (Friedman skewness rule) and transport mechanism (Passega), all percentiles (mm + φ), central-tendency values, sorting/skewness/kurtosis **with their classes**, Cu/Cc/FM **with their classes**, the pan summary, and two clearly labeled blocks — **ISO 14688-1 Fractions (%)** and **ASTM D2487 Fractions (%)**
- ✅ **📄 Multi-page PDF report** (new in v2.0 — built with Matplotlib, no extra dependency):
  - *Page 1*: report header (date, calculation basis, sample list, initial weight) + overlay of all cumulative curves with legend and ISO boundaries
  - *One A4 sheet per sample*: curve with **D10 / D30 / D50 / D60 markers**, declared provenance, and the full parameter block (percentiles + φ, PAN, central tendency, σI/Sk/KG classes, Cu/Cc/FM classes, **ISO 14688-1 & ASTM D2487 fractions**, QC recovery line)
  - PDF metadata (title, author, subject, keywords) embedded automatically
- ✅ Dedicated one-click exports for the Friedman diagrams, the Passega diagram, the **ternary diagrams (Folk/Shepard — PNG 300 DPI or PDF)**, the **distribution graphs (φ & μm — PNG/PDF)**, the **Bland-Altman plot (⚖ — PNG/PDF)** and the correlation graph — the Friedman and Passega exports render the same dual-basis filled/open circles and legend as the on-screen windows

---

## 🚀 Quick Start Workflow

1. **Enter data** on the Home Screen: set the *Initial Sample Weight (g)*, choose the *Calculation Basis*, then fill the grid — first column = sieve diameters (mm, **descending**), one additional column per sample (retained weights, g). Type `Pan`/`Bottom` on the last row if you have a pan fraction.
2. **Add samples** with *➕ Add Column* and select the **Provenance** of each sample from its dropdown (mandatory — validation blocks missing selections).
3. **Validate** (*✓ Validate Data*): the app checks sieves ≥ 4 per sample, descending order, a single pan row, and computes recovery. Sieving loss > 0.5 % raises the ASTM D6913 warning.
4. **Display Graph** → confirm the method → the Graph Screen opens with all cumulative curves.
5. **Analyse**: hover the curve for live readings, project percentiles, toggle frequency curves (*📈 Display Frequency Curves*), choose which samples are displayed (*☑ Curves* / *☑ Frequency Curves*), and open the Sedimentological / Geotechnical / Correlation / Friedman / Passega tools from the side panel.
6. **Export**: graphs, results, all-parameters tables or the multi-page PDF report from the 💾 Export menu.

> 📘 For the full click-by-click procedure (21 steps), follow the **Step-by-Step User Guide** below.

## 📘 Step-by-Step User Guide (follow the steps in order)

### 🏠 Part A — Home Screen (Data Entry)

**1. Import the data file.** Click **📂 Import CSV/Excel/TXT** and select the file from its destination source (or type the values directly in the grid: first column = sieve diameters (mm) in **descending** order, one column per sample = retained weights (g); type `Pan`/`Bottom` on the last row if you kept a pan fraction).

**2. Set the Initial Weight (grams).** Enter the dry mass of each sample before sieving — it is the reference mass for every percentage of that sample.

**3. Set the Calculation Basis (ASTM / ISO).** Use the *Calculation Basis* dropdown:
- **Recovered → 🔬 ASTM D6913** (research standard: percentages on the recovered mass, full 0–100 % curve);
- **Initial → 🏗️ NF P 94-056 / ISO 17892-4** (geotechnical standard: percentages on the initial dry mass).

**4. Select the Provenance of the sample(s).** Open the dropdown under each sample column and declare what the material is:
- **Crushed / Quarry** → anthropogenic crushed rock material;
- **Natural material with a known sedimentary environment** → pick the exact environment (Continental / Transitional / Marine families);
- **Natural material with an unknown sedimentary environment** → choose *Unknown* or *Natural – Unconfirmed*.

A tooltip on each dropdown describes the selected provenance.

**5. Click ✓ Validate Data — before displaying the graph.** The app checks the minimum number of sieves (≥ 4), the descending order, the single pan row and the recovery percentage, and reports any problem at this stage.

**6. Click 📊 Display Graph** to go to the Graph Screen, then confirm the calculation method in the dialog that appears.

### 📈 Part B — Graph Screen (Analysis)

**7. The class (ASTM / ISO) set on the Home Screen is already selected as default.** To see the *other* class subdivision (ISO ↔ ASTM), just tick the other box in **Classes (bands): ISO / ASTM** at the top of the toolbar (tick both → the two class bars are stacked; untick both → plain curve without class bands).

**8. To display the curve under the other calculation basis**, tick **⚖ Compare bases** at the top: a **dotted curve in the same colour** (the other basis) is drawn next to the solid curve of your active basis — the gap between them is the recovered-vs-initial shift.

**9. Green ☑ Curves button (top toolbar)** opens the per-sample selection panel: tick/untick each cumulative curve, or use ☑ Select All / ☐ Deselect All.

**10. Magenta ☑ Frequency Curves button (bottom)** opens the same selection panel for the frequency curves.

**11. Blue 📈 Display Frequency Curves button (bottom left)** shows / hides the frequency distribution curves (it turns red 📉 *Hide Frequency Curves* while they are displayed).

**12. 🎯 Project Value box:** enter any percentage (0–100 %) and the software reads the corresponding diameter (mm) from the selected sample's curve.

**13. 📊 Key Percentiles panel (right side)** — P5–P95 table (mm + φ) for every sample, including the pan.

**14. ⚙ Geotechnical Parameters** — Cu, Cc and Fineness Modulus with their classifications.

**15. 🔄 Correlation Graphs** — skewness–kurtosis, mean–sorting and mean–FM scatter plots + correlation heatmap.

**16. 📈 Friedman (1967) Plots** — beach-sands / river-sands discrimination diagrams. **Displayed only if the samples are natural with a determined environment:** *Crushed / Quarry* samples are excluded from these diagrams, and *Unknown / Unconfirmed* samples are plotted as a grey **X** marker.

**17. 📉 Passega C-M Diagram** — C–M transport provinces. Same provenance rule as Friedman.

**18. 🌐 Ternary Diagrams** — Folk (1954) and Shepard (1954) classifications side by side.

**19. 📊 Distribution Graphs** — GRADISTAT-style per-sieve class weights in φ and μm/mm.

**20. ⚖ Bland-Altman (ISO vs ASTM)** — dual-basis agreement plot of the two calculation bases (needs ≥ 2 samples).

**21. 💾 Export button** — export and save the different parameters and graphs under **CSV, Excel (.xlsx), PNG or PDF** format: main graph, results, all parameters, plus dedicated exports for the Friedman plots, Passega diagram, ternary diagrams, distribution graphs, Bland-Altman plot and correlation graph.

## 📜 Menu Reference

| Menu | Commands |
|------|----------|
| **File** | New Session · Open Data (CSV/XLSX/XLS/TXT/GRL) · Save Data (CSV/XLSX) · Export Graph · Export Results · Export Text Report · Exit |
| **View** | Home · Graph · Settings |
| **Tools** | Calculate Parameters (tabbed window: Sedimentological / Geotechnical / Percentiles + recovery bar) · Compare Series · Preferences |
| **Help** | Documentation · About |

---

## 📦 Installation

### Requirements
- **Python**: 3.11 or higher (tested with 3.11, 3.12, 3.13)
- **OS**: Windows 10/11 (for the executable), Linux/macOS (from source)
- **Disk Space**: ~200 MB
- **RAM**: 4 GB minimum, 8 GB recommended for large datasets

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| numpy | >= 2.0, < 3.0 | Array operations, numerical computations |
| scipy | >= 1.14, < 2.0 | CubicSpline / PchipInterpolator used for the smooth curves |
| pandas | >= 2.2, < 3.0 | Data handling, CSV/Excel I/O |
| matplotlib | >= 3.9, < 4.0 | Graph rendering, TkAgg backend, PDF report (PdfPages) |
| openpyxl | >= 3.1.5, < 4.0 | Read/write .xlsx files |
| xlrd | >= 2.0.1, < 3.0 | Read legacy .xls files |
| pillow | >= 10.3, < 11.0 | Image I/O for figure export |
| pyinstaller | >= 6.7 (optional) | Building the Windows .exe |

> ℹ️ The PDF report uses Matplotlib's built-in `PdfPages` — **no extra PDF library is required**. *tkinter* ships with the official Python installer (make sure the *tcl/tk* option is checked); on Linux install `python3-tk`, on macOS `brew install python-tk`.

### Method 1: From Source (Recommended for Development)
```bash
# 1. Clone or download the repository
git clone https://github.com/schellat/GranuloGraph.git
cd GranuloGraph

# 2. Create a virtual environment (recommended)
python -m venv venv

# 3. Activate it
venv\Scripts\activate          # Windows CMD
# or
source venv/bin/activate       # macOS/Linux

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the application
python main.py
```

### Method 2: Windows Executable
Build a standalone .exe with the included PyInstaller script:
```bash
run build_exe.bat
```
The build bundles `icon.ico` and all assets (`resource_path()` handles the frozen-app paths). The resulting .exe may trigger a Windows Defender warning — add an exclusion if needed.

### Method 3: Windows Installer (Inno Setup)
For end-user distribution, build the standalone .exe (Method 2), then compile the installer:
```bash
ISCC.exe GranuloGraph.iss        # or open GranuloGraph.iss in the Inno Setup GUI
```
The setup (`installer_output\GranuloGraph_v2.0_setup.exe`) installs `GranuloGraph.exe`, `README.md`, `LICENSE.txt`, `POST_INSTALL_INFO.txt` and `sample_data\example_data.csv`, creates the Start-Menu / optional desktop shortcuts and the Add/Remove Programs entry (uninstall key `GranuloGraph_is1`). The optional `Registry key.reg` adds the **.grl** file association, App Paths and default preferences — import it manually if you want **.grl** (GranuloGraph Data File) datasets to open by double-click and via *File → Open Data*.

---

## 🗂 Project Structure

```
GranuloGraph/
├── main.py               # Entry point: GranuloGraph app class, menus, navigation, error handling
├── home_screen.py        # Data-entry grid, provenance dropdowns, validation, import/save
├── graph_screen.py       # Main plot, statistics windows, Friedman/Passega/correlation, Folk & Shepard ternary diagrams, distribution graphs, exports, PDF report
├── settings_screen.py    # Settings & preferences screen (defaults persistence)
├── calculations.py       # GranuloCalculator: Folk & Ward parameters, percentiles, curves, pan handling, size fractions (ternary)
├── utils.py              # DataValidator, FileHandler (CSV/Excel/TXT + calculation-basis metadata), ConfigManager, UnitConverter (mm/φ/Wentworth/ISO 14688), StatisticsHelper (Folk & Ward class scales), ReportGenerator (formatted text report)
├── requirements.txt      # Pinned dependencies (see table above)
├── build_exe.bat         # PyInstaller build script (Windows executable)
├── GranuloGraph.iss      # Inno Setup installer script (Method 3 above)
├── Registry key.reg      # Optional Windows integration: .grl file association, App Paths, per-user preferences
├── version_info.txt      # Executable version metadata
├── LICENSE.txt           # MIT License + Zenodo citation entry
├── POST_INSTALL_INFO.txt # Welcome note shipped by the installer
├── example_data.csv      # Sample dataset installed to sample_data\ (File → Open Data)
└── icon.ico              # Application icon
```

---

## ✅ Validation Rules (ASTM D6913 compliant)

| Check | Rule |
|-------|------|
| Provenance | Every sample must have a provenance selected before calculations |
| Minimum data | At least **4 sieves** (plus the pan) per sample |
| Ordering | Sieve diameters must be in **descending** order |
| Pan rows | Exactly **one** `Pan`/`Bottom` row per sample |
| Initial weight | Must be positive |
| Sieving loss | Loss > **0.5 %** triggers the ASTM D6913 warning; negative loss (total > initial) is also flagged |

---

## 🛠 Troubleshooting

- **First launch is slow (10–30 s)**: Matplotlib is building its font cache — this happens only once.
- **Backend / Tcl errors**: verify tkinter is installed (`python -c "import tkinter; tkinter._test()"`); on Linux: `sudo apt install python3-tk`, on macOS: `brew install python-tk`.
- **pip install fails**: upgrade pip first (`python -m pip install --upgrade pip`); for numpy/scipy build issues on Windows install the Microsoft C++ Build Tools.
- **Application crash**: unexpected exceptions are written to `error.log` next to the program and shown in a dialog — include that file when reporting an issue.
- **.exe fails to launch**: run it from a command prompt to see the error; check missing DLLs with [Dependencies](https://github.com/lucasg/Dependencies).

---

## 📚 References & Standards

- Folk, R.L. & Ward, W.C. (1957): *Brazos River bar: a study in the significance of grain size parameters*. — Journal of Sedimentary Petrology, 27, 3–26.
- Friedman, G.M. (1967): *Dynamic processes and statistical parameters compared for size frequency distribution of beach and river sands*. — Journal of Sedimentary Petrology, 37, 327–354.
- Passega, R. & Byramjee, R. (1969): *Grain size image of clastic deposits*. — Sedimentology, 13, 233–252.
- ASTM D6913 — Standard Test Methods for Particle-Size Distribution (Gradation) of Soils Using the Sieve Analysis.
- NF P 94-056 / ISO 17892-4 — Granulometric analysis / Sieve analysis (geotechnical).
- ISO 14688-1:2017 — Geotechnical investigation and testing — Identification and classification of soil.
- Wentworth, C.K. (1922): *A scale of grade and class terms for clastic sediments*.

---

## 📝 Citation

If you use GranuloGraph in your research, please cite it via its Zenodo DOI:

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.24435516.svg)](https://doi.org/10.5281/zenodo.24435516)

```bibtex
@software{chellat2026granulograph,
  author = {Chellat, Smaine},
  title = {GranuloGraph: A granulometry analysis application for sedimentology and engineering geology},
  year = {2026},
  publisher = {Zenodo},
  version = {2.0},
  doi = {10.5281/zenodo.24435516},
  url = {https://doi.org/10.5281/zenodo.24435516}
}
```

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE.txt](LICENSE.txt) file.
© 2026 Smaine Chellat, University Constantine 1.
