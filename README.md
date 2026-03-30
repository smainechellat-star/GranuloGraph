# GranuloGraph

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19109947.svg)](https://doi.org/10.5281/zenodo.19109947)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)

> **A comprehensive, open-source desktop application for granulometric analysis supporting dual international standards (ASTM & NF/ISO).**

---

## 🚀 Quick Start: Download & Run (No Installation Required)

For users who want to run the software immediately without installing Python:

🔗 **Download the Pre-compiled Windows Executable here:**  
👉 **[Zenodo Archive (DOI: 10.5281/zenodo.19109947)](https://doi.org/10.5281/zenodo.19109947)**

1.  Click the link above.
2.  Under **"Files"**, download `GranuloGraph_Setup.exe`.
3.  Run the installer. The application is ready to use instantly.
4.  **Test it now:** Use the included `sample_data.csv` (also on Zenodo) to verify results immediately.

---

## 👤 Author & Contact

| Field | Information |
|-------|-------------|
| **Author** | Prof. Smaine CHELLAT |
| **Affiliation** | Laboratory of Geology and Environment, University Constantine 1, Algeria |
| **Email** | [smaine.chellat@umc.edu.dz](mailto:smaine.chellat@umc.edu.dz) \| [smaine.chellat@gmail.com](mailto:smaine.chellat@gmail.com) |
| **ORCID** | [0000-0003-4103-0436](https://orcid.org/0000-0003-4103-0436) |
| **Phone** | +213 699 390 172 |

---

## 📖 Overview

**GranuloGraph** is a robust Python-based desktop application designed to modernize grain-size analysis for sedimentologists, engineering geologists, and civil engineers. It replaces error-prone spreadsheet methods with a dedicated, validated interface that supports **dual calculation standards**, interactive visualization, and automated batch processing.

### 🔬 Dual Calculation Standards
GranuloGraph is the first tool to seamlessly switch between research and engineering protocols within the same interface:

| Method | Standard | Use Case |
|--------|----------|----------|
| **🔬 Recovered Weight** | **ASTM D6913** §11.2 | International research papers, sedimentological statistics. |
| **🏗️ Initial Weight** | **NF P 94-056 / ISO 17892-4** | Geotechnical reports (Algeria, France, Europe), official engineering submissions. |

> 💡 **Why this matters:** The choice of basis (recovered vs. initial) significantly affects percentage calculations and recovery validation. GranuloGraph automates this distinction, preventing common manual errors.

---

## ✅ Validation & Testing (Proof of Functionality)

To ensure scientific reliability, GranuloGraph has undergone rigorous validation against industry benchmarks:

*   **Dataset:** Tested on **15 diverse geological samples** from Algeria (Cretaceous to Quaternary), including crushed aggregates, aeolian sands, and fluvial deposits.
*   **Benchmarks:** Results compared against:
    1.  Manual calculations in Microsoft Excel.
    2.  **Gradistat Excel** (Blott & Pye, 2001), the current community standard.
*   **Results:**
    *   **Correlation Coefficient ($R^2$): > 0.999** for all percentile values ($D_5$ to $D_{95}$).
    *   **Statistical Parameters:** Deviations in Sorting ($\sigma_I$), Skewness ($Sk$), and Kurtosis ($K_G$) are < 1%, attributed solely to GranuloGraph’s superior **cubic spline interpolation** (vs. linear interpolation in legacy tools).
*   **Conclusion:** The software is mathematically robust and ready for peer-reviewed research and professional engineering use.

---

## 🎯 Key Features

### 📊 Data Management
*   Interactive spreadsheet-like interface for sieve data entry.
*   Import/Export: CSV, Excel (.xlsx), Text files.
*   **Batch Processing:** Analyze up to **10 samples simultaneously**.
*   Automatic data validation (positive values, sieve ordering, mass recovery alerts).

### 📈 Statistical Calculations (Folk & Ward, 1957)
*   **Central Tendency:** Graphic Mean ($M_z$), Median, Mode.
*   **Sorting:** Inclusive Graphic Standard Deviation ($\sigma_I$) — *7-class scale*.
*   **Skewness:** Folk & Ward coefficient ($Sk$) — *5-class interpretation*.
*   **Kurtosis:** Graphic Kurtosis ($K_G$) — *6-class scale*.
*   **Percentiles:** Full range ($D_5$ to $D_{95}$) in mm and $\phi$ units.

### ⚙ Geotechnical Indices (ASTM D2487 / BS EN 12620)
*   **Uniformity Coefficient ($C_u$):** With grading classification (Well/Moderately/Poorly graded).
*   **Curvature Coefficient ($C_c$):** Assessment of particle distribution shape.
*   **Fineness Modulus ($FM$):** With practical notes for concrete mix design.

### 🎨 Advanced Visualization
*   Cumulative curves (semi-log scale) with **ISO 14688-1:2017** classification bands.
*   **Interactive Cursor Tracking:** Real-time display of diameter and % passing.
*   **Percentile Projection Tool:** Enter a % to instantly find the corresponding grain size.
*   **Multi-series Overlay:** Compare up to 10 samples with distinct colors.

### 🔬 Scientific Interpretation Diagrams
*   **Friedman (1967):** Bivariate plots (Skewness vs. Sorting) to discriminate **Beach vs. River** sands.
*   **Passega & Byramjee (1969):** C-M diagrams to identify sediment transport mechanisms (Suspension, Saltation, Rolling).
*   **Correlation Matrices:** Heatmaps for multi-parameter statistical relationships.

### 💾 Export Options
*   **Graphs:** PNG, JPG, TIFF, PDF (Configurable DPI: **150–600** for publication quality).
*   **Data:** CSV/Excel with full metadata and calculation basis.
*   **Reports:** Comprehensive text summaries with automated interpretations.

---

## 📦 Installation

# GranuloGraph

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19109947.svg)](https://doi.org/10.5281/zenodo.19109947)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey.svg)](https://www.microsoft.com/windows)

> **A comprehensive, open-source desktop application for granulometric analysis supporting dual international standards (ASTM & NF/ISO).**

---

## 🚀 Quick Start: Download & Run (No Installation Required)

For users who want to run the software immediately without installing Python:

🔗 **Download the Pre-compiled Windows Executable here:**  
👉 **[Zenodo Archive (DOI: 10.5281/zenodo.19109947)](https://doi.org/10.5281/zenodo.19109947)**

1.  Click the link above.
2.  Under **"Files"**, download `GranuloGraph_Setup.exe`.
3.  Run the installer. The application is ready to use instantly.
4.  **Test it now:** Use the included `sample_data.csv` (also on Zenodo) to verify results immediately.

---

## 👤 Author & Contact

| Field | Information |
|-------|-------------|
| **Author** | Prof. Smaine CHELLAT |
| **Affiliation** | Laboratory of Geology and Environment, University Constantine 1, Algeria |
| **Email** | [smaine.chellat@umc.edu.dz](mailto:smaine.chellat@umc.edu.dz) \| [smaine.chellat@gmail.com](mailto:smaine.chellat@gmail.com) |
| **ORCID** | [0000-0003-4103-0436](https://orcid.org/0000-0003-4103-0436) |
| **Phone** | +213 699 390 172 |

---

## 📖 Overview

**GranuloGraph** is a robust Python-based desktop application designed to modernize grain-size analysis for sedimentologists, engineering geologists, and civil engineers. It replaces error-prone spreadsheet methods with a dedicated, validated interface that supports **dual calculation standards**, interactive visualization, and automated batch processing.

### 🔬 Dual Calculation Standards
GranuloGraph is the first tool to seamlessly switch between research and engineering protocols within the same interface:

| Method | Standard | Use Case |
|--------|----------|----------|
| **🔬 Recovered Weight** | **ASTM D6913** §11.2 | International research papers, sedimentological statistics. |
| **🏗️ Initial Weight** | **NF P 94-056 / ISO 17892-4** | Geotechnical reports (Algeria, France, Europe), official engineering submissions. |

> 💡 **Why this matters:** The choice of basis (recovered vs. initial) significantly affects percentage calculations and recovery validation. GranuloGraph automates this distinction, preventing common manual errors.

---

## ✅ Validation & Testing (Proof of Functionality)

To ensure scientific reliability, GranuloGraph has undergone rigorous validation against industry benchmarks:

*   **Dataset:** Tested on **15 diverse geological samples** from Algeria (Cretaceous to Quaternary), including crushed aggregates, aeolian sands, and fluvial deposits.
*   **Benchmarks:** Results compared against:
    1.  Manual calculations in Microsoft Excel.
    2.  **Gradistat Excel** (Blott & Pye, 2001), the current community standard.
*   **Results:**
    *   **Correlation Coefficient ($R^2$): > 0.999** for all percentile values ($D_5$ to $D_{95}$).
    *   **Statistical Parameters:** Deviations in Sorting ($\sigma_I$), Skewness ($Sk$), and Kurtosis ($K_G$) are < 1%, attributed solely to GranuloGraph’s superior **cubic spline interpolation** (vs. linear interpolation in legacy tools).
*   **Conclusion:** The software is mathematically robust and ready for peer-reviewed research and professional engineering use.

---

## 🎯 Key Features

### 📊 Data Management
*   Interactive spreadsheet-like interface for sieve data entry.
*   Import/Export: CSV, Excel (.xlsx), Text files.
*   **Batch Processing:** Analyze up to **10 samples simultaneously**.
*   Automatic data validation (positive values, sieve ordering, mass recovery alerts).

### 📈 Statistical Calculations (Folk & Ward, 1957)
*   **Central Tendency:** Graphic Mean ($M_z$), Median, Mode.
*   **Sorting:** Inclusive Graphic Standard Deviation ($\sigma_I$) — *7-class scale*.
*   **Skewness:** Folk & Ward coefficient ($Sk$) — *5-class interpretation*.
*   **Kurtosis:** Graphic Kurtosis ($K_G$) — *6-class scale*.
*   **Percentiles:** Full range ($D_5$ to $D_{95}$) in mm and $\phi$ units.

### ⚙ Geotechnical Indices (ASTM D2487 / BS EN 12620)
*   **Uniformity Coefficient ($C_u$):** With grading classification (Well/Moderately/Poorly graded).
*   **Curvature Coefficient ($C_c$):** Assessment of particle distribution shape.
*   **Fineness Modulus ($FM$):** With practical notes for concrete mix design.

### 🎨 Advanced Visualization
*   Cumulative curves (semi-log scale) with **ISO 14688-1:2017** classification bands.
*   **Interactive Cursor Tracking:** Real-time display of diameter and % passing.
*   **Percentile Projection Tool:** Enter a % to instantly find the corresponding grain size.
*   **Multi-series Overlay:** Compare up to 10 samples with distinct colors.

### 🔬 Scientific Interpretation Diagrams
*   **Friedman (1967):** Bivariate plots (Skewness vs. Sorting) to discriminate **Beach vs. River** sands.
*   **Passega & Byramjee (1969):** C-M diagrams to identify sediment transport mechanisms (Suspension, Saltation, Rolling).
*   **Correlation Matrices:** Heatmaps for multi-parameter statistical relationships.

### 💾 Export Options
*   **Graphs:** PNG, JPG, TIFF, PDF (Configurable DPI: **150–600** for publication quality).
*   **Data:** CSV/Excel with full metadata and calculation basis.
*   **Reports:** Comprehensive text summaries with automated interpretations.

---

## 📦 Installation

### Option 1: Pre-compiled Executable (Recommended for Users)
*   **OS:** Windows 10/11
*   **Steps:** Download from [Zenodo](https://doi.org/10.5281/zenodo.19109947) → Run Installer.
*   **Requirements:** None (Standalone).

### Option 2: From Source (For Developers & macOS/Linux Users)

**Requirements:**
*   Python 3.11 or higher.
*   ~200 MB Disk Space.
*   4 GB RAM minimum.

**Steps:**
```bash
# 1. Clone the repository
git clone https://github.com/smainechellat-star/GranuloGraph.git
cd GranuloGraph

# 2. Create a virtual environment (recommended)
python -m venv venv

# 3. Activate the environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the application
python main.py
### Option 1: Pre-compiled Executable (Recommended for Users)
*   **OS:** Windows 10/11
*   **Steps:** Download from [Zenodo](https://doi.org/10.5281/zenodo.19109947) → Run Installer.
*   **Requirements:** None (Standalone).

### Option 2: From Source (For Developers & macOS/Linux Users)

**Requirements:**
*   Python 3.11 or higher.
*   ~200 MB Disk Space.
*   4 GB RAM minimum.

