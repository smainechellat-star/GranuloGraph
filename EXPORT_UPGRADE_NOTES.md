# GranuloGraph Export Upgrade — Delivery Notes

**Date**: 26 November 2026
**Scope**: the four requested export enhancements (message of 26 Nov 2026), implemented on top of the `main.py` / `graph_screen.py` / `home_screen.py` / `README.md` you provided.

---

## 1. What was requested vs what was implemented

| # | Request | Implementation |
|---|---------|----------------|
| 1 | All export options available for **every graph type** in the Export button; stop labelling exports "as PNG" | Every figure export (main graph, Friedman, Passega, ternary, distribution, Bland-Altman, correlation) now opens **one unified "format + resolution" dialog**. Menu labels changed: *"Main Graph as PNG"* → *"Main Graph (all formats)"*, *"Export Distribution Graphs (PNG)"* → *"Export Distribution Graphs"* |
| 2 | Add **.crd, .dwg, .ai, .wp, .webp, .wpg** + **HD / 4K** export; add these to the bottom-left **Save the figure** button | All six requested extensions are in the format list (see §3 for how each is written). Nine resolution presets (96–600 DPI + HD/Full-HD/2K/4K). The matplotlib toolbar save button (bottom left) is replaced by `GranuloToolbar`, whose **Save the figure** action opens the same unified dialog |
| 3 | Save the **full Home Screen and Graph Screen** in HD/4K, better than screenshots | New full-window capture: Windows **PrintWindow API** (captures the complete window even when partly covered, no external tool needed), Pillow `ImageGrab` fallback on other systems; image resized to HD / Full HD / 2K / 4K with LANCZOS |
| 4 | Buttons placed **next to the Frequencies curves button** (Graph Screen) and **under Display Graph** (Home Screen) | *🖥 Save Full Screen (HD/4K)* button added right after *☑ Frequency Curves* in the Graph Screen bottom bar; *🖥 Save Home Screen (HD/4K)* button added directly under *📊 Display Graph* on the Home Screen. Also available via the Graph-Screen Export menu and *File → Save Current Screen (HD/4K)* |

## 2. Files in this package

| File | Status | Role |
|------|--------|------|
| `export_utils.py` | **NEW** | The unified export engine (formats, resolutions, DXF writer, screen capture, toolbar). Place it **next to `main.py`**. |
| `main.py` | **UPDATED** | Unified `File → Export Graph` (all formats + resolution dialog); new `File → Save Current Screen (HD/4K)`. |
| `graph_screen.py` | **UPDATED** | All 9 figure exports unified; new *Save Full Screen* button + menu entry; `GranuloToolbar` on all 7 windows (main graph, correlation, Friedman window, Passega, ternary, distribution, Bland-Altman). |
| `home_screen.py` | **UPDATED** | New *Save Home Screen (HD/4K)* button under Display Graph. |
| `README.md` | **UPDATED** | Documents the new engine, formats, resolutions and buttons; repository URL fixed to `smainechellat-star/GranuloGraph`. |
| `CHANGELOG.md` | **UPDATED** | New `[2.1.0]` entry. |
| `test_report.txt` | Generated | Automated verification output (all formats, 4K sizes, DXF structure). |

## 3. How each requested format is written (honest technical note)

`.webp`, `.gif`, `.pdf`, `.svg`, `.eps`, `.png`, `.jpg`, `.tif` — written **natively** (matplotlib + Pillow). No caveat.

| Extension | What is written | How to use it |
|-----------|-----------------|---------------|
| `.ai` | **PDF vector data** (Adobe Illustrator's own file base since CS) | Illustrator opens it as fully editable vectors |
| `.dxf` | **DXF R12** produced by the built-in pure-Python writer (curves → POLYLINE, markers → POINT, text → TEXT, millimetre units) | Opens directly in AutoCAD, QCAD, LibreCAD, DraftSight, CorelDRAW |
| `.dwg` | DXF data in a `.dwg` file (DWG is a proprietary binary format no open library can write). **If the free ODA File Converter is installed, a true DWG is written automatically** (silent conversion) | Open in AutoCAD → *Save As → DWG*. This is the standard interchange route used by all non-AutoCAD tools |
| `.crd` / `.cdr` | **SVG vector data** (CorelDRAW imports SVG natively) | CorelDRAW: *File → Open / Import* |
| `.wp` / `.wpg` | **SVG vector data** (WordPerfect Office 2020+ imports SVG) | WordPerfect: *Insert → Graphics → From File* |

These writing conventions are stated in the dialog itself (a note under the format list) and in README → Troubleshooting, so end users are never misled.

## 4. Resolution presets — what "HD" and "4K" mean here

* **DPI presets** (96/150/200/300/600): publication-grade rendering; 300 DPI is the default.
* **Pixel presets** (HD 1280, Full HD 1920, 2K 2560, 4K UHD 3840 px wide): the engine computes `dpi = target_px / figure_width_inches` and **re-renders** the figure at that DPI — e.g. an 8×6 in figure exported at 4K UHD is rendered at 480 DPI, giving an exactly-3840-px-wide image.
* **Full-screen capture**: the window is captured at its current pixel size and resized to the target (the dialog explains this). For a *native* 4K of the graph itself, use the figure export — the graph area is rendered by matplotlib and is truly resolution-independent.

## 5. Installation

1. Copy **all five files** (`export_utils.py`, `main.py`, `graph_screen.py`, `home_screen.py`, `README.md`) into the GranuloGraph source folder, replacing the old ones (`export_utils.py` is new).
2. Run from source: `python main.py` — no new dependencies (Pillow was already required).
3. **Rebuild the Windows exe** with `build_exe_onefile.bat` (PyInstaller detects `export_utils.py` automatically because it is imported normally).
4. Optional: install the free [ODA File Converter](https://www.opendesign.com/guestfiles/oda_file_converter) for native `.dwg` writing.

## 6. Verification performed (see `test_report.txt`)

* All 15 figure formats exported from a realistic cumulative-curve figure and re-opened/inspected.
* 4K UHD PNG verified at exactly 3840 px wide; Full-HD at 1920 px.
* DXF output structurally validated (sections, layers, POLYLINE/TEXT/POINT entities).
* `.ai` verified as valid PDF vector data; `.crd/.wp` verified as valid SVG data.
* `main.py`, `graph_screen.py`, `home_screen.py`, `export_utils.py` — syntax compiled and module-import tested with the real `calculations.py` / `utils.py`.
* Screen capture path is Windows-targeted (PrintWindow); it degrades gracefully to Pillow elsewhere.
