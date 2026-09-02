import time
#!/usr/bin/env python3
"""
Interactive Multi-Point Spatial Averaging Engine (Dr. Floyd Toole)
Customized for Longitudinally Split Rectangular Rooms (Right: TV/Cinema, Left: Living Area)
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

POINTS_DEF = {
    1: "Punto 1: Sofá Centro (Zona TV / Sweet Spot - Altura Oídos ~95 cm)",
    2: "Punto 2: Sofá Izquierda (Transición hacia Zona de Vida)",
    3: "Punto 3: Sofá Derecha (Cerca de Pared Lateral Derecha)",
    4: "Punto 4: Zona de Vida Centro (Mitad Izquierda - Altura Mesa ~1.15 m)",
    5: "Punto 5: Zona de Vida Fondo (Mitad Izquierda - Altura Persona ~1.35 m)"
}

def capture_point(point_num):
    if point_num not in POINTS_DEF:
        print(f"[!] Número de punto inválido ({point_num}). Debe ser del 1 al 5.")
        return
        
    label = POINTS_DEF[point_num]
    print(f"[*] Iniciando captura para: {label}...")
    
    # Run the acoustic sweep
    p = subprocess.run(["python3", SWEEP_SCRIPT], capture_output=True, text=True)
    if p.returncode != 0:
        print(f"[!] Error ejecutando barrido acústico: {p.stderr}", file=sys.stderr)
        return
        
    data = np.load(f"{DATA_DIR}/medicion_real_calibracion.npz")
    ts_str = time.strftime("%Y%m%d_%H%M%S")
    out_file_ts = f"{DATA_DIR}/medicion_punto_{point_num}_{ts_str}.npz"
    out_file_latest = f"{DATA_DIR}/medicion_punto_{point_num}.npz"
    np.savez(out_file_ts, **data)
    np.savez(out_file_latest, **data)
    print(f"[v] {label} capturado y guardado en:\n  - {out_file_ts}\n  - {out_file_latest}")

def compute_and_save_average():
    print("=== PROCESANDO PROMEDIO ESPACIAL MULTIPUNTO (DR. FLOYD TOOLE) ===")
    
    measurements = []
    for num, label in POINTS_DEF.items():
        fpath = f"{DATA_DIR}/medicion_punto_{num}.npz"
        if os.path.exists(fpath):
            d = np.load(fpath)
            smooth_l = d["smooth_l"] if "smooth_l" in d else d.get("l_smooth")
            smooth_r = d["smooth_r"] if "smooth_r" in d else d.get("r_smooth")
            measurements.append({
                "label": label,
                "freqs": d["freqs"],
                "smooth_l": smooth_l,
                "smooth_r": smooth_r
            })
            
    if not measurements:
        print("[!] No se encontraron puntos medidos (medicion_punto_*.npz).")
        return

    print(f"[*] Promediando {len(measurements)} puntos espaciales...")
    freqs = measurements[0]["freqs"]
    n_meas = len(measurements)
    
    p_l_total = np.zeros_like(freqs, dtype=float)
    p_r_total = np.zeros_like(freqs, dtype=float)
    
    for m in measurements:
        p_l_total += 10.0 ** (m["smooth_l"] / 10.0)
        p_r_total += 10.0 ** (m["smooth_r"] / 10.0)
        
    avg_l = 10.0 * np.log10(p_l_total / float(n_meas) + 1e-12)
    avg_r = 10.0 * np.log10(p_r_total / float(n_meas) + 1e-12)
    
    # Save master spatial average dataset
    ts_str = time.strftime("%Y%m%d_%H%M%S")
    out_npz_ts = f"{DATA_DIR}/medicion_promedio_espacial_{ts_str}.npz"
    out_npz_latest = f"{DATA_DIR}/medicion_promedio_espacial.npz"
    np.savez(out_npz_ts, freqs=freqs, smooth_l=avg_l, smooth_r=avg_r, raw_l=avg_l, raw_r=avg_r)
    np.savez(out_npz_latest, freqs=freqs, smooth_l=avg_l, smooth_r=avg_r, raw_l=avg_l, raw_r=avg_r)
    print(f"[v] Promedio espacial maestro guardado en:\n  - {out_npz_ts}\n  - {out_npz_latest}")
    
    # Generate Plot
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), dpi=140)
    
    colors_pts = ['#90caf9', '#81d4fa', '#80deea', '#a7ffeb', '#b9f6ca']
    
    for i, m in enumerate(measurements):
        ax1.semilogx(freqs, m["smooth_l"], color=colors_pts[i % len(colors_pts)], 
                     linestyle=':', linewidth=1.3, alpha=0.7, label=m["label"].split(':')[0])
        ax2.semilogx(freqs, m["smooth_r"], color=colors_pts[i % len(colors_pts)], 
                     linestyle=':', linewidth=1.3, alpha=0.7, label=m["label"].split(':')[0])
                     
    ax1.semilogx(freqs, avg_l, color='#0d47a1', linewidth=2.6, label='Promedio Espacial RMS (L)')
    ax1.set_title("Canal Izquierdo (Front L) - Promedio Espacial (Zona TV & Zona de Vida)", fontsize=11, fontweight='bold', color='#0d47a1')
    ax1.set_xlabel("Frecuencia (Hz)", fontsize=10)
    ax1.set_ylabel("Magnitud (dB SPL)", fontsize=10)
    ax1.set_xlim(20, 20000)
    ax1.set_ylim(-20, 18)
    ax1.grid(True, which="both", ls=":", alpha=0.6)
    ax1.legend(loc="lower left", fontsize=8.0)
    
    ax2.semilogx(freqs, avg_r, color='#b71c1c', linewidth=2.6, label='Promedio Espacial RMS (R)')
    ax2.set_title("Canal Derecho (Front R - Esquina) - Promedio Espacial (Zona TV & Zona de Vida)", fontsize=11, fontweight='bold', color='#b71c1c')
    ax2.set_xlabel("Frecuencia (Hz)", fontsize=10)
    ax2.set_ylabel("Magnitud (dB SPL)", fontsize=10)
    ax2.set_xlim(20, 20000)
    ax2.set_ylim(-20, 18)
    ax2.grid(True, which="both", ls=":", alpha=0.6)
    ax2.legend(loc="lower left", fontsize=8.0)
    
    plt.tight_layout()
    out_fig_ts = f"{FIG_DIR}/promedio_espacial_multipunto_{ts_str}.png"
    out_fig_latest = f"{FIG_DIR}/promedio_espacial_multipunto.png"
    plt.savefig(out_fig_ts)
    plt.savefig(out_fig_latest)
    plt.close()
    print(f"[v] Gráfica de promedio espacial actualizada en: {out_fig_latest}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multipoint Spatial Averaging Engine")
    parser.add_argument("--point", type=int, choices=[1, 2, 3, 4, 5], help="Capture a specific spatial point (1-5)")
    parser.add_argument("--average", action="store_true", help="Compute spatial average from captured points")
    args = parser.parse_args()
    
    if args.point:
        capture_point(args.point)
        compute_and_save_average()
    elif args.average:
        compute_and_save_average()
    else:
        parser.print_help()
