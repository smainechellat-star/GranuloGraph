# Contributing to GranuloGraph

Thank you for considering contributing to **GranuloGraph v2.0**, the granulometry analysis application for sedimentology and engineering geology. Bug reports, documentation improvements, new scientific diagrams and code fixes are all equally welcome.

---

## 👤 Project Author & Contact

| Field | Information |
|-------|-------------|
| **Author** | Smaine Chellat |
| **Email** | [smaine.chellat@gmail.com](mailto:smaine.chellat@gmail.com) |
| **ORCID** | [0000-0003-4103-0436](https://orcid.org/0000-0003-4103-0436) |
| **Affiliation** | University Constantine 1, Geological Department, Algeria |
| **DOI** | <https://doi.org/10.5281/zenodo.24435516> |

For questions about contributions, open a GitHub Issue or contact the author by email.

---

## 🧭 Ways to Contribute

- **🐞 Bug reports** — wrong parameter values, plotting glitches, import/export problems (please attach `error.log`, written next to the program when an unexpected crash occurs)
- **💡 Feature requests** — new discrimination diagrams, classification systems or export formats; describe the **scientific use case** (which standard or diagram, and why)
- **📖 Documentation** — README improvements, docstrings, worked examples with real datasets
- **🔧 Code** — bug fixes, refactoring, new features (see the workflow below)

---

## 🖥 Development Setup

**System requirements:** Python **3.11 or higher** (tested with 3.11, 3.12, 3.13) · Windows 10/11 for the .exe build (Linux/macOS run from source) · ~200 MB disk · the pinned dependencies in `requirements.txt` (numpy, scipy, pandas, matplotlib, openpyxl, xlrd, pillow).

```bash
git clone https://github.com/schellat/GranuloGraph.git
cd GranuloGraph
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Check your setup by loading **`example_data.csv`** (*File → Open Data*) and plotting it.

| Module | Role |
|--------|------|
| `main.py` | Entry point: app class, menus, navigation, error handling |
| `home_screen.py` | Data-entry grid, provenance dropdowns, validation, import/save |
| `graph_screen.py` | Main plot, statistics windows, Friedman / Passega / ternary / distribution / Bland-Altman diagrams, exports, PDF report |
| `calculations.py` | `GranuloCalculator`: Folk & Ward parameters, percentiles, curves, size fractions |
| `utils.py` | DataValidator, FileHandler, ConfigManager, UnitConverter, StatisticsHelper, ReportGenerator |

---

## 🔁 Contribution Workflow

1. **Fork the repository** — create a copy under your personal GitHub account.
2. **Create a branch** — `feature/<short-name>` for new features, `fix/<short-name>` for bug fixes.
3. **Make your changes** — implement them and keep the coding standards below.
4. **Commit your changes** — write clear, imperative commit messages, e.g. `Add Shepard field labels to the ternary diagram` or `Fix pan handling in Fineness Modulus`.
5. **Submit a pull request** — open it against the main repository with a description of *what* changed and *why*; add screenshots for UI changes.

---

## 📏 Coding Standards

- Follow **PEP 8** and keep the existing module structure (`main` → `home_screen` / `graph_screen` → `calculations` / `utils`).
- **Scientific correctness first.** `calculations.py` implements Folk & Ward (1957) statistics, the percentiles and the ISO 14688-1:2017 / ASTM D2487 size fractions. Any change touching class boundaries or parameter formulas **must cite the standard or reference paper** in a comment and be validated against published values.
- **Both calculation bases must stay in sync.** Test every statistical change under **both** bases — ASTM D6913 (recovered weight) *and* NF P94-056 / ISO 17892-4 (initial weight) — because the whole point of v2.0 is the dual-basis comparison (dotted twin curves, filled/open circles, Bland-Altman).
- **UI consistency** — Tkinter with the app palette (slate `#2c3e50`, blue `#3498db`, green `#27ae60`, magenta `#8e44ad`, red `#e74c3c`, amber `#f39c12`); Matplotlib TkAgg backend; load bundled assets through `resource_path()` so the frozen .exe keeps working.
- **Graceful degradation** — optional modules (e.g. `settings_screen`) must stay optional: the app imports fine when they are absent.
- **Dependencies** — do not add new third-party packages without discussing them first (the PDF report deliberately uses Matplotlib's built-in `PdfPages` instead of a new library).

---

## ✅ Testing Checklist (run before opening a PR)

- [ ] `python main.py` starts without errors
- [ ] `example_data.csv` loads, validates and plots under **both** calculation bases
- [ ] Folk & Ward parameters, Cu/Cc/FM and the percentiles table are unchanged where they should be
- [ ] The Friedman, Passega, ternary, distribution and Bland-Altman windows all open correctly
- [ ] Exports work: graph PNG/PDF, results CSV/XLSX, all-parameters export, multi-page PDF report
- [ ] Validation still raises the ASTM D6913 warning when sieving loss > 0.5 %
- [ ] `README.md` and `CHANGELOG.md` updated if the behavior changed

---

## 💡 Proposing Features

Open an Issue tagged `enhancement` with:

1. The **scientific motivation** (diagram, standard or workflow it supports);
2. The expected **input and output** (which data, which export);
3. Any reference (standard, paper, figure) the implementation should follow.

Features affecting published results (Folk & Ward values, fractions, classifications) will be reviewed against the referenced standard before merging.

---

## 📄 License

By contributing, you agree that your contributions are licensed under the **MIT License** that covers this project.

**Thank you for your contribution! We look forward to collaborating with you!**
