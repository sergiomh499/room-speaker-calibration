import os
import sys
import time
import socket
import threading
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
import argparse
import numpy as np
import scipy.signal
import scipy.io.wavfile as wav

IP = "192.168.1.39"
REPO_DIR = "/home/sergio/room-speaker-calibration"
DATA_DIR = f"{REPO_DIR}/data"
DEFAULT_CAL_FILE = f"{REPO_DIR}/config/ypao_stock_community.cal"
os.makedirs(DATA_DIR, exist_ok=True)

parser = argparse.ArgumentParser(description="Acoustic Measurement Sweep Engine with Microphone Calibration")
parser.add_argument("--mic", type=str, default="ypao_stock", help="Microphone profile (ypao_stock, umik1, umm6, custom)")
parser.add_argument("--cal-file", type=str, default=DEFAULT_CAL_FILE, help="Path to .cal microphone calibration file")
parser.add_argument("--no-cal", action="store_true", help="Disable microphone calibration curve")
args, _ = parser.parse_known_args()

def load_cal_curve(cal_path, target_freqs):
    if args.no_cal or not cal_path or not os.path.exists(cal_path):
        return np.zeros_like(target_freqs)
    try:
        cal_data = np.loadtxt(cal_path, comments=['*', '"', '#'])
        cal_f = cal_data[:, 0]
        cal_db = cal_data[:, 1]
        return np.interp(target_freqs, cal_f, cal_db, left=0.0, right=0.0)
    except Exception as e:
        print(f"[!] Aviso cargando archivo .cal ({cal_path}): {e}")
        return np.zeros_like(target_freqs)

def ync_cmd(xml_data):
    url = f"http://{IP}/YamahaRemoteControl/ctrl"
    req = urllib.request.Request(
        url,
        data=xml_data.encode('utf-8'),
        headers={'Content-Type': 'text/xml; charset=utf-8', 'User-Agent': 'AV_Receiver/3.1'}
    )
    try:
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            return resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"[!] Aviso conexión Yamaha: {e}")
        return ""

orig_volume_val = "-350"

def configure_yamaha_for_measurement():
    global orig_volume_val
    print("[1/5] Configurando automáticamente Yamaha RX-V673 y ganancia de micrófono...")
    if not args.no_cal and os.path.exists(args.cal_file):
        print(f"  [i] Calibración de micrófono activa: {os.path.basename(args.cal_file)}")
    
    try:
        subprocess.run(["amixer", "-c", "1", "sset", "Capture", "52"], capture_output=True)
        subprocess.run(["wpctl", "set-volume", "@DEFAULT_AUDIO_SOURCE@", "1.0"], capture_output=True)
    except Exception:
        pass
        
    res_vol = ync_cmd('<YAMAHA_AV cmd="GET"><Main_Zone><Volume><Lvl>GetParam</Lvl></Volume></Main_Zone></YAMAHA_AV>')
    try:
        root = ET.fromstring(res_vol)
        v = root.find('.//Volume/Lvl/Val')
        if v is not None:
            orig_volume_val = v.text
    except Exception:
        pass
        
    ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Power_Control><Power>On</Power></Power_Control></Main_Zone></YAMAHA_AV>')
    ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Pure_Direct><Mode>Off</Mode></Pure_Direct></Sound_Video></Main_Zone></YAMAHA_AV>')
    ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Tone><Bass><Val>0</Val><Exp>1</Exp><Unit>dB</Unit></Bass><Treble><Val>0</Val><Exp>1</Exp><Unit>dB</Unit></Treble></Tone></Sound_Video></Main_Zone></YAMAHA_AV>')
    ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Sound_Video><Adaptive_DRC>Off</Adaptive_DRC></Sound_Video></Main_Zone></YAMAHA_AV>')
    ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Surround><Program_Sel><Current><Straight>On</Straight><Enhancer>Off</Enhancer></Current></Program_Sel></Surround></Main_Zone></YAMAHA_AV>')
    ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>V-AUX</Input_Sel></Input></Main_Zone></YAMAHA_AV>')
    ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Volume><Lvl><Val>-250</Val><Exp>1</Exp><Unit>dB</Unit></Lvl></Volume></Main_Zone></YAMAHA_AV>')
    time.sleep(0.3)

configure_yamaha_for_measurement()

# Generate Farina Logarithmic Sine Sweep
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

def validate_recording(raw_samples, mic_normalized, ir, ch_name):
    peak_raw = np.max(np.abs(raw_samples))
    peak_dbfs = 20 * np.log10(peak_raw / 32768.0 + 1e-12)
    
    if peak_raw > 32200:
        return False, f"Saturación digital detectada en {ch_name} (Pico: {peak_dbfs:.1f} dBFS)."
    if peak_raw < 600:
        return False, f"Señal demasiado baja en {ch_name} (Pico: {peak_dbfs:.1f} dBFS)."
        
    noise_floor = np.mean(np.abs(mic_normalized[:int(fs * 0.3)])) + 1e-12
    peak_ir = np.max(np.abs(ir))
    snr_db = 20 * np.log10(peak_ir / (noise_floor * 3.5) + 1e-12)
    
    if snr_db < 14.0:
        return False, f"Relación Señal/Ruido (SNR) insuficiente en {ch_name} ({snr_db:.1f} dB < 14 dB)."
        
    validation_card = f"[✓ VALIDACIÓN OK - {ch_name}]: Nivel={peak_dbfs:.1f} dBFS | SNR={snr_db:.1f} dB | Pico={peak_raw} cuentas"
    return True, validation_card

def measure_channel(wav_path, ch_name):
    print(f"[2/5] Reproduciendo barrido Farina y grabando {ch_name}...")
    total_dur = int(len(sweep_full) / fs + 1.5)
    rec_file = f"/tmp/rec_sweep_{int(time.time()*1000)}.wav"
    
    cmd_rec = ["pw-record", "--rate=48000", "--channels=2", "--format=s16", rec_file]
    proc_rec = subprocess.Popen(cmd_rec)
    time.sleep(0.3)
    subprocess.run(["pw-play", wav_path])
    time.sleep(0.5)
    proc_rec.terminate()
    proc_rec.wait()
    
    if not os.path.exists(rec_file):
        raise RuntimeError("No se generó el archivo de grabación!")
        
    fs_rec, data_rec = wav.read(rec_file)
    try:
        os.remove(rec_file)
    except Exception:
        pass
        
    if len(data_rec) == 0:
        raise RuntimeError("No se detectó audio en el micrófono!")
        
    raw_samples = data_rec[:, 0] if len(data_rec.shape) > 1 else data_rec
    mic = raw_samples.astype(np.float64) / 32768.0
    ir = scipy.signal.fftconvolve(mic, inv_sweep, mode='full')
    
    is_valid, report = validate_recording(raw_samples, mic, ir, ch_name)
    print(f"  {report}")
    if not is_valid:
        raise ValueError(f"TOMA RECHAZADA: {report}")
        
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
    
    # Apply microphone calibration curve
    cal_offset = load_cal_curve(args.cal_file, freqs)
    mag_calibrated = mag_norm - cal_offset
    
    smoothed = np.zeros_like(mag_calibrated)
    factor = 2 ** (1.0 / 24.0)
    for i, f in enumerate(freqs):
        if f < 20:
            smoothed[i] = mag_calibrated[i]
            continue
        mask = (freqs >= f / factor) & (freqs <= f * factor)
        smoothed[i] = np.mean(mag_calibrated[mask]) if np.any(mask) else mag_calibrated[i]
        
    return freqs, mag_calibrated, smoothed, ir_win

try:
    freqs, raw_l, smooth_l, ir_l = measure_channel(wav_l_path, "Canal Izquierdo (Front L)")
    time.sleep(0.4)
    freqs, raw_r, smooth_r, ir_r = measure_channel(wav_r_path, "Canal Derecho (Front R)")
finally:
    print(f"[3/5] Restaurando automáticamente volumen original ({float(orig_volume_val)/10:.1f} dB) y entrada AV4 (HDMI ARC)...")
    ync_cmd(f'<YAMAHA_AV cmd="PUT"><Main_Zone><Volume><Lvl><Val>{orig_volume_val}</Val><Exp>1</Exp><Unit>dB</Unit></Lvl></Volume></Main_Zone></YAMAHA_AV>')
    ync_cmd('<YAMAHA_AV cmd="PUT"><Main_Zone><Input><Input_Sel>AV4</Input_Sel></Input></Main_Zone></YAMAHA_AV>')

# Save real measurement dataset with timestamp
ts_str = time.strftime("%Y%m%d_%H%M%S")
out_npz_ts = f"{DATA_DIR}/medicion_real_calibracion_{ts_str}.npz"
out_npz_latest = f"{DATA_DIR}/medicion_real_calibracion.npz"

np.savez(out_npz_ts, freqs=freqs, raw_l=raw_l, smooth_l=smooth_l, raw_r=raw_r, smooth_r=smooth_r, ir_l=ir_l, ir_r=ir_r)
np.savez(out_npz_latest, freqs=freqs, raw_l=raw_l, smooth_l=smooth_l, raw_r=raw_r, smooth_r=smooth_r, ir_l=ir_l, ir_r=ir_r)

print(f"[4/5] Datos acústicos validados y guardados en:")
print(f"  - {out_npz_ts}")
print(f"  - {out_npz_latest}")
print("[5/5] ¡Medición acústica completada y certificada con éxito!")
