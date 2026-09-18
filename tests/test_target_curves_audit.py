import unittest
import json
import numpy as np
from scripts.peq_optimizer import generate_bookshelf_target_curve

class TestTargetCurvesAudit(unittest.TestCase):
    def setUp(self):
        with open("config/targets.json", "r", encoding="utf-8") as f:
            self.cfg = json.load(f)
        self.freqs = np.geomspace(20.0, 20000.0, 500)

    def test_all_9_profiles_exist(self):
        profiles = [k for k in self.cfg if k != "_meta"]
        self.assertGreaterEqual(len(profiles), 9)

    def test_subsonic_protection_and_voicing(self):
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
                    self.assertLessEqual(gain_l, 0.0)
                    self.assertLessEqual(gain_r, 0.0)

    def test_bookshelf_rolloff_mathematical_consistency(self):
        for p_key in self.cfg:
            if p_key == "_meta": continue
            tc = generate_bookshelf_target_curve(self.freqs, p_key, fc_hz=64.0)
            # At 30 Hz, level must be <= -10 dB
            idx_30 = np.argmin(np.abs(self.freqs - 30.0))
            self.assertLessEqual(tc[idx_30], -10.0, f"Target {p_key} lacks proper roll-off at 30Hz")
            
            # At 64 Hz (cutoff), HPF provides -3 dB
            idx_64 = np.argmin(np.abs(self.freqs - 64.0))
            self.assertLess(tc[idx_64], 3.0)

if __name__ == "__main__":
    unittest.main()
