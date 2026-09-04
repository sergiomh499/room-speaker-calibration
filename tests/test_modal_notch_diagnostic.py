#!/usr/bin/env python3
"""
Unit tests for Modal Notch Diagnostic and Standing Wave Physics (FR-001, FR-002, FR-003, SC-001, SC-002).
"""
import unittest
import numpy as np
import pathlib
import sys

REPO_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR))

import scripts.peq_optimizer as po

class TestModalNotchDiagnostic(unittest.TestCase):
    def test_standing_wave_wavelength_and_boundary_dimensions(self):
        """FR-002, SC-002: lambda = 343 / f matches within tolerance."""
        res_125 = po.calculate_standing_wave(125.0)
        self.assertAlmostEqual(res_125["wavelength_m"], 2.74, places=2)
        self.assertAlmostEqual(res_125["half_wavelength_m"], 1.37, places=2)
        self.assertEqual(res_125["classification"], "AXIAL_ROOM_MODE")

        res_198 = po.calculate_standing_wave(198.4)
        self.assertAlmostEqual(res_198["wavelength_m"], 1.73, places=2)
        self.assertAlmostEqual(res_198["half_wavelength_m"], 0.86, places=2)

    def test_modal_peak_detection_and_q_factor_from_measurement(self):
        """FR-001, FR-003: Detect resonance peaks on empirical measurement with Q calculation."""
        d_meas = np.load(REPO_DIR / "data" / "medicion_punto_1.npz")
        freqs = d_meas["freqs"]
        norm_l = po.broadband_normalize(freqs, d_meas["smooth_l"])
        norm_r = po.broadband_normalize(freqs, d_meas["smooth_r"])
        smooth_l = po.variable_smooth(freqs, norm_l)
        smooth_r = po.variable_smooth(freqs, norm_r)

        target_zeros = np.zeros_like(freqs)
        peaks_l = po.detect_modal_resonances(freqs, smooth_l, target_zeros, min_elevation_db=1.0)
        peaks_r = po.detect_modal_resonances(freqs, smooth_r, target_zeros, min_elevation_db=1.0)

        self.assertTrue(len(peaks_l) >= 1)
        self.assertTrue(len(peaks_r) >= 1)
        # Check Q is finite and clamped between 0.5 and 5.04
        for p in peaks_l + peaks_r:
            self.assertGreaterEqual(p["q"], 0.5)
            self.assertLessEqual(p["q"], 5.04)
            self.assertTrue(p["freq_hz"] in po.YAMAHA_FREQS)

if __name__ == "__main__":
    unittest.main()
