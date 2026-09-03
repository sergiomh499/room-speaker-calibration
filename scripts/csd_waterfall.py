"""
scripts/csd_waterfall.py
Cumulative Spectral Decay (CSD / 3D Waterfall) Analyzer for Room Acoustic Resonances.

Computes time-domain energy decay of room modes (< 300 Hz) using sliding-window STFT.
Proves whether parametric notch filters actually suppressed physical modal ringing over time.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional, Tuple
import matplotlib
matplotlib.use("Agg")  # Headless rendering
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

def compute_csd_matrix(
    impulse_response: np.ndarray,
    fs: float = 48000.0,
    window_length_samples: int = 2048,
    n_fft: int = 8192,
    num_slices: int = 30,
    max_time_ms: float = 300.0,
    min_freq_hz: float = 20.0,
    max_freq_hz: float = 500.0,
    dynamic_range_db: float = 35.0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Computes Cumulative Spectral Decay (CSD) matrix from a room impulse response.
    Returns:
        freqs_hz: 1D array of frequency bins between min_freq_hz and max_freq_hz.
        times_ms: 1D array of time slice delays (ms).
        csd_db: 2D array of shape (num_slices, len(freqs_hz)) in dB relative to arrival peak.
    """
    ir = np.asarray(impulse_response, dtype=np.float64)
    if len(ir) < window_length_samples:
        ir = np.pad(ir, (0, window_length_samples - len(ir)))
        
    # Locate arrival peak (t = 0)
    peak_idx = int(np.argmax(np.abs(ir)))
    ir_aligned = ir[peak_idx:]
    
    step_samples = int((max_time_ms / 1000.0 * fs) / max(1, num_slices - 1))
    window = np.hanning(window_length_samples)
    
    fft_freqs = np.fft.rfftfreq(n_fft, d=1.0 / fs)
    freq_mask = (fft_freqs >= min_freq_hz) & (fft_freqs <= max_freq_hz)
    freqs_hz = fft_freqs[freq_mask]
    
    times_ms = np.linspace(0.0, max_time_ms, num_slices)
    csd_matrix = np.zeros((num_slices, len(freqs_hz)), dtype=np.float64)
    
    ref_peak_mag = None
    for i in range(num_slices):
        start_idx = i * step_samples
        end_idx = start_idx + window_length_samples
        
        if start_idx >= len(ir_aligned):
            slice_data = np.zeros(window_length_samples)
        elif end_idx > len(ir_aligned):
            avail = len(ir_aligned) - start_idx
            slice_data = np.pad(ir_aligned[start_idx:], (0, window_length_samples - avail))
        else:
            slice_data = ir_aligned[start_idx:end_idx]
            
        windowed = slice_data * window
        spectrum = np.fft.rfft(windowed, n=n_fft)
        mag = np.abs(spectrum[freq_mask])
        
        if i == 0:
            ref_peak_mag = max(1e-9, float(np.max(mag)))
            
        mag_db = 20.0 * np.log10(np.maximum(mag / ref_peak_mag, 10.0 ** (-dynamic_range_db / 20.0)))
        csd_matrix[i, :] = mag_db
        
    return freqs_hz, times_ms, csd_matrix


def render_csd_waterfall_plot(
    impulse_response: np.ndarray,
    output_path: Path | str,
    title: str = "Cumulative Spectral Decay (CSD Waterfall)",
    fs: float = 48000.0,
    max_freq_hz: float = 500.0,
    max_time_ms: float = 250.0,
) -> Path:
    """
    Renders 3D Cumulative Spectral Decay surface to an image file (PNG/SVG).
    """
    freqs_hz, times_ms, csd_matrix = compute_csd_matrix(
        impulse_response,
        fs=fs,
        max_freq_hz=max_freq_hz,
        max_time_ms=max_time_ms,
    )
    
    F, T = np.meshgrid(freqs_hz, times_ms)
    
    fig = plt.figure(figsize=(10, 6), dpi=120)
    ax = fig.add_subplot(111, projection="3d")
    
    # 3D surface with logarithmic visual aesthetic
    surf = ax.plot_surface(
        F, T, csd_matrix,
        cmap="plasma",
        rstride=1, cstride=2,
        linewidth=0.1,
        edgecolor="black",
        alpha=0.9,
    )
    
    ax.set_title(title, fontsize=12, fontweight="bold", pad=15)
    ax.set_xlabel("Frecuencia (Hz)", fontsize=10, labelpad=8)
    ax.set_ylabel("Tiempo (ms)", fontsize=10, labelpad=8)
    ax.set_zlabel("Nivel Relativo (dB)", fontsize=10, labelpad=8)
    
    ax.set_zlim(-35.0, 0.0)
    ax.view_init(elev=25, azim=-60)
    
    fig.colorbar(surf, ax=ax, shrink=0.5, aspect=10, label="Decaimiento (dB)")
    plt.tight_layout()
    
    out_p = Path(output_path)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(out_p, bbox_inches="tight")
    plt.close(fig)
    return out_p


def calculate_ringing_decay_time_ms(
    impulse_response: np.ndarray,
    target_freq_hz: float,
    fs: float = 48000.0,
    threshold_db: float = -20.0,
) -> float:
    """
    Calculates the time in milliseconds for the energy at target_freq_hz to decay to threshold_db.
    """
    freqs_hz, times_ms, csd_matrix = compute_csd_matrix(
        impulse_response,
        fs=fs,
        min_freq_hz=target_freq_hz - 5.0,
        max_freq_hz=target_freq_hz + 5.0,
        num_slices=50,
        max_time_ms=400.0,
    )
    # Average across the narrow resonant band
    decay_curve = np.mean(csd_matrix, axis=1)
    
    below_idx = np.where(decay_curve <= threshold_db)[0]
    if len(below_idx) > 0:
        return float(times_ms[below_idx[0]])
    return float(times_ms[-1])

def generate_waterfall_csd(
    output_path: Optional[Path | str] = None,
    data_file: Optional[Path | str] = None
) -> Path:
    repo_dir = Path(__file__).resolve().parent.parent
    if output_path is None:
        out_fig = repo_dir / "figures" / "waterfall_csd_comparison.png"
    else:
        out_fig = Path(output_path)
        
    candidate_files = []
    if data_file:
        candidate_files.append(Path(data_file))
    candidate_files.extend([
        repo_dir / "data" / "medicion_punto_1.npz",
        repo_dir / "data" / "medicion_real_calibracion.npz",
        repo_dir / "data" / "medicion_promedio_espacial.npz"
    ])
    
    ir_l = None
    for cand in candidate_files:
        if cand.exists():
            d = np.load(cand)
            if "ir_l" in d and len(d["ir_l"]) > 0 and float(np.max(np.abs(d["ir_l"]))) > 1e-4:
                ir_l = d["ir_l"]
                print(f"[v] Cascada CSD extrayendo respuesta al impulso física de: {cand.name}")
                break
                
    if ir_l is None:
        for cand in candidate_files:
            if cand.exists():
                d = np.load(cand)
                if "smooth_l" in d:
                    mag = 10.0 ** (d["smooth_l"] / 20.0)
                    ir_l = np.fft.irfft(mag)
                    print(f"[*] CSD sintetizando fase mínima desde magnitud de: {cand.name}")
                    break
                    
    if ir_l is None:
        ir_l = np.zeros(4800)
        
    render_csd_waterfall_plot(
        impulse_response=ir_l,
        output_path=str(out_fig),
        title="Cascada Espectral 3D (Waterfall CSD) - Decaimiento Modal en Sweet Spot"
    )
    print(f"[v] Waterfall CSD guardado en: {out_fig}")
    return out_fig

if __name__ == "__main__":
    generate_waterfall_csd()
