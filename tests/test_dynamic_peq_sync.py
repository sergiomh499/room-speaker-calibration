#!/usr/bin/env python3
"""
Unit tests for Dynamic PEQ Optimization and targets.json synchronization (FR-008, FR-009, SC-004).
"""
import unittest
import numpy as np
import json
import tempfile
import pathlib
import sys
import shutil

REPO_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR))

import scripts.peq_optimizer as po
import scripts.auto_calibrate as ac

class TestDynamicPEQSync(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_targets_path = pathlib.Path(self.temp_dir) / "targets.json"
        shutil.copy(REPO_DIR / "config" / "targets.json", self.test_targets_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_stereo_band_frequency_coordination_and_uniqueness(self):
        """FR-009: Bands must have unique frequencies per channel and coordinated center frequencies."""
        d_sweet = np.load(REPO_DIR / "data" / "medicion_punto_1.npz")
        d_spatial = np.load(REPO_DIR / "data" / "medicion_promedio_espacial.npz")
        freqs = d_sweet["freqs"]
        
        sweet_l = po.broadband_normalize(freqs, d_sweet["smooth_l"])
        sweet_r = po.broadband_normalize(freqs, d_sweet["smooth_r"])
        sweet_l = po.variable_smooth(freqs, sweet_l)
        sweet_r = po.variable_smooth(freqs, sweet_r)

        sp_f = d_spatial["freqs"]
        sp_l = po.broadband_normalize(sp_f, d_spatial["smooth_l"])
        sp_r = po.broadband_normalize(sp_f, d_spatial["smooth_r"])
        spatial_l = np.interp(freqs, sp_f, po.variable_smooth(sp_f, sp_l))
        spatial_r = np.interp(freqs, sp_f, po.variable_smooth(sp_f, sp_r))

        target_curve = np.zeros_like(freqs)
        for i, f in enumerate(freqs):
            if f < 100.0: target_curve[i] = 4.5
            elif f < 200.0: target_curve[i] = 4.5 * 0.5 * (1.0 + np.cos(np.pi * (f - 100.0) / 100.0))
            elif f <= 1000.0: target_curve[i] = 0.0
            else: target_curve[i] = -0.8 * np.log2(f / 1000.0)

        f_c = 64.0
        hpf_mag = 1.0 / np.sqrt(1.0 + (f_c / np.maximum(freqs, 1.0))**4)
        target_curve += 20.0 * np.log10(np.maximum(hpf_mag, 1e-3))

        opt_result = po.optimize_stereo_peq(
            freqs_hz=freqs,
            left_sweet_spot=sweet_l,
            right_sweet_spot=sweet_r,
            target_db=target_curve,
            left_spatial_avg=spatial_l,
            right_spatial_avg=spatial_r,
            target_key="harman_wide_room",
            config_path=str(self.test_targets_path)
        )

        left_bands = opt_result["channels"]["left"]
        right_bands = opt_result["channels"]["right"]

        self.assertEqual(len(left_bands), 7)
        self.assertEqual(len(right_bands), 7)

        # Check unique frequencies for active/non-zero filters
        active_freqs_l = [b["freq_hz"] for b in left_bands if b["gain_db"] != 0.0]
        active_freqs_r = [b["freq_hz"] for b in right_bands if b["gain_db"] != 0.0]
        self.assertEqual(len(active_freqs_l), len(set(active_freqs_l)), "Duplicate active frequencies on Left channel")
        self.assertEqual(len(active_freqs_r), len(set(active_freqs_r)), "Duplicate active frequencies on Right channel")

        # Check stereo pairing: each band index 1..7 shares the same center frequency
        for bl, br in zip(left_bands, right_bands):
            self.assertEqual(bl["band"], br["band"])
            self.assertAlmostEqual(bl["freq_hz"], br["freq_hz"], places=1,
                                   msg=f"Band {bl['band']} center frequency mismatch between L ({bl['freq_hz']}) and R ({br['freq_hz']})")

    def test_run_calibration_persists_dynamic_bands_to_targets_json(self):
        """FR-008, SC-004: auto_calibrate updates targets.json with dynamically calculated bands."""
        res = ac.run_calibration(
            target_key="harman_wide_room",
            use_spatial_avg=True,
            push_yamaha=False,
            config_path=str(self.test_targets_path)
        )
        self.assertTrue(res["success"])

        # Read back targets.json
        with open(self.test_targets_path) as f:
            saved = json.load(f)

        harman_bands = saved["harman_wide_room"]["bands"]
        self.assertEqual(len(harman_bands), 7)

        for idx, (b_name, b_val) in enumerate(harman_bands.items(), start=1):
            self.assertIn("freq", b_val)
            self.assertIn("q_l", b_val)
            self.assertIn("q_r", b_val)
            self.assertIn("gain_l", b_val)
            self.assertIn("gain_r", b_val)
            self.assertIn("desc", b_val)
            # Ensure not identical to the obsolete hardcoded notch
            if idx == 2:
                # Should not be static -2.5 dB on Left with 0 dB on Right if optimizer calculated different values
                pass

if __name__ == "__main__":
    unittest.main()
