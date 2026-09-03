#!/usr/bin/env python3
"""
scripts/auto_calibrate.py
Real Dynamic Electroacoustic Parametric EQ Optimization Pipeline.

Computes 7-band discrete Yamaha RX-V673 biquad parameters directly from empirical
measurements using non-linear least squares and modal resonance detection.
Zero hardcoded tables.
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR))

from scripts.peq_optimizer import (
    optimize_stereo_peq,
    multi_filter_response,
    YAMAHA_FREQS,
    YAMAHA_QS,
)
import importlib
yamaha_ctrl = importlib.import_module("scripts.04_yamaha_control")
deploy_peq_matrix_with_readback = yamaha_ctrl.deploy_peq_matrix_with_readback
from scripts.calibration_epoch import (
    create_epoch_directory,
    save_epoch_manifest,
    CalibrationEpoch,
    EpochMetrics,
    compute_file_sha256,
)

CONFIG_DIR = REPO_DIR / "config"
DATA_DIR = REPO_DIR / "data"

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_calibration(
    target_key: str = "harman_wide_room",
    use_spatial_avg: bool = True,
    push_yamaha: bool = False,
    sweet_spot_weight: float = 0.8,
) -> dict:
    targets = load_json(CONFIG_DIR / "targets.json")
    if target_key not in targets:
        print(f"[!] Target profile '{target_key}' not found. Available: {list(targets.keys())}")
        sys.exit(1)
        
    target_info = targets[target_key]
    
    # 1. Load empirical measurements
    sweet_spot_file = DATA_DIR / "medicion_real_calibracion.npz"
    spatial_avg_file = DATA_DIR / "medicion_promedio_espacial.npz"
    
    if not sweet_spot_file.exists():
        raise FileNotFoundError(f"Empirical Sweet Spot measurement missing: {sweet_spot_file}")
        
    d_sweet = np.load(sweet_spot_file)
    freqs = d_sweet["freqs"]
    sweet_l = d_sweet["smooth_l"] if "smooth_l" in d_sweet else d_sweet["raw_l"]
    sweet_r = d_sweet["smooth_r"] if "smooth_r" in d_sweet else d_sweet["raw_r"]
    
    spatial_l = None
    spatial_r = None
    if use_spatial_avg and spatial_avg_file.exists():
        d_spatial = np.load(spatial_avg_file)
        sp_f = d_spatial["freqs"]
        sp_l = d_spatial["smooth_l"] if "smooth_l" in d_spatial else d_spatial["raw_l"]
        sp_r = d_spatial["smooth_r"] if "smooth_r" in d_spatial else d_spatial["raw_r"]
        spatial_l = np.interp(freqs, sp_f, sp_l)
        spatial_r = np.interp(freqs, sp_f, sp_r)
        
    # 2. Build mathematical target curve
    target_curve = np.zeros_like(freqs)
    # Acoustic high-pass filter representing Q Acoustics 3020i (64 Hz -3 dB)
    f_c = 64.0
    hpf_mag = 1.0 / np.sqrt(1.0 + (f_c / np.maximum(freqs, 1.0))**4)
    hpf_db = 20.0 * np.log10(np.maximum(hpf_mag, 1e-3))

    k = (target_key or "").lower()
    if "bk" in k or "1974" in k:
        for i, f in enumerate(freqs):
            if f < 150.0:
                target_curve[i] = 3.0
            elif f < 200.0:
                target_curve[i] = 3.0 * 0.5 * (1.0 + np.cos(np.pi * (f - 150.0) / 50.0))
            else:
                target_curve[i] = -0.9 * np.log2(f / 200.0)
    elif "dirac" in k:
        for i, f in enumerate(freqs):
            if f < 120.0:
                target_curve[i] = 2.0
            elif f < 200.0:
                target_curve[i] = 2.0 * 0.5 * (1.0 + np.cos(np.pi * (f - 120.0) / 80.0))
            elif f <= 1000.0:
                target_curve[i] = 0.0
            else:
                target_curve[i] = -0.6 * np.log2(f / 1000.0)
    else:  # Harman target
        for i, f in enumerate(freqs):
            if f < 100.0:
                target_curve[i] = 4.5
            elif f < 200.0:
                target_curve[i] = 4.5 * 0.5 * (1.0 + np.cos(np.pi * (f - 100.0) / 100.0))
            elif f <= 1000.0:
                target_curve[i] = 0.0
            else:
                target_curve[i] = -0.8 * np.log2(f / 1000.0)
    target_curve = target_curve + hpf_db

    print("=== MOTOR DE OPTIMIZACIÓN ACÚSTICA DINÁMICA REAL ===")
    print(f"Perfil Objetivo:   {target_info['name']}")
    print(f"Ponderación:       80% Sweet Spot / 20% Promedio Espacial Multipunto")
    print(f"Límite Schroeder:  500 Hz (Cero boost en agudos)")
    print(f"Tope de Boost:     +3.0 dB")
    print(f"Calculando solución matemática óptima...")

    # 3. Dynamic Optimization
    opt_result = optimize_stereo_peq(
        freqs_hz=freqs,
        left_sweet_spot=sweet_l,
        right_sweet_spot=sweet_r,
        target_db=target_curve,
        left_spatial_avg=spatial_l,
        right_spatial_avg=spatial_r,
        sweet_spot_weight=sweet_spot_weight,
    )

    left_bands = opt_result["channels"]["left"]
    right_bands = opt_result["channels"]["right"]

    print("\n" + "="*85)
    print("TABLA DE PARÁMETROS PEQ OPTIMIZADOS MATEMÁTICAMENTE (YAMAHA RX-V673)")
    print("="*85)
    print("Banda | Frecuencia L | Q L     | Ganancia L | Frecuencia R | Q R     | Ganancia R")
    print("-"*85)
    for b_l, b_r in zip(left_bands, right_bands):
        print(f"Band {b_l['band']} | {b_l['freq_hz']:>9.1f} Hz | {b_l['q']:>7.3f} | {b_l['gain_db']:>+8.1f} dB | {b_r['freq_hz']:>9.1f} Hz | {b_r['q']:>7.3f} | {b_r['gain_db']:>+8.1f} dB")
    print("="*85)
    print(f"Reducción RMS estimada: {opt_result['metrics']['predicted_rms_reduction_db']:.2f} dB")
    print(f"Atenuación modal pico:  {opt_result['metrics']['predicted_modal_attenuation_db']:.2f} dB")
    print(f"Tiempo de cómputo:      {opt_result['metrics']['execution_time_ms']:.1f} ms")

    # 4. Optional Hardware Deployment
    if push_yamaha:
        print("\n[*] Enviando matriz PEQ al receptor Yamaha RX-V673 con verificación de lectura...")
        success, errors = deploy_peq_matrix_with_readback(
            {"left": left_bands, "right": right_bands},
            verify_readback=True,
        )
        if success:
            print("[✓] 100% de los parámetros verificados en la memoria NVRAM del receptor.")
        else:
            print(f"[!] Fallo en la verificación de hardware: {errors}")

    return opt_result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real Dynamic Room Calibration Optimizer")
    parser.add_argument("--profile", type=str, default="harman_wide_room", help="Target profile key")
    parser.add_argument("--no-spatial", action="store_true", help="Disable spatial averaging")
    parser.add_argument("--push", action="store_true", help="Push to Yamaha AVR via YNC")
    args = parser.parse_args()

    run_calibration(
        target_key=args.profile,
        use_spatial_avg=not args.no_spatial,
        push_yamaha=args.push,
    )
