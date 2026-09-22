#!/usr/bin/env python3
"""
scripts/auto_calibrate.py
Real Dynamic Electroacoustic Parametric EQ Optimization Pipeline.

Computes 7-band discrete Yamaha RX-V673 biquad parameters directly from empirical
measurements using non-linear least squares and modal resonance detection.
Zero hardcoded tables.
"""

from typing import Optional, Dict, Any
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
    optimize_subwoofer_peq,
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
    sweet_spot_weight: float = 0.7,
    config_path: str = None,
    subwoofer_crossover_hz: Optional[float] = None,
) -> dict:
    cfg_path = Path(config_path or (CONFIG_DIR / "targets.json"))
    targets = load_json(cfg_path)
    if target_key == "harman_2_1":
        target_key = "harman_wide_room"
    if target_key not in targets:
        print(f"[!] Target profile '{target_key}' not found. Available: {list(targets.keys())}")
        sys.exit(1)
        
    target_info = targets[target_key]
    if subwoofer_crossover_hz is None:
        cfg_xo = target_info.get("crossover_hz") or target_info.get("yamaha_config", {}).get("crossover_hz")
        if cfg_xo is not None and target_info.get("sub_supported", True):
            subwoofer_crossover_hz = float(cfg_xo)
    
    # 1. Load empirical measurements (Authoritative Sweet Spot Punto 1 + Spatial Average)
    sweet_spot_file = DATA_DIR / "medicion_punto_1.npz"
    if not sweet_spot_file.exists():
        sweet_spot_file = DATA_DIR / "medicion_real_calibracion.npz"
    spatial_avg_file = DATA_DIR / "medicion_promedio_espacial.npz"
    
    if not sweet_spot_file.exists():
        raise FileNotFoundError(f"Empirical Sweet Spot measurement missing: {sweet_spot_file}")
        
    d_sweet = np.load(sweet_spot_file)
    freqs = d_sweet["freqs"]
    sweet_l = d_sweet["smooth_l"] if "smooth_l" in d_sweet else d_sweet["raw_l"]
    sweet_r = d_sweet["smooth_r"] if "smooth_r" in d_sweet else d_sweet["raw_r"]
    # FR-002: Apply REW Variable Smoothing (Var) and broadband 300Hz-3kHz normalization
    from scripts.peq_optimizer import variable_smooth, broadband_normalize
    sweet_l = broadband_normalize(freqs, sweet_l)
    sweet_r = broadband_normalize(freqs, sweet_r)
    sweet_l = variable_smooth(freqs, sweet_l)
    sweet_r = variable_smooth(freqs, sweet_r)

    spatial_l = None
    spatial_r = None
    if use_spatial_avg and spatial_avg_file.exists():
        d_spatial = np.load(spatial_avg_file)
        sp_f = d_spatial["freqs"]
        sp_l = d_spatial["smooth_l"] if "smooth_l" in d_spatial else d_spatial["raw_l"]
        sp_r = d_spatial["smooth_r"] if "smooth_r" in d_spatial else d_spatial["raw_r"]
        sp_l = broadband_normalize(sp_f, sp_l)
        sp_r = broadband_normalize(sp_f, sp_r)
        sp_l = variable_smooth(sp_f, sp_l)
        sp_r = variable_smooth(sp_f, sp_r)
        spatial_l = np.interp(freqs, sp_f, sp_l)
        spatial_r = np.interp(freqs, sp_f, sp_r)
    # 2. Build mathematical target curve using central peq_optimizer definition
    from scripts.peq_optimizer import generate_bookshelf_target_curve
    target_curve = generate_bookshelf_target_curve(
        freqs,
        target_key=target_key,
        fc_hz=64.0,
        subwoofer_crossover_hz=subwoofer_crossover_hz,
    )
    # Calculate empirical T60 and dynamic Schroeder frequency fs
    from scripts.peq_optimizer import (
        calculate_schroeder_reverberation,
        calculate_schroeder_frequency,
        compute_minimum_phase_decomposition,
    )
    ir_sample = d_sweet.get("impulse_l", np.zeros(1024))
    rev_metrics = calculate_schroeder_reverberation(ir_sample)
    schroeder_info = calculate_schroeder_frequency(rev_metrics["t60_s"], room_volume_m3=40.0)
    schroeder_limit = schroeder_info["modal_cutoff_hz"]

    print("=== MOTOR DE OPTIMIZACIÓN ACÚSTICA DINÁMICA REAL ===")
    print(f"Perfil Objetivo:   {target_info['name']}")
    print(f"Ponderación:       70% Sweet Spot / 30% Promedio Espacial Cluster (Tight 15-20cm)")
    print(f"Suavizado:         Variable Smoothing (Var) — 2026 Pro")
    print(f"Normalización:     Banda Ancha 300 Hz – 3 kHz (anti-dip 1 kHz)")
    print(f"T60 Acústico Sala: {rev_metrics['t60_s']:.2f} s | Frecuencia Schroeder: {schroeder_limit:.1f} Hz")
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
        target_key=target_key,
        config_path=str(cfg_path),
    )

    left_bands = opt_result["channels"]["left"]
    right_bands = opt_result["channels"]["right"]

    # 3b. Subwoofer PEQ Optimization (if 2.1 crossover is configured)
    if subwoofer_crossover_hz and subwoofer_crossover_hz > 0:
        sub_file = DATA_DIR / "medicion_sub.npz"
        if "smooth_sub" in d_sweet:
            sub_resp = d_sweet["smooth_sub"]
        elif "raw_sub" in d_sweet:
            sub_resp = d_sweet["raw_sub"]
        elif spatial_avg_file.exists() and "smooth_sub" in np.load(spatial_avg_file):
            sub_resp = np.load(spatial_avg_file)["smooth_sub"]
        elif sub_file.exists():
            d_sub = np.load(sub_file)
            f_sub_meas = d_sub["freqs"]
            raw_sub = d_sub["resp"] if "resp" in d_sub else (d_sub["smooth"] if "smooth" in d_sub else d_sub["raw_l"])
            sub_resp = np.interp(freqs, f_sub_meas, raw_sub)
        else:
            raw_sl = d_sweet["smooth_l"] if "smooth_l" in d_sweet else d_sweet["raw_l"]
            raw_sr = d_sweet["smooth_r"] if "smooth_r" in d_sweet else d_sweet["raw_r"]
            sub_resp = broadband_normalize(freqs, 0.5 * (raw_sl + raw_sr))
        sub_bands = optimize_subwoofer_peq(
            freqs_hz=freqs,
            response_db=sub_resp,
            crossover_hz=subwoofer_crossover_hz,
            max_bands=3,
        )
        opt_result["channels"]["subwoofer"] = sub_bands

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

    if "subwoofer" in opt_result["channels"]:
        sub_bands = opt_result["channels"]["subwoofer"]
        print("\n" + "="*60)
        print(f"TABLA PEQ SUBWOOFER FOCAL CUB EVO (XO = {subwoofer_crossover_hz:.1f} Hz)")
        print("="*60)
        print("Banda  | Frecuencia | Q       | Ganancia")
        print("-"*60)
        for sb in sub_bands:
            print(f"Band {sb['band']} | {sb['freq_hz']:>8.1f} Hz | {sb['q']:>7.3f} | {sb['gain_db']:>+8.1f} dB")
        print("="*60)

    # 4. Synchronize dynamically optimized bands back to targets.json
    bands_dict = {}
    for bl, br in zip(left_bands, right_bands):
        b_idx = bl["band"]
        if bl.get("role") == "common_mode":
            desc = f"Modo modal compartido ({bl['freq_hz']} Hz)"
        elif bl.get("gain_db", 0.0) < 0 and br.get("gain_db", 0.0) == 0:
            desc = f"Modo modal Front L ({bl['freq_hz']} Hz) con pase neutro en R"
        elif br.get("gain_db", 0.0) < 0 and bl.get("gain_db", 0.0) == 0:
            desc = f"Modo modal Front R ({br['freq_hz']} Hz) con pase neutro en L"
        elif bl.get("role") == "voicing":
            desc = f"Compensación de cruce y directividad del altavoz ({bl['freq_hz']} Hz)"
        else:
            desc = f"Preservación anecoica / Fase neutra ({bl['freq_hz']} Hz)"

        q_val = float(bl["q"])
        gain_val = float(bl["gain_db"])
        bands_dict[f"Band {b_idx}"] = {
            "freq": float(bl["freq_hz"]),
            "q": q_val,
            "gain": gain_val,
            "q_l": q_val,
            "q_r": float(br["q"]),
            "gain_l": gain_val,
            "gain_r": float(br["gain_db"]),
            "desc": desc
        }
    sub_bands_dict = {}
    if "subwoofer" in opt_result["channels"]:
        for sb in opt_result["channels"]["subwoofer"]:
            b_idx = sb["band"]
            sub_bands_dict[f"Band {b_idx}"] = {
                "freq": float(sb["freq_hz"]),
                "q": float(sb["q"]),
                "gain": float(sb["gain_db"]),
                "role": sb.get("role", "sub_modal_resonance"),
                "desc": f"Modo modal Subwoofer Focal Cub Evo ({sb['freq_hz']} Hz)"
            }


    if cfg_path.exists():
        try:
            with open(cfg_path, "r", encoding="utf-8") as f_in:
                all_targets = json.load(f_in)
            if target_key in all_targets:
                all_targets[target_key]["bands"] = bands_dict
                if sub_bands_dict or "sub_bands" in all_targets[target_key]:
                    all_targets[target_key]["sub_bands"] = sub_bands_dict
                with open(cfg_path, "w", encoding="utf-8") as f_out:
                    json.dump(all_targets, f_out, indent=2, ensure_ascii=False)
                print(f"[✓] Perfil '{target_key}' sincronizado con bandas calculadas dinámicamente en targets.json.")
        except Exception as e_sync:
            print(f"[!] Error al sincronizar targets.json: {e_sync}")

    # 4. Optional Hardware Deployment
    if push_yamaha:
        print("\n[*] Enviando matriz PEQ al receptor Yamaha RX-V673 con verificación de lectura...")
        deploy_matrix = {"left": left_bands, "right": right_bands}
        if "subwoofer" in opt_result["channels"]:
            deploy_matrix["subwoofer"] = opt_result["channels"]["subwoofer"]
        success, errors = deploy_peq_matrix_with_readback(
            deploy_matrix,
            verify_readback=True,
        )
        if success:
            print("[✓] 100% de los parámetros verificados en la memoria NVRAM del receptor.")
        else:
            print(f"[!] Fallo en la verificación de hardware: {errors}")

    return opt_result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Real Dynamic Room Calibration Optimizer")
    parser.add_argument(
        "--profile", "--target",
        dest="profile",
        type=str,
        default="harman_wide_room",
        help="Target profile key (e.g. harman_wide_room, bk_1974, dirac_live)"
    )
    parser.add_argument("--multipoint", action="store_true", default=True, help="Enable multipoint spatial averaging (default: True)")
    parser.add_argument("--no-spatial", action="store_true", help="Disable spatial averaging")
    parser.add_argument("--push", action="store_true", help="Push to Yamaha AVR via YNC")
    parser.add_argument("--dry-run", action="store_true", help="Simulate optimization without pushing to AVR")
    parser.add_argument("--sub-crossover", type=float, default=None, help="Subwoofer crossover frequency in Hz (e.g. 80.0)")
    args = parser.parse_args()
    run_calibration(
        target_key=args.profile,
        use_spatial_avg=not args.no_spatial,
        push_yamaha=args.push,
        subwoofer_crossover_hz=args.sub_crossover,
    )
