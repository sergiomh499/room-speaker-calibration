#!/usr/bin/env python3
"""
Multi-Calibration Capture and Comparative Engine
Captures real-world acoustic sweeps for YPAO Flat, YPAO Natural, Through (Off),
Harman Neutral, and Harman Impact, storing each dataset and generating comparative graphs.
"""

import os
import sys
import argparse
import subprocess
import numpy as np
import matplotlib.pyplot as plt

REPO_DIR = "/home/sergio/room-speaker-calibration"
DATA_DIR = f"{REPO_DIR}/data"
FIG_DIR = f"{REPO_DIR}/figures"
SWEEP_SCRIPT = f"{REPO_DIR}/scripts/01_measure_sweep.py"

MODES = {
    "through": "Through (Sin Ecualizar)",
    "ypao_flat": "YPAO Flat (Automático)",
    "ypao_natural": "YPAO Natural (Roll-off)",
    "harman_neutral": "Harman Neutral (Equilibrado)",
    "harman_impact": "Harman Impact (Definitivo)"
}

COLORS = {
    "through": "#d32f2f",        # Red
    "ypao_flat": "#f57c00",      # Orange
    "ypao_natural": "#fbc02d",   # Yellow/Gold
    "harman_neutral": "#0288d1", # Blue
    "harman_impact": "#2e7d32"   # Green
}

LINESTYLES = {
    "through": "--",
    "ypao_flat": "-.",
    "ypao_natural": ":",
    "harman_neutral": "-.",
    "harman_impact": "-"
}

def capture_mode(mode_key):
    label = MODES.get(mode_key, mode_key.upper())
    print(f"[*] Iniciando captura acústica para el modo: {label}...")
    
    # Run the sweep script to capture fresh Left and Right sweeps
    p = subprocess.run(["python3", SWEEP_SCRIPT], capture_output=True, text=True)
    if p.returncode != 0:
        print(f"[!] Error ejecutando barrido acústico: {p.stderr}", file=sys.stderr)
        sys.exit(1)
        
    # Load current sweep data
    data = np.load(f"{DATA_DIR}/medicion_real_calibracion.npz")
    
    # Save a dedicated copy for this mode
    out_file = f"{DATA_DIR}/medicion_{mode_key}.npz"
    np.savez(out_file, **data)
    print(f"[v] Modo {label} guardado exitosamente en: {out_file}")

def plot_all_modes_comparison():
    print("[*] Generando comparativa acústica completa de todos los modos disponibles...")
    available_data = {}
    
    for k, label in MODES.items():
        fpath = f"{DATA_DIR}/medicion_{k}.npz"
        if os.path.exists(fpath):
            data = np.load(fpath)
            smooth_l = data["smooth_l"] if "smooth_l" in data else data.get("l_smooth")
            smooth_r = data["smooth_r"] if "smooth_r" in data else data.get("r_smooth")
            available_data[k] = {
                "label": label,
                "freqs": data["freqs"],
                "l_smooth": smooth_l,
                "r_smooth": smooth_r
            }
            
    if not available_data:
        print("[!] No hay mediciones disponibles para comparar.")
        return

    plt.style.use('seaborn-v0_8-whitegrid')
    fig, axs = plt.subplots(2, 2, figsize=(16, 10), dpi=140)
    
    # 1. Front Left (All Modes)
    ax = axs[0, 0]
    for k, d in available_data.items():
        ax.semilogx(d["freqs"], d["l_smooth"], label=d["label"], color=COLORS.get(k, '#333333'),
                     linestyle=LINESTYLES.get(k, '-'), linewidth=2.4 if k == 'harman_impact' else (1.8 if 'harman' in k else 1.4), alpha=0.95)
    ax.set_title("Canal Izquierdo (Front L) - Comparativa Multimodo", fontsize=12, fontweight='bold', color='#0d47a1')
    ax.set_xlabel("Frecuencia (Hz)", fontsize=10)
    ax.set_ylabel("Magnitud Relativa (dB SPL)", fontsize=10)
    ax.set_xlim(20, 20000)
    ax.set_ylim(-20, 18)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(loc="lower left", fontsize=8.5, framealpha=0.95)
    
    # 2. Front Right (All Modes)
    ax = axs[0, 1]
    for k, d in available_data.items():
        ax.semilogx(d["freqs"], d["r_smooth"], label=d["label"], color=COLORS.get(k, '#333333'),
                     linestyle=LINESTYLES.get(k, '-'), linewidth=2.4 if k == 'harman_impact' else (1.8 if 'harman' in k else 1.4), alpha=0.95)
    ax.set_title("Canal Derecho (Front R - Esquina) - Comparativa Multimodo", fontsize=12, fontweight='bold', color='#0d47a1')
    ax.set_xlabel("Frecuencia (Hz)", fontsize=10)
    ax.set_ylabel("Magnitud Relativa (dB SPL)", fontsize=10)
    ax.set_xlim(20, 20000)
    ax.set_ylim(-20, 18)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(loc="lower left", fontsize=8.5, framealpha=0.95)
    
    # 3. Stereo Imbalance (|L - R|)
    ax = axs[1, 0]
    for k, d in available_data.items():
        imb = np.abs(d["l_smooth"] - d["r_smooth"])
        mean_imb = np.mean(imb[(d["freqs"] >= 100) & (d["freqs"] <= 10000)])
        ax.semilogx(d["freqs"], imb, label=f"{d['label']} (Media: {mean_imb:.2f} dB)", 
                     color=COLORS.get(k, '#333333'), linestyle=LINESTYLES.get(k, '-'), 
                     linewidth=2.4 if k == 'harman_impact' else (1.8 if 'harman' in k else 1.4), alpha=0.9)
    ax.set_title("Simetría Estéreo y Desbalance (|L - R|)", fontsize=12, fontweight='bold', color='#0d47a1')
    ax.set_xlabel("Frecuencia (Hz)", fontsize=10)
    ax.set_ylabel("Diferencia Absoluta (dB)", fontsize=10)
    ax.set_xlim(20, 20000)
    ax.set_ylim(0, 15)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(loc="upper right", fontsize=8.5, framealpha=0.95)
    
    # 4. Zoom Graves & Control de Modos en Esquina (30 Hz - 350 Hz)
    ax = axs[1, 1]
    for k, d in available_data.items():
        mask = (d["freqs"] >= 30) & (d["freqs"] <= 350)
        ax.semilogx(d["freqs"][mask], d["r_smooth"][mask], label=d["label"], 
                     color=COLORS.get(k, '#333333'), linestyle=LINESTYLES.get(k, '-'), 
                     linewidth=2.4 if k == 'harman_impact' else (1.8 if 'harman' in k else 1.4), alpha=0.95)
    ax.set_title("Detalle Modos de Sala en Esquina (30 Hz - 350 Hz)", fontsize=12, fontweight='bold', color='#b71c1c')
    ax.set_xlabel("Frecuencia (Hz)", fontsize=10)
    ax.set_ylabel("Magnitud Relativa (dB SPL)", fontsize=10)
    ax.set_xlim(30, 350)
    ax.set_ylim(-15, 18)
    ax.grid(True, which="both", ls=":", alpha=0.6)
    ax.legend(loc="lower left", fontsize=8.5, framealpha=0.95)
    
    plt.tight_layout()
    out_fig = f"{FIG_DIR}/gran_comparativa_multimodo.png"
    plt.savefig(out_fig)
    plt.close()
    print(f"[v] Gráfica comparativa guardada en: {out_fig}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Calibration Acoustic Capture Engine")
    parser.add_argument("--mode", type=str, choices=list(MODES.keys()), help="Capture a specific mode")
    parser.add_argument("--compare", action="store_true", help="Generate multi-mode comparison figure")
    args = parser.parse_args()
    
    if args.mode:
        capture_mode(args.mode)
        plot_all_modes_comparison()
    elif args.compare:
        plot_all_modes_comparison()
    else:
        parser.print_help()
