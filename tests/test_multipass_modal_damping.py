import unittest
import numpy as np
from scripts.peq_optimizer import detect_modal_resonances, optimize_stereo_peq

class TestMultipassModalDamping(unittest.TestCase):
    def test_zero_boost_on_deep_cancellation_null(self):
        freqs = np.linspace(20, 1000, 1000)
        # Synthetic response with a deep cancellation dip at 65 Hz (-15 dB)
        resp = np.zeros_like(freqs)
        resp[np.argmin(np.abs(freqs - 65.0))] = -15.0
        target = np.zeros_like(freqs)

        peaks = detect_modal_resonances(freqs, resp, target, min_elevation_db=1.5)
        # Dips must never be detected as modal peaks
        dip_peaks = [p for p in peaks if abs(p["freq_hz"] - 65.0) < 5.0]
        self.assertEqual(len(dip_peaks), 0)

    def test_peak_priority_selection(self):
        freqs = np.linspace(20, 500, 1000)
        resp = np.zeros_like(freqs)
        # Narrow high-Q mode at 125 Hz (+6 dB, bw=25 Hz)
        resp += 6.0 * np.exp(-((freqs - 125.0) / 15.0) ** 2)
        # Low-elevation bump at 250 Hz (+2 dB)
        resp += 2.0 * np.exp(-((freqs - 250.0) / 30.0) ** 2)

        peaks = detect_modal_resonances(freqs, resp, np.zeros_like(freqs), min_elevation_db=1.5)
        self.assertGreaterEqual(len(peaks), 1)
        # The 125 Hz mode should be ranked #1
        self.assertEqual(peaks[0]["freq_hz"], 125.0)
        self.assertGreater(peaks[0]["elevation_db"], 5.0)

if __name__ == "__main__":
    unittest.main()
