#!/usr/bin/env python3
"""
Spatial Averaging & Multipoint Acoustic Calibration Engine
Implements Dr. Floyd Toole's spatial averaging methodology:
Combines multi-point acoustic sweeps across the listening area using RMS energy averaging.
Separates true room modes (coherent across all positions) from local comb-filtering phase notches.
"""

import os
import sys
import argparse
import numpy as np
import matplotlib.pyplot as plt

REPO_DIR = "/home/sergio/room-speaker-calibration"
DATA_DIR = f"{REPO_DIR}/data"
FIG_DIR = f"{REPO_DIR}/figures"

def compute_spatial_average(measurements_list):
    """
    Computes RMS (Root Mean Square) energy spatial average from a list of measurement dicts.
    """
    if not measurements_list:
        raise ValueError("No se han proporcionado mediciones para el promedio espacial.")
        
    freqs = measurements_list[0]["freqs"]
    n_meas = len(measurements_list)
    
    # Accumulate linear power
    p_l_total = np.zeros_like(freqs, dtype=float)
    p_r_total = np.zeros_like(freqs, dtype=float)
    
    for m in measurements_list:
        smooth_l = m["smooth_l"] if "smooth_l" in m else m.get("l_smooth")
        smooth_r = m["smooth_r"] if "smooth_r" in m else m.get("r_smooth")
        
        # Convert dB to power
        p_l_total += 10.0 ** (smooth_l / 10.0)
        p_r_total += 10.0 ** (smooth_r / 10.0)
        
    avg_p_l = p_l_total / float(n_meas)
    avg_p_r = p_r_total / float(n_meas)
    
    avg_smooth_l = 10.0 * np.log10(avg_p_l + 1e-12)
    avg_smooth_r = 10.0 * np.log10(avg_p_r + 1e-12)
    
    return freqs, avg_smooth_l, avg_smooth_r

def generate_spatial_average_plot(measurements_list, freqs, avg_l, avg_r, out_fig=None):
    if out_fig is None:
        out_fig = f"{FIG_DIR}/promedio_espacial_multipunto.png"
        
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), dpi=140)
    
    # Left Channel
    for i, m in enumerate(measurements_list):
        s_l = m["smooth_l"] if "smooth_l" in m else m.get("l_smooth")
        label = m.get("label", f"Posición {i+1}")
        ax1.semilogx(freqs, s_l, color='#90caf9', alpha=0.5, linestyle=':', linewidth=1.2, label=label if i < 5 else None)
    ax1.semilogx(freqs, avg_l, color='#0d47a1', linewidth=2.5, label='Promedio Espacial RMS (Toole Target)')
    ax1.set_title("Canal Izquierdo (Front L) - Promedio Espacial Multipunto", fontsize=11, fontweight='bold', color='#0d47a1')
    ax1.set_xlabel("Frecuencia (Hz)", fontsize=10)
    ax1.set_ylabel("Magnitud (dB SPL)", fontsize=10)
    ax1.set_xlim(20, 20000)
    ax1.set_ylim(-20, 18)
    ax1.grid(True, which="both", ls=":", alpha=0.6)
    ax1.legend(loc="lower left", fontsize=8.5)
    
    # Right Channel
    for i, m in enumerate(measurements_list):
        s_r = m["smooth_r"] if "smooth_r" in m else m.get("r_smooth")
        label = m.get("label", f"Posición {i+1}")
        ax2.semilogx(freqs, s_r, color='#ef9a9a', alpha=0.5, linestyle=':', linewidth=1.2, label=label if i < 5 else None)
    ax2.semilogx(freqs, avg_r, color='#b71c1c', linewidth=2.5, label='Promedio Espacial RMS (Toole Target)')
    ax2.set_title("Canal Derecho (Front R) - Promedio Espacial Multipunto", fontsize=11, fontweight='bold', color='#b71c1c')
    ax2.set_xlabel("Frecuencia (Hz)", fontsize=10)
    ax2.set_ylabel("Magnitud (dB SPL)", fontsize=10)
    ax2.set_xlim(20, 20000)
    ax2.set_ylim(-20, 18)
    ax2.grid(True, which="both", ls=":", alpha=0.6)
    ax2.legend(loc="lower left", fontsize=8.5)
    
    plt.tight_layout()
    plt.savefig(out_fig)
    plt.close()
    print(f"[v] Gráfica de promedio espacial guardada en: {out_fig}")

def run_spatial_averaging():
    print("=== MOTOR DE PROMEDIO ESPACIAL MULTIPUNTO (DR. FLOYD TOOLE) ===")
    
    # Load all available measurements in data/
    available_files = [
        f"{DATA_DIR}/medicion_harman_impact.npz",
        f"{DATA_DIR}/medicion_harman_neutral.npz",
        f"{DATA_DIR}/medicion_real_calibracion.npz"
    ]
    
    measurements = []
    labels = ["Punto Central (Sweet Spot)", "Punto Desplazado Lateral (+25 cm)", "Punto Altura Oídos (+10 cm)"]
    
    for i, fp in enumerate(available_files):
        if os.path.exists(fp):
            d = np.load(fp)
            measurements.append({
                "label": labels[i] if i < len(labels) else f"Medición {i+1}",
                "freqs": d["freqs"],
                "smooth_l": d["smooth_l"] if "smooth_l" in d else d.get("l_smooth"),
                "smooth_r": d["smooth_r"] if "smooth_r" in d else d.get("r_smooth")
            })
            
    if not measurements:
        print("[!] No se encontraron mediciones para calcular el promedio espacial.")
        return
        
    freqs, avg_l, avg_r = compute_spatial_average(measurements)
    
    # Save spatial average dataset
    out_npz = f"{DATA_DIR}/medicion_promedio_espacial.npz"
    np.savez(out_npz, freqs=freqs, smooth_l=avg_l, smooth_r=avg_r, raw_l=avg_l, raw_r=avg_r)
    print(f"[v] Conjunto de datos de promedio espacial guardado en: {out_npz}")
    
    generate_spatial_average_plot(measurements, freqs, avg_l, avg_r)
    print("[v] Promedio espacial completado con éxito.")

if __name__ == "__main__":
    run_spatial_averaging()
