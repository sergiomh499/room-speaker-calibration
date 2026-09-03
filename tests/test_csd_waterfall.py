"""
tests/test_csd_waterfall.py
Unit tests for Cumulative Spectral Decay (CSD) waterfall STFT computation and temporal ringing decay analysis.
"""

import os
import shutil
import tempfile
import unittest
from pathlib import Path
import numpy as np

from scripts.csd_waterfall import (
    calculate_ringing_decay_time_ms,
    compute_csd_matrix,
    render_csd_waterfall_plot,
)

class TestCSDWaterfall(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Synthetic impulse response with decaying room mode at 100 Hz
        fs = 48000
        t = np.linspace(0, 0.4, int(fs * 0.4), endpoint=False)
        ir = np.zeros_like(t)
        ir[100] = 1.0  # Arrival peak
        # Ringing mode at 100 Hz with slow decay
        mode = 0.5 * np.exp(-t * 10.0) * np.sin(2 * np.pi * 100.0 * t)
        self.ir = ir + mode
        self.fs = fs

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_csd_matrix_computation_dimensions(self):
        """Validates that CSD matrix output has correct dimensions and frequencies."""
        freqs_hz, times_ms, csd_matrix = compute_csd_matrix(
            self.ir,
            fs=self.fs,
            num_slices=20,
            max_time_ms=200.0,
            min_freq_hz=20.0,
            max_freq_hz=500.0,
        )
        self.assertEqual(len(times_ms), 20)
        self.assertEqual(csd_matrix.shape[0], 20)
        self.assertEqual(csd_matrix.shape[1], len(freqs_hz))
        self.assertTrue(np.all(freqs_hz >= 20.0))
        self.assertTrue(np.all(freqs_hz <= 500.0))

    def test_temporal_energy_decay_over_time(self):
        """Validates that later time slices show significant energy decay relative to t=0."""
        _, _, csd_matrix = compute_csd_matrix(
            self.ir,
            fs=self.fs,
            num_slices=10,
            max_time_ms=200.0,
        )
        # Initial slice (t = 0) should have 0 dB peak
        self.assertAlmostEqual(np.max(csd_matrix[0, :]), 0.0, delta=0.5)
        
        max_initial = float(np.max(csd_matrix[0, :]))
        max_final = float(np.max(csd_matrix[-1, :]))
        self.assertLess(max_final, max_initial - 10.0)

    def test_ringing_decay_time_calculation(self):
        """Validates estimation of modal ringing decay time in milliseconds."""
        decay_time = calculate_ringing_decay_time_ms(
            self.ir,
            target_freq_hz=100.0,
            fs=self.fs,
            threshold_db=-20.0,
        )
        self.assertGreater(decay_time, 0.0)
        self.assertLess(decay_time, 400.0)

    def test_render_csd_waterfall_plot(self):
        """Validates that CSD 3D surface plot renders to PNG without headless errors."""
        out_png = Path(self.test_dir) / "csd_test.png"
        saved = render_csd_waterfall_plot(
            self.ir,
            output_path=out_png,
            title="Test CSD",
            fs=self.fs,
            max_freq_hz=300.0,
        )
        self.assertTrue(saved.exists())
        self.assertGreater(os.path.getsize(saved), 1000)


if __name__ == "__main__":
    unittest.main()
