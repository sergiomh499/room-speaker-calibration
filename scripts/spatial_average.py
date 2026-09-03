#!/usr/bin/env python3
"""
Interactive Multi-Point Spatial Averaging Engine (Dr. Floyd Toole)
Customized for Longitudinally Split Rectangular Rooms (Right: TV/Cinema, Left: Living Area)
"""
import os
import sys
import time
import argparse
import subprocess
import numpy as np
import matplotlib
matplotlib.use('Agg')
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
    
    def professional_psychoacoustic_smooth(freqs, mag_db):
        valid = (freqs >= 20.0) & (freqs <= 20000.0)
        f_val = freqs[valid]
        m_val = mag_db[valid]
        log_f = np.log2(f_val)
        pts_per_oct = 96
        n_pts = int((log_f[-1] - log_f[0]) * pts_per_oct)
        log_grid = np.linspace(log_f[0], log_f[-1], n_pts)
        f_grid = 2.0 ** log_grid
        m_grid = np.interp(log_grid, log_f, m_val)
        
        import scipy.signal
        sigma_oct = (1.0 / 6.0) / (2.0 * np.sqrt(2.0 * np.log(2.0)))
        sigma_pts = sigma_oct * pts_per_oct
        rad = int(np.ceil(3.5 * sigma_pts))
        x_k = np.arange(-rad, rad + 1)
        k_base = np.exp(-0.5 * (x_k / sigma_pts) ** 2)
        k_base /= np.sum(k_base)
        base_smooth = scipy.signal.convolve(m_grid, k_base, mode='same')
        
        diff = m_grid - base_smooth
        m_psycho = np.where(diff < -2.0, base_smooth + 0.35 * diff, m_grid)
        
        oct_frac = np.ones_like(f_grid)
        for i, f in enumerate(f_grid):
            if f <= 100.0:
                oct_frac[i] = 12.0
            elif f <= 1000.0:
                t = (np.log2(f) - np.log2(100.0)) / (np.log2(1000.0) - np.log2(100.0))
                oct_frac[i] = 12.0 * (1.0 - t) + 6.0 * t
            elif f <= 5000.0:
                oct_frac[i] = 6.0
            else:
                t = min(1.0, (np.log2(f) - np.log2(5000.0)) / (np.log2(20000.0) - np.log2(5000.0)))
                oct_frac[i] = 6.0 * (1.0 - t) + 3.0 * t
                
        sigma_pts_arr = ((1.0 / oct_frac) / (2.0 * np.sqrt(2.0 * np.log(2.0)))) * pts_per_oct
        final_smooth = np.zeros_like(m_psycho)
        for i in range(len(m_psycho)):
            sp = sigma_pts_arr[i]
            r = int(np.ceil(3.0 * sp))
            i_min = max(0, i - r)
            i_max = min(len(m_psycho), i + r + 1)
            x = np.arange(i_min - i, i_max - i)
            w = np.exp(-0.5 * (x / sp) ** 2)
            final_smooth[i] = np.sum(m_psycho[i_min:i_max] * w) / np.sum(w)
            
        out = mag_db.copy()
        out[valid] = np.interp(freqs[valid], f_grid, final_smooth)
        return out

    # Apply psychoacoustic smoothing to spatial average
    avg_l_psy = professional_psychoacoustic_smooth(freqs, avg_l)
    avg_r_psy = professional_psychoacoustic_smooth(freqs, avg_r)

    # Save master spatial average dataset
    ts_str = time.strftime("%Y%m%d_%H%M%S")
    out_npz_ts = f"{DATA_DIR}/medicion_promedio_espacial_{ts_str}.npz"
    out_npz_latest = f"{DATA_DIR}/medicion_promedio_espacial.npz"
    np.savez(out_npz_ts, freqs=freqs, smooth_l=avg_l_psy, smooth_r=avg_r_psy, raw_l=avg_l, raw_r=avg_r)
    np.savez(out_npz_latest, freqs=freqs, smooth_l=avg_l_psy, smooth_r=avg_r_psy, raw_l=avg_l, raw_r=avg_r)
    print(f"[v] Promedio espacial maestro guardado en:\n  - {out_npz_ts}\n  - {out_npz_latest}")
    
    # Generate Normalized Plot (Standard Acoustic Engineering: 0 dB @ 1 kHz)
    plt.style.use('dark_background')
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), dpi=140)
    fig.patch.set_facecolor('#0b0f19')
    meas_time_str = time.strftime('%d/%m/%Y %H:%M:%S')
    fig.suptitle(f"Medición Acústica Multipunto Real ({meas_time_str})\n"
                 "Yamaha RX-V673 (Through / Sin Calibrar) + Q Acoustics 3020i — Suavizado Psicoacústico REW",
                 fontsize=13, fontweight='bold', color='#38bdf8', y=0.98)
    
    from matplotlib.ticker import FixedLocator, FixedFormatter
    audio_freqs = [30, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 18000]
    audio_labels = ['30', '50', '100', '200', '500', '1k', '2k', '5k', '10k', '18k']

    for ax in (ax1, ax2):
        ax.set_facecolor('#111827')
        ax.grid(True, which='major', color='#374151', linestyle='-', linewidth=0.75, alpha=0.8)
        ax.grid(True, which='minor', color='#1f2937', linestyle=':', linewidth=0.5, alpha=0.4)
        ax.set_xscale('log')
        ax.set_xlim(25, 18000)
        ax.set_ylim(-18, 12)
        ax.xaxis.set_major_locator(FixedLocator(audio_freqs))
        ax.xaxis.set_major_formatter(FixedFormatter(audio_labels))
        ax.xaxis.set_minor_locator(FixedLocator([]))
        ax.fill_between([25, 18000], -2.5, 2.5, color='#38bdf8', alpha=0.08, label='Tolerancia Nominal (±2.5 dB)')

    colors_pts = ['#64748b', '#94a3b8', '#cbd5e1', '#e2e8f0', '#f8fafc']
    idx_1k = np.argmin(np.abs(freqs - 1000.0))
    
    norm_avg_l = avg_l_psy - avg_l_psy[idx_1k]
    norm_avg_r = avg_r_psy - avg_r_psy[idx_1k]
    
    for i, m in enumerate(measurements):
        i1k_m_l = np.argmin(np.abs(freqs - 1000.0))
        m_l_psy = professional_psychoacoustic_smooth(freqs, m["smooth_l"])
        m_r_psy = professional_psychoacoustic_smooth(freqs, m["smooth_r"])
        pt_l_norm = m_l_psy - m_l_psy[i1k_m_l]
        pt_r_norm = m_r_psy - m_r_psy[i1k_m_l]
        ax1.plot(freqs, pt_l_norm, color=colors_pts[i % len(colors_pts)], 
                 linestyle=':', linewidth=1.0, alpha=0.45, label=f"Punto {i+1}")
        ax2.plot(freqs, pt_r_norm, color=colors_pts[i % len(colors_pts)], 
                 linestyle=':', linewidth=1.0, alpha=0.45, label=f"Punto {i+1}")
                     
    # Plot Spatial Averages
    ax1.plot(freqs, norm_avg_l, color='#10b981', linewidth=2.8, label='Promedio Espacial RMS (5 Pts)')
    ax1.axhline(0, color='gray', linestyle='--', alpha=0.6, lw=1.0)
    ax1.axhline(3, color='#10b981', linestyle=':', alpha=0.4, lw=0.8)
    ax1.axhline(-3, color='#10b981', linestyle=':', alpha=0.4, lw=0.8)
    
    # Peak annotation Front L (Dynamically calculated)
    mask_bass = (freqs >= 35.0) & (freqs <= 250.0)
    indices_bass = np.where(mask_bass)[0]
    idx_peak_l = indices_bass[np.argmax(norm_avg_l[mask_bass])]
    f_peak_l = float(freqs[idx_peak_l])
    peak_val_l = float(norm_avg_l[idx_peak_l])
    ax1.annotate(f'Modo de Sala L\n{f_peak_l:.1f} Hz ({peak_val_l:+.1f} dB)', 
                 xy=(f_peak_l, peak_val_l), xytext=(min(f_peak_l * 1.35, 220.0), peak_val_l + 3.0),
                 arrowprops=dict(facecolor='#ef4444', shrink=0.05, width=1.5, headwidth=6),
                 fontsize=9, fontweight='bold', color='#f87171')
    ax1.set_title("Canal Izquierdo (Front L - Zona Abierta / Sofá)", fontsize=11, fontweight='bold', color='#38bdf8')
    ax1.set_xlabel("Frecuencia (Hz)", fontsize=9, color='#9ca3af')
    ax1.set_ylabel("Magnitud Relativa (dB SPL @ 1 kHz)", fontsize=9, color='#9ca3af')
    ax1.legend(loc="lower left", fontsize=8.2, framealpha=0.92)
    
    ax2.plot(freqs, norm_avg_r, color='#38bdf8', linewidth=2.8, label='Promedio Espacial RMS (5 Pts)')
    ax2.axhline(0, color='gray', linestyle='--', alpha=0.6, lw=1.0)
    ax2.axhline(3, color='#38bdf8', linestyle=':', alpha=0.4, lw=0.8)
    ax2.axhline(-3, color='#38bdf8', linestyle=':', alpha=0.4, lw=0.8)
    
    # Peak/Feature annotation Front R (Dynamically calculated)
    idx_peak_r = indices_bass[np.argmax(norm_avg_r[mask_bass])]
    f_peak_r = float(freqs[idx_peak_r])
    peak_val_r = float(norm_avg_r[idx_peak_r])
    ax2.annotate(f'Resonancia R\n{f_peak_r:.1f} Hz ({peak_val_r:+.1f} dB)', 
                 xy=(f_peak_r, peak_val_r), xytext=(min(f_peak_r * 1.35, 220.0), peak_val_r + 3.5),
                 arrowprops=dict(facecolor='#60a5fa', shrink=0.05, width=1.5, headwidth=6),
                 fontsize=9, fontweight='bold', color='#93c5fd')
    ax2.set_title("Canal Derecho (Front R - Altavoz Reubicado Fuera de Esquina)", fontsize=11, fontweight='bold', color='#38bdf8')
    ax2.set_xlabel("Frecuencia (Hz)", fontsize=9, color='#9ca3af')
    ax2.set_ylabel("Magnitud Relativa (dB SPL @ 1 kHz)", fontsize=9, color='#9ca3af')
    ax2.legend(loc="lower left", fontsize=8.2, framealpha=0.92)
    
    plt.tight_layout()
    out_fig_ts = f"{FIG_DIR}/promedio_espacial_multipunto_{ts_str}.png"
    out_fig_latest = f"{FIG_DIR}/promedio_espacial_multipunto.png"
    plt.savefig(out_fig_ts, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.savefig(out_fig_latest, facecolor=fig.get_facecolor(), edgecolor='none')
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
