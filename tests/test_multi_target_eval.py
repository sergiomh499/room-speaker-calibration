import unittest
import numpy as np
from scripts.verify_calibration import evaluate_multi_target_alignment

class TestMultiTargetEval(unittest.TestCase):
    def setUp(self):
        data = np.load("data/medicion_verificacion_manual.npz")
        self.freqs = data["freqs"]
        self.resp_l = data["smooth_l"]
        self.resp_r = data["smooth_r"]

    def test_evaluate_multi_target_alignment(self):
        benchmark = evaluate_multi_target_alignment(self.freqs, self.resp_l, self.resp_r)
        self.assertIsInstance(benchmark, dict)
        self.assertIn("harman_wide_room", benchmark)
        self.assertIn("bk_1974", benchmark)
        self.assertIn("audiophile_flat", benchmark)

        for target_id, res in benchmark.items():
            self.assertIn("rms_error_db", res)
            self.assertIn("max_peak_error_db", res)
            self.assertIn("fidelity_score_pct", res)
            self.assertIn("rating", res)
            self.assertGreaterEqual(res["fidelity_score_pct"], 0.0)
            self.assertLessEqual(res["fidelity_score_pct"], 100.0)

if __name__ == "__main__":
    unittest.main()
