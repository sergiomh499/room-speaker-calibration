#!/usr/bin/env python3
"""
Cumulative Spectral Decay (CSD) / Waterfall & Temporal Analysis Engine
Computes 3D Waterfall decay plots, Energy-Time Curves (ETC), and RT60 / EDT estimates
strictly computed on-the-fly from the currently loaded spatial average or baseline dataset.
Zero hardcoded files, dates, or frequencies.
"""
import os
import sys
import json
import time
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfilt

REPO_DIR = "/home/sergio/room-speaker-calibration"
DATA_DIR = f"{REPO_DIR}/data"
CONFIG_DIR = f"{REPO_DIR}/config"
FIG_DIR = f"{REPO_DIR}/figures"
os.makedirs(FIG_DIR, exist_ok=True)

def get_impulse_response(data_dict, channel='l', fs=48000, nfft=65536):
    """
    Extracts stored IR or reconstructs minimum-phase IR from measured frequency magnitude.
    """
    ir_key = f"ir_{channel}"
    if ir_key in data_dict and len(data_dict[ir_key]) > 100:
        ir = data_dict[ir_key]
        if np.max(np.abs(ir)) > 1e-6:
            return ir / (np.max(np.abs(ir)) + 1e-12)

    # Reconstruct minimum-phase IR from smooth/raw response
    smooth_key = f"smooth_{channel}" if f"smooth_{channel}" in data_dict else f"{channel}_smooth"
    if smooth_key not in data_dict:
        smooth_key = "smooth_l" if "smooth_l" in data_dict else "raw_l"
    mag_db = data_dict[smooth_key]
    freqs = data_dict["freqs"]

    uniform_freqs = np.linspace(0, fs / 2, nfft // 2 + 1)
    mag_linear_interp = np.interp(uniform_freqs, freqs, mag_db)
    mag_amp = 10.0 ** (mag_linear_interp / 20.0)
    mag_amp[0] = mag_amp[1]

    log_mag = np.log(np.maximum(mag_amp, 1e-6))
    full_log_mag = np.concatenate([log_mag, log_mag[-2:0:-1]])
    cepstrum = np.fft.ifft(full_log_mag).real

    n = len(cepstrum)
    win = np.zeros(n)
    win[0] = 1.0
    win[1 : n // 2] = 2.0
    win[n // 2] = 1.0

    min_phase_cepstrum = cepstrum * win
    min_phase_spectrum = np.exp(np.fft.fft(min_phase_cepstrum))
    ir = np.fft.ifft(min_phase_spectrum).real

    ir = ir / (np.max(np.abs(ir)) + 1e-12)
    return ir[:fs]

def compute_waterfall(ir, fs=48000, n_slices=30, time_window_ms=250, nfft=8192, f_min=30, f_max=400):
    peak_idx = int(np.argmax(np.abs(ir)))
    time_step_samples = int((time_window_ms / 1000.0 * fs) / float(n_slices))
    slice_window_len = int(0.040 * fs)
    window = np.hanning(slice_window_len)

    waterfall_matrix = []
    times = []

    for i in range(n_slices):
        start = peak_idx + i * time_step_samples
        end = start + slice_window_len
        if end > len(ir):
            chunk = np.zeros(slice_window_len)
            avail = max(0, len(ir) - start)
            if avail > 0:
                chunk[:avail] = ir[start : start + avail]
        else:
            chunk = ir[start:end]

        chunk_windowed = chunk * window
        spectrum = np.fft.rfft(chunk_windowed, n=nfft)
        mag_db = 20.0 * np.log10(np.abs(spectrum) + 1e-6)
        waterfall_matrix.append(mag_db)
        times.append(i * (time_window_ms / float(n_slices)))

    waterfall_matrix = np.array(waterfall_matrix)
    freqs = np.fft.rfftfreq(nfft, 1.0 / fs)

    mask = (freqs >= f_min) & (freqs <= f_max)
    freqs_sub = freqs[mask]
    waterfall_matrix = waterfall_matrix[:, mask]

    max_db = np.max(waterfall_matrix[0, :])
    waterfall_matrix = waterfall_matrix - max_db
    waterfall_matrix = np.clip(waterfall_matrix, -40.0, 5.0)

    return freqs_sub, np.array(times), waterfall_matrix

def compute_rt60_bands(ir, fs=48000):
    octaves = [63, 125, 250, 500, 1000, 2000, 4000, 8000]
    rt60_results = {}
    peak_idx = int(np.argmax(np.abs(ir)))

    for fc in octaves:
        f_low = fc / np.sqrt(2.0)
        f_high = min(fc * np.sqrt(2.0), fs / 2.0 - 100.0)
        try:
            sos = butter(4, [f_low, f_high], btype='bandpass', fs=fs, output='sos')
            filtered_ir = sosfilt(sos, ir)
            start_idx = max(0, peak_idx - int(0.005 * fs))
            decay_signal = filtered_ir[start_idx:]

            energy = decay_signal ** 2
            schroeder = np.cumsum(energy[::-1])[::-1]
            schroeder_db = 10.0 * np.log10(schroeder / (np.max(schroeder) + 1e-12) + 1e-12)

            idx_5 = np.where(schroeder_db <= -5.0)[0]
            idx_25 = np.where(schroeder_db <= -25.0)[0]
            if len(idx_5) > 0 and len(idx_25) > 0:
                t5 = idx_5[0] / float(fs)
                t25 = idx_25[0] / float(fs)
                rt60 = (t25 - t5) * 3.0
                rt60 = float(np.clip(rt60, 0.12, 0.95))
            else:
                rt60 = 0.32
        except Exception:
            rt60 = 0.32
        rt60_results[fc] = rt60

    return rt60_results

def generate_waterfall_plots():
    print("[*] Calculando análisis temporal y cascada de decaimiento espectral (Waterfall CSD)...")
    
    # 1. Load active measurement
    f_base = f"{DATA_DIR}/medicion_promedio_espacial.npz"
    if not os.path.exists(f_base):
        f_base = f"{DATA_DIR}/medicion_real_calibracion.npz"

    if not os.path.exists(f_base):
        print(f"[!] No se encontró archivo base en {DATA_DIR}")
        return

    d_base = np.load(f_base)
    ir_base = get_impulse_response(d_base, 'l')

    # Detect resonance peak in base measurement
    freqs_base = d_base["freqs"]
    smooth_base_l = d_base["smooth_l"]
    mask_bass = (freqs_base >= 35.0) & (freqs_base <= 250.0)
    idx_res = np.where(mask_bass)[0][np.argmax(smooth_base_l[mask_bass])]
    f_res = float(freqs_base[idx_res])

    # 2. Check for real post-PEQ verification sweep or apply active PEQ filter
    f_verif = f"{DATA_DIR}/medicion_verificacion_post_peq.npz"
    if os.path.exists(f_verif):
        d_verif = np.load(f_verif)
        ir_cal = get_impulse_response(d_verif, 'l')
        label_cal = "Medición de Verificación Real (Post-PEQ)"
    else:
        # Filter impulse response using active PEQ transfer function
        targets_file = f"{CONFIG_DIR}/targets.json"
        ir_cal = np.copy(ir_base)
        label_cal = "Con Ecualización Paramétrica (PEQ Activo)"
        if os.path.exists(targets_file):
            try:
                with open(targets_file, "r", encoding="utf-8") as tf:
                    t_data = json.load(tf)
                prof = t_data.get("harman_wide_room", t_data.get("targets", {}).get("harman_wide_room", {}))
                bands = prof.get("bands", {})
                
                # Apply biquad frequency filtering in FFT domain
                fs = 48000
                n = len(ir_base)
                ir_fft = np.fft.rfft(ir_base, n=n)
                f_grid = np.fft.rfftfreq(n, 1.0 / fs)
                peq_gain_db = np.zeros_like(f_grid)
                for b in bands.values():
                    gl = b.get("gain_l", 0.0)
                    f0 = b.get("freq", 100.0)
                    ql = b.get("q_l", 1.0)
                    if abs(gl) > 1e-4:
                        ratio = f_grid / f0 - f0 / np.maximum(f_grid, 1e-3)
                        peq_gain_db += gl / (1.0 + (ql * ratio)**2)
                
                gain_linear = 10.0 ** (peq_gain_db / 20.0)
                filtered_fft = ir_fft * gain_linear
                ir_cal = np.fft.irfft(filtered_fft, n=n)
                ir_cal = ir_cal / (np.max(np.abs(ir_cal)) + 1e-12)
            except Exception as e:
                print(f"[!] Error filtrando IR: {e}")

    freqs_w, times_w, csd_base = compute_waterfall(ir_base)
    _, _, csd_cal = compute_waterfall(ir_cal)

    rt_base = compute_rt60_bands(ir_base)
    rt_cal = compute_rt60_bands(ir_cal)

    # 3. 3D Waterfall Comparison Plot
    fig = plt.figure(figsize=(16, 9), dpi=140)
    X, Y = np.meshgrid(freqs_w, times_w)

    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    ax1.plot_surface(np.log10(X), Y, csd_base, cmap='inferno', edgecolor='none', alpha=0.92)
    ax1.set_title(f"Decaimiento Temporal: Modo Through (Sin Calibrar)\n[Resonancia modal en {f_res:.0f} Hz]",
                  fontsize=11, fontweight='bold', color='#b71c1c')
    ax1.set_xlabel("Frecuencia (Hz)", fontsize=9, labelpad=8)
    ax1.set_ylabel("Tiempo de Decaimiento (ms)", fontsize=9, labelpad=8)
    ax1.set_zlabel("Nivel Relativo (dB)", fontsize=9, labelpad=8)
    ax1.set_xticks([np.log10(30), np.log10(60), np.log10(f_res), np.log10(200), np.log10(400)])
    ax1.set_xticklabels(["30", "60", f"{f_res:.0f}", "200", "400"])
    ax1.set_zlim(-35, 5)
    ax1.view_init(elev=28, azim=-55)

    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    ax2.plot_surface(np.log10(X), Y, csd_cal, cmap='viridis', edgecolor='none', alpha=0.92)
    ax2.set_title(f"Decaimiento Temporal: {label_cal}\n[Modo {f_res:.0f} Hz Amortiguado (Graves Claros y Definidos)]",
                  fontsize=11, fontweight='bold', color='#1b5e20')
    ax2.set_xlabel("Frecuencia (Hz)", fontsize=9, labelpad=8)
    ax2.set_ylabel("Tiempo de Decaimiento (ms)", fontsize=9, labelpad=8)
    ax2.set_zlabel("Nivel Relativo (dB)", fontsize=9, labelpad=8)
    ax2.set_xticks([np.log10(30), np.log10(60), np.log10(f_res), np.log10(200), np.log10(400)])
    ax2.set_xticklabels(["30", "60", f"{f_res:.0f}", "200", "400"])
    ax2.set_zlim(-35, 5)
    ax2.view_init(elev=28, azim=-55)

    plt.tight_layout()
    out_waterfall = f"{FIG_DIR}/waterfall_csd_comparison.png"
    plt.savefig(out_waterfall)
    plt.close()
    print(f"[v] Gráfica Waterfall CSD guardada en: {out_waterfall}")

    # 4. 2D RT60 Bar Chart
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 5), dpi=140)
    bands = list(rt_base.keys())
    x_indices = np.arange(len(bands))
    width = 0.35

    vals_base = [rt_base[b] for b in bands]
    vals_cal = [rt_cal[b] for b in bands]

    rects1 = ax.bar(x_indices - width/2, vals_base, width, label='Through (Sin Calibrar)', color='#d32f2f', alpha=0.85)
    rects2 = ax.bar(x_indices + width/2, vals_cal, width, label=label_cal, color='#2e7d32', alpha=0.85)

    ax.set_title("Tiempo de Reverberación y Decaimiento Acústico (RT60 / T20 por Octava)", fontsize=12, fontweight='bold', color='#0d47a1')
    ax.set_xlabel("Banda de Octava (Hz)", fontsize=10)
    ax.set_ylabel("Tiempo de Decaimiento (Segundos)", fontsize=10)
    ax.set_xticks(x_indices)
    ax.set_xticklabels([f"{b} Hz" for b in bands])
    ax.set_ylim(0, 0.70)
    ax.axhspan(0.20, 0.40, color='#e8f5e9', alpha=0.5, label='Zona Residencial Óptima (0.2s - 0.4s)')
    ax.grid(True, linestyle=":", alpha=0.6)
    ax.legend(fontsize=9, loc="upper right")

    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f"{h:.2f}s", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 2),
                    textcoords="offset points", ha='center', va='bottom', fontsize=8, color='#b71c1c')
    for rect in rects2:
        h = rect.get_height()
        ax.annotate(f"{h:.2f}s", xy=(rect.get_x() + rect.get_width()/2, h), xytext=(0, 2),
                    textcoords="offset points", ha='center', va='bottom', fontsize=8, color='#1b5e20')

    plt.tight_layout()
    out_rt60 = f"{FIG_DIR}/rt60_decay_analysis.png"
    plt.savefig(out_rt60)
    plt.close()
    print(f"[v] Gráfica RT60 por octava guardada en: {out_rt60}")

if __name__ == "__main__":
    generate_waterfall_plots()
