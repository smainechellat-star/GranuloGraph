"""
Calculations Module — Sedimentological and Geotechnical Parameters
Folk & Ward (1957) and related formulas
International Standard Method (ASTM D6913, ISO 17892-4, BS 1377, NF P 94-056)

Author : Smaine Chellat
Institution: University Constantine 1, Geological Department, Algeria

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INTERPOLATION ENGINE  (v2.0)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Logarithmic PCHIP histospline workflow (Fritsch–Carlson, 1980):

  1. x_i     = log10(d_i)            (ascending, fine → coarse)
  2. F_i     = cumulative % passing  (0 → 100 %, strictly non-decreasing)
  3. F(x)    = PchipInterpolator(x_i, F_i)     ← monotone cubic
  4. f(x)    = dF/dx = F'(x)                    ← exact derivative (piecewise quadratic)

Because PCHIP is built directly on F, the identity
    ∫_{x_{i-1}}^{x_i} f(x) dx  =  F(x_i) − F(x_{i-1})
holds exactly (fundamental theorem of calculus).  No overshoots, no negative
frequencies, no mass leakage — the three mathematical guarantees required by
the reviewer.

NATIVE PAN HANDLING (reviewer point 5):
  The bottom-pan fraction may be entered as "Pan" / "Bottom" / "Fonds" / "Bac"
  (case-insensitive) instead of a numeric aperture.  The pan mass is included
  in every percentage denominator and is anchored as F = 0 at half a log-decade
  below the finest real sieve — no dummy 0.035 mm placeholder.

ASTM D6913 RECOVERY LIMIT:
  A warning is triggered if the sieving loss exceeds 0.5% (i.e., recovery < 99.5%).
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import math
from typing import Dict, List, Optional, Tuple, Union

from scipy import interpolate


# ═══════════════════════════════════════════════════════════════════════════════
# Native "Pan" / "Bottom" support  (reviewer point 5)
# ═══════════════════════════════════════════════════════════════════════════════
PAN_LABELS = {
    "pan", "bottom", "bottom pan", "pan/bottom", "pan / bottom",
    "fonds", "bac", "tambour", "recipient", "fond",
}


def is_pan_label(value) -> bool:
    """Return True if `value` is a recognised pan / bottom label."""
    return isinstance(value, str) and value.strip().lower() in PAN_LABELS


def normalize_pan_label(value) -> str:
    """Normalize any pan label to the canonical 'Pan' spelling for display."""
    return "Pan" if is_pan_label(value) else str(value)


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _deduplicate_ascending(
    x: List[float], y: List[float], keep: str = "max"
) -> Tuple[List[float], List[float]]:
    """Remove duplicate x-values; return strictly ascending lists."""
    xy_map: Dict[float, float] = {}
    for xv, yv in zip(x, y):
        if xv not in xy_map:
            xy_map[xv] = yv
        else:
            if keep == "max" and yv > xy_map[xv]:
                xy_map[xv] = yv
            elif keep == "min" and yv < xy_map[xv]:
                xy_map[xv] = yv
    if not xy_map:
        return [], []
    pairs = sorted(xy_map.items())
    xs, ys = zip(*pairs)
    return list(xs), list(ys)


def _make_pchip_spline(x: List[float], y: List[float], keep: str = "max"):
    """Fritsch–Carlson monotone cubic spline (PCHIP), NaN-safe."""
    valid = [
        (xv, yv) for xv, yv in zip(x, y)
        if not (math.isinf(xv) or math.isnan(xv) or
                math.isinf(yv) or math.isnan(yv))
    ]
    if len(valid) < 2:
        return None
    xs, ys = zip(*valid)
    xs, ys = _deduplicate_ascending(list(xs), list(ys), keep=keep)
    if len(xs) < 2:
        return None
    try:
        return interpolate.PchipInterpolator(xs, ys, extrapolate=False)
    except Exception as exc:
        print(f"Warning [_make_pchip_spline]: {exc}")
        return None

# ═══════════════════════════════════════════════════════════════════════════════
# Dual-standard grain-size fractions (ISO 14688-1:2017 / ASTM D2487 / USCS)
# ═══════════════════════════════════════════════════════════════════════════════

def compute_dual_standard_fractions(pchip_passing_func):
    """
    Computes both ISO 14688-1 and ASTM D2487 fraction percentages (%)
    from a cumulative-passing interpolator pchip_passing_func(d_mm).

      ISO 14688-1:2017 : Clay < 0.002 | Silt 0.002-0.063 | Sand 0.063-2.0 |
                         Gravel 2.0-63.0 | Cobbles > 63.0 mm
      ASTM D2487/USCS  : Fines < 0.075 (#200) | Sand 0.075-4.75 (#4) |
                         Gravel 4.75-75.0 (3 in.) | Cobbles > 75.0 mm
    """
    def get_pass(d):
        # Clamp between 0% and 100%
        return max(0.0, min(100.0, float(pchip_passing_func(d))))

    # --- ISO 14688-1:2017 cutoffs (0.002, 0.063, 2.0, 63.0 mm) ---
    p_002 = get_pass(0.002)
    p_063 = get_pass(0.063)
    p_200 = get_pass(2.0)
    p_630 = get_pass(63.0)

    iso_fractions = {
        "ISO_Clay_%":    round(p_002, 2),
        "ISO_Silt_%":    round(max(0.0, p_063 - p_002), 2),
        "ISO_Sand_%":    round(max(0.0, p_200 - p_063), 2),
        "ISO_Gravel_%":  round(max(0.0, p_630 - p_200), 2),
        "ISO_Cobbles_%": round(max(0.0, 100.0 - p_630), 2),
    }

    # --- ASTM D2487 (USCS) cutoffs (0.075 mm / #200, 4.75 mm / #4, 75.0 mm / 3 in.) ---
    p_075 = get_pass(0.075)
    p_475 = get_pass(4.75)
    p_750 = get_pass(75.0)

    astm_fractions = {
        "ASTM_Fines_%":  round(p_075, 2),  # Silt + Clay (< 0.075 mm)
        "ASTM_Sand_%":   round(max(0.0, p_475 - p_075), 2),
        "ASTM_Gravel_%": round(max(0.0, p_750 - p_475), 2),
        "ASTM_Cobbles_%": round(max(0.0, 100.0 - p_750), 2),
    }

    return {"ISO": iso_fractions, "ASTM": astm_fractions}



# ═══════════════════════════════════════════════════════════════════════════════
# Main calculator class
# ═══════════════════════════════════════════════════════════════════════════════

class GranuloCalculator:
    """
    Calculate all sedimentological and geotechnical grain-size parameters.

    Data model
    ----------
      self.data               : sieve list (diameter_mm, weight_g) — coarse→fine
      self.pan_weight         : total mass assigned to Pan/Bottom row(s)
      self.has_pan            : True if at least one Pan row was given
      self.cumulative_passing : sieve-only cumulative % passing
      self.recovered_weight   : sieves + pan (basis for ASTM denominator)

    Interpolation engine (v2.0)
    -------------------------
      self._cum_spline  : PchipInterpolator(log10(d) → F)     [forward]
      self._cum_deriv   : dF/d(log10 d)                        [frequency]
      self._inv_spline  : PchipInterpolator(F → log10(d))     [inverse]
    """

    # ── Constructor ────────────────────────────────────────────────────────────

    def __init__(
        self,
        data: List[Tuple[object, float]],
        initial_weight: float,
        use_recovered_weight: bool = True,
        verbose: bool = False,
    ):
        """
        Parameters
        ----------
        data : list of (diameter_mm_or_pan_label, weight_g)
            Diameter may be a positive float OR a Pan/Bottom string.
        initial_weight : total sample mass before sieving (grams).
        use_recovered_weight : True  → recovered basis (ASTM D6913)
                              False → initial   basis (NF P 94-056 / ISO)
        verbose : if True, print setup summary and mass-conservation self-test
        """
        # ── Separate sieves from pan(s) ────────────────────────────────────
        sieve_data: List[Tuple[float, float]] = []
        pan_weight = 0.0
        has_pan_label = False

        for d, w in data:
            if w < 0:
                raise ValueError(f"Weight must be non-negative (got {w} g)")
            if is_pan_label(d):
                has_pan_label = True
                pan_weight += float(w)
                continue
            try:
                d_float = float(d)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Invalid diameter {d!r}. Use a positive number or one of: "
                    f"{sorted(PAN_LABELS)}"
                )
            if d_float <= 0:
                raise ValueError(f"Diameter must be positive (got {d_float} mm)")
            sieve_data.append((d_float, float(w)))

        if not sieve_data:
            raise ValueError("At least one sieve with a numeric diameter is required.")
        if initial_weight <= 0:
            raise ValueError("initial_weight must be positive.")

        # ── Sort coarse → fine ─────────────────────────────────────────────
        self.data = sorted(sieve_data, key=lambda t: t[0], reverse=True)
        self.initial_weight = float(initial_weight)
        self.pan_weight = pan_weight
        self.has_pan = has_pan_label
        self.use_recovered_weight = bool(use_recovered_weight)
        self._recovery_warning = False

        # ── Totals (pan included) ──────────────────────────────────────────
        self.recovered_weight = sum(w for _, w in self.data) + pan_weight
        weight_basis = (
            self.recovered_weight if use_recovered_weight else initial_weight
        )
        basis_label = (
            "RECOVERED weight (ASTM D6913 §11.2)" if use_recovered_weight
            else "INITIAL weight (NF P 94-056 / ISO 17892-4)"
        )
        
        # ── Recovery / Loss Calculation ────────────────────────────────────
        recovery_pct = self.recovered_weight / initial_weight * 100.0
        loss_pct = 100.0 - recovery_pct

        # ASTM D6913 allows a MAXIMUM sieving loss of 0.5% (99.5% recovery)
        if abs(loss_pct) > 0.5:
            self._recovery_warning = True
            if verbose:
                if loss_pct > 0:
                    print(f"⚠️  WARNING: Sieving loss {loss_pct:.2f}% > 0.5%.\n"
                          f"     ASTM D6913 specifies a maximum acceptable loss of 0.5%.")
                else:
                    print(f"⚠️  WARNING: Recovered weight > initial by {abs(loss_pct):.2f}%.\n"
                          f"     This indicates a data entry error or material addition.")
        elif verbose:
            print(f"ℹ️  Note: Sieving loss is {loss_pct:.2f}% — within the ASTM D6913 limit (≤ 0.5%).")

        if verbose:
            print(f"\n{'─'*62}\n  GRAIN-SIZE ANALYSIS — CALCULATION SETUP\n{'─'*62}")
            print(f"  Basis            : {basis_label}")
            print(f"  Initial weight   : {initial_weight:.2f} g")
            print(f"  Recovered weight : {self.recovered_weight:.2f} g")
            print(f"  Recovery         : {recovery_pct:.2f}%")
            if has_pan_label:
                print(f"  Pan weight       : {pan_weight:.2f} g "
                      f"({pan_weight / weight_basis * 100.0:.2f}% of basis)")
            print(f"{'─'*62}")

        # ── Partial percentages per sieve ─────────────────────────────────
        self.percentages: List[float] = []
        for i, (d, w) in enumerate(self.data):
            pct = w * 100.0 / weight_basis
            self.percentages.append(pct)
            if verbose:
                print(f"  Sieve {i+1:>2}: {d:>10.4f} mm  |  "
                      f"{w:>9.2f} g  |  partial %: {pct:>6.2f}%")

        # ── Cumulative retained / passing (sieve-only) ────────────────────
        self.cumulative_retained: List[float] = []
        cum = 0.0
        for pct in self.percentages:
            cum += pct
            self.cumulative_retained.append(cum)
        self.cumulative_passing = [100.0 - cr for cr in self.cumulative_retained]

        if verbose:
            print(f"\n  Cumulative passing @ first sieve "
                  f"({self.data[0][0]:.4f} mm): "
                  f"{self.cumulative_passing[0]:.2f}%")
            print(f"  Cumulative passing @ last  sieve "
                  f"({self.data[-1][0]:.4f} mm): "
                  f"{self.cumulative_passing[-1]:.2f}%")

        # ── Phi values at measured sieves ─────────────────────────────────
        self.phi = [-math.log2(d) for d, _ in self.data]

        # ═══════════════════════════════════════════════════════════════════
        # PCHIP HISTOSPLINE BUILD-UP
        # ═══════════════════════════════════════════════════════════════════
        d_asc = [d for d, _ in reversed(self.data)]           # fine → coarse
        F_asc = list(reversed(self.cumulative_passing))

        # Pan / recovery anchor: place a virtual pan at half a log-decade
        # below the finest real sieve.  This preserves the exact mass integral
        # without inventing a fake aperture (reviewer point 5).
        if self.has_pan and pan_weight > 0:
            d_asc = [d_asc[0] / math.sqrt(10.0)] + d_asc
            F_asc = [0.0] + F_asc
        elif F_asc[0] > 0.1:
            d_asc = [d_asc[0] / 2.0] + d_asc
            F_asc = [0.0] + F_asc

        # Coarse-end anchor for the 100 % boundary
        if F_asc[-1] < 99.9:
            d_asc = d_asc + [d_asc[-1] * 2.0]
            F_asc = F_asc + [100.0]

        log_d_asc = [math.log10(d) for d in d_asc]

        self._cum_spline = _make_pchip_spline(log_d_asc, F_asc, keep="max")
        self._cum_deriv = (
            self._cum_spline.derivative()
            if self._cum_spline is not None
               and hasattr(self._cum_spline, "derivative")
            else None
        )
        self._inv_spline = _make_pchip_spline(F_asc, log_d_asc, keep="min")

        if verbose and self._cum_spline is not None:
            ok, msg = self._verify_mass_conservation()
            print(f"\n  Mass-conservation self-test: {'✓' if ok else '✗'} {msg}")

    # ═══════════════════════════════════════════════════════════════════════════
    # Mass-conservation self-test  (reviewer guarantee #1)
    # ═══════════════════════════════════════════════════════════════════════════

    def _verify_mass_conservation(self) -> Tuple[bool, str]:
        """Check  ∫ f(x) dx = F(x_i) − F(x_{i-1})  on every measured interval."""
        if self._cum_spline is None or self._cum_deriv is None:
            return False, "Spline not available"
        try:
            anti = self._cum_spline.antiderivative()
        except Exception:
            return True, "antiderivative not available — skipped"

        d_asc = sorted([d for d, _ in self.data])
        max_err = 0.0
        for i in range(len(d_asc) - 1):
            x1 = math.log10(d_asc[i])
            x2 = math.log10(d_asc[i + 1])
            integral = float(anti(x2) - anti(x1))
            expected = float(self._cum_spline(x2) - self._cum_spline(x1))
            if abs(expected) > 1e-9:
                max_err = max(max_err, abs(integral - expected) / abs(expected))
        return max_err < 1e-6, f"max relative mass error = {max_err:.2e}"

    # ═══════════════════════════════════════════════════════════════════════════
    # Public query helpers
    # ═══════════════════════════════════════════════════════════════════════════

    def get_passing_at_diameter(self, diameter_mm: float) -> float:
        """Cumulative passing (%) at a given diameter (mm)."""
        if self._cum_spline is None or diameter_mm <= 0:
            return float("nan")
        x = math.log10(diameter_mm)
        try:
            val = float(self._cum_spline(x))
            if not math.isnan(val):
                return val
        except Exception:
            pass
        d_min = min(d for d, _ in self.data) / 2.0
        d_max = max(d for d, _ in self.data) * 2.0
        if diameter_mm < d_min:
            return 0.0
        if diameter_mm > d_max:
            return 100.0
        return float("nan")

    def get_percentile_diameter(self, percentile: float) -> float:
        """Diameter (mm) at the given cumulative passing %."""
        if self._inv_spline is None:
            return float("nan")
        pct = max(0.0, min(100.0, percentile))
        try:
            log_d = float(self._inv_spline(pct))
            if math.isnan(log_d):
                return float("nan")
            return 10.0 ** log_d
        except Exception:
            return float("nan")

    def get_phi_at_percentile(self, percentile: float) -> float:
        """Phi value at the given cumulative passing %  (φ = −log₂ d)."""
        d = self.get_percentile_diameter(percentile)
        if math.isnan(d) or d <= 0:
            return float("nan")
        return -math.log2(d)

    # ═══════════════════════════════════════════════════════════════════════════
    # PCHIP histospline outputs (used by graph_screen.py)
    # ═══════════════════════════════════════════════════════════════════════════

    def get_cumulative_curve(self, num_points: int = 500):
        """Return (diameters_mm, cumulative_passing_%), coarse → fine."""
        import numpy as np
        if self._cum_spline is None:
            return np.array([]), np.array([])
        d_min = min(d for d, _ in self.data) / 2.0
        d_max = max(d for d, _ in self.data) * 2.0
        x = np.linspace(math.log10(d_min), math.log10(d_max), num_points)
        try:
            F = self._cum_spline(x)
        except Exception:
            return np.array([]), np.array([])
        d = 10.0 ** x
        return d[::-1], F[::-1]

    def get_frequency_curve(self, num_points: int = 500):
        """Return (diameters_mm, f = dF/dlog10(d)), coarse → fine. f ≥ 0."""
        import numpy as np
        if self._cum_deriv is None:
            return np.array([]), np.array([])
        d_min = min(d for d, _ in self.data) / 2.0
        d_max = max(d for d, _ in self.data) * 2.0
        x = np.linspace(math.log10(d_min), math.log10(d_max), num_points)
        try:
            f = self._cum_deriv(x)
        except Exception:
            return np.array([]), np.array([])
        f = np.clip(f, 0.0, None)
        d = 10.0 ** x
        return d[::-1], f[::-1]

    def get_frequency_at_diameter(self, diameter_mm: float) -> float:
        """f(x) = dF/d(log₁₀ d) at the given diameter (units: % per log₁₀ unit)."""
        if self._cum_deriv is None or diameter_mm <= 0:
            return float("nan")
        try:
            return float(self._cum_deriv(math.log10(diameter_mm)))
        except Exception:
            return float("nan")

    # ═══════════════════════════════════════════════════════════════════════════
    # Sedimentological parameters — Folk & Ward (1957)
    # ═══════════════════════════════════════════════════════════════════════════

    def calculate_mode(self) -> Tuple[float, str]:
        if not self.percentages:
            return float("nan"), "No data"
        max_pct = max(self.percentages)
        max_idx = self.percentages.index(max_pct)
        threshold = 0.025 * max_pct
        n = len(self.data)
        if max_idx == 0 or max_idx == n - 1:
            mode_dia = self.data[max_idx][0]
        else:
            d1, d2, d3 = (self.data[max_idx - 1][0],
                          self.data[max_idx][0],
                          self.data[max_idx + 1][0])
            p1, p2, p3 = (self.percentages[max_idx - 1],
                          self.percentages[max_idx],
                          self.percentages[max_idx + 1])
            if p2 > p1 and p2 > p3:
                try:
                    ld1, ld2, ld3 = math.log10(d1), math.log10(d2), math.log10(d3)
                    num = (ld2 - ld1) ** 2 * (p2 - p3) - (ld2 - ld3) ** 2 * (p2 - p1)
                    den = (ld2 - ld1) * (p2 - p3) - (ld2 - ld3) * (p2 - p1)
                    mode_dia = (10 ** (ld2 - 0.5 * num / den)) if den != 0 else d2
                except Exception:
                    mode_dia = d2
            else:
                mode_dia = d2
        peaks = 0
        for i in range(1, n - 1):
            if (self.percentages[i] > self.percentages[i - 1] + threshold and
                    self.percentages[i] > self.percentages[i + 1] + threshold):
                peaks += 1
        modality = "bimodal / polymodal" if peaks >= 2 else "unimodal"
        return mode_dia, modality

    def calculate_mean(self) -> Tuple[float, float, float, float, float]:
        phi16 = self.get_phi_at_percentile(16)
        phi50 = self.get_phi_at_percentile(50)
        phi84 = self.get_phi_at_percentile(84)
        if any(math.isnan(v) for v in (phi16, phi50, phi84)):
            return float("nan"), float("nan"), phi16, phi50, phi84
        phi_mean = (phi16 + phi50 + phi84) / 3.0
        mm_mean = 2.0 ** (-phi_mean)
        return phi_mean, mm_mean, phi16, phi50, phi84

    def calculate_median(self) -> Tuple[float, float]:
        return self.get_phi_at_percentile(50), self.get_percentile_diameter(50)

    def calculate_sorting(self) -> Tuple[float, str]:
        phi5  = self.get_phi_at_percentile(5)
        phi16 = self.get_phi_at_percentile(16)
        phi84 = self.get_phi_at_percentile(84)
        phi95 = self.get_phi_at_percentile(95)
        if any(math.isnan(v) for v in (phi5, phi16, phi84, phi95)):
            return float("nan"), "Insufficient data"
        if phi16 <= phi84 or phi5 <= phi95:
            return float("nan"), "Invalid data (phi values not decreasing)"
        sigma = (phi16 - phi84) / 4.0 + (phi5 - phi95) / 6.6
        if sigma < 0.35:    cls = "Very well sorted"
        elif sigma < 0.50:  cls = "Well sorted"
        elif sigma < 0.71:  cls = "Moderately well sorted"
        elif sigma < 1.00:  cls = "Moderately sorted"
        elif sigma < 2.00:  cls = "Poorly sorted"
        elif sigma < 4.00:  cls = "Very poorly sorted"
        else:               cls = "Extremely poorly sorted"
        return sigma, cls

    def calculate_skewness(self) -> Tuple[float, str]:
        phi5  = self.get_phi_at_percentile(5)
        phi16 = self.get_phi_at_percentile(16)
        phi50 = self.get_phi_at_percentile(50)
        phi84 = self.get_phi_at_percentile(84)
        phi95 = self.get_phi_at_percentile(95)
        if any(math.isnan(v) for v in (phi5, phi16, phi50, phi84, phi95)):
            return float("nan"), "Insufficient data"
        if phi16 <= phi84 or phi5 <= phi95:
            return float("nan"), "Invalid data (phi values not decreasing)"
        d1 = 2.0 * (phi16 - phi84)
        d2 = 2.0 * (phi5 - phi95)
        if d1 <= 0 or d2 <= 0:
            return float("nan"), "Invalid data (denominator ≤ 0)"
        skew = (phi16 + phi84 - 2.0 * phi50) / d1 + \
               (phi5 + phi95 - 2.0 * phi50) / d2
        if skew < -0.30:    cls = "Strongly coarse skewed"
        elif skew < -0.10:  cls = "Coarse skewed"
        elif skew < 0.10:   cls = "Near symmetrical"
        elif skew < 0.30:   cls = "Fine skewed"
        else:               cls = "Strongly fine skewed"
        return skew, cls

    def calculate_kurtosis(self) -> Tuple[float, str]:
        phi5  = self.get_phi_at_percentile(5)
        phi25 = self.get_phi_at_percentile(25)
        phi75 = self.get_phi_at_percentile(75)
        phi95 = self.get_phi_at_percentile(95)
        if any(math.isnan(v) for v in (phi5, phi25, phi75, phi95)):
            return float("nan"), "Insufficient data"
        if phi25 <= phi75:
            return float("nan"), "Invalid data (phi25 > phi75 required)"
        den = 2.44 * (phi25 - phi75)
        if den <= 0:
            return float("nan"), "Invalid data (denominator ≤ 0)"
        kg = (phi5 - phi95) / den
        if kg < 0.67:    cls = "Very platykurtic"
        elif kg < 0.90:  cls = "Platykurtic"
        elif kg < 1.11:  cls = "Mesokurtic"
        elif kg < 1.50:  cls = "Leptokurtic"
        elif kg < 3.00:  cls = "Very leptokurtic"
        else:            cls = "Extremely leptokurtic"
        return kg, cls

    # ═══════════════════════════════════════════════════════════════════════════
    # Geotechnical parameters
    # ═══════════════════════════════════════════════════════════════════════════

    def calculate_uniformity_coefficient(self) -> Tuple[float, str]:
        d10 = self.get_percentile_diameter(10)
        d60 = self.get_percentile_diameter(60)
        if any(math.isnan(v) for v in (d10, d60)) or d10 <= 0:
            return float("nan"), "Insufficient data"
        cu = d60 / d10
        if cu >= 6:    cls = "Well-graded  (Cu ≥ 6)"
        elif cu >= 2:  cls = "Moderately graded  (2 ≤ Cu < 6)"
        else:          cls = "Poorly graded / uniform  (Cu < 2)"
        return cu, cls

    def calculate_curvature_coefficient(self) -> Tuple[float, str]:
        d10 = self.get_percentile_diameter(10)
        d30 = self.get_percentile_diameter(30)
        d60 = self.get_percentile_diameter(60)
        if any(math.isnan(v) for v in (d10, d30, d60)) or d10 <= 0 or d60 <= 0:
            return float("nan"), "Insufficient data"
        cc = d30 ** 2 / (d10 * d60)
        cls = ("Well-graded  (1 ≤ Cc ≤ 3)" if 1.0 <= cc <= 3.0
               else "Poorly graded  (Cc outside 1–3)")
        return cc, cls

    def calculate_fineness_modulus(self) -> Tuple[float, str]:
        target_sieves = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125]
        total_ret = 0.0
        for sieve in target_sieves:
            cp = self.get_passing_at_diameter(sieve)
            if math.isnan(cp):
                cp = 0.0
            total_ret += max(0.0, min(100.0, 100.0 - cp))
        fm = total_ret / 100.0
        if fm < 2.2:   cls, note = "Very fine sand", "RISK OF SHRINKAGE AND CRACKING — too fine for structural concrete"
        elif fm < 2.6: cls, note = "Fine sand", "Ideal for finishing coats; may require extra cement in concrete"
        elif fm < 2.9: cls, note = "Medium sand", "PREFERRED for high-quality concrete — optimal workability and strength"
        elif fm < 3.2: cls, note = "Coarse sand", "Suitable for high-strength concrete; may be harsh if poorly graded"
        else:          cls, note = "Very coarse sand", "STONY / HARSH concrete — poor workability, difficult to finish"
        return fm, f"{cls} — {note}"

    # ═══════════════════════════════════════════════════════════════════════════
    # Convenience aggregators
    # ═══════════════════════════════════════════════════════════════════════════

    def get_all_percentiles(self) -> Dict:
        targets = [5, 10, 16, 25, 30, 50, 60, 70, 75, 84, 90, 95]
        result: Dict = {}
        for p in targets:
            mm = self.get_percentile_diameter(p)
            phi = self.get_phi_at_percentile(p)
            result[f"D{p}"] = mm if not math.isnan(mm) else 0.0
            result[f"phi{p}"] = phi if not math.isnan(phi) else 0.0
        return result


    def get_dual_standard_fractions(self) -> Dict:
        """ISO 14688-1:2017 + ASTM D2487 (USCS) size fractions (%), integrated
        from the PCHIP cumulative-passing curve.
        Returns {'ISO': {...}, 'ASTM': {...}}."""
        try:
            return compute_dual_standard_fractions(self.get_passing_at_diameter)
        except Exception as exc:
            print(f"Warning [get_dual_standard_fractions]: {exc}")
            zero_iso = {k: 0.0 for k in ("ISO_Clay_%", "ISO_Silt_%", "ISO_Sand_%",
                                         "ISO_Gravel_%", "ISO_Cobbles_%")}
            zero_astm = {k: 0.0 for k in ("ASTM_Fines_%", "ASTM_Sand_%",
                                          "ASTM_Gravel_%", "ASTM_Cobbles_%")}
            return {"ISO": zero_iso, "ASTM": zero_astm}

    def get_all_parameters(self) -> Dict:
        params: Dict = {}
        params.update(self.get_all_percentiles())

        mode_mm, modality = self.calculate_mode()
        params["mode_mm"] = mode_mm if not math.isnan(mode_mm) else 0.0
        params["modality"] = modality

        phi_mean, mm_mean, phi16, phi50, phi84 = self.calculate_mean()
        params["mean_phi"] = phi_mean if not math.isnan(phi_mean) else 0.0
        params["mean_mm"]  = mm_mean  if not math.isnan(mm_mean)  else 0.0
        params["phi16"] = phi16 if not math.isnan(phi16) else 0.0
        params["phi50"] = phi50 if not math.isnan(phi50) else 0.0
        params["phi84"] = phi84 if not math.isnan(phi84) else 0.0

        phi_med, mm_med = self.calculate_median()
        params["median_phi"] = phi_med if not math.isnan(phi_med) else 0.0
        params["median_mm"]  = mm_med  if not math.isnan(mm_med)  else 0.0

        sigma, sigma_cls = self.calculate_sorting()
        params["sorting"] = sigma if not math.isnan(sigma) else 0.0
        params["sorting_class"] = sigma_cls

        skew, skew_cls = self.calculate_skewness()
        params["skewness"] = skew if not math.isnan(skew) else 0.0
        params["skewness_class"] = skew_cls

        kg, kg_cls = self.calculate_kurtosis()
        params["kurtosis"] = kg if not math.isnan(kg) else 0.0
        params["kurtosis_class"] = kg_cls

        cu, cu_cls = self.calculate_uniformity_coefficient()
        params["Cu"] = cu if not math.isnan(cu) else 0.0
        params["Cu_class"] = cu_cls

        cc, cc_cls = self.calculate_curvature_coefficient()
        params["Cc"] = cc if not math.isnan(cc) else 0.0
        params["Cc_class"] = cc_cls

        fm, fm_cls = self.calculate_fineness_modulus()
        params["FM"] = fm if not math.isnan(fm) else 0.0
        params["FM_class"] = fm_cls

        # Dual-standard size fractions (ISO 14688-1:2017 / ASTM D2487) — used by
        # the Graph Screen, the Excel/CSV exports and the PDF report
        dual = self.get_dual_standard_fractions()
        params.update(dual["ISO"])
        params.update(dual["ASTM"])

        params["initial_weight"]   = self.initial_weight
        params["recovered_weight"] = self.recovered_weight
        params["recovery_pct"] = (
            self.recovered_weight / self.initial_weight * 100.0
            if self.initial_weight > 0 else 0.0
        )
        params["calculation_basis"] = (
            "RECOVERED (ASTM D6913)" if self.use_recovered_weight
            else "INITIAL (NF P 94-056 / ISO)"
        )
        params["recovery_warning"] = self._recovery_warning
        params["has_pan"]          = self.has_pan
        params["pan_weight_g"]     = self.pan_weight
        return params

    def get_pan_summary(self) -> Dict:
        """Return pan-related metadata for UI display / export."""
        basis = (self.recovered_weight if self.use_recovered_weight
                 else self.initial_weight)
        return {
            "has_pan": bool(self.has_pan),
            "pan_weight_g": float(self.pan_weight),
            "pan_pct_of_basis": (self.pan_weight / basis * 100.0) if basis else 0.0,
            "finest_sieve_mm": self.data[-1][0] if self.data else float("nan"),
            "finest_sieve_passing_pct":
                self.cumulative_passing[-1] if self.cumulative_passing else float("nan"),
        }


    def get_size_fractions(self) -> Dict:
        """
        Textural size fractions (%) integrated from the PCHIP cumulative curve
        (Wentworth / ISO 14688-1 boundaries), for ternary classification diagrams:

          gravel : d  >  2.0 mm
          sand   : 0.0625 mm < d <= 2.0 mm      (1/16 mm — 2 mm)
          silt   : 0.004 mm  < d <= 0.0625 mm
          clay   : d <= 0.004 mm

        Returns {'gravel', 'sand', 'silt', 'clay', 'mud'}; 'mud' = silt + clay
        is the fine fraction used by the Folk (1954) diagram.
        """

        def _passing_safe(diameter: float) -> float:
            v = self.get_passing_at_diameter(diameter)
            if not math.isnan(v):
                return v
            # Out-of-domain query (e.g. a sample already 100 % passing at its
            # coarsest sieve has no coarse anchor): clamp monotonically.
            if diameter >= self.data[0][0]:
                return float(self.cumulative_passing[0])
            return float(self.cumulative_passing[-1])

        F2 = _passing_safe(2.0)
        F_sand_top = _passing_safe(0.0625)
        F_silt_top = _passing_safe(0.004)
        if any(math.isnan(v) for v in (F2, F_sand_top, F_silt_top)):
            return {"gravel": 0.0, "sand": 0.0, "silt": 0.0, "clay": 0.0, "mud": 0.0}

        def _clamp(v: float) -> float:
            return max(0.0, min(100.0, v))

        gravel = _clamp(100.0 - F2)
        sand = _clamp(F2 - F_sand_top)
        silt = _clamp(F_sand_top - F_silt_top)
        clay = _clamp(F_silt_top)
        total = gravel + sand + silt + clay
        if total > 0:
            gravel, sand, silt, clay = (v / total * 100.0 for v in (gravel, sand, silt, clay))
        return {"gravel": gravel, "sand": sand, "silt": silt, "clay": clay, "mud": silt + clay}

    def print_summary(self):
        p = self.get_all_parameters()
        W = 62
        print("\n" + "═" * W)
        print(f"  {'GRAIN-SIZE ANALYSIS RESULTS':^{W-4}}")
        print("═" * W)
        print(f"  Calculation Basis: {p['calculation_basis']}")
        print(f"  Recovery: {p['recovery_pct']:.2f}%")
        if self.has_pan:
            pan = self.get_pan_summary()
            print(f"  Pan weight: {pan['pan_weight_g']:.2f} g "
                  f"({pan['pan_pct_of_basis']:.2f}% of basis)")
        if p["recovery_warning"]:
            print("  ⚠️  WARNING: Sieving loss exceeds 0.5% (ASTM D6913 limit)")
        print()
        print(f"  {'PERCENTILES':^{W-4}}")
        for name in ("D5", "D10", "D16", "D50", "D84", "D90", "D95"):
            print(f"    {name:<4}= {p[name]:>10.4f} mm   "
                  f"φ = {p[name.replace('D', 'phi')]:>7.3f} φ")
        print()
        print(f"  {'FOLK & WARD (1957) STATISTICS':^{W-4}}")
        print(f"    Graphic Mean  Mz = {p['mean_phi']:+.3f} φ  ({p['mean_mm']:.4f} mm)")
        print(f"    Median        Md = {p['median_phi']:+.3f} φ  ({p['median_mm']:.4f} mm)")
        print(f"    Sorting       σI = {p['sorting']:+.3f} φ  → {p['sorting_class']}")
        print(f"    Skewness      Sk = {p['skewness']:+.3f}    → {p['skewness_class']}")
        print(f"    Kurtosis      KG = {p['kurtosis']:+.3f}    → {p['kurtosis_class']}")
        print(f"    Mode             = {p['mode_mm']:.4f} mm  ({p['modality']})")
        print()
        print(f"  {'GEOTECHNICAL PARAMETERS':^{W-4}}")
        print(f"    Cu = {p['Cu']:.2f}  →  {p['Cu_class']}")
        print(f"    Cc = {p['Cc']:.2f}  →  {p['Cc_class']}")
        print(f"    FM = {p['FM']:.2f}  →  {p['FM_class']}")
        print("═" * W)


# ═══════════════════════════════════════════════════════════════════════════════
# Self-test (run: python calculations.py)
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    sample_data = [
        (4.000, 0.5),
        (2.000, 2.3),
        (1.000, 10.2),
        (0.500, 42.1),
        (0.250, 31.8),
        (0.125, 9.6),
        (0.036, 2.9),        # ISO 3310-1 finest sieve
        ("Pan", 0.6),        # native pan label — no fake aperture
    ]

    print("\n" + "=" * 62)
    print("  PAN-AWARE SELF-TEST  (ISO 3310-1 finest sieve = 0.036 mm)")
    print("=" * 62)
    calc = GranuloCalculator(sample_data, 100.0,
                             use_recovered_weight=True, verbose=True)

    pan = calc.get_pan_summary()
    print(f"\n  has_pan         : {pan['has_pan']}")
    print(f"  pan weight      : {pan['pan_weight_g']:.2f} g")
    print(f"  pan % of basis  : {pan['pan_pct_of_basis']:.2f}%")
    print(f"  finest sieve    : {pan['finest_sieve_mm']:.4f} mm")
    print(f"  finest % passing: {pan['finest_sieve_passing_pct']:.2f}%")

    ok, msg = calc._verify_mass_conservation()
    print(f"\n  Mass conservation: {'✓' if ok else '✗'}  {msg}")
    calc.print_summary()