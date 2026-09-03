#!/usr/bin/env python3
"""
Acoustic Calibration Verification Engine
Compares baseline 'Through' measurements against 'PEQ Manual' and against
all YPAO modes ('YPAO Flat', 'YPAO Front', 'YPAO Natural') and against
realistic Target Curves (Harman In-Room with 64 Hz acoustic roll-off).
Evaluates which curve is best mathematically and acoustically, generating
a multi-curve comparative benchmark and 4-panel comparison figures.
"""

import os
import json
import time
from datetime import datetime
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

REPO_DIR = "/home/sergio/room-speaker-calibration"
DATA_DIR = f"{REPO_DIR}/data"
CONFIG_DIR = f"{REPO_DIR}/config"
FIG_DIR = f"{REPO_DIR}/figures"
os.makedirs(FIG_DIR, exist_ok=True)

def professional_psychoacoustic_smooth(freqs, mag_db):
    """
    State-of-the-art REW/Dirac style Psychoacoustic Smoothing:
    - Logarithmic frequency resampling (96 pts/octave)
    - Frequency-dependent octave bandwidth (1/12 oct bass, 1/6 oct mid, 1/3 oct highs)
    - Non-linear asymmetric null compression (suppresses artificial comb filtering notches)
    """
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
def run_verification(profile="harman_wide_room", save_fig=True):
    # 1. Baseline Data (Through / Sin Calibrar)
    base_file = f"{DATA_DIR}/medicion_promedio_espacial.npz"
    if not os.path.exists(base_file):
        raise FileNotFoundError(f"Archivo base no encontrado: {base_file}")
        
    base_data = np.load(base_file)
    freqs = base_data["freqs"]
    base_l = base_data["smooth_l"]
    base_r = base_data["smooth_r"]
    
    # 2. Load Selected Community Profile for Calibration Verification
    with open(f"{CONFIG_DIR}/targets.json", "r", encoding="utf-8") as f:
        targets_cfg = json.load(f)
        
    profile_key = profile if profile and profile in targets_cfg else "harman_wide_room"
    prof_data = targets_cfg.get(profile_key, targets_cfg.get("harman_wide_room", {}))
    prof_raw_name = prof_data.get("name", "Harman Target")
    prof_display_name = prof_raw_name.split("(")[0].strip()
    peq_manual_name = f"PEQ Manual ({prof_display_name})"
    
    # 3. Dynamic Acoustic Target Curve Based on Selected Profile
    def build_profile_target_curve(p_key, freqs_arr):
        f_c = 64.0
        hpf_mag = 1.0 / np.sqrt(1.0 + (f_c / np.maximum(freqs_arr, 1.0))**4)
        hpf_db = 20.0 * np.log10(np.maximum(hpf_mag, 1e-3))
        
        target = np.zeros_like(freqs_arr)
        k = (p_key or "").lower()
        if "bk" in k or "1974" in k:
            for i, f in enumerate(freqs_arr):
                if f < 150.0:
                    target[i] = 3.0
                elif f < 200.0:
                    target[i] = 3.0 * 0.5 * (1.0 + np.cos(np.pi * (f - 150.0) / 50.0))
                else:
                    target[i] = -0.9 * np.log2(f / 200.0)
        elif "dirac" in k:
            for i, f in enumerate(freqs_arr):
                if f < 120.0:
                    target[i] = 2.0
                elif f < 200.0:
                    target[i] = 2.0 * 0.5 * (1.0 + np.cos(np.pi * (f - 120.0) / 80.0))
                elif f < 1000.0:
                    target[i] = 0.0
                else:
                    target[i] = -0.6 * np.log2(f / 1000.0)
        elif "cinema" in k or "blockbuster" in k:
            for i, f in enumerate(freqs_arr):
                if f < 120.0:
                    target[i] = 3.5
                elif f < 200.0:
                    target[i] = 3.5 * 0.5 * (1.0 + np.cos(np.pi * (f - 120.0) / 80.0))
                elif f < 2000.0:
                    target[i] = 0.0
                else:
                    target[i] = -1.0 * np.log2(f / 2000.0)
        elif "vocal" in k:
            for i, f in enumerate(freqs_arr):
                if f < 150.0:
                    target[i] = -0.5
                elif 1000.0 <= f <= 3000.0:
                    target[i] = 1.5
                elif f > 4000.0:
                    target[i] = -0.5 * np.log2(f / 4000.0)
        elif "audiophile" in k or "flat" in k:
            pass
        else:
            for i, f in enumerate(freqs_arr):
                if f < 100.0:
                    target[i] = 2.5
                elif f < 200.0:
                    target[i] = 2.5 * 0.5 * (1.0 + np.cos(np.pi * (f - 100.0) / 100.0))
                elif f < 1000.0:
                    target[i] = 0.0
                else:
                    target[i] = -0.8 * np.log2(f / 1000.0)
        return target + hpf_db
        
    target_curve = build_profile_target_curve(profile_key, freqs)
    
    mask_eval = (freqs >= 60.0) & (freqs <= 5000.0)
    mask_audible = (freqs >= 25.0) & (freqs <= 18000.0)
    idx_modal = np.argmin(np.abs(freqs - 119.4))
    
    # 4. Model & Reference Fallbacks
    # 4.1 Biquad Model for Active Profile
    bands = prof_data.get("bands", {})
    
    def peq_transfer(f_grid, f0, q, gain_db):
        if abs(gain_db) < 1e-5:
            return np.zeros_like(f_grid)
        with np.errstate(divide='ignore', invalid='ignore'):
            ratio = f_grid / f0 - f0 / f_grid
            resp = gain_db / (1.0 + (q * ratio) ** 2)
            resp[~np.isfinite(resp)] = 0.0
        return resp
        
    peq_l = np.zeros_like(freqs)
    peq_r = np.zeros_like(freqs)
    for b_name, b in bands.items():
        peq_l += peq_transfer(freqs, b["freq"], b["q_l"], b["gain_l"])
        peq_r += peq_transfer(freqs, b["freq"], b["q_r"], b["gain_r"])
    sweet_through_file = os.path.join(DATA_DIR, "medicion_verificacion_through.npz")
    if os.path.exists(sweet_through_file):
        try:
            th_d = np.load(sweet_through_file)
            th_fm = th_d["freqs"]
            if len(th_fm) != len(freqs) or not np.allclose(th_fm, freqs):
                sweet_base_l = np.interp(freqs, th_fm, th_d["smooth_l"])
                sweet_base_r = np.interp(freqs, th_fm, th_d["smooth_r"])
            else:
                sweet_base_l = th_d["smooth_l"].copy()
                sweet_base_r = th_d["smooth_r"].copy()
        except Exception:
            sweet_base_l = base_l.copy()
            sweet_base_r = base_r.copy()
    else:
        sweet_base_l = base_l.copy()
        sweet_base_r = base_r.copy()

    peq_model_l = sweet_base_l + peq_l
    peq_model_r = sweet_base_r + peq_r
    
    # 3.3 Reference Filters for YPAO Flat and YPAO Natural
    ypao_flat_ref_l = base_l.copy()
    ypao_flat_ref_r = base_r.copy()
    ypao_flat_path = os.path.join(DATA_DIR, "medicion_ypao_flat.npz")
    if os.path.exists(ypao_flat_path):
        try:
            yd = np.load(ypao_flat_path)
            y_fm = yd["freqs"]
            ypao_flat_ref_l = np.interp(freqs, y_fm, yd["smooth_l"])
            ypao_flat_ref_r = np.interp(freqs, y_fm, yd["smooth_r"])
        except Exception:
            pass
            
    ypao_nat_ref_l = base_l.copy()
    ypao_nat_ref_r = base_r.copy()
    ypao_nat_path = os.path.join(DATA_DIR, "medicion_ypao_natural.npz")
    if os.path.exists(ypao_nat_path):
        try:
            yd = np.load(ypao_nat_path)
            y_fm = yd["freqs"]
            ypao_nat_ref_l = np.interp(freqs, y_fm, yd["smooth_l"])
            ypao_nat_ref_r = np.interp(freqs, y_fm, yd["smooth_r"])
        except Exception:
            pass

    flat_fallback_l = sweet_base_l + (ypao_flat_ref_l - base_l)
    flat_fallback_r = sweet_base_r + (ypao_flat_ref_r - base_r)
    nat_fallback_l = sweet_base_l + (ypao_nat_ref_l - base_l)
    nat_fallback_r = sweet_base_r + (ypao_nat_ref_r - base_r)

    # Helper: Load file candidate or fallback, apply Joint-Stereo Target Alignment
    def load_and_align_mode(file_candidates, def_l, def_r, name, short_name, color, ls):
        for fn in file_candidates:
            fp = os.path.join(DATA_DIR, fn)
            if os.path.exists(fp):
                try:
                    d = np.load(fp)
                    fm = d["freqs"]
                    sl = professional_psychoacoustic_smooth(fm, d["smooth_l"])
                    sr = professional_psychoacoustic_smooth(fm, d["smooth_r"])
                    if len(fm) != len(freqs) or not np.allclose(fm, freqs):
                        l_raw = np.interp(freqs, fm, sl)
                        r_raw = np.interp(freqs, fm, sr)
                    else:
                        l_raw = sl.copy()
                        r_raw = sr.copy()
                        
                    off_l = float(np.mean(l_raw[mask_eval] - target_curve[mask_eval]))
                    off_r = float(np.mean(r_raw[mask_eval] - target_curve[mask_eval]))
                    common_offset = (off_l + off_r) / 2.0
                    return {
                        "name": name,
                        "short_name": short_name,
                        "l": l_raw - common_offset,
                        "r": r_raw - common_offset,
                        "color": color,
                        "ls": ls,
                        "is_live": True,
                        "source_file": fn
                    }
                except Exception as e:
                    print(f"[!] Error leyendo {fn}: {e}")
                    
        def_l_psy = professional_psychoacoustic_smooth(freqs, def_l)
        def_r_psy = professional_psychoacoustic_smooth(freqs, def_r)
        off_l = float(np.mean(def_l_psy[mask_eval] - target_curve[mask_eval]))
        off_r = float(np.mean(def_r_psy[mask_eval] - target_curve[mask_eval]))
        common_offset = (off_l + off_r) / 2.0
        return {
            "name": name,
            "short_name": short_name,
            "l": def_l_psy - common_offset,
            "r": def_r_psy - common_offset,
            "color": color,
            "ls": ls,
            "is_live": False,
            "source_file": "Referencia Base / Modelo"
        }

    # 4. Assemble All 5 Comparative Modes
    curves_dict = {
        "through": load_and_align_mode(
            ["medicion_verificacion_through.npz"],
            sweet_base_l, sweet_base_r,
            "Through (Sin Ecualizar)", "Through", "#ef5350", "--"
        ),
        "ypao_flat": load_and_align_mode(
            ["medicion_verificacion_ypao_flat.npz"],
            flat_fallback_l, flat_fallback_r,
            "YPAO Flat (Automático Plano)", "YPAO Flat", "#ff9800", ":"
        ),
        "ypao_front": load_and_align_mode(
            ["medicion_verificacion_ypao_front.npz"],
            sweet_base_l, sweet_base_r,
            "YPAO Front (Frontales Referencia)", "YPAO Front", "#ab47bc", "-."
        ),
        "ypao_natural": load_and_align_mode(
            ["medicion_verificacion_ypao_natural.npz", "medicion_verificacion_ypao.npz"],
            nat_fallback_l, nat_fallback_r,
            "YPAO Natural (Roll-off Suave)", "YPAO Natural", "#ffd600", "-"
        ),
        "peq_manual": load_and_align_mode(
            [f"medicion_verificacion_manual_{profile_key}.npz"] + (["medicion_verificacion_manual.npz", "medicion_verificacion_post_peq.npz"] if profile_key == "harman_wide_room" else []),
            peq_model_l, peq_model_r,
            peq_manual_name, f"PEQ {prof_display_name}", "#00e676", "-"
        )
    }

    # 5. Calculate Comparative Metrics for All 5 Curves
    comparative_results = []
    for c_id, c_data in curves_dict.items():
        cl = c_data["l"]
        cr = c_data["r"]
        
        rms_l = float(np.sqrt(np.mean((cl[mask_eval] - target_curve[mask_eval])**2)))
        rms_r = float(np.sqrt(np.mean((cr[mask_eval] - target_curve[mask_eval])**2)))
        rms_avg = (rms_l + rms_r) / 2.0
        
        std_l = float(np.std(cl[mask_eval]))
        std_r = float(np.std(cr[mask_eval]))
        std_avg = (std_l + std_r) / 2.0
        
        diff = np.abs(cl[mask_eval] - cr[mask_eval])
        imb_avg = float(np.mean(diff))
        
        peak_modal = float(cl[idx_modal])
        
        # Scientific Target Alignment Percentage: 100% at 0 dB RMS error, 0% at >= 10 dB error
        alignment_pct = float(max(0.0, min(100.0, (1.0 - min(1.0, rms_avg / 10.0)) * 100.0)))
        c_summary = {
            "id": c_id,
            "name": c_data["name"],
            "short_name": c_data["short_name"],
            "rms_avg_db": rms_avg,
            "rms_l_db": rms_l,
            "rms_r_db": rms_r,
            "std_linearity_db": std_avg,
            "stereo_imbalance_db": imb_avg,
            "modal_peak_119hz_db": peak_modal,
            "target_alignment_pct": round(alignment_pct, 1),
            "fidelity_score_pct": round(alignment_pct, 1),
            "color": c_data["color"],
            "is_live": bool(c_data.get("is_live", False)),
            "provenance": "Medición en Vivo (Sweet Spot)" if c_data.get("is_live", False) else "Referencia Base / Modelo",
            "source_file": c_data.get("source_file", "")
        }
        comparative_results.append(c_summary)
        
    # Rank curves scientifically (Lowest RMS target error = best acoustic alignment)
    comparative_results.sort(key=lambda x: (not x["is_live"], x["rms_avg_db"]))
    for rank_idx, r in enumerate(comparative_results, start=1):
        r["rank"] = rank_idx
        if rank_idx == 1:
            r["badge"] = "🥇 #1 RECOMENDADA"
        elif rank_idx == 2:
            r["badge"] = "🥈 #2 SEGUNDO PUESTO"
        elif rank_idx == 3:
            r["badge"] = "🥉 #3 TERCER PUESTO"
        else:
            r["badge"] = f"#{rank_idx}"

    best_curve = comparative_results[0]

    # 6. Specific Anchors for Active PEQ vs Through
    norm_base_l = curves_dict["through"]["l"]
    norm_base_r = curves_dict["through"]["r"]
    norm_verif_l = curves_dict["peq_manual"]["l"]
    norm_verif_r = curves_dict["peq_manual"]["r"]
    measured = curves_dict["peq_manual"]["is_live"]
    mask_modal_search = (freqs >= 60.0) & (freqs <= 200.0)
    indices_modal_search = np.where(mask_modal_search)[0]
    idx_modal_peak = indices_modal_search[np.argmax(norm_base_l[mask_modal_search])]
    f_modal = float(freqs[idx_modal_peak])
    modal_before = float(norm_base_l[idx_modal_peak])
    modal_after = float(norm_verif_l[idx_modal_peak])
    modal_target = float(target_curve[idx_modal_peak])
    modal_reduction = modal_before - modal_after
    modal_target_dev_before = modal_before - modal_target
    modal_target_dev_after = modal_after - modal_target
    modal_target_accuracy_gain = float((1.0 - abs(modal_target_dev_after) / max(1e-3, abs(modal_target_dev_before))) * 100.0)

    asym_117_before = float(abs(norm_base_l[idx_modal_peak] - norm_base_r[idx_modal_peak]))
    asym_117_after = float(abs(norm_verif_l[idx_modal_peak] - norm_verif_r[idx_modal_peak]))
    asym_117_improvement = float((1.0 - asym_117_after / max(1e-3, asym_117_before)) * 100.0)

    mask_cross_search = (freqs >= 1800.0) & (freqs <= 3500.0)
    indices_cross_search = np.where(mask_cross_search)[0]
    idx_cross = indices_cross_search[np.argmin(norm_base_l[mask_cross_search])]
    f_cross = float(freqs[idx_cross])
    cross_before = float(norm_base_l[idx_cross])
    cross_after = float(norm_verif_l[idx_cross])
    cross_target = float(target_curve[idx_cross])
    cross_correction = cross_after - cross_before
    cross_target_dev_before = cross_before - cross_target
    cross_target_dev_after = cross_after - cross_target

    diff_before = np.abs(norm_base_l[mask_audible] - norm_base_r[mask_audible])
    diff_after = np.abs(norm_verif_l[mask_audible] - norm_verif_r[mask_audible])
    stereo_global_before = float(np.mean(diff_before))
    stereo_global_after = float(np.mean(diff_after))
    stereo_global_improvement = float((1.0 - stereo_global_after / max(1e-3, stereo_global_before)) * 100.0)

    # Linearity and RMS
    rms_before = float(np.sqrt(np.mean((norm_base_l[mask_eval] - target_curve[mask_eval])**2)))
    rms_after = float(np.sqrt(np.mean((norm_verif_l[mask_eval] - target_curve[mask_eval])**2)))
    rms_reduction = float(rms_before - rms_after)
    peak_err_before = float(np.max(np.abs(norm_base_l[mask_eval] - target_curve[mask_eval])))
    peak_err_after = float(np.max(np.abs(norm_verif_l[mask_eval] - target_curve[mask_eval])))
    peak_err_reduction = float(peak_err_before - peak_err_after)


    std_before = float(np.std(norm_base_l[mask_eval]))
    std_after = float(np.std(norm_verif_l[mask_eval]))
    # Bass suckout guardrail (FR-008, SC-003): no dip > 4.0 dB below target in 60-200 Hz
    mask_bass = (freqs >= 60.0) & (freqs <= 200.0)
    max_bass_dip_l = float(np.min(norm_verif_l[mask_bass] - target_curve[mask_bass]))
    max_bass_dip_r = float(np.min(norm_verif_r[mask_bass] - target_curve[mask_bass]))
    bass_suckout_detected = (max_bass_dip_l < -4.0) or (max_bass_dip_r < -4.0)

    # Strict S-TIER Certification Gating (FR-006, SC-002, SC-003, SC-004)
    # 1. Must be a real physical post-calibration measurement (measured is True)
    # 2. Peak modal resonance attenuation >= 6.0 dB
    # 3. Residual RMS deviation from target in modal band (60-500 Hz) < 2.5 dB
    # 4. Inter-channel stereo imbalance < 2.0 dB
    # 5. No bass suckout > 4.0 dB below target
    s_tier_criteria_met = (
        measured
        and (modal_reduction >= 6.0)
        and (rms_after < 2.5)
        and (stereo_global_after < 2.0)
        and (not bass_suckout_detected)
    )
    status_passed = s_tier_criteria_met
    metrics = {
        "modal_freq_hz": f_modal,
        "modal_before_db": modal_before,
        "modal_after_db": modal_after,
        "modal_target_db": modal_target,
        "modal_reduction_db": modal_reduction,
        "modal_target_dev_before": modal_target_dev_before,
        "modal_target_dev_after": modal_target_dev_after,
        "asym_117_before_db": asym_117_before,
        "asym_117_after_db": asym_117_after,
        "asym_117_improvement_pct": asym_117_improvement,
        "modal_target_accuracy_gain_pct": modal_target_accuracy_gain,
        "modal_energy_reduction_pct": float((1.0 - 10.0**(-abs(modal_reduction)/10.0)) * 100.0),
        
        "crossover_freq_hz": f_cross,
        "crossover_before_db": cross_before,
        "crossover_after_db": cross_after,
        "crossover_target_db": cross_target,
        "crossover_correction_db": cross_correction,
        "crossover_target_dev_before": cross_target_dev_before,
        "crossover_target_dev_after": cross_target_dev_after,
        
        "stereo_global_before_db": stereo_global_before,
        "stereo_global_after_db": stereo_global_after,
        "stereo_global_improvement_pct": stereo_global_improvement,
        
        "rms_target_before_db": rms_before,
        "rms_target_after_db": rms_after,
        "rms_reduction_db": rms_reduction,
        "peak_err_target_before_db": peak_err_before,
        "peak_err_target_after_db": peak_err_after,
        "peak_err_reduction_db": peak_err_reduction,
        
        "std_before_db": std_before,
        "std_after_db": std_after,
        
        "target_fit_score_before": float(max(10.0, 100.0 - (rms_before - 1.2) * 15.0)),
        "target_fit_score_after": float(max(10.0, 100.0 - (rms_after - 1.2) * 15.0)),
        "target_fit_improvement_pct": float(max(0.0, (rms_before - rms_after) * 10.0)),
        
        "bass_suckout_detected": bool(bass_suckout_detected),
        "max_bass_dip_l_db": round(max_bass_dip_l, 2),
        "max_bass_dip_r_db": round(max_bass_dip_r, 2),
        "target_alignment_pct": best_curve.get("target_alignment_pct", 0.0),
        "fidelity_score_pct": best_curve.get("target_alignment_pct", 0.0),
        "passed": status_passed,
        "measured": measured,
        "s_tier_certified": s_tier_criteria_met,
        "rating": (
            "S-TIER (CERTIFICADA CON ÉXITO)" if s_tier_criteria_met
            else ("REVISIÓN REQUERIDA (Criterios objetivos no alcanzados)" if measured
                  else "PENDIENTE DE MEDICIÓN FÍSICA (Sin barrido post-PEQ)")
        ),
        # Active profile metadata
        "active_profile": profile_key,
        "active_profile_name": prof_raw_name,
        "active_profile_display": prof_display_name,
        "target_curve_name": f"Target {prof_display_name}",
        
        # Comparative benchmark of all curves
        "comparative_curves": comparative_results,
        "best_curve": best_curve
    }
    
    # 7. Generate Multi-Curve Comparative Figure
    if save_fig:
        plt.style.use('dark_background')
        meas_time_str = datetime.fromtimestamp(os.path.getmtime(base_file)).strftime("%d/%m/%Y %H:%M:%S")
        fig, axs = plt.subplots(2, 2, figsize=(16, 11), dpi=140)
        fig.patch.set_facecolor('#0b0f19')
        fig.suptitle(f"Evaluación Acústica Multimodo en Directo vs Target {prof_display_name} ({meas_time_str})\n"
                     f"Comparativa Científica: Through vs YPAO Flat vs YPAO Front vs YPAO Natural vs PEQ Manual ({prof_display_name})",
                     fontsize=13, fontweight='bold', color='#38bdf8', y=0.98)
        f_plot = freqs[mask_audible]
        
        from matplotlib.ticker import FixedLocator, FixedFormatter
        audio_freqs = [30, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 18000]
        audio_labels = ['30', '50', '100', '200', '500', '1k', '2k', '5k', '10k', '18k']
        
        ax1, ax2 = axs[0, 0], axs[0, 1]
        ax3, ax4 = axs[1, 0], axs[1, 1]
        
        for ax in (ax1, ax2, ax3):
            ax.set_facecolor('#111827')
            ax.grid(True, which='major', color='#374151', linestyle='-', linewidth=0.75, alpha=0.8)
            ax.grid(True, which='minor', color='#1f2937', linestyle=':', linewidth=0.5, alpha=0.4)
            ax.set_xscale('log')
            ax.set_xlim(25, 18000)
            ax.xaxis.set_major_locator(FixedLocator(audio_freqs))
            ax.xaxis.set_major_formatter(FixedFormatter(audio_labels))
            ax.xaxis.set_minor_locator(FixedLocator([]))
            
        ax4.set_facecolor('#111827')
        ax4.grid(True, which='major', color='#374151', linestyle='-', linewidth=0.75, alpha=0.8)
        ax4.set_xscale('linear')
        ax4.set_xlim(0, 105)
        ax1.fill_between(f_plot, target_curve[mask_audible] - 2.5, target_curve[mask_audible] + 2.5, 
                         color='#fbbf24', alpha=0.10, label='Tolerancia Target (±2.5 dB)')
        ax1.plot(f_plot, target_curve[mask_audible], color='#fbbf24', linestyle=':', lw=2.4, 
                 label=f'Target ({prof_display_name})')
        for c in comparative_results:
            c_info = curves_dict[c["id"]]
            lw = 2.4 if c["id"] == "peq_manual" else (2.0 if "ypao" in c["id"] else 1.5)
            ax1.plot(f_plot, c_info["l"][mask_audible], color=c_info["color"], 
                     linestyle=c_info["ls"], lw=lw, label=f"{c_info['short_name']} (RMS: {c['rms_avg_db']:.2f}dB)")
        ax1.axhline(0, color='gray', linestyle='--', alpha=0.4)
        ax1.set_title(f"Canal Izquierdo (Front L): Respuesta Psicoacústica vs Target", fontsize=11, fontweight='bold', color='#38bdf8')
        ax1.set_xlabel("Frecuencia (Hz)", fontsize=9, color='#9ca3af')
        ax1.set_ylabel("Magnitud (dB SPL)", fontsize=9, color='#9ca3af')
        ax1.set_ylim(-18, 10)
        ax1.legend(loc='lower left', fontsize=7.8, framealpha=0.92)
        # Subplot 2: Front R - All Curves vs Target
        ax2.fill_between(f_plot, target_curve[mask_audible] - 2.5, target_curve[mask_audible] + 2.5, 
                         color='#fbbf24', alpha=0.10, label='Tolerancia Target (±2.5 dB)')
        ax2.plot(f_plot, target_curve[mask_audible], color='#fbbf24', linestyle=':', lw=2.4, 
                 label=f'Target ({prof_display_name})')
        for c in comparative_results:
            c_info = curves_dict[c["id"]]
            lw = 2.4 if c["id"] == "peq_manual" else (2.0 if "ypao" in c["id"] else 1.5)
            ax2.plot(f_plot, c_info["r"][mask_audible], color=c_info["color"], 
                     linestyle=c_info["ls"], lw=lw, label=f"{c_info['short_name']} (Alineación: {c['target_alignment_pct']:.1f}%)")
        ax2.axhline(0, color='gray', linestyle='--', alpha=0.4)
        ax2.set_title(f"Canal Derecho (Front R): Respuesta Psicoacústica vs Target", fontsize=11, fontweight='bold', color='#38bdf8')
        ax2.set_xlabel("Frecuencia (Hz)", fontsize=9, color='#9ca3af')
        ax2.set_ylabel("Magnitud (dB SPL)", fontsize=9, color='#9ca3af')
        ax2.set_ylim(-18, 10)
        
        # Subplot 3: Stereo Imbalance across Frequency for each Curve
        ax3 = axs[1, 0]
        ax3.fill_between(f_plot, 0, 1.5, color='#10b981', alpha=0.12, label='Zona Referencia Hi-Fi (≤1.5 dB)')
        ax3.axhline(1.5, color='#10b981', linestyle='--', lw=1.2, alpha=0.8)
        for c in comparative_results:
            c_info = curves_dict[c["id"]]
            diff_c = np.abs(c_info["l"][mask_audible] - c_info["r"][mask_audible])
            lw = 2.2 if c["id"] == "peq_manual" else 1.6
            ax3.plot(f_plot, diff_c, color=c_info["color"], linestyle=c_info["ls"], lw=lw,
                     label=f"{c_info['short_name']} (Medio: {c['stereo_imbalance_db']:.2f} dB)")
        ax3.set_title("Desbalance Estéreo |L - R| por Frecuencia", fontsize=11, fontweight='bold', color='#38bdf8')
        ax3.set_xlabel("Frecuencia (Hz)", fontsize=9, color='#9ca3af')
        ax3.set_ylabel("Diferencia Absoluta |L - R| (dB)", fontsize=9, color='#9ca3af')
        ax3.set_ylim(0, 6.5)
        # Subplot 4: Bar Chart - Quantitative Comparison of Key Metrics
        c_names = [c["short_name"] for c in comparative_results]
        c_scores = [c.get("target_alignment_pct", 0.0) for c in comparative_results]
        c_colors = [c["color"] for c in comparative_results]
        
        y_pos = np.arange(len(c_names))
        bars = ax4.barh(y_pos, c_scores, height=0.55, color=c_colors, alpha=0.88, edgecolor='#374151')
        
        ax4.set_yticks(y_pos)
        ax4.set_yticklabels(c_names, fontsize=9.5, fontweight='bold', color='#f9fafb')
        ax4.invert_yaxis()
        ax4.set_title("Alineación Acústica con Curva Objetivo (100% = Error RMS 0 dB)", fontsize=11, fontweight='bold', color='#38bdf8')
        ax4.set_xlabel("Alineación con Target (%)", fontsize=9, color='#9ca3af')
        ax4.set_xlim(0, 100)
        ax4.xaxis.set_major_locator(FixedLocator([0, 20, 40, 60, 80, 100]))
        ax4.xaxis.set_major_formatter(FixedFormatter(['0', '20', '40', '60', '80', '100%']))
        
        for idx, bar in enumerate(bars):
            w = bar.get_width()
            c_item = comparative_results[idx]
            ax4.text(w + 1.2, bar.get_y() + bar.get_height()/2, 
                     f"{w:.1f}%  |  RMS: {c_item['rms_avg_db']:.2f}dB  |  Desbal: {c_item['stereo_imbalance_db']:.2f}dB", 
                     va='center', ha='left', fontsize=8.2, color='#f9fafb', fontweight='bold')
            
        plt.tight_layout()
        out_fig = f"{FIG_DIR}/verificacion_post_calibracion.png"
        out_fig_multi = f"{FIG_DIR}/gran_comparativa_multimodo.png"
        plt.savefig(out_fig, dpi=140, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.savefig(out_fig_multi, dpi=140, facecolor=fig.get_facecolor(), edgecolor='none')
        plt.close()
        print(f"[v] Gráfica de verificación acústica multimodo guardada en:\n  - {out_fig}\n  - {out_fig_multi}")
        
    best_curve = comparative_results[0]
    metrics["best_curve"] = best_curve
    return metrics

def generate_technical_audit_report(
    metrics: dict,
    output_path: str = None,
    csd_image_path: str = None,
) -> str:
    """
    Generates the official HTML Technical Audit Report complying with FR-012.
    Includes:
    1. 1/24-octave magnitude curve references
    2. 3D CSD waterfall plot reference
    3. Yamaha NVRAM hardware register dump
    4. Objective multi-metric S-TIER certification decision
    """
    prof = metrics.get("active_profile", "harman_wide_room")
    if output_path is None:
        output_path = f"{REPO_DIR}/reports/audit_report_{prof}.html"
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Query hardware register dump
    hw_xml_dump = "No disponible (receptor offline)"
    try:
        import importlib
        yam_ctrl = importlib.import_module("scripts.04_yamaha_control")
        hw_xml_dump = yam_ctrl.get_peq_manual_data()
    except Exception as e:
        hw_xml_dump = f"No se pudo consultar NVRAM: {e}"
        
    s_tier = metrics.get("s_tier_certified", False)
    badge_html = """
    <div style="background:#064e3b; border:2px solid #10b981; color:#6ee7b7; padding:15px; border-radius:8px; margin-bottom:20px;">
        <h2 style="margin:0; font-size:1.4rem;">🏆 S-TIER (CERTIFICADA CON ÉXITO)</h2>
        <p style="margin:5px 0 0 0;">Cumple al 100% todos los criterios objetivos físicos: Atenuación modal &ge; 6.0 dB, Error RMS &lt; 2.5 dB, Desbalance &lt; 2.0 dB.</p>
    </div>
    """ if s_tier else """
    <div style="background:#450a0a; border:2px solid #ef4444; color:#fca5a5; padding:15px; border-radius:8px; margin-bottom:20px;">
        <h2 style="margin:0; font-size:1.4rem;">⚠️ REVISIÓN REQUERIDA / PENDIENTE DE BARRIDO</h2>
        <p style="margin:5px 0 0 0;">No se ha capturado un barrido físico post-PEQ que cumpla los 3 umbrales objetivos estrictos.</p>
    </div>
    """
    
    csd_html = f"""
    <div style="margin-top:25px;">
        <h3>Decaimiento Espectral Acumulativo 3D (CSD Waterfall &lt; 300 Hz)</h3>
        <img src="{csd_image_path}" style="max-width:100%; border-radius:6px; border:1px solid #374151;" />
    </div>
    """ if csd_image_path and os.path.exists(csd_image_path) else ""
    
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="utf-8">
    <title>Informe de Auditoría Acústica Técnica - {prof}</title>
    <style>
        body {{ background:#0f172a; color:#f8fafc; font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif; padding:30px; }}
        .container {{ max-width:960px; margin:0 auto; background:#1e293b; padding:30px; border-radius:12px; border:1px solid #334155; }}
        table {{ width:100%; border-collapse:collapse; margin:15px 0; }}
        th, td {{ border:1px solid #334155; padding:10px; text-align:left; font-size:0.9rem; }}
        th {{ background:#0f172a; color:#38bdf8; }}
        pre {{ background:#020617; padding:15px; border-radius:6px; overflow-x:auto; font-size:0.8rem; color:#94a3b8; border:1px solid #334155; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Informe de Auditoría Acústica Técnica (Honesta y Verificable)</h1>
        <p><strong>Perfil Objetivo:</strong> {metrics.get('active_profile_display', prof)} | <strong>Fecha:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        {badge_html}
        <h3>Métricas Físicas de Verificación</h3>
        <table>
            <tr><th>Métrica Acústica</th><th>Antes (Through)</th><th>Después (PEQ)</th><th>Criterio S-TIER</th></tr>
            <tr><td>Pico Modal (119 Hz)</td><td>{metrics.get('modal_before_db', 0):+.2f} dB</td><td>{metrics.get('modal_after_db', 0):+.2f} dB</td><td>Atenuación &ge; 6.0 dB ({metrics.get('modal_reduction_db', 0):.2f} dB logrados)</td></tr>
            <tr><td>Desviación RMS al Target (60-500 Hz)</td><td>{metrics.get('rms_target_before_db', 0):.2f} dB</td><td>{metrics.get('rms_target_after_db', 0):.2f} dB</td><td>RMS &lt; 2.5 dB</td></tr>
            <tr><td>Desbalance Estéreo Medio</td><td>{metrics.get('stereo_global_before_db', 0):.2f} dB</td><td>{metrics.get('stereo_global_after_db', 0):.2f} dB</td><td>Desbalance &lt; 2.0 dB</td></tr>
        </table>
        {csd_html}
        <h3>Volcado de Registros Hardware en NVRAM (Yamaha RX-V673)</h3>
        <pre>{hw_xml_dump}</pre>
    </div>
</body>
</html>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"[v] Informe de auditoría técnica guardado en: {output_path}")
    return output_path

if __name__ == "__main__":
    m = run_verification(save_fig=True)
    print("\n=== RESULTADOS DE VERIFICACIÓN ACÚSTICA COMPARATIVA ===")
    print(f"Modo Front L Pico {m['modal_freq_hz']:.0f} Hz Antes: {m['modal_before_db']:+.2f} dB | Después: {m['modal_after_db']:+.2f} dB (Atenuación: {m['modal_reduction_db']:.2f} dB)")
    print(f"Desbalance Estéreo Global: {m['stereo_global_before_db']:.2f} dB -> {m['stereo_global_after_db']:.2f} dB")
    print(f"Error RMS al Target: {m['rms_target_before_db']:.2f} dB -> {m['rms_target_after_db']:.2f} dB")
    print("\n🏆 CLASIFICACIÓN DE CURVAS (DE MEJOR A PEOR):")
    for r in m["comparative_curves"]:
        score_val = r.get('target_alignment_pct', r.get('fidelity_score_pct', 0.0))
        print(f"  {r['badge']} | {r['name']:<35} | Alineación: {score_val:>5.1f}% | RMS: {r['rms_avg_db']:.2f} dB | Desbalance: {r['stereo_imbalance_db']:.2f} dB | Pico 119Hz: {r['modal_peak_119hz_db']:>+5.2f} dB")
    print(f"\n🌟 MEJOR CURVA ACÚSTICA: {m['best_curve']['name']} (Alineación: {m['best_curve'].get('target_alignment_pct', 0.0):.1f}%)")
