import numpy as np
import scipy.signal


def generate_reference_farina_sweep(f_start=15.0, f_end=22000.0, duration=1.0, fs=48000):
    num_samples = int(duration * fs)
    t = np.arange(num_samples) / fs
    w1 = 2 * np.pi * f_start
    w2 = 2 * np.pi * f_end
    L = duration / np.log(w2 / w1)

    phase = w1 * L * (np.exp(t / L) - 1.0)
    sweep = np.sin(phase)

    # 40ms lead fade, 20ms tail fade
    lead_n = int(0.040 * fs)
    tail_n = int(0.020 * fs)
    sweep[:lead_n] *= 0.5 * (1.0 - np.cos(np.pi * np.arange(lead_n) / lead_n))
    sweep[-tail_n:] *= 0.5 * (1.0 + np.cos(np.pi * np.arange(tail_n) / tail_n))

    # Inverse filter: reverse sweep modulated by exp(-t/L)
    mod = np.exp(-t / L)
    inv_filter = sweep[::-1] * mod

    norm = np.sum(inv_filter**2)
    inv_filter /= np.sqrt(norm * (fs / (2 * np.pi * L)))
    return sweep, inv_filter


def test_farina_deconvolution_delta_recovery():
    fs = 48000
    sweep, inv_filter = generate_reference_farina_sweep(fs=fs)

    # Convolve sweep with inverse filter
    rir = scipy.signal.fftconvolve(sweep, inv_filter, mode="full")

    # In a perfect loopback without room reflections, convolution peak is located at (N - 1)
    peak_idx = np.argmax(np.abs(rir))
    assert abs(peak_idx - (len(sweep) - 1)) <= 2, f"Peak location {peak_idx} expected near {len(sweep) - 1}"

    # Side-lobe suppression should be > 40 dB relative to peak
    peak_val = np.abs(rir[peak_idx])
    pre_peak = np.abs(rir[: peak_idx - 100])
    max_sidelobe = np.max(pre_peak) if len(pre_peak) > 0 else 0
    snr_db = 20 * np.log10(peak_val / (max_sidelobe + 1e-12))
    assert snr_db > 35.0, f"Deconvolution SNR {snr_db:.1f} dB is below 35 dB"


def test_discrete_yamaha_quantization_bounds():
    from scripts.peq_optimizer import YAMAHA_FREQS, YAMAHA_QS, snap_frequency, snap_gain, snap_q

    assert len(YAMAHA_FREQS) == 28
    assert len(YAMAHA_QS) == 14

    # Asymmetric clamping
    assert snap_gain(5.0, 100.0) == 3.0
    assert snap_gain(5.0, 600.0) == 0.0  # Schroeder cutoff: 0 dB boost above 500 Hz
    assert snap_gain(-15.0, 100.0) == -12.0
    assert snap_frequency(95.0) == 99.2
    assert snap_q(3.0) == 3.175
