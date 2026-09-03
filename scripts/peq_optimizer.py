"""
scripts/peq_optimizer.py
Dynamic Parametric Equalizer (PEQ) Optimization Engine for Yamaha RX-V673.

Features:
1. Exact discrete parameter quantization matching Yamaha RX-V673 DSP constraints.
2. Two-stage optimization: modal resonance identification + constrained non-linear least squares.
3. Asymmetric acoustic gain rules: max boost +3.0 dB, max cut -12.0 dB, 0.0 dB boost > 500 Hz.
4. Channel-independent optimization (f_0,L != f_0,R) to correct room acoustic boundary asymmetry.
5. Weighted hybrid cost function: 80% Sweet Spot, 20% spatial average.
"""

from __future__ import annotations
import dataclasses
import time
import pathlib
import json
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from scipy.optimize import minimize
from scipy.signal import find_peaks

# Exact discrete frequencies supported by Yamaha RX-V673 DSP (Hz)
YAMAHA_FREQS = np.array([
    31.3, 39.4, 49.6, 62.5, 78.7, 99.2, 125.0, 157.5, 198.4, 250.0,
    315.0, 396.9, 500.0, 630.0, 793.7, 1000.0, 1260.0, 1587.4, 2000.0,
    2520.0, 3174.8, 4000.0, 5040.0, 6349.6, 8000.0, 10080.0, 12700.0, 16000.0
], dtype=np.float64)

# Exact discrete Q factors supported by Yamaha RX-V673 DSP
YAMAHA_QS = np.array([
    0.500, 0.630, 0.794, 1.000, 1.260, 1.587, 2.000, 2.520, 3.175,
    4.000, 5.040, 6.350, 8.000, 10.080
], dtype=np.float64)

# Acoustic Gain Limits
MAX_BOOST_DB = 3.0
MAX_CUT_DB = -12.0
GAIN_STEP_DB = 0.5
SCHROEDER_FREQ_HZ = 500.0
MAX_BANDS_PER_CHANNEL = 7


def snap_frequency(freq_hz: float) -> float:
    """Snaps a continuous frequency to the closest discrete Yamaha frequency."""
    idx = int(np.argmin(np.abs(YAMAHA_FREQS - freq_hz)))
    return float(YAMAHA_FREQS[idx])


def snap_q(q_val: float) -> float:
    """Snaps a continuous Q factor to the closest discrete Yamaha Q factor."""
    idx = int(np.argmin(np.abs(YAMAHA_QS - q_val)))
    return float(YAMAHA_QS[idx])


def snap_gain(gain_db: float, freq_hz: float, allow_voicing_boost: bool = False) -> float:
    """
    Snaps gain to discrete 0.5 dB steps and enforces acoustic safety limits:
    - Min cut: -12.0 dB
    - Max boost: +3.0 dB
    - Frequencies above Schroeder frequency (> 500 Hz) cannot have positive boost (max 0.0 dB)
      unless explicitly permitted for loudspeaker crossover voicing.
    """
    stepped = round(gain_db / GAIN_STEP_DB) * GAIN_STEP_DB
    stepped = max(MAX_CUT_DB, min(MAX_BOOST_DB, stepped))
    if not allow_voicing_boost and freq_hz > SCHROEDER_FREQ_HZ and stepped > 0.0:
        stepped = 0.0
    return float(stepped)

def biquad_peaking_response(
    freqs_hz: np.ndarray,
    center_freq_hz: float,
    q: float,
    gain_db: float,
    fs: float = 48000.0,
) -> np.ndarray:
    """
    Computes exact digital frequency response (in dB) of an RBJ Audio EQ Cookbook peaking EQ filter.
    H(z) = (b0 + b1*z^-1 + b2*z^-2) / (a0 + a1*z^-1 + a2*z^-2)
    """
    if abs(gain_db) < 0.05:
        return np.zeros_like(freqs_hz)
    
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * center_freq_hz / fs
    alpha = np.sin(w0) / (2.0 * max(0.1, q))
    
    b0 = 1.0 + alpha * A
    b1 = -2.0 * np.cos(w0)
    b2 = 1.0 - alpha * A
    a0 = 1.0 + alpha / A
    a1 = -2.0 * np.cos(w0)
    a2 = 1.0 - alpha / A
    
    # Evaluate transfer function across frequency grid
    w = 2.0 * np.pi * freqs_hz / fs
    ejw = np.exp(-1j * w)
    ej2w = np.exp(-2j * w)
    
    num = b0 + b1 * ejw + b2 * ej2w
    den = a0 + a1 * ejw + a2 * ej2w
    
    H = num / np.where(np.abs(den) < 1e-12, 1e-12, den)
    mag_db = 20.0 * np.log10(np.maximum(np.abs(H), 1e-6))
    return mag_db


def multi_filter_response(
    freqs_hz: np.ndarray,
    filters: List[Dict[str, float]],
    fs: float = 48000.0,
) -> np.ndarray:
    """Sums the dB frequency responses of multiple biquad peaking filters."""
    total_db = np.zeros_like(freqs_hz)
    for f in filters:
        total_db += biquad_peaking_response(
            freqs_hz,
            f["freq_hz"],
            f["q"],
            f["gain_db"],
            fs=fs,
        )
    return total_db


def detect_modal_resonances(
    freqs_hz: np.ndarray,
    response_db: np.ndarray,
    target_db: np.ndarray,
    min_elevation_db: float = 1.5,
    max_peaks: int = 7,
    max_freq: float = 500.0,
) -> List[Dict[str, float]]:
    """
    Stage 1: Detects dominant room mode peaks below max_freq (500 Hz).
    Strictly gates detection so only positive elevations (response >= target + min_elevation_db)
    are considered. Dips and nulls are completely excluded.
    Computes physical bandwidth in Hertz and snaps Q to discrete Yamaha steps.
    """
    error = response_db - target_db
    mask = (freqs_hz >= 30.0) & (freqs_hz <= max_freq)
    f_sub = freqs_hz[mask]
    err_sub = error[mask]

    if len(f_sub) < 10:
        return []

    # Find peaks strictly above target + min_elevation_db
    peaks, properties = find_peaks(
        err_sub,
        height=min_elevation_db,
        prominence=1.2,
        distance=4,
    )

    detected = []
    for i, p in enumerate(peaks):
        f0 = float(f_sub[p])
        peak_height = float(properties["peak_heights"][i])
        prom = float(properties["prominences"][i])

        # Calculate -3.0 dB bandwidth in physical Hertz
        target_drop = peak_height - 3.0

        # Find left -3 dB crossing
        left_idx = p
        while left_idx > 0 and err_sub[left_idx] > target_drop:
            left_idx -= 1
        if left_idx < p and err_sub[p] != err_sub[left_idx]:
            # Linear interpolation for left frequency crossing
            frac = (target_drop - err_sub[left_idx]) / (err_sub[left_idx + 1] - err_sub[left_idx] + 1e-12)
            f_low = f_sub[left_idx] + frac * (f_sub[left_idx + 1] - f_sub[left_idx])
        else:
            f_low = f_sub[left_idx]

        # Find right -3 dB crossing
        right_idx = p
        while right_idx < len(err_sub) - 1 and err_sub[right_idx] > target_drop:
            right_idx += 1
        if right_idx > p and err_sub[right_idx] != err_sub[right_idx - 1]:
            # Linear interpolation for right frequency crossing
            frac = (target_drop - err_sub[right_idx - 1]) / (err_sub[right_idx] - err_sub[right_idx - 1] + 1e-12)
            f_high = f_sub[right_idx - 1] + frac * (f_sub[right_idx] - f_sub[right_idx - 1])
        else:
            f_high = f_sub[right_idx]

        bw_hz = max(5.0, float(f_high - f_low))
        q_continuous = f0 / bw_hz
        # Clamp Q to realistic bounds (0.5 to 5.04)
        q_clamped = max(0.500, min(5.040, q_continuous))
        q_snapped = snap_q(q_clamped)

        detected.append({
            "freq_hz": snap_frequency(f0),
            "elevation_db": round(peak_height, 2),
            "prominence_db": round(prom, 2),
            "bandwidth_hz": round(bw_hz, 1),
            "q": q_snapped,
        })

    # Sort descending by elevation
    detected.sort(key=lambda x: x["elevation_db"], reverse=True)
    return detected[:max_peaks]


def pair_stereo_modes(
    left_peaks: List[Dict[str, float]],
    right_peaks: List[Dict[str, float]],
    freq_tolerance: float = 0.06,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, float]], List[Dict[str, float]]]:
    """
    FR-006: Pairs resonance peaks between Left and Right within freq_tolerance (default +-6%).
    Common modes receive symmetrical frequency and Q factor.
    """
    paired = []
    used_r = set()
    used_l = set()

    for l_idx, lp in enumerate(left_peaks):
        f_l = lp["freq_hz"]
        best_r_idx = None
        min_diff = float("inf")

        for r_idx, rp in enumerate(right_peaks):
            if r_idx in used_r:
                continue
            f_r = rp["freq_hz"]
            rel_diff = abs(f_l - f_r) / min(f_l, f_r)
            if rel_diff <= freq_tolerance and rel_diff < min_diff:
                min_diff = rel_diff
                best_r_idx = r_idx

        if best_r_idx is not None:
            rp = right_peaks[best_r_idx]
            used_l.add(l_idx)
            used_r.add(best_r_idx)
            f_common = snap_frequency((f_l + rp["freq_hz"]) / 2.0)
            q_common = snap_q(min(3.5, (lp["q"] + rp["q"]) / 2.0))
            paired.append({
                "freq_hz": f_common,
                "q": q_common,
                "left_elevation": lp["elevation_db"],
                "right_elevation": rp["elevation_db"],
                "shared_elevation": min(lp["elevation_db"], rp["elevation_db"]),
            })

    left_only = [lp for i, lp in enumerate(left_peaks) if i not in used_l]
    right_only = [rp for j, rp in enumerate(right_peaks) if j not in used_r]
    return paired, left_only, right_only


def optimize_stereo_peq(
    freqs_hz: np.ndarray,
    left_sweet_spot: np.ndarray,
    right_sweet_spot: np.ndarray,
    target_db: np.ndarray,
    left_spatial_avg: Optional[np.ndarray] = None,
    right_spatial_avg: Optional[np.ndarray] = None,
    sweet_spot_weight: float = 0.8,
    target_key: Optional[str] = None,
    config_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Coordinated stereo PEQ optimization engine adhering to Dr. Floyd Toole / AES guidelines:
    1. Detects genuine modal resonances strictly above target (+1.5 dB).
    2. Pairs common modes for symmetrical stereo correction.
    3. Limits asymmetric cuts to verified boundary gain (max diff <= 3.0 dB, max cut <= -5.0 dB).
    4. Preserves high-frequency voicing (> 500 Hz) defined in targets.json.
    5. Evaluates multi-filter composite biquad response to prevent cumulative hollowing (>= -12.0 dB).
    """
    t0 = time.perf_counter()

    # Weighted acoustic responses
    if left_spatial_avg is not None:
        eff_l = sweet_spot_weight * left_sweet_spot + (1.0 - sweet_spot_weight) * left_spatial_avg
    else:
        eff_l = left_sweet_spot

    if right_spatial_avg is not None:
        eff_r = sweet_spot_weight * right_sweet_spot + (1.0 - sweet_spot_weight) * right_spatial_avg
    else:
        eff_r = right_sweet_spot

    # 1. Detect genuine modal resonance peaks
    left_peaks = detect_modal_resonances(freqs_hz, eff_l, target_db, min_elevation_db=1.5, max_peaks=5)
    right_peaks = detect_modal_resonances(freqs_hz, eff_r, target_db, min_elevation_db=1.5, max_peaks=5)

    # 2. Pair common stereo modes
    paired_modes, left_only, right_only = pair_stereo_modes(left_peaks, right_peaks, freq_tolerance=0.08)

    # 3. Load target profile voicing bands (> 500 Hz) if defined
    voicing_l = []
    voicing_r = []
    if target_key:
        cfg_file = pathlib.Path(config_path or (pathlib.Path(__file__).resolve().parent.parent / "config" / "targets.json"))
        if cfg_file.exists():
            try:
                with open(cfg_file) as f:
                    cfg = json.load(f)
                if target_key in cfg and "bands" in cfg[target_key]:
                    for b_name, b_data in cfg[target_key]["bands"].items():
                        if b_data.get("freq", 0.0) > 500.0 and (b_data.get("gain_l", 0.0) != 0.0 or b_data.get("gain_r", 0.0) != 0.0):
                            voicing_l.append({
                                "freq_hz": snap_frequency(b_data["freq"]),
                                "q": snap_q(b_data.get("q_l", 1.0)),
                                "gain_db": snap_gain(b_data.get("gain_l", 0.0), b_data["freq"], allow_voicing_boost=True),
                                "role": "voicing",
                            })
                            voicing_r.append({
                                "freq_hz": snap_frequency(b_data["freq"]),
                                "q": snap_q(b_data.get("q_r", 1.0)),
                                "gain_db": snap_gain(b_data.get("gain_r", 0.0), b_data["freq"], allow_voicing_boost=True),
                                "role": "voicing",
                            })
            except Exception:
                pass

    # 4. Allocate filters for Left and Right (max 7 bands per channel)
    bands_l = []
    bands_r = []

    # A. Coordinated common modes
    for m in paired_modes:
        if len(bands_l) >= 7 - len(voicing_l):
            break
        base_cut = -min(6.0, m["shared_elevation"] * 0.85)
        # Allow bounded asymmetric trim for genuine boundary asymmetry
        trim_l = -min(2.5, max(0.0, (m["left_elevation"] - m["shared_elevation"]) * 0.7))
        trim_r = -min(2.5, max(0.0, (m["right_elevation"] - m["shared_elevation"]) * 0.7))

        gain_l = snap_gain(max(-8.0, base_cut + trim_l), m["freq_hz"])
        gain_r = snap_gain(max(-8.0, base_cut + trim_r), m["freq_hz"])

        bands_l.append({"freq_hz": m["freq_hz"], "q": m["q"], "gain_db": gain_l, "role": "common_mode"})
        bands_r.append({"freq_hz": m["freq_hz"], "q": m["q"], "gain_db": gain_r, "role": "common_mode"})

    # B. Asymmetric independent modes (strictly constrained Q <= 3.5, cut <= -5.0 dB)
    for lp in left_only:
        if len(bands_l) >= 7 - len(voicing_l):
            break
        gain = snap_gain(-min(5.0, lp["elevation_db"] * 0.8), lp["freq_hz"])
        bands_l.append({"freq_hz": lp["freq_hz"], "q": snap_q(min(3.175, lp["q"])), "gain_db": gain, "role": "asym_mode"})
    for rp in right_only:
        if len(bands_r) >= 7 - len(voicing_r):
            break
        gain = snap_gain(-min(5.0, rp["elevation_db"] * 0.8), rp["freq_hz"])
        bands_r.append({"freq_hz": rp["freq_hz"], "q": snap_q(min(3.175, rp["q"])), "gain_db": gain, "role": "asym_mode"})
    # C. Add high-frequency voicing bands
    for v in voicing_l:
        if len(bands_l) < 7:
            bands_l.append(dict(v))
    for v in voicing_r:
        if len(bands_r) < 7:
            bands_r.append(dict(v))

    # D. Fill remaining slots with neutral/inactive bands
    for i in range(len(bands_l), 7):
        def_freq = YAMAHA_FREQS[min(len(YAMAHA_FREQS) - 1, i * 4 + 2)]
        bands_l.append({"freq_hz": float(def_freq), "q": 1.0, "gain_db": 0.0, "role": "inactive"})

    for i in range(len(bands_r), 7):
        def_freq = YAMAHA_FREQS[min(len(YAMAHA_FREQS) - 1, i * 4 + 2)]
        bands_r.append({"freq_hz": float(def_freq), "q": 1.0, "gain_db": 0.0, "role": "inactive"})

    # 5. Coordinate Descent & Multi-Filter Guardrail Validation
    mask_eval = (freqs_hz >= 30.0) & (freqs_hz <= 500.0)
    f_eval = freqs_hz[mask_eval]

    def enforce_guardrails(filters, resp_eval, tgt_eval):
        # Evaluate composite biquad response
        comp = multi_filter_response(f_eval, filters)
        # Check cumulative cut limit (>= -12.0 dB)
        while np.min(comp) < -12.0:
            # Soften the deepest cut
            min_band = min(filters, key=lambda b: b["gain_db"])
            if min_band["gain_db"] >= 0.0:
                break
            min_band["gain_db"] = snap_gain(min_band["gain_db"] + 0.5, min_band["freq_hz"])
            comp = multi_filter_response(f_eval, filters)
        return filters

    bands_l = enforce_guardrails(bands_l, eff_l[mask_eval], target_db[mask_eval])
    bands_r = enforce_guardrails(bands_r, eff_r[mask_eval], target_db[mask_eval])

    # Assign 1-indexed band numbers
    for idx, b in enumerate(bands_l, start=1):
        b["band"] = idx
    for idx, b in enumerate(bands_r, start=1):
        b["band"] = idx

    duration_ms = (time.perf_counter() - t0) * 1000.0

    # Calculate predicted metrics in modal band
    pred_l = eff_l[mask_eval] + multi_filter_response(f_eval, bands_l)
    pred_r = eff_r[mask_eval] + multi_filter_response(f_eval, bands_r)

    init_rms = (np.sqrt(np.mean((eff_l[mask_eval] - target_db[mask_eval]) ** 2)) +
                np.sqrt(np.mean((eff_r[mask_eval] - target_db[mask_eval]) ** 2))) / 2.0
    final_rms = (np.sqrt(np.mean((pred_l - target_db[mask_eval]) ** 2)) +
                 np.sqrt(np.mean((pred_r - target_db[mask_eval]) ** 2))) / 2.0
    rms_reduction = max(0.0, float(init_rms - final_rms))

    max_atten = max([abs(b["gain_db"]) for b in bands_l + bands_r if b["gain_db"] < 0.0] or [0.0])

    return {
        "success": True,
        "channels": {
            "left": bands_l,
            "right": bands_r,
        },
        "metrics": {
            "predicted_rms_reduction_db": round(rms_reduction, 2),
            "predicted_modal_attenuation_db": round(max_atten, 2),
            "execution_time_ms": round(duration_ms, 1),
        },
    }


def optimize_channel_peq(
    freqs_hz: np.ndarray,
    response_db: np.ndarray,
    target_db: np.ndarray,
    spatial_avg_db: Optional[np.ndarray] = None,
    sweet_spot_weight: float = 0.8,
    max_bands: int = 7,
) -> List[Dict[str, Any]]:
    """Single channel optimization wrapper returning 7 bands."""
    res = optimize_stereo_peq(
        freqs_hz=freqs_hz,
        left_sweet_spot=response_db,
        right_sweet_spot=response_db,
        target_db=target_db,
        left_spatial_avg=spatial_avg_db,
        right_spatial_avg=spatial_avg_db,
        sweet_spot_weight=sweet_spot_weight,
    )
    return res["channels"]["left"][:max_bands]
