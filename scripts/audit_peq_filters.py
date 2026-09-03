"""
scripts/audit_peq_filters.py
Audit and Diagnostic Verification Engine for Yamaha RX-V673 Parametric EQ Filters.

Evaluates active PEQ filters against physical room acoustics, detects hardware & mathematical
constraint violations, and provides automated re-optimization if filters are suboptimal.
"""

from __future__ import annotations
import argparse
import dataclasses
import json
import os
import sys
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.signal import find_peaks

# Ensure current scripts directory is available for local imports
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from peq_optimizer import (
    YAMAHA_FREQS,
    YAMAHA_QS,
    MAX_BOOST_DB,
    MAX_CUT_DB,
    GAIN_STEP_DB,
    SCHROEDER_FREQ_HZ,
    snap_frequency,
    snap_q,
    snap_gain,
    biquad_peaking_response,
    multi_filter_response,
    optimize_channel_peq,
)
@dataclasses.dataclass
class ParametricFilterBand:
    band: int
    channel: str  # "L" or "R"
    freq_hz: float
    q: float
    gain_db: float
    status: str = "PENDING"  # "ALIGNED", "MISALIGNED", "HARDWARE_VIOLATION", "ACOUSTIC_VIOLATION", "FLAT"
    discrepancy_hz: float = 0.0
    associated_mode: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "band": self.band,
            "channel": self.channel,
            "freq_hz": float(self.freq_hz),
            "q": float(self.q),
            "gain_db": float(self.gain_db),
            "status": self.status,
            "discrepancy_hz": float(self.discrepancy_hz),
            "associated_mode": float(self.associated_mode) if self.associated_mode is not None else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ParametricFilterBand:
        return cls(
            band=int(data.get("band", 1)),
            channel=str(data.get("channel", "L")),
            freq_hz=float(data.get("freq_hz", data.get("frequency", data.get("f", 100.0)))),
            q=float(data.get("q", data.get("q_factor", 1.0))),
            gain_db=float(data.get("gain_db", data.get("gain", 0.0))),
            status=str(data.get("status", "PENDING")),
            discrepancy_hz=float(data.get("discrepancy_hz", 0.0)),
            associated_mode=float(data["associated_mode"]) if data.get("associated_mode") is not None else None,
        )


@dataclasses.dataclass
class RoomResonanceMode:
    frequency_hz: float
    peak_prominence_db: float
    q_estimate: float
    target_attenuation_db: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "frequency_hz": float(self.frequency_hz),
            "peak_prominence_db": float(self.peak_prominence_db),
            "q_estimate": float(self.q_estimate),
            "target_attenuation_db": float(self.target_attenuation_db),
        }


@dataclasses.dataclass
class FilterAuditDiagnosis:
    verdict: str  # "ACCURATE", "SUBOPTIMAL", "ERRONEOUS"
    composite_error_score: float
    left_channel: List[ParametricFilterBand]
    right_channel: List[ParametricFilterBand]
    misaligned_bands: List[ParametricFilterBand]
    hardware_violations: List[str]
    acoustic_violations: List[str]
    detected_modes_l: List[RoomResonanceMode] = dataclasses.field(default_factory=list)
    detected_modes_r: List[RoomResonanceMode] = dataclasses.field(default_factory=list)
    recommended_peq: Optional[Dict[str, List[ParametricFilterBand]]] = None
    comparative_metrics: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        rec = None
        if self.recommended_peq:
            rec = {
                k: [b.to_dict() if isinstance(b, ParametricFilterBand) else b for b in v]
                for k, v in self.recommended_peq.items()
            }
        return {
            "verdict": self.verdict,
            "composite_error_score": float(self.composite_error_score),
            "left_channel": [b.to_dict() for b in self.left_channel],
            "right_channel": [b.to_dict() for b in self.right_channel],
            "misaligned_bands": [b.to_dict() for b in self.misaligned_bands],
            "hardware_violations": self.hardware_violations,
            "acoustic_violations": self.acoustic_violations,
            "detected_modes_left": [m.to_dict() for m in self.detected_modes_l],
            "detected_modes_right": [m.to_dict() for m in self.detected_modes_r],
            "recommended_peq": rec,
            "comparative_metrics": self.comparative_metrics,
        }


def load_composite_baseline(
    sweet_spot_path: str,
    spatial_avg_path: Optional[str] = None,
    weight_sweet_spot: float = 0.8,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Loads empirical acoustic baseline applying 80% Sweet Spot and 20% Spatial Average weighting.
    """
    if not os.path.exists(sweet_spot_path):
        raise FileNotFoundError(f"Baseline file not found: {sweet_spot_path}")

    data_p1 = np.load(sweet_spot_path)
    freqs = data_p1["freqs"]
    spl_l = data_p1["smooth_l"] if "smooth_l" in data_p1 else (data_p1["raw_l"] if "raw_l" in data_p1 else data_p1["spl_left"])
    spl_r = data_p1["smooth_r"] if "smooth_r" in data_p1 else (data_p1["raw_r"] if "raw_r" in data_p1 else data_p1["spl_right"])

    if spatial_avg_path and os.path.exists(spatial_avg_path):
        data_avg = np.load(spatial_avg_path)
        avg_freqs = data_avg["freqs"]
        avg_l = data_avg["smooth_l"] if "smooth_l" in data_avg else (data_avg["raw_l"] if "raw_l" in data_avg else data_avg["spl_left"])
        avg_r = data_avg["smooth_r"] if "smooth_r" in data_avg else (data_avg["raw_r"] if "raw_r" in data_avg else data_avg["spl_right"])
        avg_spl_l = np.interp(freqs, avg_freqs, avg_l)
        avg_spl_r = np.interp(freqs, avg_freqs, avg_r)

        w_p1 = weight_sweet_spot
        w_avg = 1.0 - weight_sweet_spot
        spl_l = w_p1 * spl_l + w_avg * avg_spl_l
        spl_r = w_p1 * spl_r + w_avg * avg_spl_r
    return freqs, spl_l, spl_r


def validate_discrete_yamaha_parameters(band: ParametricFilterBand) -> List[str]:
    """
    Validates filter parameters against Yamaha RX-V673 hardware constraints.
    """
    violations = []
    # 1. Frequency match
    min_f_dist = float(np.min(np.abs(YAMAHA_FREQS - band.freq_hz)))
    if min_f_dist > 0.2:
        violations.append(
            f"Channel {band.channel} Band {band.band}: Frequency {band.freq_hz:.1f} Hz is not on Yamaha discrete grid."
        )

    # 2. Q factor match
    min_q_dist = np.min(np.abs(YAMAHA_QS - band.q))
    if min_q_dist > 0.01:
        violations.append(
            f"Channel {band.channel} Band {band.band}: Q factor {band.q:.3f} is not in Yamaha discrete table."
        )

    # 3. Gain limits and steps
    if band.gain_db < MAX_CUT_DB or band.gain_db > MAX_BOOST_DB:
        violations.append(
            f"Channel {band.channel} Band {band.band}: Gain {band.gain_db:.1f} dB exceeds Yamaha bounds [{MAX_CUT_DB}, +{MAX_BOOST_DB}] dB."
        )

    rem = abs(round(band.gain_db / GAIN_STEP_DB) * GAIN_STEP_DB - band.gain_db)
    if rem > 1e-3:
        violations.append(
            f"Channel {band.channel} Band {band.band}: Gain {band.gain_db:.2f} dB violates 0.5 dB step resolution."
        )

    return violations


def detect_room_resonances(
    freqs: np.ndarray,
    spl: np.ndarray,
    max_freq_hz: float = 500.0,
    min_prominence_db: float = 2.0,
) -> List[RoomResonanceMode]:
    """
    Identifies standing wave modal peaks below max_freq_hz.
    """
    modal_mask = (freqs >= 20.0) & (freqs <= max_freq_hz)
    f_sub = freqs[modal_mask]
    spl_sub = spl[modal_mask]

    if len(f_sub) < 10:
        return []

    # Find peaks with minimum prominence
    peak_indices, properties = find_peaks(spl_sub, prominence=min_prominence_db, distance=3)
    modes = []

    for idx, prom in zip(peak_indices, properties["prominences"]):
        f0 = float(f_sub[idx])
        # Estimate Q by half-power bandwidth
        peak_val = spl_sub[idx]
        half_power = peak_val - 3.0
        # search left and right bounds
        left_idx = idx
        while left_idx > 0 and spl_sub[left_idx] > half_power:
            left_idx -= 1
        right_idx = idx
        while right_idx < len(spl_sub) - 1 and spl_sub[right_idx] > half_power:
            right_idx += 1

        bw = max(2.0, float(f_sub[right_idx] - f_sub[left_idx]))
        q_est = snap_q(f0 / bw)
        target_cut = snap_gain(-float(prom), f0)

        modes.append(
            RoomResonanceMode(
                frequency_hz=f0,
                peak_prominence_db=float(prom),
                q_estimate=q_est,
                target_attenuation_db=target_cut,
            )
        )

    return modes


def audit_channel_filters(
    filters: List[ParametricFilterBand],
    freqs: np.ndarray,
    spl: np.ndarray,
    channel: str,
) -> Tuple[List[ParametricFilterBand], List[ParametricFilterBand], List[str], List[str]]:
    """
    Audits an individual channel's filter list against room acoustics.
    """
    audited = []
    misaligned = []
    hw_violations = []
    acoustic_violations = []

    modes = detect_room_resonances(freqs, spl, max_freq_hz=500.0)

    for band in filters:
        band_copy = ParametricFilterBand(
            band=band.band,
            channel=channel,
            freq_hz=band.freq_hz,
            q=band.q,
            gain_db=band.gain_db,
        )

        # Hardware checks
        hw_errs = validate_discrete_yamaha_parameters(band_copy)
        if hw_errs:
            hw_violations.extend(hw_errs)
            band_copy.status = "HARDWARE_VIOLATION"

        # Acoustic rule 1: No positive gain in modal region (< 500 Hz)
        if band_copy.freq_hz <= SCHROEDER_FREQ_HZ and band_copy.gain_db > 0.0:
            msg = (
                f"Channel {channel} Band {band_copy.band} ({band_copy.freq_hz:.1f} Hz): "
                f"Positive boost (+{band_copy.gain_db:.1f} dB) violates acoustic rule (never boost room modes)."
            )
            acoustic_violations.append(msg)
            band_copy.status = "ACOUSTIC_VIOLATION"

        # Acoustic rule 2: Check frequency alignment against modes if filter applies cut
        if band_copy.gain_db < 0.0 and band_copy.freq_hz <= SCHROEDER_FREQ_HZ:
            if modes:
                # Find closest mode
                dists = [abs(m.frequency_hz - band_copy.freq_hz) for m in modes]
                min_idx = int(np.argmin(dists))
                closest_mode = modes[min_idx]
                disc = dists[min_idx]
                band_copy.discrepancy_hz = disc
                band_copy.associated_mode = closest_mode.frequency_hz

                if disc > 5.0:
                    band_copy.status = "MISALIGNED"
                    misaligned.append(band_copy)
                elif band_copy.status == "PENDING":
                    band_copy.status = "ALIGNED"
            else:
                band_copy.status = "MISALIGNED"
                band_copy.discrepancy_hz = 99.0
                misaligned.append(band_copy)
        elif abs(band_copy.gain_db) < 1e-2:
            band_copy.status = "FLAT"
        elif band_copy.status == "PENDING":
            band_copy.status = "ALIGNED"

        audited.append(band_copy)

    return audited, misaligned, hw_violations, acoustic_violations

def run_diagnostic_audit(
    freqs: np.ndarray,
    spl_l: np.ndarray,
    spl_r: np.ndarray,
    peq_data: Dict[str, List[ParametricFilterBand]],
    reoptimize: bool = False,
) -> FilterAuditDiagnosis:
    """
    Executes full diagnostic audit across both channels.
    """
    bands_l = peq_data.get("left_channel", peq_data.get("L", []))
    bands_r = peq_data.get("right_channel", peq_data.get("R", []))

    audited_l, mis_l, hw_l, ac_l = audit_channel_filters(bands_l, freqs, spl_l, "L")
    audited_r, mis_r, hw_r, ac_r = audit_channel_filters(bands_r, freqs, spl_r, "R")

    all_mis = mis_l + mis_r
    all_hw = hw_l + hw_r
    all_ac = ac_l + ac_r

    # Detect modes for reporting
    modes_l = detect_room_resonances(freqs, spl_l, max_freq_hz=500.0)
    modes_r = detect_room_resonances(freqs, spl_r, max_freq_hz=500.0)

    # Compute baseline score
    # Evaluate applied response
    corr_l = spl_l.copy()
    corr_r = spl_r.copy()
    for b in audited_l:
        corr_l += biquad_peaking_response(freqs, b.freq_hz, b.q, b.gain_db)
    for b in audited_r:
        corr_r += biquad_peaking_response(freqs, b.freq_hz, b.q, b.gain_db)

    # Focus error score on modal region 30 - 300 Hz
    modal_idx = (freqs >= 30.0) & (freqs <= 300.0)
    ref_l = np.mean(corr_l[modal_idx]) if np.any(modal_idx) else 75.0
    ref_r = np.mean(corr_r[modal_idx]) if np.any(modal_idx) else 75.0
    rms_curr = 0.5 * (
        np.sqrt(np.mean((corr_l[modal_idx] - ref_l) ** 2))
        + np.sqrt(np.mean((corr_r[modal_idx] - ref_r) ** 2))
    )

    # Determine verdict
    if len(all_hw) > 0 or len(all_ac) > 0:
        verdict = "ERRONEOUS"
    elif len(all_mis) > 0 or rms_curr > 4.5:
        verdict = "SUBOPTIMAL"
    else:
        verdict = "ACCURATE"

    rec_peq = None
    comp_metrics = None

    if reoptimize or verdict in ("SUBOPTIMAL", "ERRONEOUS"):
        rec_peq, comp_metrics = reoptimize_peq_filters(
            freqs, spl_l, spl_r, rms_curr
        )

    return FilterAuditDiagnosis(
        verdict=verdict,
        composite_error_score=round(float(rms_curr), 2),
        left_channel=audited_l,
        right_channel=audited_r,
        misaligned_bands=all_mis,
        hardware_violations=all_hw,
        acoustic_violations=all_ac,
        detected_modes_l=modes_l,
        detected_modes_r=modes_r,
        recommended_peq=rec_peq,
        comparative_metrics=comp_metrics,
    )


def reoptimize_peq_filters(
    freqs: np.ndarray,
    spl_l: np.ndarray,
    spl_r: np.ndarray,
    rms_before: float,
) -> Tuple[Dict[str, List[ParametricFilterBand]], Dict[str, Any]]:
    """
    Re-optimizes filters using peq_optimizer engine and calculates comparative improvements.
    """
    # Create target curve (flat at median SPL in 200 - 1000 Hz)
    mid_idx = (freqs >= 200.0) & (freqs <= 1000.0)
    target_l = np.full_like(spl_l, np.median(spl_l[mid_idx]) if np.any(mid_idx) else 75.0)
    target_r = np.full_like(spl_r, np.median(spl_r[mid_idx]) if np.any(mid_idx) else 75.0)

    opt_l_dicts = optimize_channel_peq(freqs, spl_l, target_l)
    opt_r_dicts = optimize_channel_peq(freqs, spl_r, target_r)

    rec_l = [
        ParametricFilterBand(
            band=i + 1,
            channel="L",
            freq_hz=f["freq_hz"],
            q=f["q"],
            gain_db=f["gain_db"],
            status="ALIGNED",
        )
        for i, f in enumerate(opt_l_dicts)
    ]
    rec_r = [
        ParametricFilterBand(
            band=i + 1,
            channel="R",
            freq_hz=f["freq_hz"],
            q=f["q"],
            gain_db=f["gain_db"],
            status="ALIGNED",
        )
        for i, f in enumerate(opt_r_dicts)
    ]

    # Evaluate new corrected response
    corr_l = spl_l + multi_filter_response(freqs, opt_l_dicts)
    corr_r = spl_r + multi_filter_response(freqs, opt_r_dicts)

    modal_idx = (freqs >= 30.0) & (freqs <= 300.0)
    ref_l = np.mean(corr_l[modal_idx]) if np.any(modal_idx) else 75.0
    ref_r = np.mean(corr_r[modal_idx]) if np.any(modal_idx) else 75.0
    rms_after = 0.5 * (
        np.sqrt(np.mean((corr_l[modal_idx] - ref_l) ** 2))
        + np.sqrt(np.mean((corr_r[modal_idx] - ref_r) ** 2))
    )

    impr_pct = max(0.0, float((rms_before - rms_after) / max(1e-2, rms_before) * 100.0))

    comparative = {
        "rms_before_db": round(float(rms_before), 2),
        "rms_after_db": round(float(rms_after), 2),
        "rms_improvement_pct": round(impr_pct, 1),
        "stereo_balance_delta_db": round(float(abs(ref_l - ref_r)), 2),
    }
    return {"left_channel": rec_l, "right_channel": rec_r}, comparative


def parse_peq_file(file_path: str) -> Dict[str, List[ParametricFilterBand]]:
    """Loads PEQ JSON or npz file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PEQ file not found: {file_path}")

    if file_path.endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        res = {"left_channel": [], "right_channel": []}
        # Handle various json schemas
        l_list = data.get("left_channel", data.get("L", data.get("bands_l", [])))
        r_list = data.get("right_channel", data.get("R", data.get("bands_r", [])))

        for i, item in enumerate(l_list):
            item["band"] = item.get("band", i + 1)
            item["channel"] = "L"
            res["left_channel"].append(ParametricFilterBand.from_dict(item))

        for i, item in enumerate(r_list):
            item["band"] = item.get("band", i + 1)
            item["channel"] = "R"
            res["right_channel"].append(ParametricFilterBand.from_dict(item))

        return res

    elif file_path.endswith(".npz"):
        data = np.load(file_path, allow_pickle=True)
        res = {"left_channel": [], "right_channel": []}
        if "peq_l" in data:
            peq_l = data["peq_l"]
            for i, row in enumerate(peq_l):
                res["left_channel"].append(
                    ParametricFilterBand(band=i + 1, channel="L", freq_hz=row[0], q=row[1], gain_db=row[2])
                )
        if "peq_r" in data:
            peq_r = data["peq_r"]
            for i, row in enumerate(peq_r):
                res["right_channel"].append(
                    ParametricFilterBand(band=i + 1, channel="R", freq_hz=row[0], q=row[1], gain_db=row[2])
                )

        # Fallback: if npz contains measured curve without peq_l/peq_r, check active calibration profile
        if not res["left_channel"] and not res["right_channel"]:
            import auto_calibrate as ac
            cal = ac.run_calibration(target_key="harman_wide_room", push_yamaha=False)
            channels = cal.get("channels", {})
            for b in channels.get("left", []):
                res["left_channel"].append(ParametricFilterBand.from_dict(b))
            for b in channels.get("right", []):
                res["right_channel"].append(ParametricFilterBand.from_dict(b))

        return res
    else:
        raise ValueError(f"Unsupported PEQ format: {file_path}")


def format_cli_output(diag: FilterAuditDiagnosis) -> str:
    """Generates clean, readable terminal output."""
    lines = []
    lines.append("================================================================================")
    lines.append(f"  DIAGNOSTIC AUDIT REPORT: YAMAHA RX-V673 PEQ FILTERS")
    lines.append("================================================================================")
    verdict_color = (
        "\033[92mACCURATE\033[0m"
        if diag.verdict == "ACCURATE"
        else ("\033[93mSUBOPTIMAL\033[0m" if diag.verdict == "SUBOPTIMAL" else "\033[91mERRONEOUS\033[0m")
    )
    lines.append(f"OVERALL VERDICT : {diag.verdict} (Residual Error: {diag.composite_error_score:.2f} dB RMS)")
    lines.append("")

    lines.append("--- [LEFT CHANNEL ACTIVE FILTERS] ---")
    lines.append(f"{'Band':<5} | {'Freq (Hz)':<10} | {'Q':<6} | {'Gain (dB)':<10} | {'Status':<16} | {'Discrepancy'}")
    lines.append("-" * 75)
    for b in diag.left_channel:
        disc_str = f"+{b.discrepancy_hz:.1f} Hz (mode: {b.associated_mode:.1f} Hz)" if b.associated_mode else "-"
        lines.append(f"{b.band:<5} | {b.freq_hz:<10.1f} | {b.q:<6.3f} | {b.gain_db:<10.1f} | {b.status:<16} | {disc_str}")

    lines.append("")
    lines.append("--- [RIGHT CHANNEL ACTIVE FILTERS] ---")
    lines.append(f"{'Band':<5} | {'Freq (Hz)':<10} | {'Q':<6} | {'Gain (dB)':<10} | {'Status':<16} | {'Discrepancy'}")
    lines.append("-" * 75)
    for b in diag.right_channel:
        disc_str = f"+{b.discrepancy_hz:.1f} Hz (mode: {b.associated_mode:.1f} Hz)" if b.associated_mode else "-"
        lines.append(f"{b.band:<5} | {b.freq_hz:<10.1f} | {b.q:<6.3f} | {b.gain_db:<10.1f} | {b.status:<16} | {disc_str}")

    if diag.hardware_violations:
        lines.append("")
        lines.append("--- [HARDWARE CONSTRAINT VIOLATIONS] ---")
        for v in diag.hardware_violations:
            lines.append(f"  [!] {v}")

    if diag.acoustic_violations:
        lines.append("")
        lines.append("--- [ACOUSTIC & MODAL VIOLATIONS] ---")
        for v in diag.acoustic_violations:
            lines.append(f"  [!] {v}")

    if diag.recommended_peq:
        lines.append("")
        lines.append("================================================================================")
        lines.append("  RECOMMENDED RE-OPTIMIZED MATRIX (Yamaha RX-V673 Discrete Grid)")
        lines.append("================================================================================")
        if diag.comparative_metrics:
            m = diag.comparative_metrics
            lines.append(
                f"Metrics: RMS Error {m['rms_before_db']:.2f} dB -> {m['rms_after_db']:.2f} dB "
                f"(-{m['rms_improvement_pct']}%) | Stereo Delta: {m['stereo_balance_delta_db']:.2f} dB"
            )
            lines.append("")

        for ch_key, name in [("left_channel", "Left Channel (L)"), ("right_channel", "Right Channel (R)")]:
            lines.append(f"[{name}]")
            for b in diag.recommended_peq.get(ch_key, []):
                lines.append(f"  Band {b.band}: {b.freq_hz:.1f} Hz, Q={b.q:.3f}, Gain={b.gain_db:+.1f} dB")
            lines.append("")

    lines.append("================================================================================")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Audit Yamaha RX-V673 PEQ filters against room acoustics.")
    parser.add_argument(
        "--baseline",
        default=os.path.join(SCRIPT_DIR, "..", "data", "medicion_real_calibracion.npz"),
        help="Path to empirical sweet spot baseline npz",
    )
    parser.add_argument(
        "--spatial-avg",
        default=os.path.join(SCRIPT_DIR, "..", "data", "medicion_promedio_espacial.npz"),
        help="Path to spatial average baseline npz",
    )
    parser.add_argument(
        "--peq-file",
        default=os.path.join(SCRIPT_DIR, "..", "data", "medicion_verificacion_manual.npz"),
        help="Path to deployed PEQ file (json or npz)",
    )
    parser.add_argument("--reoptimize", action="store_true", help="Calculate optimal replacement if flawed")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    # Load baseline
    freqs, spl_l, spl_r = load_composite_baseline(args.baseline, args.spatial_avg)

    # Load PEQ filters
    peq_data = parse_peq_file(args.peq_file)

    # Run audit
    diag = run_diagnostic_audit(freqs, spl_l, spl_r, peq_data, reoptimize=args.reoptimize)

    if args.json:
        print(json.dumps(diag.to_dict(), indent=2))
    else:
        print(format_cli_output(diag))


if __name__ == "__main__":
    main()
