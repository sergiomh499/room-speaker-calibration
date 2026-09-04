#!/usr/bin/env python3
"""
Unit tests for Electroacoustic PEQ Band Rationales (FR-005, FR-006, SC-001).
"""
import unittest
import pathlib
import sys

REPO_DIR = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR))

import scripts.peq_optimizer as po

class TestPEQBandRationales(unittest.TestCase):
    def test_modal_notch_classification(self):
        """FR-005: Bands with cuts (< 0 dB) are classified as MODAL_NOTCH."""
        res_l = po.classify_peq_band_function(band_idx=1, freq_hz=157.5, gain_l=-3.5, gain_r=0.0, q_l=2.0, q_r=1.0)
        self.assertEqual(res_l["category"], "MODAL_NOTCH")
        self.assertIn("Front L", res_l["rationale"])

        res_stereo = po.classify_peq_band_function(band_idx=2, freq_hz=125.0, gain_l=-2.5, gain_r=-2.0, q_l=4.0, q_r=4.0)
        self.assertEqual(res_stereo["category"], "MODAL_NOTCH")
        self.assertIn("estéreo", res_stereo["rationale"])

    def test_crossover_voicing_classification(self):
        """FR-006: Bands with positive boost in 2.0-3.0 kHz are classified as CROSSOVER_VOICING."""
        res = po.classify_peq_band_function(band_idx=3, freq_hz=2520.0, gain_l=1.5, gain_r=2.0, q_l=1.26, q_r=1.26)
        self.assertEqual(res["category"], "CROSSOVER_VOICING")
        self.assertIn("Q Acoustics 3020i", res["rationale"])

    def test_transparent_pass_classification(self):
        """FR-005: Bands with 0.0 dB gain are classified as TRANSPARENT_PASS."""
        res = po.classify_peq_band_function(band_idx=4, freq_hz=62.5, gain_l=0.0, gain_r=0.0, q_l=1.0, q_r=1.0)
        self.assertEqual(res["category"], "TRANSPARENT_PASS")
        self.assertEqual(res["phase_distortion_risk"], "Ninguno (filtro en bypass digital 0.0 dB)")

if __name__ == "__main__":
    unittest.main()
