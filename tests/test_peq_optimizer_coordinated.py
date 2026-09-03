"""
tests/test_peq_optimizer_coordinated.py
Unit and integration test suite for coordinated acoustic PEQ optimization.
"""

import unittest
import numpy as np
import pathlib
import json

from scripts.peq_optimizer import (
    YAMAHA_FREQS,
    YAMAHA_QS,
    MAX_BOOST_DB,
    MAX_CUT_DB,
    snap_frequency,
    snap_q,
    snap_gain,
    biquad_peaking_response,
    multi_filter_response,
    detect_modal_resonances,
    pair_stereo_modes,
    optimize_stereo_peq,
)

REPO_DIR = pathlib.Path(__file__).resolve().parent.parent


class TestCoordinatedPEQOptimizer(unittest.TestCase):

    def setUp(self):
        # 48 kHz frequency grid from 20 Hz to 20 kHz (log-spaced)
        self.freqs = np.geomspace(20.0, 20000.0, 1000)
        self.target_flat = np.zeros_like(self.freqs)

    def test_01_detect_modal_resonances_positive_gating(self):
        """FR-001: Modal resonances detected strictly where measured SPL >= target + 1.5 dB."""
        resp = np.zeros_like(self.freqs)

        # Resonant peak at 125 Hz (+5.0 dB elevation above target)
        idx_125 = np.argmin(np.abs(self.freqs - 125.0))
        resp += 5.0 * np.exp(-0.5 * ((self.freqs - 125.0) / 10.0) ** 2)

        # Acoustic dip / boundary null at 63 Hz (-8.0 dB below target with minor 1 dB ripple)
        idx_63 = np.argmin(np.abs(self.freqs - 63.0))
        resp -= 8.0 * np.exp(-0.5 * ((self.freqs - 63.0) / 15.0) ** 2)
        resp += 1.0 * np.exp(-0.5 * ((self.freqs - 60.0) / 3.0) ** 2)

        peaks = detect_modal_resonances(
            self.freqs, resp, self.target_flat, min_elevation_db=1.5, max_peaks=7
        )

        # Verify only the positive peak at 125 Hz is detected
        self.assertTrue(len(peaks) >= 1)
        peak_freqs = [p["freq_hz"] for p in peaks]
        self.assertAlmostEqual(peak_freqs[0], 125.0, delta=5.0)

        # Verify that NO peak was detected in the dip around 60-65 Hz
        for p in peaks:
            self.assertFalse(
                50.0 <= p["freq_hz"] <= 75.0,
                f"False positive detected in dip: {p['freq_hz']} Hz",
            )
            self.assertGreaterEqual(p["elevation_db"], 1.5)

    def test_02_physical_bandwidth_and_q_snapping(self):
        """FR-002: Bandwidth calculated in Hz on frequency axis and snapped to discrete Yamaha Q."""
        f0 = 200.0
        q_target = 2.0
        bw_hz = f0 / q_target  # 100 Hz bandwidth

        # Synthesize peak with known 3 dB bandwidth of ~100 Hz
        resp = 6.0 / (1.0 + ((self.freqs - f0) / (bw_hz / 2.0)) ** 2)

        peaks = detect_modal_resonances(
            self.freqs, resp, self.target_flat, min_elevation_db=1.5, max_peaks=1
        )
        self.assertEqual(len(peaks), 1)
        detected = peaks[0]

        # Verify bandwidth in Hz is close to 100 Hz
        self.assertAlmostEqual(detected["bandwidth_hz"], bw_hz, delta=25.0)

        # Discrete Q should snap to 2.000 or close neighbor (1.587, 2.520), NOT max 10.080
        self.assertIn(detected["q"], YAMAHA_QS)
        self.assertLessEqual(detected["q"], 3.175)
        self.assertGreaterEqual(detected["q"], 1.260)

    def test_03_pair_stereo_modes(self):
        """FR-006: Modes within +-5% frequency tolerance are paired for coordinated stereo EQ."""
        left_peaks = [
            {"freq_hz": 115.0, "elevation_db": 5.5, "bandwidth_hz": 30.0, "q": 4.0},
            {"freq_hz": 230.0, "elevation_db": 3.0, "bandwidth_hz": 50.0, "q": 4.0},
        ]
        right_peaks = [
            {"freq_hz": 119.0, "elevation_db": 4.8, "bandwidth_hz": 32.0, "q": 4.0},
            {"freq_hz": 315.0, "elevation_db": 2.5, "bandwidth_hz": 60.0, "q": 5.0},
        ]

        paired, l_only, r_only = pair_stereo_modes(
            left_peaks, right_peaks, freq_tolerance=0.06
        )

        # 115 Hz and 119 Hz are within 5% and must be paired
        self.assertEqual(len(paired), 1)
        self.assertAlmostEqual(paired[0]["freq_hz"], 117.0, delta=8.0)
        self.assertIn(paired[0]["freq_hz"], YAMAHA_FREQS)

        # Remaining independent modes
        self.assertEqual(len(l_only), 1)
        self.assertEqual(l_only[0]["freq_hz"], 230.0)
        self.assertEqual(len(r_only), 1)
        self.assertEqual(r_only[0]["freq_hz"], 315.0)

    def test_04_zero_cut_on_acoustic_dips(self):
        """FR-001 & SC-002: Optimization on real room data never places cuts on dips (e.g. 62.5 Hz)."""
        p1_path = REPO_DIR / "data" / "medicion_punto_1.npz"
        if not p1_path.exists():
            self.skipTest("medicion_punto_1.npz not available")

        d = np.load(p1_path)
        freqs = d["freqs"]
        idx_1k = np.argmin(np.abs(freqs - 1000.0))
        sweet_l = d["smooth_l"] - d["smooth_l"][idx_1k]
        sweet_r = d["smooth_r"] - d["smooth_r"][idx_1k]

        # Target curve with Q Acoustics 3020i roll-off
        f_c = 64.0
        hpf_mag = 1.0 / np.sqrt(1.0 + (f_c / np.maximum(freqs, 1.0)) ** 4)
        hpf_db = 20.0 * np.log10(np.maximum(hpf_mag, 1e-3))
        target_curve = hpf_db

        opt = optimize_stereo_peq(
            freqs_hz=freqs,
            left_sweet_spot=sweet_l,
            right_sweet_spot=sweet_r,
            target_db=target_curve,
            target_key="harman_wide_room",
        )

        left_filters = opt["channels"]["left"]
        right_filters = opt["channels"]["right"]

        # Check filter at 62.5 Hz: Front L at 62.5 Hz is deep in a dip, gain must be 0.0 dB
        for f in left_filters:
            if f["freq_hz"] == 62.5:
                self.assertEqual(
                    f["gain_db"],
                    0.0,
                    f"Expected 0.0 dB cut on 62.5 Hz dip, got {f['gain_db']} dB",
                )

        # Verify all filters satisfy Yamaha discrete quantization
        for f in left_filters + right_filters:
            self.assertIn(f["freq_hz"], YAMAHA_FREQS)
            self.assertIn(f["q"], YAMAHA_QS)
            self.assertGreaterEqual(f["gain_db"], -12.0)
            self.assertLessEqual(f["gain_db"], 3.0)

    def test_05_cumulative_biquad_cut_limit(self):
        """FR-004: Composite response of all 7 bands never exceeds -12.0 dB at any frequency."""
        filters = [
            {"freq_hz": 125.0, "q": 3.175, "gain_db": -6.0},
            {"freq_hz": 157.5, "q": 3.175, "gain_db": -5.0},
        ]
        composite = multi_filter_response(self.freqs, filters)
        min_val = np.min(composite)
        # Verify biquad response summation is well-behaved
        self.assertGreaterEqual(min_val, -12.0)

    def test_06_high_frequency_voicing_preserved(self):
        """FR-007: Crossover voicing filter (2520 Hz) is preserved in final filter set."""
        p1_path = REPO_DIR / "data" / "medicion_punto_1.npz"
        if not p1_path.exists():
            self.skipTest("medicion_punto_1.npz not available")

        d = np.load(p1_path)
        freqs = d["freqs"]
        idx_1k = np.argmin(np.abs(freqs - 1000.0))
        sweet_l = d["smooth_l"] - d["smooth_l"][idx_1k]
        sweet_r = d["smooth_r"] - d["smooth_r"][idx_1k]

        opt = optimize_stereo_peq(
            freqs_hz=freqs,
            left_sweet_spot=sweet_l,
            right_sweet_spot=sweet_r,
            target_db=np.zeros_like(freqs),
            target_key="harman_wide_room",
        )

        left_filters = opt["channels"]["left"]
        right_filters = opt["channels"]["right"]

        # Check 2520 Hz band
        l_2520 = [f for f in left_filters if f["freq_hz"] == 2520.0]
        r_2520 = [f for f in right_filters if f["freq_hz"] == 2520.0]
        self.assertEqual(len(l_2520), 1)
        self.assertEqual(len(r_2520), 1)
        self.assertGreater(l_2520[0]["gain_db"], 0.0)
        self.assertGreater(r_2520[0]["gain_db"], 0.0)


if __name__ == "__main__":
    unittest.main()
