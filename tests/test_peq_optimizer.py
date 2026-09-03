"""
tests/test_peq_optimizer.py
Unit tests and mathematical convergence benchmarks for the dynamic discrete PEQ optimizer.
"""

import time
import unittest
import numpy as np

from scripts.peq_optimizer import (
    YAMAHA_FREQS,
    YAMAHA_QS,
    MAX_BOOST_DB,
    MAX_CUT_DB,
    biquad_peaking_response,
    detect_modal_resonances,
    multi_filter_response,
    optimize_channel_peq,
    optimize_stereo_peq,
    snap_frequency,
    snap_gain,
    snap_q,
)

class TestPEQOptimizer(unittest.TestCase):
    def test_parameter_snapping_to_yamaha_hardware_matrix(self):
        """Validates that continuous inputs snap strictly to discrete allowable Yamaha DSP values."""
        # Frequencies
        self.assertEqual(snap_frequency(61.2), 62.5)
        self.assertEqual(snap_frequency(110.0), 99.2)
        self.assertEqual(snap_frequency(118.0), 125.0)
        self.assertEqual(snap_frequency(2450.0), 2520.0)
        self.assertIn(snap_frequency(150.0), YAMAHA_FREQS)

        # Q factors
        self.assertEqual(snap_q(0.95), 1.000)
        self.assertEqual(snap_q(1.8), 2.000)
        self.assertEqual(snap_q(15.0), 10.080)  # Capped at highest hardware Q
        self.assertIn(snap_q(2.4), YAMAHA_QS)

    def test_gain_clamping_and_schroeder_boundary_rules(self):
        """Validates acoustic safety gain limits and zero-boost above 500 Hz."""
        # Low frequency mode: allow up to +3.0 dB boost
        self.assertEqual(snap_gain(2.8, 80.0), 3.0)
        self.assertEqual(snap_gain(5.5, 80.0), 3.0)  # Clamped to +3.0 dB
        self.assertEqual(snap_gain(-15.0, 80.0), -12.0)  # Clamped to -12.0 dB
        self.assertEqual(snap_gain(-4.23, 80.0), -4.0)  # Snapped to 0.5 dB step

        # High frequency (> 500 Hz): positive boost prohibited
        self.assertEqual(snap_gain(2.0, 1000.0), 0.0)
        self.assertEqual(snap_gain(-3.0, 1000.0), -3.0)  # Cuts are allowed

    def test_biquad_peaking_frequency_response(self):
        """Validates that the digital biquad peaking filter computes correct notch attenuation."""
        freqs = np.linspace(20, 1000, 500)
        f0 = 100.0
        gain = -6.0
        q = 2.0
        resp = biquad_peaking_response(freqs, f0, q, gain, fs=48000.0)
        
        # At center frequency, gain should be approximately -6 dB
        idx_f0 = np.argmin(np.abs(freqs - f0))
        self.assertAlmostEqual(resp[idx_f0], gain, delta=0.2)
        
        # Far from center frequency, gain should approach 0 dB
        self.assertAlmostEqual(resp[0], 0.0, delta=0.5)
        self.assertAlmostEqual(resp[-1], 0.0, delta=0.5)

    def test_channel_independent_dual_optimization(self):
        """Validates that Left and Right channels receive independent center frequencies targeting distinct modes."""
        freqs = np.logspace(np.log10(20.0), np.log10(5000.0), 1000)
        target = np.zeros_like(freqs)
        
        # Left channel has modal resonance at 112 Hz
        left_resp = np.zeros_like(freqs)
        idx_112 = np.argmin(np.abs(freqs - 112.0))
        left_resp[idx_112 - 5:idx_112 + 6] += 9.0
        
        # Right channel has corner mode at 63 Hz
        right_resp = np.zeros_like(freqs)
        idx_63 = np.argmin(np.abs(freqs - 63.0))
        right_resp[idx_63 - 5:idx_63 + 6] += 12.0

        res = optimize_stereo_peq(
            freqs_hz=freqs,
            left_sweet_spot=left_resp,
            right_sweet_spot=right_resp,
            target_db=target,
            sweet_spot_weight=0.8,
        )

        self.assertTrue(res["success"])
        l_bands = res["channels"]["left"]
        r_bands = res["channels"]["right"]

        # Left should have a notch near 112 Hz (99.2 or 125 Hz)
        l_freqs = [b["freq_hz"] for b in l_bands if b["gain_db"] < 0]
        self.assertTrue(any(f in [99.2, 125.0] for f in l_freqs))

        # Right should have a notch near 63 Hz (62.5 Hz)
        r_freqs = [b["freq_hz"] for b in r_bands if b["gain_db"] < 0]
        self.assertTrue(62.5 in r_freqs)

    def test_benchmark_convergence_speed_under_3_seconds(self):
        """Benchmark: optimizer must converge in well under 3.0 seconds per channel (target < 100 ms)."""
        freqs = np.linspace(20, 20000, 32768)
        target = np.zeros_like(freqs)
        
        # Add realistic domestic peaks
        resp = np.zeros_like(freqs)
        resp += 8.0 * np.exp(-((freqs - 63.0) / 10.0)**2)
        resp += 10.0 * np.exp(-((freqs - 119.0) / 12.0)**2)
        resp += 6.0 * np.exp(-((freqs - 240.0) / 20.0)**2)

        t0 = time.perf_counter()
        res = optimize_stereo_peq(
            freqs_hz=freqs,
            left_sweet_spot=resp,
            right_sweet_spot=resp,
            target_db=target,
        )
        elapsed_sec = time.perf_counter() - t0

        self.assertLess(elapsed_sec, 3.0, f"Optimization took {elapsed_sec:.2f}s (exceeds 3.0s limit)")
        self.assertGreater(res["metrics"]["predicted_modal_attenuation_db"], 5.0)


if __name__ == "__main__":
    unittest.main()
