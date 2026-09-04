import unittest
import numpy as np
from scripts.peq_optimizer import optimize_stereo_peq, YAMAHA_FREQS, YAMAHA_QS

class TestPEQOptimizerGroundTruth(unittest.TestCase):
    def setUp(self):
        data = np.load('data/medicion_promedio_espacial.npz')
        self.freqs = data['freqs']
        self.resp_l = data['smooth_l']
        self.resp_r = data['smooth_r']

    def test_optimize_stereo_peq_structure(self):
        res = optimize_stereo_peq(
            freqs_hz=self.freqs,
            left_sweet_spot=self.resp_l,
            right_sweet_spot=self.resp_r,
            target_db=np.zeros_like(self.freqs),
            target_key='harman_wide_room'
        )
        self.assertTrue(res.get('ok', res.get('success', False)))
        channels = res.get('channels', {})
        bands_l = channels.get('left', res.get('bands_l', []))
        bands_r = channels.get('right', res.get('bands_r', []))
        self.assertEqual(len(bands_l), 7)
        self.assertEqual(len(bands_r), 7)

        # Verify discrete snapping
        for b in bands_l:
            self.assertIn(b.get('freq_hz', b.get('freq')), YAMAHA_FREQS)
            self.assertIn(b['q'], YAMAHA_QS)
            gain = b.get('gain_db', b.get('gain'))
            self.assertTrue(-12.0 <= gain <= 3.0)

        for b in bands_r:
            self.assertIn(b.get('freq_hz', b.get('freq')), YAMAHA_FREQS)
            self.assertIn(b['q'], YAMAHA_QS)
            gain = b.get('gain_db', b.get('gain'))
            self.assertTrue(-12.0 <= gain <= 3.0)

        metrics = res.get('metrics', {})
        self.assertGreaterEqual(metrics.get('predicted_rms_reduction_db', 0.0), 0.0)

if __name__ == '__main__':
    unittest.main()
