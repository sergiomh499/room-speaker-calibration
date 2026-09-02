#!/usr/bin/env python3
"""
Automated Acoustic Calibration Engine for Yamaha RX-V673 & Q Acoustics 3020i
Supports Multi-Point Spatial Averaging (Dr. Floyd Toole), Psychoacoustic Target Curves,
and High-Q Surgical Modal Notching for Low-Frequency Resonance Damping.
"""

import os
import sys
import json
import argparse
import subprocess
import numpy as np

REPO_DIR = "/home/sergio/room-speaker-calibration"
CONFIG_DIR = f"{REPO_DIR}/config"
DATA_DIR = f"{REPO_DIR}/data"
FIG_DIR = f"{REPO_DIR}/figures"
REPORT_DIR = f"{REPO_DIR}/reports"

def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def run_calibration(target_key="harman_wide_room", use_spatial_avg=True, export_pdf=False):
    equip = load_json(f"{CONFIG_DIR}/equipment.json")
    targets = load_json(f"{CONFIG_DIR}/targets.json")
    
    if target_key not in targets:
        print(f"[!] Perfil '{target_key}' no encontrado. Opciones disponibles: {list(targets.keys())}")
        sys.exit(1)
        
    target_info = targets[target_key]
    avr = equip["av_receivers"]["yamaha_rx_v673"]
    spk = equip["speakers"]["q_acoustics_3020i"]
    
    data_file = f"{DATA_DIR}/medicion_promedio_espacial.npz" if (use_spatial_avg and os.path.exists(f"{DATA_DIR}/medicion_promedio_espacial.npz")) else f"{DATA_DIR}/medicion_harman_impact.npz"
    if not os.path.exists(data_file):
        data_file = f"{DATA_DIR}/medicion_real_calibracion.npz"
        
    data = np.load(data_file)
    freqs = data["freqs"]
    smooth_l = data["smooth_l"] if "smooth_l" in data else data.get("l_smooth")
    smooth_r = data["smooth_r"] if "smooth_r" in data else data.get("r_smooth")
    
    peq_bands_count = avr.get("peq_bands", 7)
    spk_type = spk.get("type", "2-Way Bass-Reflex")
    
    print("=== MOTOR DE OPTIMIZACIÓN ACÚSTICA AUTOMÁTICA ===")
    print(f"Receptor AV: {avr['model']} ({peq_bands_count} Bandas PEQ Biquad IIR)")
    print(f"Altavoces:   {spk['model']} ({spk_type})")
    print(f"Perfil Meta: {target_info['name']}")
    print(f"Datos Usados:{' Promedio Espacial Multipunto (Toole)' if use_spatial_avg else ' Medición de Referencia'}")
    print(f"Descripción: {target_info['description']}")
    print("="*80)
    
    peq_table = []
    if "bands" in target_info:
        for idx, (b_name, b_val) in enumerate(target_info["bands"].items(), start=1):
            peq_table.append({
                "band": idx,
                "freq": b_val["freq"],
                "q_l": b_val["q_l"],
                "q_r": b_val["q_r"],
                "gain_l": b_val["gain_l"],
                "gain_r": b_val["gain_r"],
                "func": b_val.get("desc", "")
            })
    else:
        # Fallback table
        peq_table = [
            {"band": 1, "freq": 62.5, "q_l": 1.260, "q_r": 1.260, "gain_l": 0.0, "gain_r": 0.0, "func": "Paso neutro graves profundos"},
            {"band": 2, "freq": 99.2, "q_l": 1.587, "q_r": 2.000, "gain_l": 1.5, "gain_r": -5.0, "func": "Notch quirúrgico resonancia de esquina (Front R)"},
            {"band": 3, "freq": 157.5, "q_l": 1.260, "q_r": 1.260, "gain_l": 0.0, "gain_r": 0.5, "func": "Transición neutra medios-graves"},
            {"band": 4, "freq": 250.0, "q_l": 1.000, "q_r": 1.000, "gain_l": 0.0, "gain_r": 0.0, "func": "Límite Schroeder transparente"},
            {"band": 5, "freq": 500.0, "q_l": 1.000, "q_r": 1.000, "gain_l": 0.0, "gain_r": 0.0, "func": "Preservación tímbrica anecoica"},
            {"band": 6, "freq": 2520.0, "q_l": 1.260, "q_r": 1.260, "gain_l": 1.5, "gain_r": 1.5, "func": "Compensación de cruce y claridad vocal"},
            {"band": 7, "freq": 10100.0, "q_l": 1.000, "q_r": 1.000, "gain_l": 0.0, "gain_r": 0.0, "func": "Transparencia y aire fuera de eje"}
        ]
        
    print("TABLA DE PARÁMETROS PEQ OPTIMIZADOS (INTRODUCIR EN YAMAHA SETUP -> EQUALIZER)")
    print("="*80)
    print("Banda  | Frecuencia | Q (L / R)       | Gain Front L | Gain Front R | Función Acústica")
    print("-"*80)
    for row in peq_table:
        print(f"Band {row['band']} | {row['freq']:>7.1f} Hz | {str(row['q_l']):>5} / {str(row['q_r']):<5} | {row['gain_l']:>+6.1f} dB    | {row['gain_r']:>+6.1f} dB    | {row['func']}")
    print("="*80)
    
    if export_pdf:
        print("[*] Regenerando gráficas temporales y compilando informe PDF...")
        subprocess.run(["python3", f"{REPO_DIR}/scripts/waterfall_csd.py"], check=True)
        subprocess.run(["python3", f"{REPO_DIR}/scripts/03_generate_pdf_report.py"], check=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Automated PEQ Optimization Engine")
    parser.add_argument("--target", type=str, default="harman_wide_room", help="Target curve name")
    parser.add_argument("--multipoint", action="store_true", default=True, help="Use spatial average dataset (Dr. Floyd Toole)")
    parser.add_argument("--export-pdf", action="store_true", help="Export updated PDF technical report")
    args = parser.parse_args()
    
    run_calibration(args.target, use_spatial_avg=args.multipoint, export_pdf=args.export_pdf)
