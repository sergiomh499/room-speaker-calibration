"""
tests/test_calibration_epoch.py
Unit tests for Calibration Epoch management, provenance validation, and rejection of synthetic/faked curves.
Compatible with standard library unittest and pytest.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np

from scripts.calibration_epoch import (
    AcousticTransferFunction,
    BiquadFilter,
    CalibrationEpoch,
    EpochMetrics,
    compute_file_sha256,
    create_epoch_directory,
    evaluate_s_tier_certification,
    load_acoustic_transfer_function,
    load_epoch_manifest,
    save_acoustic_transfer_function,
    save_epoch_manifest,
)

class TestCalibrationEpoch(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.epoch_dir = Path(self.test_dir) / "epochs"
        self.epoch_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_authentic_acoustic_transfer_function_validation(self):
        """Validates that real measurement data passes validation."""
        freqs = np.logspace(np.log10(20.0), np.log10(20000.0), 500)
        mag = -10.0 + np.sin(freqs / 100.0)
        ir = np.zeros(1024, dtype=np.float32)
        ir[100] = 0.5
        
        tf = AcousticTransferFunction(
            freqs_hz=freqs,
            raw_magnitude_db=mag,
            smoothed_magnitude_db=mag,
            impulse_response=ir,
            peak_dbfs=-6.0,
            snr_db=22.0,
            timestamp="2026-09-03T20:00:00Z",
            channel="L",
            provenance_tag="REAL_MEASUREMENT",
        )
        is_valid, msg = tf.validate()
        self.assertTrue(is_valid)
        self.assertEqual(msg, "Valid")

    def test_rejection_of_synthetic_provenance(self):
        """Validates that synthetic or simulated data is rejected when authentic data is required."""
        freqs = np.linspace(20, 20000, 100)
        mag = np.zeros(100)
        ir = np.zeros(100, dtype=np.float32)
        
        tf = AcousticTransferFunction(
            freqs_hz=freqs,
            raw_magnitude_db=mag,
            smoothed_magnitude_db=mag,
            impulse_response=ir,
            peak_dbfs=-12.0,
            snr_db=30.0,
            timestamp="2026-09-03T20:00:00Z",
            channel="L",
            provenance_tag="THEORETICAL_TARGET",
        )
        is_valid, msg = tf.validate()
        self.assertFalse(is_valid)
        self.assertIn("Invalid provenance", msg)

    def test_rejection_of_clipped_or_noisy_signals(self):
        """Validates that digital clipping (> -3 dBFS) or inadequate SNR (< 14 dB) fails validation."""
        freqs = np.linspace(20, 20000, 100)
        mag = np.zeros(100)
        ir = np.zeros(100, dtype=np.float32)
        
        # Clipped signal
        tf_clipped = AcousticTransferFunction(
            freqs_hz=freqs,
            raw_magnitude_db=mag,
            smoothed_magnitude_db=mag,
            impulse_response=ir,
            peak_dbfs=-1.5,  # Clipped!
            snr_db=25.0,
            timestamp="2026-09-03T20:00:00Z",
            channel="L",
            provenance_tag="REAL_MEASUREMENT",
        )
        is_valid, msg = tf_clipped.validate()
        self.assertFalse(is_valid)
        self.assertIn("clipped", msg.lower())

        # Noisy signal
        tf_noisy = AcousticTransferFunction(
            freqs_hz=freqs,
            raw_magnitude_db=mag,
            smoothed_magnitude_db=mag,
            impulse_response=ir,
            peak_dbfs=-15.0,
            snr_db=11.2,  # Too noisy!
            timestamp="2026-09-03T20:00:00Z",
            channel="L",
            provenance_tag="REAL_MEASUREMENT",
        )
        is_valid, msg = tf_noisy.validate()
        self.assertFalse(is_valid)
        self.assertIn("snr", msg.lower())

    def test_epoch_directory_creation_and_manifest_roundtrip(self):
        """Validates epoch directory creation, manifest saving, and loading."""
        epoch_dir, epoch_id = create_epoch_directory("baseline", "harman_wide_room", epoch_index=0, root=self.epoch_dir)
        self.assertTrue(epoch_dir.exists())
        self.assertIn("epoch_000_baseline_", epoch_id)
        
        metrics = EpochMetrics(
            modal_peak_attenuation_db=0.0,
            residual_rms_error_db=4.2,
            stereo_imbalance_db=1.1,
            snr_db=24.5,
            s_tier_certified=False,
        )
        
        epoch = CalibrationEpoch(
            epoch_index=0,
            epoch_id=epoch_id,
            stage="baseline",
            timestamp="2026-09-03T20:00:00Z",
            profile_key="harman_wide_room",
            active_peq={"left": [], "right": []},
            metrics=metrics,
            provenance={"rir_left_sha256": "abcdef123456", "rir_right_sha256": "fedcba654321", "hardware_readback_verified": True},
        )
        
        manifest_path = save_epoch_manifest(epoch, epoch_dir)
        self.assertTrue(manifest_path.exists())
        
        loaded = load_epoch_manifest(manifest_path)
        self.assertEqual(loaded.epoch_index, 0)
        self.assertEqual(loaded.stage, "baseline")
        self.assertEqual(loaded.metrics.residual_rms_error_db, 4.2)
        self.assertFalse(loaded.metrics.s_tier_certified)

    def test_s_tier_certification_gating(self):
        """Validates strict multi-metric S-TIER certification logic."""
        # Passing case: modal cut >= 6.0 dB, RMS < 2.5 dB, stereo imbalance < 2.0 dB
        self.assertTrue(evaluate_s_tier_certification(
            modal_peak_attenuation_db=6.8,
            residual_rms_error_db=2.1,
            stereo_imbalance_db=1.4,
        ))
        
        # Failing case 1: Insufficient modal peak attenuation
        self.assertFalse(evaluate_s_tier_certification(
            modal_peak_attenuation_db=4.5,
            residual_rms_error_db=2.0,
            stereo_imbalance_db=1.0,
        ))

        # Failing case 2: Excessive RMS error
        self.assertFalse(evaluate_s_tier_certification(
            modal_peak_attenuation_db=7.2,
            residual_rms_error_db=2.9,
            stereo_imbalance_db=1.0,
        ))

        # Failing case 3: Excessive stereo imbalance
        self.assertFalse(evaluate_s_tier_certification(
            modal_peak_attenuation_db=7.0,
            residual_rms_error_db=2.2,
            stereo_imbalance_db=2.4,
        ))


if __name__ == "__main__":
    unittest.main()
