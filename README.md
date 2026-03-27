# GranuloGraph - Granulometry Analysis Software

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19109947.svg)](https://doi.org/10.5281/zenodo.19109947)
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

**GranuloGraph** is a comprehensive granulometry analysis application designed for sedimentologists, engineering geologists, and civil engineers. It provides tools for sieve analysis, statistical parameters calculation, and data visualization using **Folk & Ward (1957)** methodology.

### 🔬 Dual Calculation Methods
GranuloGraph supports **two calculation bases** to comply with different international standards:

| Method | Standard | Use Case |
|--------|----------|----------|
| **🔬 Recovered Weight** | ASTM D6913 §11.2 | Research papers, journals, sedimentology statistics |
| **🏗️ Initial Weight** | NF P 94-056 / ISO 17892-4 | Geotechnical reports, Algerian/French engineering standards |

> 💡 **Tip**: Select your preferred method in the Home Screen dropdown or set a default in Settings → Preferences.

---

## 🎯 Key Features

### 📊 Data Management
- ✅ Interactive spreadsheet-like interface for sieve data entry
- ✅ Import/Export: CSV, Excel (.xlsx), Text files
- ✅ Multiple series comparison (up to 10 samples simultaneously)
- ✅ Automatic data validation with error warnings
- ✅ Recovery percentage calculation with quality alerts

### 📈 Statistical Calculations (Folk & Ward, 1957)
- ✅ **Central Tendency**: Graphic Mean (Mz), Median, Mode (with parabolic refinement)
- ✅ **Sorting**: Inclusive Graphic Standard Deviation (σI) — *7-class Folk & Ward scale*
- ✅ **Skewness**: Folk & Ward skewness coefficient (Sk) — *5-class interpretation*
- ✅ **Kurtosis**: Graphic Kurtosis (KG) — *6-class Folk & Ward scale*
- ✅ **Percentiles**: D5, D10, D16, D25, D30, D50, D60, D70, D75, D84, D90, D95 (mm & φ)

### ⚙ Geotechnical Indices (BS EN 12620 / ASTM D2487)
- ✅ **Uniformity Coefficient (Cu)**: D60/D10 with grading classification
- ✅ **Curvature Coefficient (Cc)**: (D30)²/(D10×D60) with well-graded assessment
- ✅ **Fineness Modulus (FM)**: With practical engineering notes for concrete applications

### 🎨 Advanced Visualization
- ✅ Cumulative curves (semi-log scale) with ISO 14688-1:2017 classification bands
- ✅ Frequency distribution curves (toggle on/off)
- ✅ Wentworth (1922) grain size classification labels
- ✅ Cursor tracking with real-time diameter/%passing display
- ✅ Percentile projection tool (enter % → get diameter)
- ✅ Multi-series overlay with distinct colors

### 🔬 Scientific Diagrams
- ✅ **Friedman (1967)**: Skewness vs Sorting discrimination diagrams (beach vs river sands)
- ✅ **Passega & Byramjee (1969)**: C-M diagram for sediment transportation mechanisms
- ✅ **Correlation matrices**: Multi-parameter statistical relationships (heatmaps)

### 💾 Export Options
- ✅ **Graphs**: PNG, JPG, TIFF, PDF (configurable DPI: 150-600)
- ✅ **Results**: CSV, Excel with formatted tables + calculation basis metadata
- ✅ **Reports**: Comprehensive text/PDF reports with parameters + interpretations + citations

---

## 📦 Installation

### Requirements
- **Python**: 3.11 or higher (tested with 3.11, 3.12, 3.13)
- **OS**: Windows 10/11 (for executable), Linux/macOS (source only)
- **Disk Space**: ~200 MB
- **RAM**: 4 GB minimum, 8 GB recommended for large datasets

### Method 1: From Source (Recommended for Development)
```bash
# 1. Clone or download the repository
git clone https://github.com/smainechellat/GranuloGraph.git
cd GranuloGraph

# 2. Create virtual environment (recommended)
python -m venv venv

# 3. Activate virtual environment
venv\Scripts\activate          # Windows CMD
# or
source venv/bin/activate       # macOS/Linux

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the application
python main.py
