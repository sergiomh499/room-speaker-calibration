"""
tests/test_measure_sweep.py
Unit tests for sweep recording validation, anti-clipping safeguards, and SNR threshold checks.
"""

import unittest
import numpy as np
import importlib
measure_mod = importlib.import_module("scripts.01_measure_sweep")
validate_recording = measure_mod.validate_recording

class TestMeasureSweepValidation(unittest.TestCase):
    def test_valid_recording_passes(self):
        """Valid recording with clean peak and good SNR passes validation."""
        # 16-bit PCM samples with peak around -12 dBFS (~8200 counts)
        raw_samples = np.zeros(48000, dtype=np.int16)
        raw_samples[1000] = 8200
        mic_norm = raw_samples.astype(np.float64) / 32768.0
        
        # Clean impulse response
        ir = np.zeros(48000, dtype=np.float64)
        ir[1000] = 0.5
        
        is_valid, msg = validate_recording(raw_samples, mic_norm, ir, "Front_L")
        self.assertTrue(is_valid)
        self.assertIn("VALIDACIÓN OK", msg)

    def test_clipping_detection_aborts(self):
        """Digital clipping (> 32200 counts / > -0.15 dBFS) fails validation."""
        raw_samples = np.zeros(48000, dtype=np.int16)
        raw_samples[1000] = 32500  # Clipped!
        mic_norm = raw_samples.astype(np.float64) / 32768.0
        ir = np.zeros(48000, dtype=np.float64)
        ir[1000] = 0.99
        
        is_valid, msg = validate_recording(raw_samples, mic_norm, ir, "Front_L")
        self.assertFalse(is_valid)
        self.assertIn("Saturación digital detectada", msg)

    def test_signal_too_low_fails(self):
        """Excessively low signal (< 600 counts / < -35 dBFS) fails validation."""
        raw_samples = np.zeros(48000, dtype=np.int16)
        raw_samples[1000] = 250  # Far too quiet
        mic_norm = raw_samples.astype(np.float64) / 32768.0
        ir = np.zeros(48000, dtype=np.float64)
        ir[1000] = 0.01
        
        is_valid, msg = validate_recording(raw_samples, mic_norm, ir, "Front_R")
        self.assertFalse(is_valid)
        self.assertIn("demasiado baja", msg)

    def test_inadequate_snr_fails(self):
        """Noisy capture with SNR under 14 dB fails validation."""
        raw_samples = np.zeros(48000, dtype=np.int16)
        raw_samples[1000] = 4000
        
        # High noise floor
        mic_norm = np.random.normal(0, 0.05, 48000)
        mic_norm[1000] = 0.12
        
        ir = np.zeros(48000, dtype=np.float64)
        ir[1000] = 0.15  # Low peak compared to noise
        
        is_valid, msg = validate_recording(raw_samples, mic_norm, ir, "Front_L")
        self.assertFalse(is_valid)
        self.assertIn("SNR", msg)


if __name__ == "__main__":
    unittest.main()
