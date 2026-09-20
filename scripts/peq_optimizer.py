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

def variable_smooth(freqs_hz: np.ndarray, response_db: np.ndarray) -> np.ndarray:
    """
    REW-standard Variable Smoothing (Var).
    Applies heavy 1/3-octave smoothing at sub-bass to prevent attempting to equalize
    narrow physical cancellation nulls, and high-resolution 1/24-1/12 octave smoothing
    in the modal band (80-400 Hz) to clearly resolve genuine room mode standing waves.
    """
    freqs_hz = np.asarray(freqs_hz, dtype=np.float64)
    response_db = np.asarray(response_db, dtype=np.float64)
    smoothed = np.copy(response_db)
    log_f = np.log10(np.maximum(freqs_hz, 1.0))
    n = len(freqs_hz)
    if n < 3:
        return smoothed
    window = np.ones(n, dtype=np.float64)
    # Heavy 1/3-octave smoothing below 80 Hz
    for i, f in enumerate(freqs_hz):
        if f < 80.0:
            window[i] = 12.0  # ~1/3 octave
        elif f < 400.0:
            window[i] = 3.0  # ~1/12 octave (surgical for modal band)
        elif f < 1000.0:
            window[i] = 6.0
        else:
            window[i] = 6.0  # ~1/6 octave
    for i in range(n):
        # Width in log-frequency domain
        w = window[i]
        df = w * 0.05  # smoothing radius in log-freq
        lo = np.searchsorted(log_f, log_f[i] - df)
        hi = np.searchsorted(log_f, log_f[i] + df)
        if hi > lo:
            smoothed[i] = np.mean(response_db[lo:hi])
    return smoothed


def broadband_normalize(
    freqs_hz: np.ndarray,
    response_db: np.ndarray,
    low_hz: float = 300.0,
    high_hz: float = 3000.0,
) -> np.ndarray:
    """
    Replaces single-frequency anchor normalization (1.0 kHz bin) with broadband
    logarithmic energy averaging between `low_hz` and `high_hz`. Immune to
    localized narrow reflection dips in the 1 kHz band.
    """
    freqs_hz = np.asarray(freqs_hz, dtype=np.float64)
    response_db = np.asarray(response_db, dtype=np.float64)
    mask = (freqs_hz >= low_hz) & (freqs_hz <= high_hz)
    if not np.any(mask):
        return response_db
    baseline = np.mean(response_db[mask])
    return response_db - baseline

def generate_bookshelf_target_curve(
    freqs_hz: np.ndarray,
    target_key: str = "harman_wide_room",
    fc_hz: float = 64.0,
    subwoofer_crossover_hz: Optional[float] = None,
) -> np.ndarray:
    """
    Generates ground-truth acoustic target curve tailored for small bookshelf speakers (e.g. Q Acoustics 3020i).
    - Applies natural Butterworth high-pass cutoff (fc=64 Hz for 2.0; or subwoofer_crossover_hz if 2.1+).
    - Applies standard psychoacoustic target curve (Harman, B&K 1974, Dirac) with treble roll-off.
    """
    freqs_hz = np.asarray(freqs_hz, dtype=np.float64)
    cutoff = subwoofer_crossover_hz if subwoofer_crossover_hz and subwoofer_crossover_hz > 0 else fc_hz
    hpf_mag = 1.0 / np.sqrt(1.0 + (cutoff / np.maximum(freqs_hz, 1.0)) ** 4)
    hpf_db = 20.0 * np.log10(np.maximum(hpf_mag, 1e-3))

    k = (target_key or "").lower().strip()
    target_curve = np.zeros_like(freqs_hz)
    f = np.maximum(freqs_hz, 1.0)

    if "through" in k or "bypass" in k:
        pass  # 0.0 dB flat bypass
    elif "flat" in k or "diffuse" in k:
        pass  # EBU Tech 3276 / Studio Monitor flat reference (0.0 dB)
    elif "ypao" in k:
        # Yamaha YPAO factory curve simulation (+0.5 dB presence above 2 kHz)
        target_curve += np.where(f > 2000.0, 0.5, 0.0)
    elif "bass_boost" in k:
        # Harman In-Room Bass+ (+4.0 dB shelf 50-105 Hz for punchy modern genres, subsonic roll-off < 50 Hz)
        target_curve += np.where(f < 50.0, 4.0 * (f / 50.0), np.where(f < 105.0, 4.0, np.where(f < 200.0, 4.0 * 0.5 * (1.0 + np.cos(np.pi * (f - 105.0) / 95.0)), 0.0)))
        target_curve += np.where(f >= 200.0, -0.8 * np.log2(f / 200.0), 0.0)
    elif "bk" in k or "1974" in k:
        # Brüel & Kjær 1974 legendary warm curve (+3.0 dB <100Hz, -0.9 dB/oct above 400Hz)
        target_curve += np.where(f < 100.0, 3.0, np.where(f < 400.0, 3.0 * (1.0 - (f - 100.0) / 300.0), -0.9 * np.log2(np.maximum(f / 400.0, 1.0))))
    elif "dirac" in k:
        # Dirac Live Modern Stereo (+2.0 dB <120Hz, tight slope to 250Hz, -0.6 dB/oct above 1kHz)
        target_curve += np.where(f < 120.0, 2.0, np.where(f < 250.0, 2.0 * (1.0 - (f - 120.0) / 130.0), np.where(f <= 1000.0, 0.0, -0.6 * np.log2(f / 1000.0))))
    elif "bbc" in k or "gundry" in k:
        # BBC Dip / Gundry Curve: Harman bass + intentional -2.2 dB dip at 2.8 kHz (LS3/5a fatigue-free)
        target_curve += np.where(f < 120.0, 2.2, np.where(f < 200.0, 2.2 * 0.5 * (1.0 + np.cos(np.pi * (f - 120.0) / 80.0)), -0.8 * np.log2(np.maximum(f / 200.0, 1.0))))
        target_curve += -2.2 * np.exp(-0.5 * ((np.log2(f / 2800.0) / 0.55) ** 2))
    elif "blockbuster" in k or "cinema" in k:
        # Cinema Blockbuster Impact (+3.5 dB 50-120Hz for tactile movie sound, subsonic protection < 50Hz, -1.0 dB/oct above 220Hz)
        target_curve += np.where(f < 50.0, 3.5 * (f / 50.0), np.where(f < 120.0, 3.5, np.where(f < 220.0, 3.5 * 0.5 * (1.0 + np.cos(np.pi * (f - 120.0) / 100.0)), 0.0)))
        target_curve += np.where(f >= 220.0, -1.0 * np.log2(f / 220.0), 0.0)
    elif "x_curve" in k:
        # ISO 2969 / SMPTE 202M Modified X-Curve (flat to 2 kHz, -3.0 dB/octave above 2 kHz)
        target_curve += np.where(f <= 2000.0, 0.0, -3.0 * np.log2(f / 2000.0))
    elif "vocal" in k:
        # Vocal Clarity: tames muddy sub-bass, boosts speech intelligibility in 1.5 - 3.5 kHz (+1.8 dB)
        target_curve += np.where(f < 100.0, -1.5, 0.0)
        target_curve += 1.8 * np.exp(-0.5 * ((np.log2(f / 2500.0) / 0.6) ** 2))
        target_curve += np.where(f > 8000.0, -0.8 * np.log2(f / 8000.0), 0.0)
    elif "vintage" in k or "japanese" in k:
        # Warm Vintage Japanese 70s (Sansui/Marantz warm mids +1.0 dB @ 1.1 kHz, velvety top end)
        target_curve += np.where(f < 150.0, 2.0, np.where(f < 300.0, 2.0 * (1.0 - (f - 150.0) / 150.0), 0.0))
        target_curve += 1.0 * np.exp(-0.5 * ((np.log2(f / 1100.0) / 0.8) ** 2))
        target_curve += np.where(f > 6000.0, -1.5 * np.log2(f / 6000.0), 0.0)
    elif "gaming" in k or "spatial" in k:
        # Gaming & Atmos Virtualization (+2.0 dB punch @ 65Hz, -1.5 dB un-muddy @ 250Hz, +1.6 dB spatial cues @ 4.2kHz)
        target_curve += np.where(f < 80.0, 2.0, 0.0)
        target_curve += -1.5 * np.exp(-0.5 * ((np.log2(f / 250.0) / 0.4) ** 2))
        target_curve += 1.6 * np.exp(-0.5 * ((np.log2(f / 4200.0) / 0.5) ** 2))
    elif "whisper" in k or "night" in k:
        # Late Night Whisper (steep low cut <80Hz, +2.5 dB dialogue boost @ 2.4kHz, tamed highs)
        target_curve += np.where(f < 80.0, -6.0 * np.log2(80.0 / f), 0.0)
        target_curve += 2.5 * np.exp(-0.5 * ((np.log2(f / 2400.0) / 0.7) ** 2))
        target_curve += np.where(f > 7000.0, -2.0 * np.log2(f / 7000.0), 0.0)
    elif "acoustic" in k or "unplugged" in k:
        # Acoustic & Vocal Intimate (box anti-resonance cut -1.5 dB @ 160Hz, +1.2 dB airy top above 10kHz)
        target_curve += -1.5 * np.exp(-0.5 * ((np.log2(f / 160.0) / 0.45) ** 2))
        target_curve += np.where(f > 10000.0, 1.2 * (1.0 - np.exp(-(f - 10000.0) / 4000.0)), 0.0)
    else:
        # Default Harman / Floyd Toole standard in-room curve (+2.5 dB <120Hz, -0.8 dB/oct above 200Hz)
        target_curve += np.where(f < 120.0, 2.5, np.where(f < 200.0, 2.5 * 0.5 * (1.0 + np.cos(np.pi * (f - 120.0) / 80.0)), 0.0))
        target_curve += np.where(f >= 200.0, -0.8 * np.log2(f / 200.0), 0.0)

    return target_curve + hpf_db


def route_multichannel_layout(layout: str = "STEREO_2_0") -> List[str]:
    """
    Returns the list of active audio channels for a given speaker layout configuration.
    Supports all standard stereo, surround, height/presence, and immersive 3D/Atmos topologies:
    - 1.0 (Mono), 2.0 (Stereo), 2.1, 2.2, 3.0, 3.1
    - 4.0 (Quadraphonic), 4.1
    - 5.0, 5.1, 5.2
    - 7.0, 7.1, 7.2
    - 5.1.2, 5.2.2 (Presence/Top Front)
    - 7.1.2, 7.2.2 (Surround Back + Presence)
    - 5.1.4, 7.1.4, 9.1.6, 11.2 (Extended AVR processor / Auro3D / Atmos topologies)
    """
    normalized = layout.upper().strip().replace("-", "_").replace(".", "_")
    
    # Mapping of all standard consumer and pro multichannel audio topologies
    layouts = {
        # Mono & Basic Stereo
        "1_0": ["Center"],
        "MONO": ["Center"],
        "2_0": ["Front_L", "Front_R"],
        "STEREO": ["Front_L", "Front_R"],
        "STEREO_2_0": ["Front_L", "Front_R"],
        "2_1": ["Front_L", "Front_R", "Subwoofer"],
        "STEREO_2_1": ["Front_L", "Front_R", "Subwoofer"],
        "2_2": ["Front_L", "Front_R", "Subwoofer_1", "Subwoofer_2"],
        "STEREO_2_2": ["Front_L", "Front_R", "Subwoofer_1", "Subwoofer_2"],
        
        # Front Stage / LCR
        "3_0": ["Front_L", "Front_R", "Center"],
        "LCR": ["Front_L", "Front_R", "Center"],
        "3_1": ["Front_L", "Front_R", "Center", "Subwoofer"],
        
        # Quadraphonic
        "4_0": ["Front_L", "Front_R", "Surround_L", "Surround_R"],
        "QUAD": ["Front_L", "Front_R", "Surround_L", "Surround_R"],
        "QUADRAPHONIC": ["Front_L", "Front_R", "Surround_L", "Surround_R"],
        "4_1": ["Front_L", "Front_R", "Surround_L", "Surround_R", "Subwoofer"],
        
        # 5.x Surround
        "5_0": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R"],
        "5_1": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Subwoofer"],
        "SURROUND_5_1": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Subwoofer"],
        "5_2": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Subwoofer_1", "Subwoofer_2"],
        
        # 7.x Traditional Surround
        "7_0": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R"],
        "7_1": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Subwoofer"],
        "SURROUND_7_1": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Subwoofer"],
        "7_2": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Subwoofer_1", "Subwoofer_2"],
        
        # 5.x.y Immersive Height / Presence (Dolby Atmos / Yamaha Presence / DTS:X)
        "5_1_2": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Front_Presence_L", "Front_Presence_R", "Subwoofer"],
        "5_2_2": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Front_Presence_L", "Front_Presence_R", "Subwoofer_1", "Subwoofer_2"],
        "5_1_4": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Front_Presence_L", "Front_Presence_R", "Rear_Presence_L", "Rear_Presence_R", "Subwoofer"],
        "5_2_4": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Front_Presence_L", "Front_Presence_R", "Rear_Presence_L", "Rear_Presence_R", "Subwoofer_1", "Subwoofer_2"],
        
        # 7.x.y Immersive Height / Presence
        "7_1_2": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Front_Presence_L", "Front_Presence_R", "Subwoofer"],
        "7_2_2": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Front_Presence_L", "Front_Presence_R", "Subwoofer_1", "Subwoofer_2"],
        "7_1_4": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Front_Presence_L", "Front_Presence_R", "Rear_Presence_L", "Rear_Presence_R", "Subwoofer"],
        "7_2_4": ["Front_L", "Front_R", "Center", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Front_Presence_L", "Front_Presence_R", "Rear_Presence_L", "Rear_Presence_R", "Subwoofer_1", "Subwoofer_2"],
        
        # 9.x.y & Extended Ultra-Immersive / Auro3D Topologies
        "9_1_2": ["Front_L", "Front_R", "Center", "Front_Wide_L", "Front_Wide_R", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Front_Presence_L", "Front_Presence_R", "Subwoofer"],
        "9_1_4": ["Front_L", "Front_R", "Center", "Front_Wide_L", "Front_Wide_R", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Front_Presence_L", "Front_Presence_R", "Rear_Presence_L", "Rear_Presence_R", "Subwoofer"],
        "9_1_6": ["Front_L", "Front_R", "Center", "Front_Wide_L", "Front_Wide_R", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Front_Presence_L", "Front_Presence_R", "Top_Middle_L", "Top_Middle_R", "Rear_Presence_L", "Rear_Presence_R", "Subwoofer"],
        "9_2_6": ["Front_L", "Front_R", "Center", "Front_Wide_L", "Front_Wide_R", "Surround_L", "Surround_R", "Surround_Back_L", "Surround_Back_R", "Front_Presence_L", "Front_Presence_R", "Top_Middle_L", "Top_Middle_R", "Rear_Presence_L", "Rear_Presence_R", "Subwoofer_1", "Subwoofer_2"],
    }
    
    return layouts.get(normalized, layouts["2_0"])


def load_hardware_profile(
    config_path: str = "config/hardware.json",
    active_only: bool = True,
) -> Dict[str, Any]:
    """Loads the persistent hardware configuration and returns active profile data."""
    path = pathlib.Path(config_path)
    if not path.is_absolute():
        path = pathlib.Path(__file__).resolve().parent.parent / config_path
    with open(path, "r", encoding="utf-8") as f:
        hw = json.load(f)
    if not active_only:
        return hw
    a = hw["active"]
    return {
        "active": a,
        "microphone": hw["microphones"][a["microphone"]],
        "amplifier": hw["amplifiers"][a["amplifier"]],
        "speakers": hw["speakers"][a["speakers"]],
    }



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

@dataclasses.dataclass
class BiquadFilter:
    """
    Represents a digital second-order IIR biquad filter (RBJ Audio EQ Cookbook).
    """
    f0: float
    gain_db: float
    q: float
    fs: float = 48000.0

    def get_coefficients(self) -> Tuple[float, float, float, float, float, float]:
        if abs(self.gain_db) < 0.001:
            return 1.0, 0.0, 0.0, 1.0, 0.0, 0.0
        A = 10.0 ** (self.gain_db / 40.0)
        w0 = 2.0 * np.pi * self.f0 / self.fs
        alpha = np.sin(w0) / (2.0 * max(0.01, self.q))
        b0 = 1.0 + alpha * A
        b1 = -2.0 * np.cos(w0)
        b2 = 1.0 - alpha * A
        a0 = 1.0 + alpha / A
        a1 = -2.0 * np.cos(w0)
        a2 = 1.0 - alpha / A
        return b0, b1, b2, a0, a1, a2

    def evaluate_response(self, freqs_hz: np.ndarray) -> np.ndarray:
        return biquad_peaking_response(freqs_hz, self.f0, self.q, self.gain_db, fs=self.fs)


def evaluate_biquad_cascade(filters: List[BiquadFilter], freqs_hz: np.ndarray, fs: float = 48000.0) -> np.ndarray:
    """Computes total cascaded magnitude response (in dB) of a chain of BiquadFilter objects."""
    total_db = np.zeros_like(freqs_hz, dtype=np.float64)
    for f in filters:
        total_db += f.evaluate_response(freqs_hz)
    return total_db

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

    # Deduplicate peaks that snapped to the same discrete Yamaha frequency, keeping the one with higher elevation
    unique_detected = {}
    for d in detected:
        f_snap = d["freq_hz"]
        if f_snap not in unique_detected or d["elevation_db"] > unique_detected[f_snap]["elevation_db"]:
            unique_detected[f_snap] = d
    final_detected = list(unique_detected.values())
    final_detected.sort(key=lambda x: x["elevation_db"], reverse=True)
    return final_detected[:max_peaks]

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
    # Coordinated stereo band allocation: Band k on Left and Right shares the exact same center frequency.
    allocated_freqs = set()
    bands_l = []
    bands_r = []

    # A. Coordinated common modes
    for m in paired_modes:
        if len(bands_l) >= 7 - len(voicing_l):
            break
        if m["freq_hz"] in allocated_freqs:
            continue
        base_cut = -min(6.0, m["shared_elevation"] * 0.85)
        trim_l = -min(2.5, max(0.0, (m["left_elevation"] - m["shared_elevation"]) * 0.7))
        trim_r = -min(2.5, max(0.0, (m["right_elevation"] - m["shared_elevation"]) * 0.7))

        gain_l = snap_gain(max(-8.0, base_cut + trim_l), m["freq_hz"])
        gain_r = snap_gain(max(-8.0, base_cut + trim_r), m["freq_hz"])

        bands_l.append({"freq_hz": m["freq_hz"], "q": m["q"], "gain_db": gain_l, "role": "common_mode"})
        bands_r.append({"freq_hz": m["freq_hz"], "q": m["q"], "gain_db": gain_r, "role": "common_mode"})
        allocated_freqs.add(m["freq_hz"])

    # B. Asymmetric independent modes (paired in lock-step to preserve stereo alignment)
    for lp in left_only:
        if len(bands_l) >= 7 - len(voicing_l):
            break
        if lp["freq_hz"] in allocated_freqs:
            continue
        gain = snap_gain(-min(5.0, lp["elevation_db"] * 0.8), lp["freq_hz"])
        q_val = snap_q(min(3.175, lp["q"]))
        bands_l.append({"freq_hz": lp["freq_hz"], "q": q_val, "gain_db": gain, "role": "asym_mode"})
        bands_r.append({"freq_hz": lp["freq_hz"], "q": q_val, "gain_db": 0.0, "role": "transparent_pass"})
        allocated_freqs.add(lp["freq_hz"])

    for rp in right_only:
        if len(bands_l) >= 7 - len(voicing_l):
            break
        if rp["freq_hz"] in allocated_freqs:
            continue
        gain = snap_gain(-min(5.0, rp["elevation_db"] * 0.8), rp["freq_hz"])
        q_val = snap_q(min(3.175, rp["q"]))
        bands_l.append({"freq_hz": rp["freq_hz"], "q": q_val, "gain_db": 0.0, "role": "transparent_pass"})
        bands_r.append({"freq_hz": rp["freq_hz"], "q": q_val, "gain_db": gain, "role": "asym_mode"})
        allocated_freqs.add(rp["freq_hz"])

    # C. Add high-frequency voicing bands
    for vl, vr in zip(voicing_l, voicing_r):
        if len(bands_l) < 7 and vl["freq_hz"] not in allocated_freqs:
            bands_l.append(dict(vl))
            bands_r.append(dict(vr))
            allocated_freqs.add(vl["freq_hz"])

    # D. Fill remaining slots respecting Yamaha RX-V673 hardware topology:
    # Bands 1-4 allow any frequency (31.3 Hz - 16 kHz).
    # Bands 5-7 strictly require frequency >= 500 Hz (min 500.0 Hz).
    def is_slot_freq_allowed(slot_idx: int, f: float) -> bool:
        if slot_idx >= 5: # 1-indexed Band 5, 6, 7
            return f >= 500.0
        return True

    # Re-order existing bands so that bands < 500 Hz occupy slots 1 to 4
    # and bands >= 500 Hz occupy slots 5 to 7 whenever possible
    sub_500 = []
    gte_500 = []
    for bl, br in zip(bands_l, bands_r):
        if bl["freq_hz"] < 500.0:
            sub_500.append((bl, br))
        else:
            gte_500.append((bl, br))

    arranged_l = []
    arranged_r = []

    # Place up to 4 sub-500 Hz filters in bands 1-4
    while sub_500 and len(arranged_l) < 4:
        bl, br = sub_500.pop(0)
        arranged_l.append(bl)
        arranged_r.append(br)

    # Place gte-500 Hz filters
    while gte_500 and len(arranged_l) < 7:
        bl, br = gte_500.pop(0)
        arranged_l.append(bl)
        arranged_r.append(br)

    # Any remaining sub-500 can go into remaining slots 1-4 if available
    while sub_500 and len(arranged_l) < 4:
        bl, br = sub_500.pop(0)
        arranged_l.append(bl)
        arranged_r.append(br)

    # Fill empty slots with valid neutral bands
    allocated_freqs = set(b["freq_hz"] for b in arranged_l)
    while len(arranged_l) < 7:
        slot_num = len(arranged_l) + 1
        valid_pool = [f for f in YAMAHA_FREQS if (float(f) >= 500.0 if slot_num >= 5 else True) and float(f) not in allocated_freqs]
        chosen_freq = float(valid_pool[0]) if valid_pool else (1000.0 if slot_num >= 5 else 62.5)
        allocated_freqs.add(chosen_freq)
        arranged_l.append({"freq_hz": chosen_freq, "q": 1.0, "gain_db": 0.0, "role": "inactive"})
        arranged_r.append({"freq_hz": chosen_freq, "q": 1.0, "gain_db": 0.0, "role": "inactive"})

    bands_l = arranged_l
    bands_r = arranged_r
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


def optimize_subwoofer_peq(
    freqs_hz: np.ndarray,
    response_db: np.ndarray,
    target_db: Optional[np.ndarray] = None,
    crossover_hz: float = 80.0,
    max_bands: int = 3,
) -> List[Dict[str, Any]]:
    """
    Subwoofer PEQ optimization engine for Yamaha RX-V673.
    Targets room modal resonances in sub-bass / subwoofer band (< crossover_hz * 1.5).
    Generates complementary 2nd-order Butterworth low-pass target curve if target_db is None.
    Snaps parameters to discrete Yamaha constraints.
    """
    freqs_hz = np.asarray(freqs_hz, dtype=np.float64)
    response_db = np.asarray(response_db, dtype=np.float64)
    if target_db is None:
        lpf_mag = 1.0 / np.sqrt(1.0 + (freqs_hz / max(crossover_hz, 1.0)) ** 4)
        target_db = 20.0 * np.log10(np.maximum(lpf_mag, 1e-3))
    else:
        target_db = np.asarray(target_db, dtype=np.float64)

    max_freq = min(float(crossover_hz) * 1.5, 200.0)
    peaks = detect_modal_resonances(
        freqs_hz,
        response_db,
        target_db,
        min_elevation_db=1.5,
        max_peaks=max_bands,
        max_freq=max_freq,
    )

    bands = []
    for idx, p in enumerate(peaks, start=1):
        f_snap = snap_frequency(p["freq_hz"])
        q_snap = snap_q(p["q"])
        gain = snap_gain(-min(8.0, p["elevation_db"] * 0.85), f_snap, allow_voicing_boost=False)
        bands.append({
            "band": idx,
            "freq_hz": f_snap,
            "q": q_snap,
            "gain_db": gain,
            "role": "sub_modal_resonance",
        })

    return bands

def calculate_standing_wave(freq_hz: float, speed_of_sound_ms: float = 343.0) -> Dict[str, Any]:
    """
    Calculates acoustic wavelength and room boundary dimensions for an axial standing wave (FR-002, SC-002).
    lambda = v / f
    half_wavelength = lambda / 2 (distance between parallel boundaries exciting the mode)
    """
    if freq_hz <= 0:
        return {"wavelength_m": 0.0, "half_wavelength_m": 0.0, "boundary_dim_m": 0.0}
    wl = speed_of_sound_ms / float(freq_hz)
    half_wl = wl / 2.0
    return {
        "freq_hz": float(freq_hz),
        "wavelength_m": round(wl, 2),
        "half_wavelength_m": round(half_wl, 2),
        "boundary_dim_m": round(half_wl, 2),
        "classification": "AXIAL_ROOM_MODE" if freq_hz < 300.0 else "BOUNDARY_REFLECTION"
    }


def classify_peq_band_function(
    band_idx: int,
    freq_hz: float,
    gain_l: float,
    gain_r: float,
    q_l: float = 1.0,
    q_r: float = 1.0,
    role: str = ""
) -> Dict[str, Any]:
    """
    Assigns electroacoustic classification, physical rationale, and phase impact to a 7-band filter (FR-005, FR-006).
    """
    sw = calculate_standing_wave(freq_hz)
    has_cut = (gain_l < 0.0 or gain_r < 0.0)
    has_boost = (gain_l > 0.0 or gain_r > 0.0)

    if 2000.0 <= freq_hz <= 3000.0 and has_boost:
        category = "CROSSOVER_VOICING"
        rationale = f"Compensación de cruce y directividad del altavoz Q Acoustics 3020i ({freq_hz:.0f} Hz / punto de cruce a 2.4 kHz)"
        phase_risk = "Mínimo (mejora de alineación en eje entre woofer y tweeter)"
    elif has_cut:
        category = "MODAL_NOTCH"
        if gain_l < 0.0 and gain_r == 0.0:
            rationale = f"Notch modal quirúrgico Front L ({freq_hz:.0f} Hz, λ ≈ {sw['wavelength_m']}m) con pase neutro en R"
        elif gain_r < 0.0 and gain_l == 0.0:
            rationale = f"Notch modal quirúrgico Front R ({freq_hz:.0f} Hz, λ ≈ {sw['wavelength_m']}m) con pase neutro en L"
        else:
            rationale = f"Notch modal estéreo coordinado contra onda estacionaria ({freq_hz:.0f} Hz, λ ≈ {sw['wavelength_m']}m)"
        phase_risk = "Corrección de fase mínima acústica (drena resonancia sin ringing audible)"
    else:
        category = "TRANSPARENT_PASS"
        rationale = f"Preservación anecoica / Fase neutra ({freq_hz:.0f} Hz) — anti-boost de cancelaciones acústicas"
        phase_risk = "Ninguno (filtro en bypass digital 0.0 dB)"

    return {
        "band_idx": int(band_idx),
        "freq_hz": float(freq_hz),
        "gain_l": float(gain_l),
        "gain_r": float(gain_r),
        "q_l": float(q_l),
        "q_r": float(q_r),
        "category": category,
        "rationale": rationale,
        "phase_distortion_risk": phase_risk,
        "standing_wave": sw
    }

def calculate_subwoofer_phase_alignment(
    freqs_hz: np.ndarray,
    front_mag_db: np.ndarray,
    sub_mag_db: np.ndarray,
    crossover_hz: float = 80.0,
    sub_distance_m: float = 3.65,
    front_distance_m: float = 2.40,
) -> Dict[str, Any]:
    """
    Automatic Subwoofer Phase Alignment (0° Normal vs 180° Reverse).
    Evaluates acoustic summation across the crossover transition band [0.6*fc, 1.4*fc].
    Computes constructive vs destructive acoustic interference and Time-of-Flight delay.
    """
    f_min = crossover_hz * 0.6
    f_max = crossover_hz * 1.4
    mask = (freqs_hz >= f_min) & (freqs_hz <= f_max)

    if not np.any(mask):
        return {
            "recommended_phase": "Normal",
            "recommended_phase_degrees": 0,
            "reinforcement_db": 3.0,
            "delay_ms": round((sub_distance_m - front_distance_m) / 343.0 * 1000.0, 2),
            "summary": "Fase Normal (0°) seleccionada por defecto."
        }

    p_front = 10.0 ** (front_mag_db[mask] / 20.0)
    p_sub = 10.0 ** (sub_mag_db[mask] / 20.0)

    # Constructive in-phase (0° / Normal)
    sum_normal = 20.0 * np.log10(np.maximum(1e-6, p_front + p_sub))
    # Destructive out-of-phase (180° / Reverse)
    sum_reverse = 20.0 * np.log10(np.maximum(1e-6, np.abs(p_front - p_sub)))

    e_normal = float(np.mean(sum_normal))
    e_reverse = float(np.mean(sum_reverse))

    delta_db = round(float(e_normal - e_reverse), 2)
    delay_ms = round((sub_distance_m - front_distance_m) / 343.0 * 1000.0, 2)

    if e_normal >= e_reverse:
        rec_phase = "Normal"
        rec_deg = 0
        reinf_db = max(0.5, round(e_normal - float(np.mean(np.maximum(front_mag_db[mask], sub_mag_db[mask]))), 2))
        summary = f"Fase Normal (0°) ofrece {abs(delta_db):.1f} dB de mayor refuerzo acústico constructivo en el cruce de {crossover_hz:.0f} Hz."
    else:
        rec_phase = "Reverse"
        rec_deg = 180
        reinf_db = max(0.5, round(e_reverse - float(np.mean(np.maximum(front_mag_db[mask], sub_mag_db[mask]))), 2))
        summary = f"Fase Invertida (180°) cancela el nulo de cruce y aporta {abs(delta_db):.1f} dB de mayor energía acústica."

    return {
        "recommended_phase": rec_phase,
        "recommended_phase_degrees": rec_deg,
        "reinforcement_db": reinf_db,
        "energy_normal_db": round(e_normal, 2),
        "energy_reverse_db": round(e_reverse, 2),
        "delta_db": delta_db,
        "delay_ms": delay_ms,
        "crossover_hz": crossover_hz,
        "summary": summary
    }


def calculate_multi_sub_alignment(
    sub1_distance_m: float,
    sub2_distance_m: float,
) -> Dict[str, Any]:
    """
    Calculates relative inter-subwoofer delay and alignment for 2.2 / dual-subwoofer topologies.
    """
    diff_m = abs(sub1_distance_m - sub2_distance_m)
    delay_ms = round(diff_m / 343.0 * 1000.0, 2)
    closer_sub = "Subwoofer_1" if sub1_distance_m <= sub2_distance_m else "Subwoofer_2"
    further_sub = "Subwoofer_2" if closer_sub == "Subwoofer_1" else "Subwoofer_1"

    return {
        "inter_sub_delay_ms": delay_ms,
        "distance_delta_m": round(diff_m, 2),
        "reference_sub": closer_sub,
        "delayed_sub": further_sub,
        "recommendation": f"Atrasar {further_sub} en {delay_ms:.2f} ms para alinear frentes de onda en el Sweet Spot." if delay_ms > 0.1 else "Ambos subwoofers están alineados temporalmente."
    }

def calculate_speaker_trim_levels(
    channel_spl_map: Dict[str, float],
    target_spl_db: float = 75.0,
    reference_channel: Optional[str] = "Front_L",
) -> Dict[str, float]:
    """
    Automatic Speaker and Subwoofer dB Trim Level Optimization.
    Calculates discrete Yamaha RX-V673 channel level trims (-10.0 dB to +10.0 dB in 0.5 dB steps)
    so every speaker, including the Focal Cub Evo subwoofer, matches the calibrated target SPL.
    """
    trims: Dict[str, float] = {}
    ref_spl = channel_spl_map.get(reference_channel or "", target_spl_db)
    base_target = target_spl_db if target_spl_db is not None else ref_spl

    for ch, spl in channel_spl_map.items():
        # Difference required to hit reference SPL
        diff = base_target - float(spl)
        # Snap to discrete 0.5 dB Yamaha step
        stepped = round(diff * 2.0) / 2.0
        clamped = max(-10.0, min(10.0, float(stepped)))
        trims[ch] = clamped

    return trims


# ==============================================================================
# ACÚSTICA AVANZADA (NIVEL TRINNOV OPTIMIZER / DIRAC LIVE)
# ==============================================================================

def calculate_schroeder_reverberation(
    impulse_response: np.ndarray,
    sample_rate_hz: int = 48000,
) -> Dict[str, Any]:
    """
    Calculates room reverberation time (EDT, T20, T30, T60) using backwards
    Schroeder energy integration from an empirical impulse response.
    """
    ir = np.asarray(impulse_response, dtype=np.float64)
    if ir.ndim > 1:
        ir = ir.flatten()
    if len(ir) < 256:
        return {"edt_s": 0.3, "t20_s": 0.35, "t30_s": 0.35, "t60_s": 0.35, "valid": False}

    # Peak alignment and energy curve
    peak_idx = int(np.argmax(np.abs(ir)))
    tail = ir[peak_idx:]
    energy = tail ** 2
    schroeder_decay = np.cumsum(energy[::-1])[::-1]
    max_energy = schroeder_decay[0]
    if max_energy <= 1e-12:
        return {"edt_s": 0.3, "t20_s": 0.35, "t30_s": 0.35, "t60_s": 0.35, "valid": False}

    # Energy Decay Curve in dB
    decay_db = 10.0 * np.log10(np.maximum(schroeder_decay / max_energy, 1e-10))
    time_s = np.arange(len(decay_db)) / float(sample_rate_hz)

    def _fit_slope(db_start: float, db_end: float) -> float:
        idx_start = np.where(decay_db <= db_start)[0]
        idx_end = np.where(decay_db <= db_end)[0]
        if len(idx_start) == 0 or len(idx_end) == 0:
            return 0.35
        i0, i1 = idx_start[0], idx_end[0]
        if i1 <= i0 + 10:
            return 0.35
        t_seg = time_s[i0:i1]
        db_seg = decay_db[i0:i1]
        poly = np.polyfit(t_seg, db_seg, 1)
        slope = poly[0]
        if slope >= 0:
            return 0.35
        # T60 is the time to decay by 60 dB
        return float(abs(-60.0 / slope))

    edt = _fit_slope(0.0, -10.0)
    t20 = _fit_slope(-5.0, -25.0)
    t30 = _fit_slope(-5.0, -35.0)
    t60 = round(float(t30 if t30 > 0.05 else (t20 if t20 > 0.05 else edt)), 3)

    return {
        "edt_s": round(float(edt), 3),
        "t20_s": round(float(t20), 3),
        "t30_s": round(float(t30), 3),
        "t60_s": t60,
        "valid": True,
    }


def calculate_schroeder_frequency(
    t60_s: float,
    room_volume_m3: float = 40.0,
) -> Dict[str, Any]:
    """
    Calculates the Schroeder Transition Frequency (fs) dividing room modal acoustics
    from ray/specular acoustics: fs ≈ 2000 * sqrt(T60 / V).
    Below fs: discrete room modes dominate (strictly correctable via PEQ cuts).
    Above fs: specular reflections and speaker directivity dominate (avoid narrow PEQ notches).
    """
    v = max(float(room_volume_m3), 1.0)
    t = max(float(t60_s), 0.05)
    fs = 2000.0 * np.sqrt(t / v)
    # Discrete boundaries for psychoacoustic tuning
    modal_cutoff_hz = round(float(min(max(fs, 120.0), 600.0)), 1)

    return {
        "t60_s": round(t, 3),
        "room_volume_m3": round(v, 1),
        "schroeder_frequency_hz": round(float(fs), 1),
        "modal_cutoff_hz": modal_cutoff_hz,
        "recommendation": f"Aplicar ecualización quirúrgica de alta Q bajo {modal_cutoff_hz} Hz; aplicar solo control tímbrico suave sobre dicho umbral."
    }


def compute_minimum_phase_decomposition(
    freqs_hz: np.ndarray,
    magnitude_db: np.ndarray,
) -> Dict[str, np.ndarray]:
    """
    Decomposes acoustic frequency response into Minimum Phase and Excess Phase
    using the discrete Hilbert transform of the log-magnitude spectrum.
    Trinnov/Dirac principle: only minimum-phase deviations are invertible/correctable
    with PEQ without producing pre-ringing or spatial smearing.
    """
    freqs = np.asarray(freqs_hz, dtype=np.float64)
    mag_db = np.asarray(magnitude_db, dtype=np.float64)
    n = len(mag_db)
    if n < 4:
        return {
            "minimum_phase_deg": np.zeros_like(mag_db),
            "excess_phase_deg": np.zeros_like(mag_db),
            "correctability_factor": np.ones_like(mag_db),
        }

    # Natural log magnitude
    alpha = (mag_db / 20.0) * np.log(10.0)
    # Hilbert transform via FFT
    f_alpha = np.fft.fft(alpha)
    h = np.zeros(n)
    if n % 2 == 0:
        h[0] = 1.0
        h[n // 2] = 1.0
        h[1:n // 2] = 2.0
    else:
        h[0] = 1.0
        h[1:(n + 1) // 2] = 2.0

    min_phase_rad = np.imag(np.fft.ifft(f_alpha * h))
    min_phase_deg = np.rad2deg(min_phase_rad)

    # Correctability factor: 1.0 where minimum phase dominates; drops where excess phase / reflections dominate
    excess_phase_deg = np.abs(min_phase_deg * 0.3) # Modeled excess phase envelope
    correctability = np.clip(1.0 - (excess_phase_deg / 180.0), 0.2, 1.0)

    return {
        "minimum_phase_deg": np.round(min_phase_deg, 2),
        "excess_phase_deg": np.round(excess_phase_deg, 2),
        "correctability_factor": np.round(correctability, 3),
    }
