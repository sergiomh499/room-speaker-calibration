"""
tests/test_verify_calibration.py
Unit tests for verification metrics calculation, S-TIER multi-metric gating, and provenance enforcement.
"""

import unittest
import numpy as np

from scripts.calibration_epoch import evaluate_s_tier_certification
from scripts.verify_calibration import run_verification

class TestVerifyCalibration(unittest.TestCase):
    def test_s_tier_certification_thresholds(self):
        """Validates that S-TIER is only granted when all 3 physical criteria pass."""
        # 1. Passing case
        self.assertTrue(evaluate_s_tier_certification(
            modal_peak_attenuation_db=6.5,
            residual_rms_error_db=2.1,
            stereo_imbalance_db=1.5,
        ))

        # 2. Failing: modal attenuation < 6.0 dB
        self.assertFalse(evaluate_s_tier_certification(
            modal_peak_attenuation_db=5.9,
            residual_rms_error_db=2.1,
            stereo_imbalance_db=1.5,
        ))

        # 3. Failing: RMS error >= 2.5 dB
        self.assertFalse(evaluate_s_tier_certification(
            modal_peak_attenuation_db=8.0,
            residual_rms_error_db=2.55,
            stereo_imbalance_db=1.5,
        ))

        # 4. Failing: Stereo imbalance >= 2.0 dB
        self.assertFalse(evaluate_s_tier_certification(
            modal_peak_attenuation_db=8.0,
            residual_rms_error_db=2.0,
            stereo_imbalance_db=2.1,
        ))

    def test_unmeasured_profile_never_certified(self):
        """Validates that when physical post-PEQ sweep does not exist, S-TIER is NEVER awarded."""
        # Test with a profile that has no live physical sweep
        res = run_verification(profile="audiophile_flat", save_fig=False)
        self.assertFalse(res["s_tier_certified"])
        self.assertFalse(res["passed"])
        self.assertIn("PENDIENTE DE MEDICIÓN FÍSICA", res["rating"])

    def test_scientific_metrics_without_arbitrary_multipliers(self):
        """Validates that metrics contain empirical RMS, modal attenuation, and stereo imbalance in dB."""
        res = run_verification(profile="harman_wide_room", save_fig=False)
        self.assertIn("modal_reduction_db", res)
        self.assertIn("rms_target_after_db", res)
        self.assertIn("stereo_global_after_db", res)
        self.assertIsInstance(res["modal_reduction_db"], float)
        self.assertIsInstance(res["rms_target_after_db"], float)


if __name__ == "__main__":
    unittest.main()
