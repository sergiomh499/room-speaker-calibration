#!/usr/bin/env python3
"""
Multi-Calibration Capture and Comparative Engine
Captures real-world acoustic sweeps for YPAO Flat, YPAO Natural, Through (Off),
and Manual PEQ, storing each dataset and generating side-by-side comparative reports.
"""
import os
import sys
import time
import argparse
import subprocess
import numpy as np
import matplotlib.pyplot as plt
import scipy.signal
import scipy.io.wavfile as wav
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
FIG_DIR = os.path.join(BASE_DIR, "figures")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
IP = "192.168.1.39"

def ync_cmd(xml_data):
    url = f"http://{IP}/YamahaRemoteControl/ctrl"
    req = urllib.request.Request(
        url,
        data=xml_data.encode('utf-8'),
        headers={'Content-Type': 'text/xml; charset=utf-8', 'User-Agent': 'AV_Receiver/3.1'}
    )
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        return resp.read().decode('utf-8', errors='ignore')

def run_sweep(ch="L"):
    wav_path = os.path.join(DATA_DIR, f"sweep_signal_{ch}.wav")
    total_dur = 7.0
    rec_buf = []
    
    def _rec():
        nonlocal rec_buf
        cmd = ["arecord", "-D", "hw:1,0", "-f", "S16_LE", "-r", "48000", "-c", "2", "-d", str(int(total_dur)), "-t", "raw"]
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if len(p.stdout) > 0:
            rec_buf = np.frombuffer(p.stdout, dtype=np.int16)
            
    import threading
    th = threading.Thread(target=_rec)
    th.start()
    time.sleep(0.3)
    subprocess.run(["pw-play", wav_path])
    th.join()
    
    fs = 48000
    duration = 5.0
    f1, f2 = 15.0, 22000.0
    N = int(duration * fs)
    t = np.linspace(0, duration, N, endpoint=False)
    w1, w2 = 2 * np.pi * f1, 2 * np.pi * f2
    L = duration / np.log(w2 / w1)
    phi = w1 * L * (np.exp(t / L) - 1.0)
    sweep_core = np.sin(phi)
    fade_samples = int(fs * 0.05)
    fade_in = np.sin(np.linspace(0, np.pi/2, fade_samples))**2
    sweep_core[:fade_samples] *= fade_in
    sweep_core[-fade_samples:] *= fade_in[::-1]
    envelope = np.exp(-t / L)
    inv_sweep = sweep_core[::-1] * envelope
    conv_unit = scipy.signal.fftconvolve(sweep_core, inv_sweep, mode='full')
    inv_sweep /= np.max(conv_unit)
    
    mic = rec_buf[::2].astype(np.float64) / 32768.0
    ir = scipy.signal.fftconvolve(mic, inv_sweep, mode='full')
    peak = np.argmax(np.abs(ir))
    start = max(0, peak - int(0.010 * fs))
    end = min(len(ir), peak + int(0.500 * fs))
    ir_win = ir[start:end]
    
    n_fft = 65536
    H = np.fft.rfft(ir_win, n=n_fft)
    freqs = np.fft.rfftfreq(n_fft, d=1.0/fs)
    mag_db = 20 * np.log10(np.abs(H) + 1e-9)
    ref_mask = (freqs >= 500) & (freqs <= 2000)
    mag_norm = mag_db - np.mean(mag_db[ref_mask])
    
    smoothed = np.zeros_like(mag_norm)
    factor = 2 ** (1.0 / 24.0)
    for i, f in enumerate(freqs):
        if f < 20:
            smoothed[i] = mag_norm[i]
            continue
        mask = (freqs >= f / factor) & (freqs <= f * factor)
        smoothed[i] = np.mean(mag_norm[mask]) if np.any(mask) else mag_norm[i]
        
    return freqs, mag_norm, smoothed

def capture_mode(mode_name):
    print(f"[*] Iniciando captura acústica para el modo: {mode_name.upper()}...")
    ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>V-AUX</Input_Sel></Input></Main_Zone></YAMAHA_AV>')
    ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Straight>On</Straight><Enhancer>Off</Enhancer></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>')
    
    print(" - Midiendo Canal Izquierdo (Front L)...")
    freqs, raw_l, smooth_l = run_sweep("L")
    time.sleep(0.5)
    print(" - Midiendo Canal Derecho (Front R)...")
    freqs, raw_r, smooth_r = run_sweep("R")
    
    ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>AV4</Input_Sel></Input></Main_Zone></YAMAHA_AV>')
    
    out_file = os.path.join(DATA_DIR, f"medicion_{mode_name.lower()}.npz")
    np.savez(out_file, freqs=freqs, raw_l=raw_l, smooth_l=smooth_l, raw_r=raw_r, smooth_r=smooth_r)
    print(f"[✓] Modo {mode_name.upper()} guardado exitosamente en: {out_file}\n")
    return out_file

def generate_multi_comparison():
    print("[*] Generando comparativa acústica completa de todos los modos disponibles...")
    modes = ["through", "ypao_flat", "ypao_natural", "harman_neutral"]
    available_data = {}
    
    for m in modes:
        fpath = os.path.join(DATA_DIR, f"medicion_{m}.npz")
        if os.path.exists(fpath):
            available_data[m] = np.load(fpath)
            
    if not available_data:
        print("No hay suficientes modos capturados aún.")
        return
        
    plt.style.use('dark_background')
    fig, axs = plt.subplots(2, 2, figsize=(16, 10), dpi=140)
    fig.suptitle("Gran Comparativa Acústica Multimodo: Through vs YPAO Flat vs YPAO Natural vs Harman Neutral\nYamaha RX-V673 + Q Acoustics 3020i", 
                 fontsize=13, fontweight='bold', color='#4fc3f7', y=0.98)
                 
    colors_map = {
        "through": ("#ff5252", "--", "Sin Calibrar (Through)"),
        "ypao_flat": ("#ff9100", "-.", "YPAO Flat"),
        "ypao_natural": ("#ffd600", ":", "YPAO Natural"),
        "harman_neutral": ("#00e676", "-", "Calibración Híbrida (Harman Neutral)")
    }
    
    # Left channel
    ax1 = axs[0, 0]
    for m, d in available_data.items():
        c, ls, label = colors_map.get(m, ("white", "-", m))
        mask = (d['freqs'] >= 25) & (d['freqs'] <= 18000)
        ax1.semilogx(d['freqs'][mask], d['smooth_l'][mask], color=c, ls=ls, label=label, lw=1.8 if m == "harman_neutral" else 1.2)
    ax1.set_title("Canal Izquierdo (Front L - Abierto)", fontsize=11, color='#e0e0e0')
    ax1.set_xlim(25, 18000)
    ax1.set_ylim(-18, 14)
    ax1.grid(True, which='both', ls=':', alpha=0.3)
    ax1.legend(loc='lower right', fontsize=8)
    
    # Right channel
    ax2 = axs[0, 1]
    for m, d in available_data.items():
        c, ls, label = colors_map.get(m, ("white", "-", m))
        mask = (d['freqs'] >= 25) & (d['freqs'] <= 18000)
        ax2.semilogx(d['freqs'][mask], d['smooth_r'][mask], color=c, ls=ls, label=label, lw=1.8 if m == "harman_neutral" else 1.2)
    ax2.set_title("Canal Derecho (Front R - Esquina)", fontsize=11, color='#e0e0e0')
    ax2.set_xlim(25, 18000)
    ax2.set_ylim(-18, 14)
    ax2.grid(True, which='both', ls=':', alpha=0.3)
    ax2.legend(loc='lower right', fontsize=8)
    
    # Stereo symmetry
    ax3 = axs[1, 0]
    for m, d in available_data.items():
        c, ls, label = colors_map.get(m, ("white", "-", m))
        mask = (d['freqs'] >= 25) & (d['freqs'] <= 18000)
        diff = np.abs(d['smooth_l'][mask] - d['smooth_r'][mask])
        ax3.semilogx(d['freqs'][mask], diff, color=c, ls=ls, label=f"{label} (Media: {np.mean(diff):.2f} dB)", lw=1.8 if m == "harman_neutral" else 1.2)
    ax3.axhline(1.0, color='#76ff03', ls=':', label='Objetivo de Referencia (±1 dB)')
    ax3.set_title("Simetría Estéreo (|L - R|)", fontsize=11, color='#e0e0e0')
    ax3.set_xlim(25, 18000)
    ax3.set_ylim(0, 10)
    ax3.grid(True, which='both', ls=':', alpha=0.3)
    ax3.legend(loc='upper right', fontsize=8)
    
    # Bass zoom
    ax4 = axs[1, 1]
    for m, d in available_data.items():
        c, ls, label = colors_map.get(m, ("white", "-", m))
        mask = (d['freqs'] >= 30) & (d['freqs'] <= 350)
        ax4.plot(d['freqs'][mask], d['smooth_r'][mask], color=c, ls=ls, label=f"Front R - {label}", lw=1.8 if m == "harman_neutral" else 1.2)
    ax4.set_title("Detalle Modos de Sala en Esquina (30 Hz - 350 Hz)", fontsize=11, color='#e0e0e0')
    ax4.set_xlim(30, 350)
    ax4.set_ylim(-15, 14)
    ax4.grid(True, which='both', ls=':', alpha=0.3)
    ax4.legend(loc='lower right', fontsize=8)
    
    plt.tight_layout()
    out_img = os.path.join(FIG_DIR, "gran_comparativa_multimodo.png")
    plt.savefig(out_img, dpi=140)
    plt.close()
    print(f"[✓] Gráfica comparativa guardada en: {out_img}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capturador de Modos Acústicos")
    parser.add_argument("--mode", choices=["through", "ypao_flat", "ypao_natural", "harman_neutral"], help="Modo acústico a capturar")
    parser.add_argument("--compare", action="store_true", help="Generar la gran comparativa de todos los modos")
    args = parser.parse_args()
    
    if args.mode:
        capture_mode(args.mode)
    if args.compare or not args.mode:
        generate_multi_comparison()
