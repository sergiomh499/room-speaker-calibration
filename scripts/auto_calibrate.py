#!/usr/bin/env python3
"""
Automated Acoustic Calibration Engine for Yamaha RX-V673 & Multi-Speaker Systems
Computes optimal discrete 7-band PEQ parameters based on measured room data,
target psychoacoustic house curves, and speaker spinorama corrections.
"""
import os
import sys
import json
import argparse
import numpy as np
import scipy.signal
import scipy.optimize
import matplotlib.pyplot as plt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(BASE_DIR, "config")
DATA_DIR = os.path.join(BASE_DIR, "data")
FIG_DIR = os.path.join(BASE_DIR, "figures")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

def load_configs():
    with open(os.path.join(CONFIG_DIR, "equipment.json"), "r", encoding="utf-8") as f:
        equip = json.load(f)
    with open(os.path.join(CONFIG_DIR, "targets.json"), "r", encoding="utf-8") as f:
        targets = json.load(f)
    return equip, targets

def biquad_peq_tf(freqs, f0, Q, gain_db, fs=48000):
    """Calculates exact magnitude response of an analog/digital biquad peak filter."""
    if abs(gain_db) < 0.05:
        return np.zeros_like(freqs)
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * np.pi * f0 / fs
    alpha = np.sin(w0) / (2.0 * Q)
    
    b0 = 1.0 + alpha * A
    b1 = -2.0 * np.cos(w0)
    b2 = 1.0 - alpha * A
    a0 = 1.0 + alpha / A
    a1 = -2.0 * np.cos(w0)
    a2 = 1.0 - alpha / A
    
    b = np.array([b0/a0, b1/a0, b2/a0])
    a = np.array([1.0, a1/a0, a2/a0])
    
    w, h = scipy.signal.freqz(b, a, worN=freqs, fs=fs)
    return 20.0 * np.log10(np.abs(h) + 1e-9)

def generate_target_curve(freqs, target_cfg):
    """Generates the target psychoacoustic house curve across frequency grid."""
    target = np.zeros_like(freqs)
    
    # Bass boost
    b_boost = target_cfg.get("bass_boost_db", 0.0)
    b_cut = target_cfg.get("bass_boost_cutoff_hz", 100.0)
    if b_boost > 0:
        target += b_boost / (1.0 + (freqs / b_cut)**2)
        
    # Presence boost
    p_boost = target_cfg.get("presence_boost_db", 0.0)
    p_center = target_cfg.get("presence_center_hz", 2800.0)
    if p_boost > 0:
        target += p_boost * np.exp(-0.5 * ((np.log(freqs) - np.log(p_center)) / 0.3)**2)
        
    # Treble roll-off
    t_slope = target_cfg.get("treble_rolloff_db_octave", 0.0)
    t_start = target_cfg.get("treble_start_hz", 8000.0)
    if t_slope != 0:
        mask_t = freqs > t_start
        octaves = np.log2(freqs[mask_t] / t_start)
        target[mask_t] += t_slope * octaves
        
    return target

def optimize_channel(measured_curve, freqs, target_curve, avr_cfg, spk_cfg, is_corner=False):
    """
    Optimizes the 7 PEQ bands under AVR discrete constraints (allowed Q, gain step, frequencies).
    """
    bands_hz = avr_cfg.get("default_user_bands_hz", [62.5, 99.2, 157.5, 250.0, 500.0, 2520.0, 10080.0])
    allowed_q = avr_cfg.get("allowed_q_values", [1.000, 1.260, 1.587])
    gain_step = avr_cfg.get("gain_step_db", 0.5)
    max_boost = avr_cfg.get("max_boost_db", 3.0)
    max_cut = avr_cfg.get("max_cut_db", -12.0)
    
    spinorama = spk_cfg.get("spinorama_notch_compensation")
    
    # Target difference
    delta = target_curve - measured_curve
    
    optimized_filters = []
    accum_correction = np.zeros_like(freqs)
    
    for i, f0 in enumerate(bands_hz):
        # Check if this band is reserved for speaker spinorama compensation
        if spinorama and abs(f0 - spinorama["center_hz"]) < 100.0:
            best_q = spinorama["recommended_q"]
            best_gain = spinorama["recommended_boost_db"]
            role = f"Compensación Crossover ({spk_cfg['model']})"
        elif f0 >= 10000.0:
            # Treble shaping
            best_q = 1.000
            best_gain = -1.0 if target_cfg_name != "audiophile_flat" else 0.0
            role = "Control de sibilancias / House Curve"
        elif f0 in [250.0, 500.0]:
            # Mid-band neutrality
            best_q = 1.000
            best_gain = 0.0
            role = "Paso transparente neutro"
        else:
            # Bass modal optimization
            # Evaluate error around filter band
            f_mask = (freqs >= f0 / 1.4) & (freqs <= f0 * 1.4)
            local_error = np.mean(delta[f_mask] - accum_correction[f_mask])
            
            # Clamp to allowed gain step and limits
            raw_gain = np.clip(local_error, max_cut, max_boost)
            best_gain = round(raw_gain / gain_step) * gain_step
            
            # Select optimal Q
            if f0 <= 100.0:
                best_q = 1.587 if (not is_corner and f0 > 80) else 1.260
            else:
                best_q = 1.260
                
            role = "Control de modo de sala / Resonancia" if best_gain < 0 else "Refuerzo acústico"
            if best_gain == 0:
                role = "Paso neutro"
                
        filter_tf = biquad_peq_tf(freqs, f0, best_q, best_gain)
        accum_correction += filter_tf
        
        optimized_filters.append({
            "band": i + 1,
            "freq": f0,
            "q": best_q,
            "gain": best_gain,
            "role": role
        })
        
    return optimized_filters, accum_correction

def main():
    global target_cfg_name
    parser = argparse.ArgumentParser(description="Calibrador Acústico Automático Yamaha & Q Acoustics")
    parser.add_argument("--target", default="harman_neutral", choices=["harman_neutral", "audiophile_flat", "cinema_impact", "vocal_clarity", "warm_music"], help="Perfil de curva acústica deseada")
    parser.add_argument("--speaker", default="q_acoustics_3020i", help="Perfil de altavoz (equipment.json)")
    parser.add_argument("--avr", default="yamaha_rx_v673", help="Perfil de receptor AV (equipment.json)")
    parser.add_argument("--measure", action="store_true", help="Lanzar barrido real con micrófono antes de optimizar")
    parser.add_argument("--export-pdf", action="store_true", help="Regenerar y compilar informe técnico en PDF")
    args = parser.parse_args()
    
    target_cfg_name = args.target
    equip, targets = load_configs()
    
    avr_cfg = equip["av_receivers"].get(args.avr, equip["av_receivers"]["yamaha_rx_v673"])
    spk_cfg = equip["speakers"].get(args.speaker, equip["speakers"]["q_acoustics_3020i"])
    target_cfg = targets.get(args.target, targets["harman_neutral"])
    
    print(f"=== MOTOR DE OPTIMIZACIÓN ACÚSTICA AUTOMÁTICA ===")
    print(f" Receptor AV:  {avr_cfg['brand']} {avr_cfg['model']}")
    print(f" Altavoces:    {spk_cfg['brand']} {spk_cfg['model']}")
    print(f" Perfil Meta:  {target_cfg['name']}")
    print(f" Descripción:  {target_cfg['description']}\n")
    
    if args.measure:
        print("[!] Ejecutando medición en tiempo real...")
        os.system(f"python3 {BASE_DIR}/scripts/01_measure_sweep.py")
        
    data_file = os.path.join(DATA_DIR, "medicion_real_calibracion.npz")
    if not os.path.exists(data_file):
        print(f"Error: No se encontró el archivo de mediciones {data_file}. Ejecuta con --measure primero.")
        sys.exit(1)
        
    data = np.load(data_file)
    freqs = data['freqs']
    smooth_l = data['smooth_l']
    smooth_r = data['smooth_r']
    
    target_curve = generate_target_curve(freqs, target_cfg)
    
    opt_l, corr_l_tf = optimize_channel(smooth_l, freqs, target_curve, avr_cfg, spk_cfg, is_corner=False)
    opt_r, corr_r_tf = optimize_channel(smooth_r, freqs, target_curve, avr_cfg, spk_cfg, is_corner=True)
    
    final_l = smooth_l + corr_l_tf
    final_r = smooth_r + corr_r_tf
    
    eval_mask = (freqs >= 40) & (freqs <= 16000)
    std_before_l = np.std(smooth_l[eval_mask])
    std_after_l = np.std((final_l - target_curve)[eval_mask])
    std_before_r = np.std(smooth_r[eval_mask])
    std_after_r = np.std((final_r - target_curve)[eval_mask])
    sym_before = np.mean(np.abs(smooth_l[eval_mask] - smooth_r[eval_mask]))
    sym_after = np.mean(np.abs(final_l[eval_mask] - final_r[eval_mask]))
    
    print("=" * 80)
    print("TABLA DE PARÁMETROS PEQ OPTIMIZADOS (INTRODUCIR EN YAMAHA SETUP -> EQUALIZER)")
    print("=" * 80)
    print(f"{'Banda':<8} | {'Frecuencia':<12} | {'Q (L / R)':<14} | {'Gain Front L':<14} | {'Gain Front R':<14} | {'Función Acústica'}")
    print("-" * 80)
    for bl, br in zip(opt_l, opt_r):
        q_str = f"{bl['q']:.3f}" if bl['q'] == br['q'] else f"{bl['q']:.3f} / {br['q']:.3f}"
        print(f"Band {bl['band']:<3} | {bl['freq']:>7.1f} Hz   | {q_str:<14} | {bl['gain']:>+5.1f} dB       | {br['gain']:>+5.1f} dB       | {bl['role']}")
    print("=" * 80)
    
    print(f"\n📊 IMPACTO Y MEJORA CUANTITATIVA ({target_cfg_name.upper()}):")
    print(f" - Desviación Estándar Front L: de ±{std_before_l:.2f} dB a ±{std_after_l:.2f} dB (Reducción de error: -{(1 - std_after_l/std_before_l)*100:.1f}%)")
    print(f" - Desviación Estándar Front R: de ±{std_before_r:.2f} dB a ±{std_after_r:.2f} dB (Reducción de error: -{(1 - std_after_r/std_before_r)*100:.1f}%)")
    print(f" - Simetría Estéreo (|L - R|): de {sym_before:.2f} dB a {sym_after:.2f} dB\n")
    
    if args.export_pdf:
        print("[*] Regenerando gráficas e informe PDF...")
        os.system(f"python3 {BASE_DIR}/scripts/02_plot_responses.py")
        os.system(f"python3 {BASE_DIR}/scripts/03_generate_pdf_report.py")
        print("[✓] Informe PDF actualizado en: /home/sergio/Informe_Calibracion_Acustica_Yamaha_Q_Acoustics.pdf")

if __name__ == "__main__":
    main()
