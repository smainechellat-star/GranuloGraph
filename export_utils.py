"""
export_utils.py - GranuloGraph Unified Export Engine
====================================================

One engine for EVERY export in GranuloGraph:

  * Every figure export (main graph, Friedman plots, Passega diagram,
    ternary diagrams, distribution graphs, Bland-Altman plot, correlation
    graph) shares ONE "format + resolution" dialog.
  * Formats: PNG, JPEG, TIFF, WebP, GIF (raster) - PDF, SVG, EPS (native
    vector) - AI (Adobe Illustrator, PDF vector data) - DXF (open CAD
    interchange) - DWG (DXF data; true DWG when ODA File Converter is
    installed) - CRD/CDR (CorelDRAW, SVG vector data) - WP/WPG
    (WordPerfect, SVG vector data).
  * Resolutions: 96 / 150 / 200 / 300 / 600 DPI plus HD 1280, Full HD 1920,
    2K QHD 2560 and 4K UHD 3840 pixel presets. Pixel presets are converted
    to the exact DPI, so a "4K" export is a REAL re-render, not an upscale.
  * Full-window capture of the Home / Graph screens (Windows PrintWindow
    API, Pillow ImageGrab fallback) resized to HD / 4K - much better than
    manual screenshots.

Drop-in toolbar
---------------
    class GranuloToolbar(NavigationToolbar2Tk)
    The toolbar "Save the figure" button (disk icon, bottom left) opens the
    same unified dialog for the figure it belongs to.

Author: Smaine Chellat - University Constantine 1, Geological Department, Algeria
License: MIT
"""
import os
import io
import math

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import matplotlib
from matplotlib import lines as mlines, text as mtext, patches as mpatches
from matplotlib import collections as mcoll
from matplotlib import colors as mcolors
try:
    # Present in every normal GranuloGraph run (the app itself uses TkAgg).
    from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
except Exception:
    # Headless / Tcl-less environments (CI, docs builds): GranuloToolbar
    # becomes an inert placeholder so the export engine still imports.
    NavigationToolbar2Tk = object
from PIL import Image

__all__ = [
    "EXPORT_FORMATS", "FIGURE_RESOLUTIONS", "SCREEN_RESOLUTIONS",
    "DEFAULT_FIGURE_RESOLUTION", "DEFAULT_SCREEN_RESOLUTION",
    "build_filetypes", "build_screen_filetypes", "figure_dpi",
    "export_figure", "export_screen", "capture_tk_window",
    "prompt_export_figure", "prompt_export_screen",
    "ExportOptionsDialog", "GranuloToolbar",
    "GraphScreenExportMixin", "HomeScreenExportMixin",
]

# ═════════════════════════════════════════════════════════════════════
# 1. FORMAT AND RESOLUTION CATALOGUES
# ═════════════════════════════════════════════════════════════════════
# Each format: (extension, menu label, writer key, compatibility note)
# writer keys: 'mpl'      -> matplotlib savefig (native)
#              'pillow'   -> PNG buffer, then Pillow convert (WebP/GIF)
#              'pdfbytes' -> PDF bytes written under another extension (AI)
#              'svgbytes' -> SVG bytes written under another extension
#                            (CRD/CDR/WP/WPG - CorelDRAW and WordPerfect
#                            import SVG natively)
#              'dxf'      -> built-in DXF R12 writer (pure Python)
#              'dwg'      -> DXF data in .dwg file + optional ODA convert
EXPORT_FORMATS = [
    ("png",  "PNG  - raster (universal)",   "mpl",      "Lossless raster image - universal support."),
    ("jpg",  "JPEG - raster",               "mpl",      "Compact raster image (photo-style)."),
    ("tif",  "TIFF - raster (print)",       "mpl",      "High-quality raster for print / journals."),
    ("webp", "WebP - raster (web)",         "pillow",   "Modern web raster format - small files."),
    ("gif",  "GIF  - raster",               "pillow",   "Classic 256-colour raster format."),
    ("pdf",  "PDF  - vector (publication)", "mpl",      "True vector output - publication quality."),
    ("svg",  "SVG  - vector (web/design)",  "mpl",      "Vector - opens in Illustrator, Inkscape, CorelDRAW."),
    ("eps",  "EPS  - vector (LaTeX/print)", "mpl",      "Vector - LaTeX and print workflows."),
    ("ai",   "AI   - Adobe Illustrator",    "pdfbytes", "PDF vector data - Adobe Illustrator opens it as fully editable vectors."),
    ("dxf",  "DXF  - CAD interchange",      "dxf",      "Open CAD format - AutoCAD, QCAD, LibreCAD, CorelDRAW import it directly."),
    ("dwg",  "DWG  - AutoCAD",              "dwg",      "Written as DXF data (AutoCAD's open interchange): open in AutoCAD and Save As -> DWG. With ODA File Converter installed a true DWG is written automatically."),
    ("crd",  "CRD  - CorelDRAW",            "svgbytes", "SVG vector data - CorelDRAW imports SVG natively (File -> Open / Import)."),
    ("cdr",  "CDR  - CorelDRAW",            "svgbytes", "SVG vector data - CorelDRAW imports SVG natively (File -> Open / Import)."),
    ("wp",   "WP   - WordPerfect",          "svgbytes", "SVG vector data - WordPerfect Office (2020 and later) imports SVG."),
    ("wpg",  "WPG  - WordPerfect Graphics", "svgbytes", "SVG vector data - WordPerfect Office (2020 and later) imports SVG; convert to legacy WPG with LibreOffice if needed."),
]

# Each figure resolution: (key, label, ('dpi', n) or ('px', target_width_px))
FIGURE_RESOLUTIONS = [
    ("screen",     "Screen - 96 DPI",                    ("dpi", 96)),
    ("draft150",   "Draft - 150 DPI",                    ("dpi", 150)),
    ("quality200", "High quality - 200 DPI",             ("dpi", 200)),
    ("print300",   "Print quality - 300 DPI (default)",  ("dpi", 300)),
    ("print600",   "Print quality - 600 DPI",            ("dpi", 600)),
    ("hd",         "HD - 1280 px wide",                  ("px", 1280)),
    ("fhd",        "Full HD - 1920 px wide",             ("px", 1920)),
    ("qhd",        "2K QHD - 2560 px wide",              ("px", 2560)),
    ("uhd4k",      "4K UHD - 3840 px wide",              ("px", 3840)),
]
DEFAULT_FIGURE_RESOLUTION = "print300"

SCREEN_FORMATS = [
    ("png",  "PNG  - lossless",   "pillow", "Lossless - best for screenshots."),
    ("jpg",  "JPEG - compact",    "pillow", "Smaller file (photo compression)."),
    ("webp", "WebP - compact",    "pillow", "Modern web format - small files."),
    ("tif",  "TIFF - print",      "pillow", "Lossless - print workflows."),
]

# Screen capture: the window is captured at its current pixel size, then
# resized (LANCZOS) to the chosen target width. None = keep native size.
SCREEN_RESOLUTIONS = [
    ("native", "Native window size",       None),
    ("hd",     "HD - 1280 px wide",        1280),
    ("fhd",    "Full HD - 1920 px wide",   1920),
    ("qhd",    "2K QHD - 2560 px wide",    2560),
    ("uhd4k",  "4K UHD - 3840 px wide",    3840),
]
DEFAULT_SCREEN_RESOLUTION = "fhd"

_FORMAT_BY_EXT = {f[0]: f for f in EXPORT_FORMATS}


def _format_spec(ext):
    """(ext, label, writer, note) for an extension; raises a clear error."""
    ext = ext.lower().lstrip('.')
    if ext in ('jpeg',): ext = 'jpg'
    if ext in ('tiff',): ext = 'tif'
    if ext not in _FORMAT_BY_EXT:
        raise ValueError(
            f"Unsupported export format '.{ext}'. Supported: "
            + ", ".join(f".{e}" for e, *_ in EXPORT_FORMATS))
    return _FORMAT_BY_EXT[ext]


def build_filetypes():
    """Tk file-dialog filetypes list: all formats, then one entry each."""
    all_ext = ' '.join(f'*.{e}' for e, *_ in EXPORT_FORMATS)
    types = [('All supported formats', all_ext)]
    for ext, label, _writer, _note in EXPORT_FORMATS:
        name = label.split(' - ')[0].strip()
        types.append((f'{name} (*.{ext})', f'*.{ext}'))
    types.append(('All files', '*.*'))
    return types


def build_screen_filetypes():
    types = [('All supported formats', ' '.join(f'*.{f[0]}' for f in SCREEN_FORMATS))]
    for ext, label, _w, _n in SCREEN_FORMATS:
        types.append((label + f' (*.{ext})', f'*.{ext}'))
    types.append(('All files', '*.*'))
    return types


# ═════════════════════════════════════════════════════════════════════
# 2. RESOLUTION HANDLING (HD / 4K = real re-render, not an upscale)
# ═════════════════════════════════════════════════════════════════════
def figure_dpi(fig, res_key=None):
    """DPI that realises the chosen resolution preset for this figure.

    DPI presets are used directly. Pixel presets (HD/Full HD/2K/4K) are
    converted to the exact DPI: dpi = target_px / figure_width_inches, so
    the saved image is a true re-render at the requested pixel width."""
    key = res_key or DEFAULT_FIGURE_RESOLUTION
    kind, value = ('dpi', 300)
    for k, _label, (kd, kv) in FIGURE_RESOLUTIONS:
        if k == key:
            kind, value = kd, kv
            break
    if kind == 'dpi':
        return value
    width_in = max(float(fig.get_size_inches()[0]), 0.1)
    return max(72, int(round(value / width_in)))


def _uses_px_target(res_key=None):
    """True when the preset targets an exact pixel width (HD/4K...).
    Pixel presets save WITHOUT the tight-bbox crop so the pixel width of
    the saved file is exactly the requested one."""
    key = res_key or DEFAULT_FIGURE_RESOLUTION
    for k, _label, (kd, _v) in FIGURE_RESOLUTIONS:
        if k == key:
            return kd == 'px'
    return False


def _bbox_for(res_key=None):
    return None if _uses_px_target(res_key) else 'tight'


def resize_screen_image(img, res_key=None):
    """Resize a captured window image to the target width (aspect kept)."""
    key = res_key or DEFAULT_SCREEN_RESOLUTION
    target = None
    for k, _label, val in SCREEN_RESOLUTIONS:
        if k == key:
            target = val
            break
    if not target or img.width == target:
        return img
    new_h = max(1, round(img.height * target / img.width))
    return img.resize((target, new_h), Image.LANCZOS)


# ═════════════════════════════════════════════════════════════════════
# 3. FIGURE EXPORT - every format through one function
# ═════════════════════════════════════════════════════════════════════
def export_figure(fig, filename, res_key=None):
    """Save a matplotlib Figure in ANY supported format at ANY resolution.

    Returns the file path. Raises ValueError for unknown extensions."""
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    if not ext:
        raise ValueError("File name must include an extension (e.g. .png).")
    _ext, _label, writer, _note = _format_spec(ext)
    dpi = figure_dpi(fig, res_key)
    facecolor = fig.get_facecolor()

    if writer == 'mpl':
        fig.savefig(filename, dpi=dpi, facecolor=facecolor, bbox_inches=_bbox_for(res_key))

    elif writer == 'pillow':
        # Reliable path for Pillow-backed raster formats (WebP, GIF):
        # render PNG in memory, then convert.
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=dpi, facecolor=facecolor, bbox_inches=_bbox_for(res_key))
        buf.seek(0)
        img = Image.open(buf)
        if ext == 'gif':
            img.convert('RGB').save(filename, 'GIF')
        else:
            img.save(filename, 'WEBP', quality=95)

    elif writer == 'pdfbytes':      # .ai - Illustrator-compatible PDF data
        buf = io.BytesIO()
        fig.savefig(buf, format='pdf', dpi=dpi, facecolor=facecolor, bbox_inches=_bbox_for(res_key))
        with open(filename, 'wb') as fh:
            fh.write(buf.getvalue())

    elif writer == 'svgbytes':      # .crd/.cdr/.wp/.wpg - SVG vector data
        buf = io.BytesIO()
        fig.savefig(buf, format='svg', dpi=dpi, facecolor=facecolor, bbox_inches=_bbox_for(res_key))
        with open(filename, 'wb') as fh:
            fh.write(buf.getvalue())

    elif writer == 'dxf':
        with open(filename, 'w', encoding='ascii', errors='replace', newline='\n') as fh:
            fh.write(figure_to_dxf(fig))

    elif writer == 'dwg':
        # DXF data (AutoCAD's documented interchange format), then try a
        # silent ODA File Converter pass for a true DWG.
        with open(filename, 'w', encoding='ascii', errors='replace', newline='\n') as fh:
            fh.write(figure_to_dxf(fig))
        _try_oda_convert(filename)

    return filename


def _try_oda_convert(dwg_path):
    """If ODA File Converter (free, Open Design Alliance) is installed,
    convert the DXF data just written into a true DWG file (same path).
    Silently returns False when the tool is absent or fails."""
    import shutil
    import subprocess
    import tempfile
    import glob
    exe = shutil.which('ODAFileConverter')
    if not exe:
        for pat in (r'C:\Program Files\ODA\*\ODAFileConverter*.exe',
                    r'C:\Program Files (x86)\ODA\*\ODAFileConverter*.exe'):
            hits = glob.glob(pat)
            if hits:
                exe = hits[0]
                break
    if not exe:
        return False
    try:
        with tempfile.TemporaryDirectory() as tmp:
            inbox = os.path.join(tmp, 'in')
            outbox = os.path.join(tmp, 'out')
            os.makedirs(inbox)
            os.makedirs(outbox)
            tmp_dxf = os.path.join(inbox, os.path.splitext(os.path.basename(dwg_path))[0] + '.dxf')
            shutil.copyfile(dwg_path, tmp_dxf)
            flags = getattr(subprocess, 'CREATE_NO_WINDOW', 0) if os.name == 'nt' else 0
            subprocess.run([exe, inbox, outbox, 'DWG', 'ACAD2018', '0', '1'],
                           check=True, timeout=180, creationflags=flags)
            produced = glob.glob(os.path.join(outbox, '*.dwg'))
            if produced:
                shutil.copyfile(produced[0], dwg_path)
                return True
    except Exception:
        return False
    return False


# ═════════════════════════════════════════════════════════════════════
# 4. DXF WRITER (pure Python, no external dependency)
#    Curves/axes -> POLYLINE, scatter markers -> POINT, text -> TEXT.
#    Units: millimetres. DXF R12 (AC1009) - readable by AutoCAD, QCAD,
#    LibreCAD, DraftSight, CorelDRAW and most CAD viewers.
# ═════════════════════════════════════════════════════════════════════
_DXF_TEXT_REPL = {
    'φ': 'phi', 'Φ': 'Phi', 'σ': 'sigma', 'Σ': 'Sigma', 'μ': 'um',
    '°': 'deg', '±': '+/-', '×': 'x', '·': '.', '—': '-', '–': '-',
    '≤': '<=', '≥': '>=', '≈': '~', '≠': '!=', '∝': '~',
    '²': '^2', '³': '^3', '¹': '^1', '⁰': '^0', '⁴': '^4',
    '⁻': '^-', '₀': '0', '₁': '1', '₂': '2', '₃': '3', '₄': '4',
    '½': '1/2', '¼': '1/4', '¾': '3/4', '√': 'sqrt', '⌀': 'D',
    '₁₀': '10', '←': '<-', '→': '->', '⚠': '(!)', '☑': '[x]', '☐': '[ ]',
    '①': '1)', '②': '2)', '③': '3)', '④': '4)',
}

_DXF_ACI_PALETTE = {
    1: (255, 0, 0), 2: (255, 255, 0), 3: (0, 255, 0), 4: (0, 255, 255),
    5: (0, 0, 255), 6: (255, 0, 255), 7: (255, 255, 255),
    8: (128, 128, 128), 9: (192, 192, 192),
    30: (128, 0, 0), 38: (128, 128, 0), 52: (0, 128, 0),
    62: (0, 128, 128), 212: (0, 0, 128), 232: (128, 0, 128),
}

_DXF_LAYERS = [
    ('GRANULO_CURVES', 5), ('GRANULO_AXES', 7), ('GRANULO_GRID', 8),
    ('GRANULO_POINTS', 2), ('GRANULO_TEXT', 7), ('GRANULO_LEGEND', 3),
]

_DXF_MAX_ENTITIES = 30000


def _ascii_safe(text):
    s = str(text)
    for k, v in _DXF_TEXT_REPL.items():
        s = s.replace(k, v)
    return ''.join(ch if 32 <= ord(ch) < 127 else '?' for ch in s)


def _rgb255(color):
    try:
        r, g, b, _a = mcolors.to_rgba(color)
        return (int(round(r * 255)), int(round(g * 255)), int(round(b * 255)))
    except Exception:
        return (0, 0, 0)


def _aci(rgb):
    best, best_d = 7, None
    for idx, ref in _DXF_ACI_PALETTE.items():
        d = sum((a - b) ** 2 for a, b in zip(rgb, ref))
        if best_d is None or d < best_d:
            best_d, best = d, idx
    return best


def figure_to_dxf(fig):
    """Convert a matplotlib Figure into a DXF R12 document (string)."""
    import numpy as np

    try:
        fig.canvas.draw()
    except Exception:
        pass

    out = []

    def t(code, val):
        out.append(str(code))
        out.append(str(val))

    def to_mm(disp):
        arr = np.asarray(disp, dtype=float)
        return arr / float(fig.dpi) * 25.4

    def artist_to_mm(artist, data_xy):
        try:
            disp = artist.get_transform().transform(np.asarray(data_xy, dtype=float))
            keep = np.isfinite(disp).all(axis=1)
            return to_mm(disp[keep])
        except Exception:
            return None

    def write_polyline(pts_mm, layer, color, closed=False):
        if len(pts_mm) < 2 or len(out) // 2 > _DXF_MAX_ENTITIES:
            return
        t(0, 'POLYLINE'); t(8, layer); t(66, 1); t(70, 1 if closed else 0); t(62, color)
        for x, y in pts_mm:
            t(0, 'VERTEX'); t(8, layer)
            t(10, f'{x:.4f}'); t(20, f'{y:.4f}'); t(30, '0.0')
        t(0, 'SEQEND'); t(8, layer)

    def write_points(pts_mm, layer, color):
        for x, y in pts_mm:
            if len(out) // 2 > _DXF_MAX_ENTITIES:
                return
            t(0, 'POINT'); t(8, layer)
            t(10, f'{x:.4f}'); t(20, f'{y:.4f}'); t(30, '0.0'); t(62, color)

    # -- header ---------------------------------------------------------
    t(0, 'SECTION'); t(2, 'HEADER')
    t(9, '$ACADVER'); t(1, 'AC1009')
    t(9, '$INSUNITS'); t(70, 4)          # 4 = millimetres
    t(0, 'ENDSEC')

    # -- tables: line type + layers -------------------------------------
    t(0, 'SECTION'); t(2, 'TABLES')
    t(0, 'TABLE'); t(2, 'LTYPE'); t(70, 1)
    t(0, 'LTYPE'); t(2, 'CONTINUOUS'); t(70, 0)
    t(3, 'Solid line'); t(72, 65); t(73, 0); t(40, '0.0')
    t(0, 'ENDTAB')
    t(0, 'TABLE'); t(2, 'LAYER'); t(70, len(_DXF_LAYERS))
    for name, color in _DXF_LAYERS:
        t(0, 'LAYER'); t(2, name); t(70, 0); t(62, color); t(6, 'CONTINUOUS')
    t(0, 'ENDTAB')
    t(0, 'ENDSEC')

    # -- entities --------------------------------------------------------
    t(0, 'SECTION'); t(2, 'ENTITIES')

    grid_ids = set()
    for ax in fig.axes:
        for gl in list(ax.get_xgridlines()) + list(ax.get_ygridlines()):
            grid_ids.add(id(gl))

    # 4a. Lines (curves, axes ticks, legend lines)
    for line in fig.findobj(mlines.Line2D):
        if not line.get_visible() or len(out) // 2 > _DXF_MAX_ENTITIES:
            continue
        try:
            data = line.get_xydata()
        except Exception:
            continue
        pts = artist_to_mm(line, data)
        if pts is None or len(pts) < 2:
            continue
        layer = 'GRANULO_GRID' if id(line) in grid_ids else 'GRANULO_CURVES'
        write_polyline(pts, layer, _aci(_rgb255(line.get_color())))

    # 4b. Collections (scatter markers of the Friedman / Passega / correlation plots)
    for coll in fig.findobj(mcoll.Collection):
        if not coll.get_visible() or len(out) // 2 > _DXF_MAX_ENTITIES:
            continue
        try:
            offsets = coll.get_offsets()
            if offsets is None or len(offsets) == 0:
                continue
            pts = artist_to_mm(coll, offsets)
        except Exception:
            continue
        if pts is None or not len(pts):
            continue
        try:
            color = _aci(_rgb255(coll.get_facecolor()[0]))
        except Exception:
            color = 7
        write_points(pts, 'GRANULO_POINTS', color)

    # 4c. Patches (bars, boxes, spines, legend frames)
    for patch in fig.findobj(mpatches.Patch):
        if not patch.get_visible() or len(out) // 2 > _DXF_MAX_ENTITIES:
            continue
        try:
            fc = mcolors.to_rgba(patch.get_facecolor())
            ec = mcolors.to_rgba(patch.get_edgecolor())
            if fc[3] <= 0.02 and ec[3] <= 0.02:
                continue                      # invisible helper patch
            path = patch.get_path()
            if path is None or len(path.vertices) < 2:
                continue
            pts = artist_to_mm(patch, path.vertices)
        except Exception:
            continue
        if pts is None or len(pts) < 2:
            continue
        if len(pts) > 1500:
            step = max(1, len(pts) // 1500)
            pts = pts[::step]
        write_polyline(pts, 'GRANULO_AXES', _aci(_rgb255(patch.get_edgecolor())), closed=True)

    # 4d. Text (titles, labels, ticks, annotations)
    for txt in fig.findobj(mtext.Text):
        if not txt.get_visible() or len(out) // 2 > _DXF_MAX_ENTITIES:
            continue
        s = txt.get_text()
        if not s or not s.strip():
            continue
        try:
            import numpy as np2
            disp = txt.get_transform().transform(np2.asarray([txt.get_position()], dtype=float))
            x, y = to_mm(disp)[0]
        except Exception:
            continue
        h_mm = float(txt.get_fontsize()) / 72.0 * 25.4
        try:
            color = _aci(_rgb255(txt.get_color()))
        except Exception:
            color = 7
        t(0, 'TEXT'); t(8, 'GRANULO_TEXT')
        t(10, f'{x:.4f}'); t(20, f'{y:.4f}'); t(30, '0.0')
        t(40, f'{h_mm:.3f}'); t(1, _ascii_safe(s))
        t(50, int(round(float(txt.get_rotation()) % 360))); t(62, color)

    t(0, 'ENDSEC')
    t(0, 'EOF')
    return '\n'.join(out) + '\n'


# ═════════════════════════════════════════════════════════════════════
# 5. FULL-WINDOW CAPTURE (Home / Graph screens, HD to 4K)
# ═════════════════════════════════════════════════════════════════════
def capture_tk_window(widget):
    """Capture the whole Tk window (client area) as a PIL RGB Image.

    Windows: PrintWindow API (PW_RENDERFULLCONTENT) - captures the complete
    window surface even when partly covered or off-screen, without any
    external screenshot tool. Other systems: Pillow ImageGrab fallback."""
    img = None
    if os.name == 'nt':
        img = _capture_windows(widget)
    if img is None:
        img = _capture_imagegrab(widget)
    if img.mode in ('RGBA', 'LA', 'P'):
        img = img.convert('RGB')
    return img


def _capture_windows(widget):
    """Windows PrintWindow capture (ctypes, no extra dependency)."""
    import ctypes
    from ctypes import wintypes

    class RECT(ctypes.Structure):
        _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG),
                    ('right', wintypes.LONG), ('bottom', wintypes.LONG)]
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [('biSize', wintypes.DWORD), ('biWidth', wintypes.LONG),
                    ('biHeight', wintypes.LONG), ('biPlanes', wintypes.WORD),
                    ('biBitCount', wintypes.WORD), ('biCompression', wintypes.DWORD),
                    ('biSizeImage', wintypes.DWORD), ('biXPelsPerMeter', wintypes.LONG),
                    ('biYPelsPerMeter', wintypes.LONG), ('biClrUsed', wintypes.DWORD),
                    ('biClrImportant', wintypes.DWORD)]

    class BITMAPINFO(ctypes.Structure):
        _fields_ = [('bmiHeader', BITMAPINFOHEADER),
                    ('bmiColors', wintypes.DWORD * 3)]

    try:
        user32, gdi32 = ctypes.windll.user32, ctypes.windll.gdi32
        try:
            user32.SetProcessDPIAware()          # crisp capture on scaled displays
        except Exception:
            pass
        GA_ROOT = 2
        PW_RENDERFULLCONTENT = 2   # Win 8.1+: full window incl. title/menu bars

        hwnd = widget.winfo_id()
        root_hwnd = user32.GetAncestor(hwnd, GA_ROOT)
        if not root_hwnd:
            return None
        rc = RECT()
        if not user32.GetWindowRect(root_hwnd, ctypes.byref(rc)):
            return None
        w, h = rc.right - rc.left, rc.bottom - rc.top
        if w <= 0 or h <= 0:
            return None

        hdc = user32.GetDC(root_hwnd)
        mem_dc = gdi32.CreateCompatibleDC(hdc)
        bmp = gdi32.CreateCompatibleBitmap(hdc, w, h)
        old_bmp = gdi32.SelectObject(mem_dc, bmp)
        try:
            ok = user32.PrintWindow(root_hwnd, mem_dc, PW_RENDERFULLCONTENT)
            if not ok:
                return None
            bi = BITMAPINFOHEADER()
            bi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
            bi.biWidth, bi.biHeight = w, -h          # negative = top-down
            bi.biPlanes, bi.biBitCount = 1, 32
            bi.biCompression = 0                     # BI_RGB
            buf = ctypes.create_string_buffer(w * h * 4)
            if not gdi32.GetDIBits(mem_dc, bmp, 0, h, buf, ctypes.byref(bi), 0):
                return None
            return Image.frombytes('RGBA', (w, h), buf.raw, 'raw', 'BGRA')
        finally:
            gdi32.SelectObject(mem_dc, old_bmp)
            gdi32.DeleteObject(bmp)
            gdi32.DeleteDC(mem_dc)
            user32.ReleaseDC(root_hwnd, hdc)
    except Exception:
        return None


def _capture_imagegrab(widget):
    """Pillow screen-grab fallback (Windows/macOS native, Linux with X11)."""
    from PIL import ImageGrab
    widget.update_idletasks()
    x = widget.winfo_rootx()
    y = widget.winfo_rooty()
    w = widget.winfo_width()
    h = widget.winfo_height()
    if w <= 10 or h <= 10:
        raise RuntimeError("The window is too small to capture.")
    try:
        return ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
    except TypeError:
        return ImageGrab.grab(bbox=(x, y, x + w, y + h))


def export_screen(widget, filename, res_key=None):
    """Capture a Tk window and save it as PNG/JPEG/WebP/TIFF at the chosen
    resolution (Native / HD / Full HD / 2K / 4K). Returns the path."""
    ext = os.path.splitext(filename)[1].lower()
    img = capture_tk_window(widget)
    img = resize_screen_image(img, res_key)
    if ext in ('.jpg', '.jpeg'):
        img.save(filename, 'JPEG', quality=95)
    elif ext == '.webp':
        img.save(filename, 'WEBP', quality=95)
    elif ext in ('.tif', '.tiff'):
        img.save(filename, 'TIFF')
    else:
        img.save(filename, 'PNG')
    return filename


# ═════════════════════════════════════════════════════════════════════
# 6. THE UNIFIED "FORMAT + RESOLUTION" DIALOG
# ═════════════════════════════════════════════════════════════════════
class ExportOptionsDialog(tk.Toplevel):
    """One dialog for every export: file format + resolution."""

    def __init__(self, parent, kind='figure', title='Export options'):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.resizable(False, False)

        if kind == 'figure':
            formats, resolutions = EXPORT_FORMATS, FIGURE_RESOLUTIONS
            default_res = DEFAULT_FIGURE_RESOLUTION
        else:
            formats, resolutions = SCREEN_FORMATS, SCREEN_RESOLUTIONS
            default_res = DEFAULT_SCREEN_RESOLUTION
        notes = {f[0]: f[3] for f in formats}

        frm = ttk.Frame(self, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text='File format', font=('Segoe UI', 10, 'bold')).pack(anchor='w')
        box = ttk.Frame(frm)
        box.pack(fill=tk.X, pady=(2, 0))
        self._fmt_var = tk.StringVar(value=formats[0][0])
        self._notes = notes
        cols = 2 if len(formats) > 6 else 1
        for i, (ext, label, _w, _n) in enumerate(formats):
            r, c = divmod(i, cols)
            ttk.Radiobutton(box, text=label, value=ext, variable=self._fmt_var,
                            command=self._update_note).grid(row=r, column=c, sticky='w', padx=6, pady=1)
        self._note_var = tk.StringVar(value=notes[self._fmt_var.get()])
        ttk.Label(frm, textvariable=self._note_var, wraplength=440, foreground='#555555',
                  font=('Segoe UI', 8, 'italic')).pack(fill=tk.X, pady=(6, 2), anchor='w')

        ttk.Label(frm, text='Resolution', font=('Segoe UI', 10, 'bold')).pack(anchor='w', pady=(8, 0))
        rbox = ttk.Frame(frm)
        rbox.pack(fill=tk.X, pady=(2, 0))
        self._res_var = tk.StringVar(value=default_res)
        for i, (key, label, _val) in enumerate(resolutions):
            ttk.Radiobutton(rbox, text=label, value=key, variable=self._res_var).grid(
                row=i, column=0, sticky='w', padx=6, pady=1)
        if kind == 'screen':
            ttk.Label(frm, foreground='#555555', wraplength=440,
                      font=('Segoe UI', 8, 'italic'),
                      text='The window is captured at its current pixel size and resized to the '
                           'target (high-quality LANCZOS). For a true native 4K render of the graph '
                           'itself, use the figure export at 4K UHD.').pack(fill=tk.X, pady=(6, 0), anchor='w')

        btns = ttk.Frame(frm)
        btns.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(btns, text='OK', command=self._ok).pack(side=tk.RIGHT, padx=4)
        ttk.Button(btns, text='Cancel', command=self.destroy).pack(side=tk.RIGHT, padx=4)

        self.protocol('WM_DELETE_WINDOW', self.destroy)
        self.bind('<Return>', lambda _e: self._ok())
        self.bind('<Escape>', lambda _e: self.destroy())

        if parent is not None:
            self.transient(parent)
        self.update_idletasks()
        try:
            px, py = parent.winfo_rootx(), parent.winfo_rooty()
            pw, ph = parent.winfo_width(), parent.winfo_height()
        except Exception:
            px, py = 0, 0
            pw, ph = self.winfo_screenwidth(), self.winfo_screenheight()
        x = px + max(0, (pw - self.winfo_reqwidth()) // 2)
        y = py + max(0, (ph - self.winfo_reqheight()) // 3)
        self.geometry(f'+{x}+{y}')
        self.grab_set()

    def _update_note(self):
        self._note_var.set(self._notes[self._fmt_var.get()])

    def _ok(self):
        self.result = (self._fmt_var.get(), self._res_var.get())
        self.destroy()

    @classmethod
    def ask(cls, parent, kind='figure', title='Export options'):
        dlg = cls(parent, kind=kind, title=title)
        dlg.wait_window()
        return dlg.result


# ═════════════════════════════════════════════════════════════════════
# 7. ONE-CALL PROMPTS (used by every export button in the app)
# ═════════════════════════════════════════════════════════════════════
def prompt_export_figure(fig, parent=None, suggested_name='GranuloGraph_figure'):
    """Format + resolution dialog, Save-As dialog, export. Returns the path
    or None when the user cancels."""
    if fig is None:
        messagebox.showwarning('No Graph', 'There is no figure to export.', parent=parent)
        return None
    choice = ExportOptionsDialog.ask(parent, kind='figure',
                                     title='Export Figure - Format & Resolution')
    if not choice:
        return None
    ext, res_key = choice
    filename = filedialog.asksaveasfilename(
        parent=parent, title='Save Figure',
        defaultextension=f'.{ext}', initialfile=f'{suggested_name}.{ext}',
        filetypes=build_filetypes())
    if not filename:
        return None
    root_part, given_ext = os.path.splitext(filename)
    if not given_ext:
        filename = f'{filename}.{ext}'
    export_figure(fig, filename, res_key)
    return filename


def prompt_export_screen(widget, parent=None, suggested_name='GranuloGraph_screen'):
    """Resolution dialog, Save-As dialog, full-window capture + save.
    Returns the path or None when the user cancels."""
    if widget is None:
        messagebox.showwarning('No Screen', 'There is no window to capture.', parent=parent)
        return None
    choice = ExportOptionsDialog.ask(parent, kind='screen',
                                     title='Save Screen Image - Format & Resolution')
    if not choice:
        return None
    ext, res_key = choice
    filename = filedialog.asksaveasfilename(
        parent=parent, title='Save Screen Image',
        defaultextension=f'.{ext}', initialfile=f'{suggested_name}.{ext}',
        filetypes=build_screen_filetypes())
    if not filename:
        return None
    root_part, given_ext = os.path.splitext(filename)
    if not given_ext:
        filename = f'{filename}.{ext}'
    export_screen(widget, filename, res_key)
    return filename


# ═════════════════════════════════════════════════════════════════════
# 8. TOOLBAR - the "Save the figure" button (disk icon, bottom left)
#    now opens the same unified dialog (all formats + HD/4K).
# ═════════════════════════════════════════════════════════════════════
class GranuloToolbar(NavigationToolbar2Tk):
    """matplotlib navigation toolbar whose save button exports through the
    unified GranuloGraph dialog instead of the plain matplotlib dialog."""

    def save_figure(self, *args):
        if self.canvas is None:
            return
        fig = self.canvas.figure
        saved = prompt_export_figure(fig, parent=self, suggested_name='GranuloGraph_figure')
        if saved:
            try:
                messagebox.showinfo('Export Successful', f'Figure saved to:\n{saved}', parent=self)
            except Exception:
                pass


# ═════════════════════════════════════════════════════════════════════
# 9. DROP-IN MIXINS for GraphScreen / HomeScreen
# ═════════════════════════════════════════════════════════════════════
class GraphScreenExportMixin:
    """Add to GraphScreen's base classes to get the full-screen capture."""

    def save_full_screen(self, suggested_name='GranuloGraph_graph_screen'):
        """Capture the whole Graph Screen window (toolbar, graph, side panels)
        in HD / Full HD / 2K / 4K - better than any manual screenshot."""
        saved = prompt_export_screen(self.winfo_toplevel(), parent=self,
                                     suggested_name=suggested_name)
        if saved:
            messagebox.showinfo('Export Successful', f'Full screen image saved to:\n{saved}',
                                parent=self)


class HomeScreenExportMixin:
    """Add to HomeScreen's base classes to get the full-screen capture."""

    def save_home_screen(self, suggested_name='GranuloGraph_home_screen'):
        """Capture the whole Home Screen window (menu, grid, side panel) in
        HD / Full HD / 2K / 4K - better than any manual screenshot."""
        saved = prompt_export_screen(self.winfo_toplevel(), parent=self,
                                     suggested_name=suggested_name)
        if saved:
            messagebox.showinfo('Export Successful', f'Home screen image saved to:\n{saved}',
                                parent=self)
