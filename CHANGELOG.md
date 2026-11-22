# Changelog

All notable changes to **GranuloGraph** are documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2.0.0] - 2026-11-22

### Added
- **Dual calculation basis** — ASTM D6913 (recovered weight, research) ↔ NF P94-056 / ISO 17892-4 (initial weight, geotechnical); selectable on the Home Screen / Settings and stamped into every export
- **Compare bases** — dotted twin curve in the same colour recomputed with the other calculation basis; drawn only where the two bases actually differ (segments with a gap < 0.2 % are masked)
- **Bland-Altman dual-basis agreement plot (ISO vs ASTM)** — D50 and Inclusive Graphic Standard Deviation (σI) panels with zero line, mean bias, ±1.96 SD limits of agreement and recovery-loss colour coding
- **Mandatory provenance metadata** — 18 sedimentary environments (Continental / Transitional / Marine families, plus Unknown, Natural – Unconfirmed and Crushed / Quarry) with a built-in Provenance Environment Guide; Friedman & Passega discrimination is provenance-aware
- **Ternary classification diagrams** — Folk (1954) Gravel–Sand–Mud and Shepard (1954) Sand–Silt–Clay side by side with all classification fields
- **Distribution graphs (GRADISTAT-style)** — per-sieve class weights in two panels: φ linear scale and μm logarithmic scale
- **Multi-page PDF report** — curves overlay page + one A4 sheet per sample with D10/D30/D50/D60 markers and the full parameter block (built with Matplotlib PdfPages — no extra dependency)
- **Dual-standard class bars** — ISO 14688-1:2017 and ASTM D2487/USCS header bands above the graph, tickable individually, stacked or hidden
- ISO 14688-1 + ASTM D2487 size-fraction columns (%) in the results and all-parameters exports
- Frequency distribution curves f(x) = dF/d(log₁₀ d) on a secondary axis
- Per-sample curve and frequency-curve selection panels (☑ Select All / ☐ Deselect All)
- Percentile projection tool (any percentage → diameter) and Key Percentiles panel (P5–P95, mm + φ)
- Cursor tracking (live diameter / % passing readout in the side panel)
- Application icon (`icon.ico`) embedded in the .exe and in the installer
- Windows installer (Inno Setup) with Start-Menu / optional desktop shortcuts, Add/Remove Programs entry and executable version metadata
- Optional `Registry key.reg` for the `.grl` file association, App Paths and default preferences
- MIT `LICENSE.txt`, `POST_INSTALL_INFO.txt`, `example_data.csv` sample dataset and a 21-step user guide in the README

### Fixed
- The graph title is now drawn as figure-level text in the empty band above the ISO/ASTM class labels — it no longer slides into the ISO class band on large / maximized windows

## [1.0.0] - 2024-03-XX

### Added
- Initial release
- Data entry interface
- Folk & Ward statistical parameters
- Geotechnical indices
- Interactive graphs
- Export functionality

[2.0.0]: https://github.com/schellat/GranuloGraph/compare/v1.0.0...v2.0.0
[1.0.0]: https://github.com/schellat/GranuloGraph/releases/tag/v1.0.0
