import os
import sys
import time
import socket
import threading
import subprocess
import urllib.request
import numpy as np
import scipy.signal
import scipy.io.wavfile as wav

IP = "192.168.1.39"
DATA_DIR = "/home/sergio/yamaha-qacoustics-calibration/data"
os.makedirs(DATA_DIR, exist_ok=True)

def ync_cmd(xml_data):
    url = f"http://{IP}/YamahaRemoteControl/ctrl"
    req = urllib.request.Request(
        url,
        data=xml_data.encode('utf-8'),
        headers={'Content-Type': 'text/xml; charset=utf-8', 'User-Agent': 'AV_Receiver/3.1'}
    )
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        return resp.read().decode('utf-8', errors='ignore')

# 1. Switch Yamaha to V-AUX and Straight On
print("[1/5] Configurando Yamaha RX-V673 en entrada V-AUX y modo Straight...")
ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>V-AUX</Input_Sel></Input></Main_Zone></YAMAHA_AV>')
ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Straight>On</Straight><Enhancer>Off</Enhancer></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>')

# 2. Generate Farina Logarithmic Sine Sweep
fs = 48000
duration = 5.0
f1, f2 = 15.0, 22000.0

N = int(duration * fs)
t = np.linspace(0, duration, N, endpoint=False)
w1 = 2 * np.pi * f1
w2 = 2 * np.pi * f2
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

silence_pre = np.zeros(int(fs * 0.5))
silence_post = np.zeros(int(fs * 0.5))
sweep_full = np.concatenate([silence_pre, 0.7 * sweep_core, silence_post])

wav_l_path = f"{DATA_DIR}/sweep_signal_L.wav"
wav_r_path = f"{DATA_DIR}/sweep_signal_R.wav"

stereo_l = np.column_stack([(sweep_full * 32767).astype(np.int16), np.zeros(len(sweep_full), dtype=np.int16)])
stereo_r = np.column_stack([np.zeros(len(sweep_full), dtype=np.int16), (sweep_full * 32767).astype(np.int16)])

wav.write(wav_l_path, fs, stereo_l)
wav.write(wav_r_path, fs, stereo_r)

def measure_channel(wav_path, ch_name):
    print(f"[2/5] Reproduciendo barrido y grabando canal {ch_name}...")
    total_dur = int(len(sweep_full) / fs + 1.5)
    rec_buf = []
    
    def _rec():
        nonlocal rec_buf
        cmd = ["arecord", "-D", "hw:1,0", "-f", "S16_LE", "-r", "48000", "-c", "2", "-d", str(total_dur), "-t", "raw"]
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if len(p.stdout) > 0:
            rec_buf = np.frombuffer(p.stdout, dtype=np.int16)
            
    th = threading.Thread(target=_rec)
    th.start()
    time.sleep(0.3)
    subprocess.run(["pw-play", wav_path])
    th.join()
    
    if len(rec_buf) == 0:
        raise RuntimeError("No se detectó audio en el micrófono!")
        
    mic = rec_buf[::2].astype(np.float64) / 32768.0
    ir = scipy.signal.fftconvolve(mic, inv_sweep, mode='full')
    peak = np.argmax(np.abs(ir))
    
    pre_samples = int(0.010 * fs)
    post_samples = int(0.500 * fs)
    start = max(0, peak - pre_samples)
    end = min(len(ir), peak + post_samples)
    ir_win = ir[start:end]
    
    n_fft = 65536
    H = np.fft.rfft(ir_win, n=n_fft)
    freqs = np.fft.rfftfreq(n_fft, d=1.0/fs)
    mag_db = 20 * np.log10(np.abs(H) + 1e-9)
    
    ref_mask = (freqs >= 500) & (freqs <= 2000)
    mag_norm = mag_db - np.mean(mag_db[ref_mask])
    
    # 1/24th octave smoothing
    smoothed = np.zeros_like(mag_norm)
    factor = 2 ** (1.0 / 24.0)
    for i, f in enumerate(freqs):
        if f < 20:
            smoothed[i] = mag_norm[i]
            continue
        mask = (freqs >= f / factor) & (freqs <= f * factor)
        smoothed[i] = np.mean(mag_norm[mask]) if np.any(mask) else mag_norm[i]
        
    return freqs, mag_norm, smoothed, ir_win

# Measure Left and Right
freqs, raw_l, smooth_l, ir_l = measure_channel(wav_l_path, "Left (Front L)")
time.sleep(0.5)
freqs, raw_r, smooth_r, ir_r = measure_channel(wav_r_path, "Right (Front R)")

# Restore Yamaha to AV4 (TV ARC)
print("[3/5] Restaurando entrada del Yamaha a AV4 (HDMI ARC)...")
ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>AV4</Input_Sel></Input></Main_Zone></YAMAHA_AV>')

# Save real measurement dataset
out_npz = f"{DATA_DIR}/medicion_real_calibracion.npz"
np.savez(out_npz, freqs=freqs, raw_l=raw_l, smooth_l=smooth_l, raw_r=raw_r, smooth_r=smooth_r, ir_l=ir_l, ir_r=ir_r)
print(f"[4/5] Datos reales acústicos guardados en: {out_npz}")
print("[5/5] ¡Medición acústica en tiempo real completada con éxito!")
