"""
tests/test_sweep_multi_channel.py
Regression tests for multi-channel acoustic sweep playback, channel routing,
Farina deconvolution time-of-flight estimation, and per-point multi-channel validation.
"""

import unittest
import numpy as np
import scipy.signal

class TestMultiChannelSweepRouting(unittest.TestCase):
    def test_channel_mapping_front_l_not_confused_with_r(self):
        """Regression test: Ensure 'Front_L' does not trigger 'R' routing due to 'R' in 'FRONT'."""
        ch_map = {
            "l": "L", "front_l": "L", "fl": "L",
            "r": "R", "front_r": "R", "fr": "R",
            "sub": "SUB", "subwoofer": "SUB", "subwoofer_1": "SUB",
            "c": "Center", "center": "Center",
        }
        
        for raw in ["Front_L", "front_l", "FL", "L", "front_left"]:
            raw_clean = raw.lower()
            mapped = ch_map.get(raw_clean, "L")
            is_sub = mapped == "SUB" or "sub" in raw_clean
            is_r = mapped == "R" or raw_clean in ["r", "front_r", "fr"] or raw_clean.endswith("_r")
            
            self.assertFalse(is_sub)
            self.assertFalse(is_r, f"Channel '{raw}' was wrongly flagged as Right channel!")
            self.assertEqual(mapped, "L")

    def test_channel_mapping_front_r_and_sub(self):
        """Ensure Front_R maps to R and Subwoofer maps to SUB."""
        ch_map = {
            "l": "L", "front_l": "L", "fl": "L",
            "r": "R", "front_r": "R", "fr": "R",
            "sub": "SUB", "subwoofer": "SUB", "subwoofer_1": "SUB",
        }
        self.assertEqual(ch_map.get("front_r", "L"), "R")
        self.assertEqual(ch_map.get("subwoofer", "L"), "SUB")

    def test_farina_deconvolution_tof_accuracy(self):
        """Test Farina deconvolution time-of-flight estimation subtracts (len(inv_sweep) - 1)."""
        fs = 48000
        duration = 5.0
        f1, f2 = 15.0, 22000.0
        N = int(duration * fs)
        t = np.linspace(0, duration, N, endpoint=False)
        w1, w2 = 2 * np.pi * f1, 2 * np.pi * f2
        L = duration / np.log(w2 / w1)
        phi = w1 * L * (np.exp(t / L) - 1.0)
        sweep_core = np.sin(phi)

        envelope = np.exp(-t / L)
        inv_sweep = sweep_core[::-1] * envelope
        conv_unit = scipy.signal.fftconvolve(sweep_core, inv_sweep, mode='full')
        inv_sweep /= np.max(conv_unit)

        # 0.5s silence (24000 samples) + 8.0ms room flight (384 samples) -> 24384 delay
        room_flight_ms = 8.0
        room_flight_samples = int((room_flight_ms / 1000.0) * fs)
        silence_samples = int(0.5 * fs)
        total_delay = silence_samples + room_flight_samples

        rec_signal = np.zeros(int(fs * 6.0), dtype=np.float64)
        rec_signal[total_delay:total_delay + len(sweep_core)] = 0.7 * sweep_core

        ir = scipy.signal.fftconvolve(rec_signal, inv_sweep, mode='full')
        peak_idx = int(np.argmax(np.abs(ir)))

        # Accurate peak offset subtraction
        inv_len = len(inv_sweep) - 1
        net_peak = peak_idx - inv_len if peak_idx >= inv_len else peak_idx
        acoustic_delay_samples = net_peak - silence_samples
        measured_delay_ms = (acoustic_delay_samples / fs) * 1000.0
        measured_dist_m = (acoustic_delay_samples / fs) * 343.0

        self.assertAlmostEqual(measured_delay_ms, room_flight_ms, delta=0.2)
        expected_dist_m = (room_flight_ms / 1000.0) * 343.0
        self.assertAlmostEqual(measured_dist_m, expected_dist_m, delta=0.1)

    def test_multichannel_point_completion_logic(self):
        """Ensure point_complete is only True when all channels in active layout are satisfied."""
        active_ch_ids_2_1 = ["Front_L", "Front_R", "Subwoofer"]
        
        # Scenario 1: Only Front_L uploaded
        buf_1 = {"Front_L": True}
        done_1 = all(
            (cid in buf_1 or ("L" in buf_1 and cid == "Front_L") or ("R" in buf_1 and cid == "Front_R") or ("SUB" in buf_1 and cid == "Subwoofer"))
            for cid in active_ch_ids_2_1
        )
        self.assertFalse(done_1)

        # Scenario 2: Front_L and Front_R uploaded
        buf_2 = {"Front_L": True, "Front_R": True}
        done_2 = all(
            (cid in buf_2 or ("L" in buf_2 and cid == "Front_L") or ("R" in buf_2 and cid == "Front_R") or ("SUB" in buf_2 and cid == "Subwoofer"))
            for cid in active_ch_ids_2_1
        )
        self.assertFalse(done_2)

        # Scenario 3: All channels uploaded (L, R, SUB)
        buf_3 = {"Front_L": True, "Front_R": True, "Subwoofer": True}
        done_3 = all(
            (cid in buf_3 or ("L" in buf_3 and cid == "Front_L") or ("R" in buf_3 and cid == "Front_R") or ("SUB" in buf_3 and cid == "Subwoofer"))
            for cid in active_ch_ids_2_1
        )
        self.assertTrue(done_3)

    def test_acoustic_timing_reference_and_differential_distance(self):
        """Ensure Acoustic Timing Reference (5-20 kHz chirp) resolves precise differential distances."""
        import soundfile as sf
        import os
        fs = 48000
        c = 343.4
        d0_l = 2.45
        d0_r = 2.35
        d0_sub = 3.65

        # Load inv_sweep, inv_chirp, inv_sweep_sub from web_calibration_server
        from scripts.web_calibration_server import inv_sweep, inv_chirp, inv_sweep_sub

        wav_r = os.path.join("data", "sweep_signal_R.wav")
        wav_sub = os.path.join("data", "sweep_signal_SUB.wav")
        self.assertTrue(os.path.exists(wav_r))
        self.assertTrue(os.path.exists(wav_sub))

        d_r, _ = sf.read(wav_r)
        d_sub, _ = sf.read(wav_sub)

        tof_l = int(round((d0_l / c) * fs))
        tof_r = int(round((d0_r / c) * fs))
        tof_sub = int(round((d0_sub / c) * fs))
        jitter = int(0.500 * fs)

        # Front_R simulation
        mic_r = np.zeros(jitter + len(d_r) + 5000)
        mic_r[jitter + tof_l : jitter + tof_l + len(d_r)] += d_r[:, 0]
        mic_r[jitter + tof_r : jitter + tof_r + len(d_r)] += d_r[:, 1]

        corr_c = scipy.signal.fftconvolve(mic_r, inv_chirp, mode='full')
        t_chirp = np.argmax(np.abs(corr_c)) - (len(inv_chirp) - 1)
        ir_r = scipy.signal.fftconvolve(mic_r, inv_sweep, mode='full')
        t_sweep = np.argmax(np.abs(ir_r)) - (len(inv_sweep) - 1)
        meas_r = (t_sweep - t_chirp) - 33600
        calc_r = round(d0_l + (meas_r / float(fs)) * c, 2)
        self.assertEqual(calc_r, d0_r)

        # Subwoofer simulation
        mic_sub = np.zeros(jitter + len(d_sub) + 5000)
        mic_sub[jitter + tof_l : jitter + tof_l + len(d_sub)] += d_sub[:, 0]
        mic_sub[jitter + tof_sub : jitter + tof_sub + len(d_sub)] += d_sub[:, 1]

        corr_c_sub = scipy.signal.fftconvolve(mic_sub, inv_chirp, mode='full')
        t_chirp_sub = np.argmax(np.abs(corr_c_sub)) - (len(inv_chirp) - 1)
        ir_sub = scipy.signal.fftconvolve(mic_sub, inv_sweep_sub, mode='full')
        t_sweep_sub = np.argmax(np.abs(ir_sub)) - (len(inv_sweep_sub) - 1)
        meas_sub = (t_sweep_sub - t_chirp_sub) - 33600
        calc_sub = round(d0_l + (meas_sub / float(fs)) * c, 2)
        self.assertEqual(calc_sub, d0_sub)

if __name__ == "__main__":
    unittest.main()
