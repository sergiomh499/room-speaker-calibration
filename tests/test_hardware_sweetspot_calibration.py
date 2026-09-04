"""
tests/test_hardware_sweetspot_calibration.py
Regression and contract tests for hardware profile and tight sweet-spot calibration.
"""
import json
import unittest
import numpy as np
from pathlib import Path

REPO_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = REPO_DIR / "config"
CAL_DIR = CONFIG_DIR / "calibrations"


class TestHardwareProfile(unittest.TestCase):
    def setUp(self):
        with open(CONFIG_DIR / "hardware.json", "r", encoding="utf-8") as f:
            self.hw = json.load(f)

    def test_hardware_config_has_active_section(self):
        self.assertIn("active", self.hw)
        self.assertIn("microphone", self.hw["active"])
        self.assertIn("amplifier", self.hw["active"])
        self.assertIn("speakers", self.hw["active"])

    def test_active_ids_resolve_to_known_profiles(self):
        a = self.hw["active"]
        self.assertIn(a["microphone"], self.hw["microphones"])
        self.assertIn(a["amplifier"], self.hw["amplifiers"])
        self.assertIn(a["speakers"], self.hw["speakers"])

    def test_yamaha_rx_v673_discrete_matrix(self):
        amp = self.hw["amplifiers"]["yamaha_rx_v673"]
        self.assertEqual(amp["peq_bands"], 7)
        self.assertEqual(amp["gain_step_db"], 0.5)
        self.assertEqual(amp["max_boost_db"], 3.0)
        self.assertEqual(amp["max_cut_db"], -12.0)
        self.assertEqual(amp["protocol"], "ync_xml")
        self.assertIn(2520.0, amp["discrete_frequencies_hz"])
        self.assertIn(125.0, amp["discrete_frequencies_hz"])
        self.assertIn(2.520, amp["discrete_qs"])

    def test_q_acoustics_3020i_voicing_dip_compensation(self):
        sp = self.hw["speakers"]["q_acoustics_3020i"]
        self.assertEqual(sp["f3_cutoff_hz"], 64.0)
        self.assertIsNotNone(sp["voicing_compensation"])
        self.assertEqual(sp["voicing_compensation"]["freq_hz"], 2520.0)

    def test_mandatory_90_degree_orientation(self):
        for mic_id, mic in self.hw["microphones"].items():
            self.assertEqual(
                mic["orientation"], "90_degrees_vertical",
                f"Microphone '{mic_id}' must enforce 90° vertical orientation"
            )


class TestCalibrationCurves(unittest.TestCase):
    def test_calibration_files_exist_for_built_in_mics(self):
        expected = [
            "pixel_9_pro_90deg.cal",
            "umik1_90deg.cal",
            "dayton_umm6_90deg.cal",
        ]
        for filename in expected:
            path = CAL_DIR / filename
            self.assertTrue(path.exists(), f"Missing calibration file: {path}")
            content = path.read_text(encoding="utf-8")
            self.assertIn("Calibration:", content)
            # Must contain frequency points
            for line in content.splitlines():
                if line.strip() and not line.startswith("#"):
                    parts = line.split()
                    self.assertGreater(len(parts), 1)


class TestVariableSmoothing(unittest.TestCase):
    def test_variable_smoothing_reduces_subbass_narrows_modes(self):
        from scripts.peq_optimizer import variable_smooth
        freqs = np.geomspace(20, 20000, 500)
        raw = np.zeros_like(freqs)
        # Inject a sharp 100 Hz peak (mimicking a room mode)
        raw += 6.0 * np.exp(-((np.log10(freqs) - np.log10(100.0)) ** 2) / 0.0008)
        smoothed = variable_smooth(freqs, raw)
        # 100 Hz peak should be present but spread
        idx_100 = np.argmin(np.abs(freqs - 100.0))
        self.assertLess(smoothed[idx_100], raw[idx_100])
        # Sub-bass null at 30 Hz: should NOT be amplified
        idx_30 = np.argmin(np.abs(freqs - 30.0))
        self.assertLess(abs(smoothed[idx_30]), 1.5)


class TestBroadbandNormalization(unittest.TestCase):
    def test_broadband_normalization_anchors_at_300_3000hz_energy(self):
        from scripts.peq_optimizer import broadband_normalize
        freqs = np.geomspace(20, 20000, 500)
        resp = np.zeros_like(freqs)
        # Inject a deep null at 1.0 kHz to verify resilience
        resp += -10.0 * np.exp(-((np.log10(freqs) - np.log10(1000.0)) ** 2) / 0.0005)
        norm = broadband_normalize(freqs, resp)
        # Broadband 300-3000 Hz should center near 0 dB
        mask = (freqs >= 300.0) & (freqs <= 3000.0)
        # Energy mean should be small (broadband balance)
        self.assertLess(abs(np.mean(norm[mask])), 2.0)


class TestAdaptiveModalThreshold(unittest.TestCase):
    def test_adaptive_threshold_under_schroeder(self):
        from scripts.peq_optimizer import detect_modal_resonances
        freqs = np.geomspace(20, 20000, 1000)
        target = np.zeros_like(freqs)
        response = np.zeros_like(freqs)
        # Inject a 119 Hz peak at +3 dB above target
        response += 3.0 * np.exp(-((np.log10(freqs) - np.log10(119.0)) ** 2) / 0.0005)
        peaks = detect_modal_resonances(
            freqs, response, target,
            min_elevation_db=1.0, max_peaks=7, max_freq=500.0,
        )
        detected = [p["freq_hz"] for p in peaks]
        self.assertTrue(any(100 < d < 140 for d in detected),
                        f"Expected peak near 119 Hz, got: {detected}")


if __name__ == "__main__":
    unittest.main()
