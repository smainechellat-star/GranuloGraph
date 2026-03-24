"""
Calculations Module — Sedimentological and Geotechnical Parameters
Folk & Ward (1957) and related formulas
International Standard Method (ASTM D6913, ISO 17892-4, BS 1377, NF P 94-056)

Author : Smaine Chellat
Institution: University Constantine 1, Geological Department, Algeria

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CALCULATION BASIS (Selectable via use_recovered_weight parameter)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  • use_recovered_weight = True   → ASTM D6913 (Research/Journals)
                                    Percentages based on total recovered mass
                                    Ensures cumulative curve spans 0–100%
                                    
  • use_recovered_weight = False  → NF P 94-056 / ISO 17892-4 (Geotechnical)
                                    Percentages based on initial dry mass
                                    Standard for Algerian/French engineering reports

CORRECTIONS APPLIED (v4 – Dual-Method Production Ready):
  [FIX 1]  Interpolation x-direction: interp1d always receives ascending x
  [FIX 2]  passing_interp wired to get_passing_at_diameter() & FM calculation
  [FIX 3]  Sorting classification: complete 7-class Folk & Ward (1957) scale
  [FIX 4]  Kurtosis classification: complete 6-class scale (adds Extremely leptokurtic)
  [FIX 5]  Partial % denominator: selectable (recovered or initial weight)
  [FIX 6]  100% anchor point at 2×max_sieve for safe coarse-end interpolation
  [FIX 7]  Bimodality: 5% amplitude threshold to suppress noise peaks
  [FIX 8]  Fineness Modulus uses get_passing_at_diameter() — no duplicate loop
  [FIX 9]  Skewness terminology aligned with Folk & Ward original
  [FIX 10] Sorting & Skewness formulas adapted for % passing convention
"""

import math
from typing import Dict, List, Optional, Tuple
from scipy import interpolate


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level helper — Deduplicate and sort for interpolation
# ═══════════════════════════════════════════════════════════════════════════════

def _deduplicate_ascending(x: List[float], y: List[float]) -> Tuple[List[float], List[float]]:
    """
    Remove duplicate x-values (keep highest y), return lists sorted by
    strictly ascending x. Required because scipy raises ValueError on
    duplicate interpolation knots.
    """
    xy_map: Dict[float, float] = {}
    for xv, yv in zip(x, y):
        if xv not in xy_map or yv > xy_map[xv]:
            xy_map[xv] = yv
    if not xy_map:
        return [], []
    pairs = sorted(xy_map.items())
    xs, ys = zip(*pairs)
    return list(xs), list(ys)


# ═══════════════════════════════════════════════════════════════════════════════
# Factory functions for scipy interpolators
# ═══════════════════════════════════════════════════════════════════════════════

def _make_interp1d(x: List[float], y: List[float]) -> Optional[object]:
    """
    Linear scipy interp1d. x must be ASCENDING on entry (callers ensure this).
    Out-of-range queries are clamped to boundary values (no exception raised).
    """
    valid = [
        (xv, yv) for xv, yv in zip(x, y)
        if not (math.isinf(xv) or math.isnan(xv) or
                math.isinf(yv) or math.isnan(yv))
    ]
    if len(valid) < 2:
        return None
    xs, ys = zip(*valid)
    xs, ys = _deduplicate_ascending(list(xs), list(ys))
    if len(xs) < 2:
        return None
    try:
        return interpolate.interp1d(xs, ys, kind="linear",
                                    bounds_error=False,
                                    fill_value=(ys[0], ys[-1]))
    except Exception as exc:
        print(f"Warning [_make_interp1d]: {exc}")
        return None


def _make_pchip_or_linear(x: List[float], y: List[float]) -> Optional[object]:
    """
    PCHIP (≥4 pts, monotone-preserving cubic) or linear fallback.
    x must be strictly ascending.
    """
    valid = [
        (xv, yv) for xv, yv in zip(x, y)
        if not (math.isinf(xv) or math.isnan(xv) or
                math.isinf(yv) or math.isnan(yv))
    ]
    if len(valid) < 2:
        return None
    xs, ys = zip(*valid)
    xs, ys = _deduplicate_ascending(list(xs), list(ys))
    if len(xs) < 2:
        return None
    try:
        if len(xs) >= 4:
            return interpolate.PchipInterpolator(xs, ys, extrapolate=False)
        return interpolate.interp1d(xs, ys, kind="linear",
                                    bounds_error=False,
                                    fill_value=(ys[0], ys[-1]))
    except Exception as exc:
        print(f"Warning [_make_pchip_or_linear]: {exc}")
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# Main calculator class
# ═══════════════════════════════════════════════════════════════════════════════

class GranuloCalculator:
    """
    Calculate all sedimentological and geotechnical grain-size parameters.

    Two primary data arrays (built in __init__):
      • self.percentages        — partial % per sieve (frequency histogram)
      • self.cumulative_passing — cumulative passing (%) per sieve

    Three scipy interpolators (all with strictly ASCENDING x):
      passing_interp  : diameter (mm)     → cumulative passing (%)
      _inv_interp     : cumulative passing (%) → diameter (mm)      [PCHIP]
      phi_interp      : cumulative passing (%) → phi value

    Calculation Basis (selectable):
      • use_recovered_weight=True   → ASTM D6913 (Research/Journals)
      • use_recovered_weight=False  → NF P 94-056 / ISO (Geotechnical)
    """

    # ── Constructor ────────────────────────────────────────────────────────────

    def __init__(
        self,
        data: List[Tuple[float, float]],
        initial_weight: float,
        use_recovered_weight: bool = True,  # Default: ASTM (Research)
        verbose: bool = False,              # Control console output
    ):
        """
        Parameters
        ----------
        data : list of (diameter_mm, weight_g) — any input order.
        initial_weight : total sample mass before sieving (grams).
        use_recovered_weight :
            True  → partial % based on recovered mass (ASTM D6913 §11.2) [Default]
            False → partial % based on initial mass (NF P 94-056 / ISO)
        verbose :
            True  → print initialization summary and warnings
            False → silent (for production/batch processing)
        """
        if not data:
            raise ValueError("data must not be empty.")
        if initial_weight <= 0:
            raise ValueError("initial_weight must be positive.")

        # ── Sort coarse → fine (descending diameter) ────────────────────────
        self.data: List[Tuple[float, float]] = sorted(
            data, key=lambda t: t[0], reverse=True
        )
        self.initial_weight: float = initial_weight
        self.recovered_weight: float = sum(w for _, w in self.data)
        self.use_recovered_weight: bool = use_recovered_weight

        # ── Select denominator  [FIX 5] ────────────────────────────────────
        weight_basis = (self.recovered_weight if use_recovered_weight
                        else initial_weight)
        basis_label = ("RECOVERED weight (ASTM D6913 §11.2)"
                       if use_recovered_weight
                       else "INITIAL weight (NF P 94-056 / ISO 17892-4)")

        recovery_pct = (self.recovered_weight / initial_weight) * 100.0
        
        # ── Recovery Validation for Interpolation Reliability ───────────────
        self._recovery_warning = False
        if not use_recovered_weight and recovery_pct < 95.0:
            self._recovery_warning = True
            if verbose:
                print(f"⚠️  WARNING: Recovery {recovery_pct:.1f}% < 95%.\n"
                      f"     Using initial_weight — D5/D95 percentiles may have\n"
                      f"     increased uncertainty due to extrapolation.")
        elif verbose and recovery_pct < 98.0:
            print(f"ℹ️  Note: Recovery {recovery_pct:.1f}% — results are reliable.")

        if verbose:
            print(f"\n{'─'*62}")
            print(f"  GRAIN-SIZE ANALYSIS — CALCULATION SETUP")
            print(f"{'─'*62}")
            print(f"  Basis            : {basis_label}")
            print(f"  Initial weight   : {initial_weight:.3f} g")
            print(f"  Recovered weight : {self.recovered_weight:.3f} g")
            print(f"  Recovery         : {recovery_pct:.2f}%")
            print(f"{'─'*62}")

        # ── Partial percentages (frequency curve) ──────────────────────────
        self.percentages: List[float] = []
        for i, (d, w) in enumerate(self.data):
            pct = (w * 100.0) / weight_basis
            self.percentages.append(pct)
            if verbose:
                print(
                    f"  Sieve {i+1:>2}: {d:>9.4f} mm  |  "
                    f"{w:>8.3f} g  |  partial %: {pct:>6.2f}%"
                )

        # ── Cumulative retained (coarse → fine, running sum) ────────────────
        self.cumulative_retained: List[float] = []
        cum = 0.0
        for pct in self.percentages:
            cum += pct
            self.cumulative_retained.append(cum)

        # ── Cumulative passing = 100 − cumulative retained ──────────────────
        self.cumulative_passing: List[float] = [
            100.0 - cr for cr in self.cumulative_retained
        ]
        
        if verbose:
            print(
                f"\n  Cumulative passing @ first sieve "
                f"({self.data[0][0]:.4f} mm): "
                f"{self.cumulative_passing[0]:.2f}%"
            )
            print(
                f"  Cumulative passing @ last  sieve "
                f"({self.data[-1][0]:.4f} mm): "
                f"{self.cumulative_passing[-1]:.2f}%"
            )

        # ── Phi scale : φ = −log₂(d) ───────────────────────────────────────
        self.phi: List[float] = [
            -math.log2(d) if d > 0 else float("inf")
            for d, _ in self.data
        ]

        # ── Build interpolation arrays (measured data + 100% anchor)  [FIX 6]
        anchor_d = self.data[0][0] * 2.0
        anchor_phi = -math.log2(anchor_d)

        interp_d = [anchor_d] + [d for d, _ in self.data]
        interp_cp = [100.0] + list(self.cumulative_passing)
        interp_phi = [anchor_phi] + list(self.phi)

        # Reverse → ascending diameter order  [FIX 1]
        interp_d.reverse()
        interp_cp.reverse()
        interp_phi.reverse()

        # ── Interpolator 1 : diameter → cumulative passing  [FIX 1, 2] ────
        self.passing_interp = _make_interp1d(interp_d, interp_cp)

        # ── Interpolator 2 : cumulative passing → diameter  (PCHIP inverse)
        pairs_cp_d = sorted(zip(interp_cp, interp_d))
        cp_asc = [p[0] for p in pairs_cp_d]
        d_asc = [p[1] for p in pairs_cp_d]
        self._inv_interp = _make_pchip_or_linear(cp_asc, d_asc)

        # ── Interpolator 3 : cumulative passing → phi ───────────────────────
        pairs_cp_phi = sorted(zip(interp_cp, interp_phi))
        cp_asc_phi = [p[0] for p in pairs_cp_phi]
        phi_asc = [p[1] for p in pairs_cp_phi]
        self.phi_interp = _make_interp1d(cp_asc_phi, phi_asc)

    # ═══════════════════════════════════════════════════════════════════════════
    # Public query helpers
    # ═══════════════════════════════════════════════════════════════════════════

    def get_passing_at_diameter(self, diameter_mm: float) -> float:
        """Cumulative passing (%) at a given diameter (mm).  [FIX 2]"""
        if self.passing_interp is None:
            return float("nan")
        try:
            return float(self.passing_interp(diameter_mm))
        except Exception:
            return float("nan")

    def get_percentile_diameter(self, percentile: float) -> float:
        """
        Diameter (mm) at the given cumulative passing %.
        D50 → 50th percentile (median), D10 → 10th percentile, etc.
        """
        if self._inv_interp is None:
            return float("nan")
        try:
            val = float(self._inv_interp(max(0.0, min(100.0, percentile))))
            return val if not math.isnan(val) else float("nan")
        except Exception:
            return float("nan")

    def get_phi_at_percentile(self, percentile: float) -> float:
        """
        Phi value at the given cumulative passing %.

        Note (% passing convention):
          percentile=5  → phi of D5 = fine grain → HIGH phi value
          percentile=95 → phi of D95 = coarse grain → LOW phi value
          phi5 > phi16 > phi50 > phi84 > phi95
        """
        if self.phi_interp is None:
            return float("nan")
        try:
            return float(self.phi_interp(percentile))
        except Exception:
            return float("nan")

    # ═══════════════════════════════════════════════════════════════════════════
    # Sedimentological parameters — Folk & Ward (1957)
    # ═══════════════════════════════════════════════════════════════════════════

    def calculate_mode(self) -> Tuple[float, str]:
        """
        Mode from the frequency (partial %) curve.

        • Dominant peak refined with log-space parabolic interpolation.
        • Subsidiary peaks must exceed neighbours by ≥ 5% of modal amplitude
          to count as genuine modes  [FIX 7].

        Returns
        -------
        (mode_diameter_mm, modality_string)
        """
        if not self.percentages:
            return float("nan"), "No data"

        max_pct = max(self.percentages)
        max_idx = self.percentages.index(max_pct)
        threshold = 0.05 * max_pct  # 5% of modal amplitude  [FIX 7]

        n = len(self.data)

        # ── Parabolic refinement of mode position ────────────────────────────
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
                    num = (ld2 - ld1)**2 * (p2 - p3) - (ld2 - ld3)**2 * (p2 - p1)
                    denom = (ld2 - ld1) * (p2 - p3) - (ld2 - ld3) * (p2 - p1)
                    mode_dia = (10 ** (ld2 - 0.5 * num / denom)
                                if denom != 0 else d2)
                except Exception:
                    mode_dia = d2
            else:
                mode_dia = d2

        # ── Count genuine peaks  [FIX 7] ─────────────────────────────────────
        peaks = 0
        for i in range(1, n - 1):
            if (self.percentages[i] > self.percentages[i - 1] + threshold and
                    self.percentages[i] > self.percentages[i + 1] + threshold):
                peaks += 1

        modality = "bimodal / polymodal" if peaks >= 2 else "unimodal"
        return mode_dia, modality

    def calculate_mean(self) -> Tuple[float, float, float, float, float]:
        """
        Graphic Mean (Mz) — Folk & Ward (1957)
        Mz = (φ16 + φ50 + φ84) / 3

        Returns
        -------
        (phi_mean, mm_mean, phi16, phi50, phi84)
        """
        phi16 = self.get_phi_at_percentile(16)
        phi50 = self.get_phi_at_percentile(50)
        phi84 = self.get_phi_at_percentile(84)

        if any(math.isnan(v) for v in (phi16, phi50, phi84)):
            return float("nan"), float("nan"), phi16, phi50, phi84

        phi_mean = (phi16 + phi50 + phi84) / 3.0
        mm_mean = 2.0 ** (-phi_mean)
        return phi_mean, mm_mean, phi16, phi50, phi84

    def calculate_median(self) -> Tuple[float, float]:
        """
        Median (Md) — diameter at the 50th cumulative passing percentile.

        Returns
        -------
        (phi50, mm50)
        """
        phi50 = self.get_phi_at_percentile(50)
        mm50 = self.get_percentile_diameter(50)
        return phi50, mm50

    def calculate_sorting(self) -> Tuple[float, str]:
        """
        Inclusive Graphic Standard Deviation (σI) — Folk & Ward (1957)

        Adapted to % PASSING convention  [FIX 10]:
            σI = (φ16 − φ84)/4  +  (φ5 − φ95)/6.6
            where φ16 > φ84 and φ5 > φ95 (phi decreases with % passing)

        Full 7-class scale per original paper  [FIX 3]:
          < 0.35 φ  → Very well sorted
          0.35–0.50 → Well sorted
          0.50–0.71 → Moderately well sorted
          0.71–1.00 → Moderately sorted
          1.00–2.00 → Poorly sorted
          2.00–4.00 → Very poorly sorted
          > 4.00    → Extremely poorly sorted

        Returns
        -------
        (sigma_value, classification)
        """
        phi5 = self.get_phi_at_percentile(5)
        phi16 = self.get_phi_at_percentile(16)
        phi84 = self.get_phi_at_percentile(84)
        phi95 = self.get_phi_at_percentile(95)

        if any(math.isnan(v) for v in (phi5, phi16, phi84, phi95)):
            return float("nan"), "Insufficient data"

        sigma = (phi16 - phi84) / 4.0 + (phi5 - phi95) / 6.6

        if sigma < 0.35:
            cls = "Very well sorted"
        elif sigma < 0.50:
            cls = "Well sorted"
        elif sigma < 0.71:
            cls = "Moderately well sorted"
        elif sigma < 1.00:
            cls = "Moderately sorted"
        elif sigma < 2.00:
            cls = "Poorly sorted"
        elif sigma < 4.00:
            cls = "Very poorly sorted"
        else:
            cls = "Extremely poorly sorted"

        return sigma, cls

    def calculate_skewness(self) -> Tuple[float, str]:
        """
        Inclusive Graphic Skewness (Sk₁) — Folk & Ward (1957)

        Adapted to % PASSING convention  [FIX 10]:
            Sk = (φ16+φ84−2φ50) / [2(φ16−φ84)]
               + (φ5+φ95−2φ50)  / [2(φ5−φ95)]
            Denominators are now positive (φ16>φ84, φ5>φ95).

        Classification  [FIX 9]:
          Sk < −0.30 → Strongly coarse skewed
         −0.30–−0.10 → Coarse skewed
         −0.10–+0.10 → Near symmetrical
         +0.10–+0.30 → Fine skewed
          Sk > +0.30 → Strongly fine skewed

        Returns
        -------
        (skewness_value, classification)
        """
        phi5 = self.get_phi_at_percentile(5)
        phi16 = self.get_phi_at_percentile(16)
        phi50 = self.get_phi_at_percentile(50)
        phi84 = self.get_phi_at_percentile(84)
        phi95 = self.get_phi_at_percentile(95)

        if any(math.isnan(v) for v in (phi5, phi16, phi50, phi84, phi95)):
            return float("nan"), "Insufficient data"

        denom1 = 2.0 * (phi16 - phi84)
        denom2 = 2.0 * (phi5 - phi95)

        if denom1 == 0:
            denom1 = 1e-9
        if denom2 == 0:
            denom2 = 1e-9

        skew = ((phi16 + phi84 - 2.0 * phi50) / denom1 +
                (phi5 + phi95 - 2.0 * phi50) / denom2)

        if skew < -0.30:
            cls = "Strongly coarse skewed"
        elif skew < -0.10:
            cls = "Coarse skewed"
        elif skew < 0.10:
            cls = "Near symmetrical"
        elif skew < 0.30:
            cls = "Fine skewed"
        else:
            cls = "Strongly fine skewed"

        return skew, cls

    def calculate_kurtosis(self) -> Tuple[float, str]:
        """
        Graphic Kurtosis (KG) — Folk & Ward (1957)

        Adapted to % PASSING convention  [FIX 10]:
            KG = (φ5 − φ95) / [2.44 × (φ25 − φ75)]

        Full 6-class scale  [FIX 4]:
          KG < 0.67         → Very platykurtic
          0.67–0.90         → Platykurtic
          0.90–1.11         → Mesokurtic
          1.11–1.50         → Leptokurtic
          1.50–3.00         → Very leptokurtic
          KG > 3.00         → Extremely leptokurtic

        Returns
        -------
        (kurtosis_value, classification)
        """
        phi5 = self.get_phi_at_percentile(5)
        phi25 = self.get_phi_at_percentile(25)
        phi75 = self.get_phi_at_percentile(75)
        phi95 = self.get_phi_at_percentile(95)

        if any(math.isnan(v) for v in (phi5, phi25, phi75, phi95)):
            return float("nan"), "Insufficient data"

        denom = 2.44 * (phi25 - phi75)
        if denom == 0:
            denom = 1e-9
        kg = (phi5 - phi95) / denom

        if kg < 0.67:
            cls = "Very platykurtic"
        elif kg < 0.90:
            cls = "Platykurtic"
        elif kg < 1.11:
            cls = "Mesokurtic"
        elif kg < 1.50:
            cls = "Leptokurtic"
        elif kg < 3.00:
            cls = "Very leptokurtic"
        else:
            cls = "Extremely leptokurtic"

        return kg, cls

    # ═══════════════════════════════════════════════════════════════════════════
    # Geotechnical parameters — ASTM D2487 (USCS) / BS EN 12620 / ASTM C136
    # ═══════════════════════════════════════════════════════════════════════════

    def calculate_uniformity_coefficient(self) -> Tuple[float, str]:
        """
        Uniformity Coefficient  Cu = D60 / D10  (ASTM D2487).

        Returns
        -------
        (cu_value, classification)
        """
        d10 = self.get_percentile_diameter(10)
        d60 = self.get_percentile_diameter(60)

        if any(math.isnan(v) for v in (d10, d60)) or d10 <= 0:
            return float("nan"), "Insufficient data"

        cu = d60 / d10
        if cu >= 6:
            cls = "Well-graded  (Cu ≥ 6)"
        elif cu >= 2:
            cls = "Moderately graded  (2 ≤ Cu < 6)"
        else:
            cls = "Poorly graded / uniform  (Cu < 2)"
        return cu, cls

    def calculate_curvature_coefficient(self) -> Tuple[float, str]:
        """
        Curvature Coefficient  Cc = D30² / (D10 × D60)  (ASTM D2487).

        Returns
        -------
        (cc_value, classification)
        """
        d10 = self.get_percentile_diameter(10)
        d30 = self.get_percentile_diameter(30)
        d60 = self.get_percentile_diameter(60)

        if any(math.isnan(v) for v in (d10, d30, d60)) or d10 <= 0 or d60 <= 0:
            return float("nan"), "Insufficient data"

        cc = d30 ** 2 / (d10 * d60)
        cls = ("Well-graded  (1 ≤ Cc ≤ 3)"
               if 1.0 <= cc <= 3.0
               else "Poorly graded  (Cc outside 1–3)")
        return cc, cls

    def calculate_fineness_modulus(self) -> Tuple[float, str]:
        """
        Fineness Modulus (FM) — BS EN 12620 / ASTM C136
        FM = Σ(cumulative % retained on 4, 2, 1, 0.5, 0.25, 0.125 mm) / 100

        Uses get_passing_at_diameter() via passing_interp  [FIX 2, 8].

        Returns
        -------
        (fm_value, "classification — engineering note")
        """
        target_sieves = [4.0, 2.0, 1.0, 0.5, 0.25, 0.125]
        total_ret = 0.0

        for sieve in target_sieves:
            cp = self.get_passing_at_diameter(sieve)
            if math.isnan(cp):
                cp = 0.0
            cr = max(0.0, min(100.0, 100.0 - cp))
            total_ret += cr

        fm = total_ret / 100.0

        if fm < 2.2:
            cls = "Very fine sand"
            note = "RISK OF SHRINKAGE AND CRACKING — too fine for structural concrete"
        elif fm < 2.6:
            cls = "Fine sand"
            note = "Ideal for finishing coats; may require extra cement in concrete"
        elif fm < 2.9:
            cls = "Medium sand"
            note = "PREFERRED for high-quality concrete — optimal workability and strength"
        elif fm < 3.2:
            cls = "Coarse sand"
            note = "Suitable for high-strength concrete; may be harsh if poorly graded"
        else:
            cls = "Very coarse sand"
            note = "STONY / HARSH concrete — poor workability, difficult to finish"

        return fm, f"{cls} — {note}"

    # ═══════════════════════════════════════════════════════════════════════════
    # Convenience aggregators
    # ═══════════════════════════════════════════════════════════════════════════

    def get_all_percentiles(self) -> Dict:
        """
        D-values (mm) and φ-values for the standard percentile set:
        D5, D10, D16, D25, D30, D50, D60, D70, D75, D84, D90, D95.
        """
        targets = [5, 10, 16, 25, 30, 50, 60, 70, 75, 84, 90, 95]
        result: Dict = {}
        for p in targets:
            mm = self.get_percentile_diameter(p)
            phi = self.get_phi_at_percentile(p)
            result[f"D{p}"] = mm if not math.isnan(mm) else 0.0
            result[f"phi{p}"] = phi if not math.isnan(phi) else 0.0
        return result

    def get_all_parameters(self) -> Dict:
        """
        Single dictionary containing every calculated parameter
        (percentiles, Folk & Ward statistics, geotechnical indices, recovery).
        """
        params: Dict = {}

        # Percentiles
        params.update(self.get_all_percentiles())

        # Mode
        mode_mm, modality = self.calculate_mode()
        params["mode_mm"] = mode_mm if not math.isnan(mode_mm) else 0.0
        params["modality"] = modality

        # Mean (Folk & Ward)
        phi_mean, mm_mean, phi16, phi50, phi84 = self.calculate_mean()
        params["mean_phi"] = phi_mean if not math.isnan(phi_mean) else 0.0
        params["mean_mm"] = mm_mean if not math.isnan(mm_mean) else 0.0
        params["phi16"] = phi16 if not math.isnan(phi16) else 0.0
        params["phi50"] = phi50 if not math.isnan(phi50) else 0.0
        params["phi84"] = phi84 if not math.isnan(phi84) else 0.0

        # Median
        phi_med, mm_med = self.calculate_median()
        params["median_phi"] = phi_med if not math.isnan(phi_med) else 0.0
        params["median_mm"] = mm_med if not math.isnan(mm_med) else 0.0

        # Sorting
        sigma, sigma_cls = self.calculate_sorting()
        params["sorting"] = sigma if not math.isnan(sigma) else 0.0
        params["sorting_class"] = sigma_cls

        # Skewness
        skew, skew_cls = self.calculate_skewness()
        params["skewness"] = skew if not math.isnan(skew) else 0.0
        params["skewness_class"] = skew_cls

        # Kurtosis
        kg, kg_cls = self.calculate_kurtosis()
        params["kurtosis"] = kg if not math.isnan(kg) else 0.0
        params["kurtosis_class"] = kg_cls

        # Geotechnical
        cu, cu_cls = self.calculate_uniformity_coefficient()
        params["Cu"] = cu if not math.isnan(cu) else 0.0
        params["Cu_class"] = cu_cls

        cc, cc_cls = self.calculate_curvature_coefficient()
        params["Cc"] = cc if not math.isnan(cc) else 0.0
        params["Cc_class"] = cc_cls

        fm, fm_cls = self.calculate_fineness_modulus()
        params["FM"] = fm if not math.isnan(fm) else 0.0
        params["FM_class"] = fm_cls

        # Recovery & Basis Info
        params["initial_weight"] = self.initial_weight
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

        return params

    def print_summary(self):
        """
        Print a formatted summary of all calculated parameters.
        Call this explicitly when verbose=False in __init__.
        """
        p = self.get_all_parameters()
        W = 62
        print("\n" + "═" * W)
        print(f"  {'GRAIN-SIZE ANALYSIS RESULTS':^{W-4}}")
        print("═" * W)
        print(f"  Calculation Basis: {params['calculation_basis']}")
        print(f"  Recovery: {p['recovery_pct']:.2f}%")
        if p['recovery_warning']:
            print(f"  ⚠️  WARNING: Low recovery may affect D5/D95 accuracy")
        print()
        print(f"  {'PERCENTILES':}")
        print(f"    D5  = {p['D5']:.4f} mm   φ5  = {p['phi5']:.3f} φ")
        print(f"    D10 = {p['D10']:.4f} mm   φ10 = {p['phi10']:.3f} φ")
        print(f"    D16 = {p['D16']:.4f} mm   φ16 = {p['phi16']:.3f} φ")
        print(f"    D50 = {p['D50']:.4f} mm   φ50 = {p['phi50']:.3f} φ")
        print(f"    D84 = {p['D84']:.4f} mm   φ84 = {p['phi84']:.3f} φ")
        print(f"    D90 = {p['D90']:.4f} mm   φ90 = {p['phi90']:.3f} φ")
        print(f"    D95 = {p['D95']:.4f} mm   φ95 = {p['phi95']:.3f} φ")
        print()
        print(f"  {'FOLK & WARD (1957) STATISTICS':}")
        print(f"    Graphic Mean  Mz = {p['mean_phi']:+.3f} φ  ({p['mean_mm']:.4f} mm)")
        print(f"    Median        Md = {p['median_phi']:+.3f} φ  ({p['median_mm']:.4f} mm)")
        print(f"    Sorting       σI = {p['sorting']:+.3f} φ  → {p['sorting_class']}")
        print(f"    Skewness      Sk = {p['skewness']:+.3f}    → {p['skewness_class']}")
        print(f"    Kurtosis      KG = {p['kurtosis']:+.3f}    → {p['kurtosis_class']}")
        print(f"    Mode             = {p['mode_mm']:.4f} mm  ({p['modality']})")
        print()
        print(f"  {'GEOTECHNICAL PARAMETERS':}")
        print(f"    Cu = {p['Cu']:.2f}  →  {p['Cu_class']}")
        print(f"    Cc = {p['Cc']:.2f}  →  {p['Cc_class']}")
        print(f"    FM = {p['FM']:.2f}  →  {p['FM_class']}")
        print("═" * W)


# ═══════════════════════════════════════════════════════════════════════════════
# Quick self-test
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Typical medium sand sample — 8 sieves
    sample_data = [
        (4.000, 0.5),
        (2.000, 2.3),
        (1.000, 10.2),
        (0.500, 42.1),
        (0.250, 31.8),
        (0.125, 9.6),
        (0.063, 2.9),
        (0.020, 0.6),
    ]
    initial_mass = 100.0  # grams

    # Test 1: Recovered Weight (ASTM - Research)
    print("\n" + "="*62)
    print("  TEST 1: RECOVERED WEIGHT (ASTM D6913 — Research/Journals)")
    print("="*62)
    calc1 = GranuloCalculator(sample_data, initial_mass,
                              use_recovered_weight=True, verbose=True)
    p1 = calc1.get_all_parameters()
    print(f"\n  Basis: {p1['calculation_basis']}")
    print(f"  Sorting: {p1['sorting']:.3f} φ → {p1['sorting_class']}")
    print(f"  D50: {p1['D50']:.4f} mm")

    # Test 2: Initial Weight (NF/ISO - Geotechnical)
    print("\n" + "="*62)
    print("  TEST 2: INITIAL WEIGHT (NF P 94-056 — Geotechnical)")
    print("="*62)
    calc2 = GranuloCalculator(sample_data, initial_mass,
                              use_recovered_weight=False, verbose=True)
    p2 = calc2.get_all_parameters()
    print(f"\n  Basis: {p2['calculation_basis']}")
    print(f"  Sorting: {p2['sorting']:.3f} φ → {p2['sorting_class']}")
    print(f"  D50: {p2['D50']:.4f} mm")

    # Sanity checks
    print("\n" + "="*62)
    print("  SANITY CHECKS")
    print("="*62)
    errs = []
    if not (p1['D5'] < p1['D16'] < p1['D50'] < p1['D84'] < p1['D95']):
        errs.append("FAIL  D5 < D16 < D50 < D84 < D95")
    if not (p1['phi5'] > p1['phi16'] > p1['phi50'] > p1['phi84'] > p1['phi95']):
        errs.append("FAIL  phi5 > phi16 > phi50 > phi84 > phi95")
    if p1['sorting'] <= 0:
        errs.append(f"FAIL  σI must be positive (got {p1['sorting']:.4f})")
    if p1['kurtosis'] <= 0:
        errs.append(f"FAIL  KG must be positive (got {p1['kurtosis']:.4f})")

    if errs:
        print("\n⚠️  SANITY CHECK FAILURES:")
        for e in errs:
            print(f"     {e}")
    else:
        print("\n✅  All sanity checks passed.")
    print("="*62 + "\n")