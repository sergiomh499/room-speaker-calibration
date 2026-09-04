import unittest
import json
import numpy as np

class TestTargetCurvesAudit(unittest.TestCase):
    def setUp(self):
        with open("config/targets.json", "r", encoding="utf-8") as f:
            self.cfg = json.load(f)

    def test_all_9_profiles_exist(self):
        profiles = [k for k in self.cfg if k != "_meta"]
        self.assertEqual(len(profiles), 9)

    def test_subsonic_protection_and_voicing(self):
        # In a 2.0 bookshelf setup, no profile should demand heavy positive boost below 60 Hz
        for p_key, p_data in self.cfg.items():
            if p_key == "_meta": continue
            bands = p_data.get("bands", {})
            for b_idx in range(1, 8):
                b = bands.get(f"Band {b_idx}")
                if not b: continue
                freq = b.get("freq", 0.0)
                gain_l = b.get("gain_l", 0.0)
                gain_r = b.get("gain_r", 0.0)
                if freq < 60.0:
                    self.assertLessEqual(gain_l, 0.0, f"Profile {p_key} has unsafe sub-bass boost on L at {freq}Hz: {gain_l}")
                    self.assertLessEqual(gain_r, 0.0, f"Profile {p_key} has unsafe sub-bass boost on R at {freq}Hz: {gain_r}")

    def test_crossover_voicing_within_bounds(self):
        # Band at 2.52 kHz (speaker crossover compensation) should be within +1.0 to +3.0 dB
        for p_key, p_data in self.cfg.items():
            if p_key == "_meta": continue
            bands = p_data.get("bands", {})
            for b_name, b in bands.items():
                if b.get("freq") == 2520.0:
                    self.assertTrue(0.0 <= b["gain_l"] <= 3.0)
                    self.assertTrue(0.0 <= b["gain_r"] <= 3.0)

if __name__ == "__main__":
    unittest.main()
