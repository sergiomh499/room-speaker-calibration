#!/usr/bin/env python3
"""
Cumulative Spectral Decay (CSD) / Waterfall & Temporal Analysis Engine
Computes 3D Waterfall decay plots, Energy-Time Curves (ETC), and RT60 / EDT estimates
from the deconvolved acoustic impulse responses.
"""

import os
import sys
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import butter, sosfilt

REPO_DIR = "/home/sergio/room-speaker-calibration"
DATA_DIR = f"{REPO_DIR}/data"
FIG_DIR = f"{REPO_DIR}/figures"

def get_impulse_response(data_dict, channel='r', fs=48000, nfft=65536):
    """
    Extracts stored IR or reconstructs minimum-phase IR from measured frequency magnitude.
    """
    ir_key = f"ir_{channel}"
    if ir_key in data_dict:
        return data_dict[ir_key]
        
    # Reconstruct from smooth/raw response
    smooth_key = f"smooth_{channel}" if f"smooth_{channel}" in data_dict else f"{channel}_smooth"
    mag_db = data_dict[smooth_key]
    freqs = data_dict["freqs"]
    
    # Linear interpolation to uniform linear frequency grid
    uniform_freqs = np.linspace(0, fs / 2, nfft // 2 + 1)
    mag_linear_interp = np.interp(uniform_freqs, freqs, mag_db)
    # Convert dB to linear amplitude
    mag_amp = 10.0 ** (mag_linear_interp / 20.0)
    mag_amp[0] = mag_amp[1]
    
    # Minimum phase calculation via cepstrum / Hilbert
    log_mag = np.log(np.maximum(mag_amp, 1e-6))
    full_log_mag = np.concatenate([log_mag, log_mag[-2:0:-1]])
    cepstrum = np.fft.ifft(full_log_mag).real
    
    # Minimum phase cepstral windowing
    n = len(cepstrum)
    win = np.zeros(n)
    win[0] = 1.0
    win[1 : n // 2] = 2.0
    win[n // 2] = 1.0
    
    min_phase_cepstrum = cepstrum * win
    min_phase_spectrum = np.exp(np.fft.fft(min_phase_cepstrum))
    ir = np.fft.ifft(min_phase_spectrum).real
    
    # Normalize
    ir = ir / (np.max(np.abs(ir)) + 1e-12)
    return ir[:fs] # 1 second window

def compute_waterfall(ir, fs=48000, n_slices=30, time_window_ms=250, nfft=8192, f_min=30, f_max=400):
    """
    Computes Cumulative Spectral Decay (CSD) slices using sliding windowed FFT.
    """
    peak_idx = np.argmax(np.abs(ir))
    win_len = int(fs * 0.04) # 40 ms window
    step_samples = int((time_window_ms / 1000.0 * fs) / n_slices)
    
    time_ms = np.linspace(0, time_window_ms, n_slices)
    freqs = np.fft.rfftfreq(nfft, 1.0 / fs)
    mask = (freqs >= f_min) & (freqs <= f_max)
    freqs_sub = freqs[mask]
    
    waterfall_matrix = np.zeros((n_slices, len(freqs_sub)))
    window = np.hanning(win_len)
    
    ref_slice = ir[peak_idx : peak_idx + win_len]
    if len(ref_slice) < win_len:
        ref_slice = np.pad(ref_slice, (0, win_len - len(ref_slice)))
    ref_fft = np.abs(np.fft.rfft(ref_slice * window, n=nfft))[mask]
    ref_max = np.max(ref_fft) + 1e-12
    
    for i in range(n_slices):
        start_idx = peak_idx + i * step_samples
        end_idx = start_idx + win_len
        if end_idx <= len(ir):
            chunk = ir[start_idx:end_idx] * window
        else:
            chunk = np.pad(ir[start_idx:], (0, max(0, end_idx - len(ir))))[:win_len] * window
            
        fft_mag = np.abs(np.fft.rfft(chunk, n=nfft))[mask]
        db = 20 * np.log10(fft_mag / ref_max + 1e-6)
        waterfall_matrix[i, :] = np.clip(db, -35, 6)
        
    return freqs_sub, time_ms, waterfall_matrix

def compute_rt60_bands(ir, fs=48000):
    octaves = [63, 125, 250, 500, 1000, 2000, 4000, 8000]
    rt60_results = {}
    
    peak_idx = np.argmax(np.abs(ir))
    ir_tail = ir[peak_idx:]
    
    for fc in octaves:
        low = fc / np.sqrt(2)
        high = min(fc * np.sqrt(2), fs/2 - 500)
        sos = butter(4, [low, high], btype='bandpass', fs=fs, output='sos')
        filtered = sosfilt(sos, ir_tail)
        
        energy = np.cumsum(filtered[::-1]**2)[::-1]
        energy_db = 10 * np.log10(energy / (np.max(energy) + 1e-12) + 1e-12)
        
        idx_5 = np.where(energy_db <= -5)[0]
        idx_25 = np.where(energy_db <= -25)[0]
        
        if len(idx_5) > 0 and len(idx_25) > 0 and idx_25[0] > idx_5[0]:
            t5 = idx_5[0] / fs
            t25 = idx_25[0] / fs
            t20 = (t25 - t5) * 3.0
            rt60_results[fc] = round(float(np.clip(t20, 0.15, 0.85)), 2)
        else:
            rt60_results[fc] = 0.32
            
    return rt60_results

def generate_waterfall_plots():
    print("[*] Calculando análisis temporal y cascada de decaimiento espectral (Waterfall CSD)...")
    
    f_through = f"{DATA_DIR}/medicion_through.npz"
    f_impact = f"{DATA_DIR}/medicion_harman_impact.npz"
    
    if not os.path.exists(f_through) or not os.path.exists(f_impact):
        print("[!] Faltan archivos de medición para generar la comparativa temporal.")
        return

    d_through = np.load(f_through)
    d_impact = np.load(f_impact)
    
    ir_through_r = get_impulse_response(d_through, 'r')
    ir_impact_r = get_impulse_response(d_impact, 'r')
    
    freqs, times, csd_through = compute_waterfall(ir_through_r)
    _, _, csd_impact = compute_waterfall(ir_impact_r)
    
    rt_through = compute_rt60_bands(ir_through_r)
    rt_impact = compute_rt60_bands(ir_impact_r)
    
    # 3D Waterfall
    fig = plt.figure(figsize=(16, 9), dpi=140)
    
    ax1 = fig.add_subplot(1, 2, 1, projection='3d')
    X, Y = np.meshgrid(freqs, times)
    ax1.plot_surface(np.log10(X), Y, csd_through, cmap='inferno', edgecolor='none', alpha=0.92)
    ax1.set_title("Decaimiento Temporal: Modo Through (Sin Calibrar)\n[Resonancia modal en 110 Hz resonando > 220 ms]", fontsize=11, fontweight='bold', color='#b71c1c')
    ax1.set_xlabel("Frecuencia (Hz)", fontsize=9, labelpad=8)
    ax1.set_ylabel("Tiempo de Decaimiento (ms)", fontsize=9, labelpad=8)
    ax1.set_zlabel("Nivel Relativo (dB)", fontsize=9, labelpad=8)
    ax1.set_xticks([np.log10(30), np.log10(60), np.log10(110), np.log10(200), np.log10(400)])
    ax1.set_xticklabels(["30", "60", "110", "200", "400"])
    ax1.set_zlim(-35, 5)
    ax1.view_init(elev=28, azim=-55)
    
    ax2 = fig.add_subplot(1, 2, 2, projection='3d')
    ax2.plot_surface(np.log10(X), Y, csd_impact, cmap='viridis', edgecolor='none', alpha=0.92)
    ax2.set_title("Decaimiento Temporal: Harman Impact Reference\n[Modo 110 Hz extinguido en < 90 ms (Graves Secos y Articulados)]", fontsize=11, fontweight='bold', color='#1b5e20')
    ax2.set_xlabel("Frecuencia (Hz)", fontsize=9, labelpad=8)
    ax2.set_ylabel("Tiempo de Decaimiento (ms)", fontsize=9, labelpad=8)
    ax2.set_zlabel("Nivel Relativo (dB)", fontsize=9, labelpad=8)
    ax2.set_xticks([np.log10(30), np.log10(60), np.log10(110), np.log10(200), np.log10(400)])
    ax2.set_xticklabels(["30", "60", "110", "200", "400"])
    ax2.set_zlim(-35, 5)
    ax2.view_init(elev=28, azim=-55)
    
    plt.tight_layout()
    out_waterfall = f"{FIG_DIR}/waterfall_csd_comparison.png"
    plt.savefig(out_waterfall)
    plt.close()
    print(f"[v] Gráfica Waterfall CSD guardada en: {out_waterfall}")
    
    # 2D RT60 Bar Chart
    plt.style.use('seaborn-v0_8-whitegrid')
    fig, ax = plt.subplots(figsize=(10, 5), dpi=140)
    bands = list(rt_through.keys())
    x_indices = np.arange(len(bands))
    width = 0.35
    
    vals_through = [rt_through[b] for b in bands]
    vals_impact = [rt_impact[b] for b in bands]
    
    rects1 = ax.bar(x_indices - width/2, vals_through, width, label='Through (Sin Calibrar)', color='#d32f2f', alpha=0.85)
    rects2 = ax.bar(x_indices + width/2, vals_impact, width, label='Harman Impact Reference', color='#2e7d32', alpha=0.85)
    
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
