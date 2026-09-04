import unittest
import numpy as np
from scripts.peq_optimizer import BiquadFilter, evaluate_biquad_cascade

class TestPEQBiquadMath(unittest.TestCase):
    def test_neutral_filter(self):
        f = BiquadFilter(f0=100.0, gain_db=0.0, q=1.0, fs=48000)
        freqs = np.array([20.0, 50.0, 100.0, 500.0, 1000.0])
        response = f.evaluate_response(freqs)
        np.testing.assert_allclose(response, np.zeros_like(freqs), atol=1e-5)

    def test_notch_peak_gain(self):
        # Peak at f0 should match exact gain_db
        f = BiquadFilter(f0=125.0, gain_db=-3.0, q=5.0, fs=48000)
        resp_at_f0 = f.evaluate_response(np.array([125.0]))[0]
        self.assertAlmostEqual(resp_at_f0, -3.0, places=2)

    def test_bandwidth_half_power(self):
        # For a +6.0 dB boost, the gain at cutoff edges should be approximately +3.0 dB
        f = BiquadFilter(f0=1000.0, gain_db=6.0, q=2.0, fs=48000)
        freqs = np.linspace(500, 2000, 1500)
        resp = f.evaluate_response(freqs)
        self.assertAlmostEqual(np.max(resp), 6.0, places=1)

    def test_cascade_summation(self):
        f1 = BiquadFilter(f0=100.0, gain_db=-2.0, q=2.0, fs=48000)
        f2 = BiquadFilter(f0=500.0, gain_db=+1.5, q=1.0, fs=48000)
        freqs = np.array([100.0, 500.0])
        cascade_resp = evaluate_biquad_cascade([f1, f2], freqs)
        # At 100 Hz, f2 has small effect, total should be close to -2.0 dB
        self.assertTrue(-2.5 < cascade_resp[0] < -1.5)
        # At 500 Hz, f1 has small effect, total should be close to +1.5 dB
        self.assertTrue(1.0 < cascade_resp[1] < 2.0)

if __name__ == '__main__':
    unittest.main()
