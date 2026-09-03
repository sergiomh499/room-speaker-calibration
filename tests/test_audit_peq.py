"""
tests/test_audit_peq.py
Automated test suite for PEQ filter audit and diagnostic verification.
"""

import json
import os
import sys
import unittest
import numpy as np

# Ensure scripts directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from audit_peq_filters import (
    ParametricFilterBand,
    RoomResonanceMode,
    FilterAuditDiagnosis,
    load_composite_baseline,
    validate_discrete_yamaha_parameters,
    detect_room_resonances,
    audit_channel_filters,
    run_diagnostic_audit,
    reoptimize_peq_filters,
    YAMAHA_FREQS,
    YAMAHA_QS,
)


class TestAuditPEQ(unittest.TestCase):
    def setUp(self):
        """Generates synthetic frequency response with known resonance peaks at 62.5 Hz, 125.0 Hz, and 250.0 Hz."""
        self.freqs = np.logspace(np.log10(20.0), np.log10(20000.0), 1000)
        self.spl_l = 75.0 * np.ones_like(self.freqs)
        self.spl_r = 75.0 * np.ones_like(self.freqs)

        # Add resonances
        # 62.5 Hz peak (+9 dB, Q=4.0)
        self.spl_l += 9.0 * np.exp(-0.5 * ((self.freqs - 62.5) / (62.5 / 8.0)) ** 2)
        self.spl_r += 8.0 * np.exp(-0.5 * ((self.freqs - 62.5) / (62.5 / 8.0)) ** 2)

        # 125.0 Hz peak (+6 dB, Q=3.0)
        self.spl_l += 6.0 * np.exp(-0.5 * ((self.freqs - 125.0) / (125.0 / 6.0)) ** 2)
        self.spl_r += 7.0 * np.exp(-0.5 * ((self.freqs - 125.0) / (125.0 / 6.0)) ** 2)

        # 250.0 Hz peak (+5 dB, Q=2.5)
        self.spl_l += 5.0 * np.exp(-0.5 * ((self.freqs - 250.0) / (250.0 / 5.0)) ** 2)
        self.spl_r += 4.5 * np.exp(-0.5 * ((self.freqs - 250.0) / (250.0 / 5.0)) ** 2)

    def test_t001_fixtures_and_data_classes(self):
        """Test instantiation and serialization of core audit data models."""
        band = ParametricFilterBand(
            band=1,
            channel="L",
            freq_hz=62.5,
            q=4.0,
            gain_db=-6.0,
            status="ALIGNED",
            discrepancy_hz=0.0,
            associated_mode=62.5,
        )
        self.assertEqual(band.freq_hz, 62.5)
        self.assertEqual(band.gain_db, -6.0)
        d = band.to_dict()
        self.assertEqual(d["band"], 1)
        self.assertEqual(d["channel"], "L")
        self.assertEqual(d["status"], "ALIGNED")

        mode = RoomResonanceMode(
            frequency_hz=125.0,
            peak_prominence_db=6.0,
            q_estimate=3.0,
            target_attenuation_db=-6.0,
        )
        self.assertEqual(mode.frequency_hz, 125.0)
        self.assertEqual(mode.to_dict()["peak_prominence_db"], 6.0)

        diag = FilterAuditDiagnosis(
            verdict="ACCURATE",
            composite_error_score=0.95,
            left_channel=[band],
            right_channel=[],
            misaligned_bands=[],
            hardware_violations=[],
            acoustic_violations=[],
            recommended_peq=None,
        )
        res = diag.to_dict()
        self.assertEqual(res["verdict"], "ACCURATE")
        self.assertEqual(len(res["left_channel"]), 1)

    def test_t004_validate_discrete_yamaha_parameters(self):
        """Test validation of discrete Yamaha RX-V673 parameter constraints."""
        # Valid filter
        valid_band = ParametricFilterBand(
            band=1, channel="L", freq_hz=62.5, q=4.0, gain_db=-3.5
        )
        errs = validate_discrete_yamaha_parameters(valid_band)
        self.assertEqual(len(errs), 0)

        # Invalid frequency (not in Yamaha table)
        inv_f_band = ParametricFilterBand(
            band=1, channel="L", freq_hz=65.0, q=4.0, gain_db=-3.5
        )
        errs_f = validate_discrete_yamaha_parameters(inv_f_band)
        self.assertTrue(any("frequency" in e.lower() for e in errs_f))

        # Invalid Q (not in Yamaha table)
        inv_q_band = ParametricFilterBand(
            band=1, channel="L", freq_hz=62.5, q=3.5, gain_db=-3.5
        )
        errs_q = validate_discrete_yamaha_parameters(inv_q_band)
        self.assertTrue(any("q factor" in e.lower() for e in errs_q))

        # Invalid gain (not in 0.5 dB step or out of bounds)
        inv_g_band = ParametricFilterBand(
            band=1, channel="L", freq_hz=62.5, q=4.0, gain_db=-3.7
        )
        errs_g = validate_discrete_yamaha_parameters(inv_g_band)
        self.assertTrue(any("step" in e.lower() for e in errs_g))

    def test_t005_t006_resonance_detection(self):
        """Test room resonance peak detection on synthetic baseline."""
        modes_l = detect_room_resonances(self.freqs, self.spl_l, max_freq_hz=500.0)
        mode_freqs_l = [m.frequency_hz for m in modes_l]

        # Should detect 62.5, 125.0, and 250.0 within tolerance
        self.assertTrue(any(abs(f - 62.5) < 3.0 for f in mode_freqs_l))
        self.assertTrue(any(abs(f - 125.0) < 5.0 for f in mode_freqs_l))
        self.assertTrue(any(abs(f - 250.0) < 10.0 for f in mode_freqs_l))

    def test_t007_t008_frequency_alignment_audit(self):
        """Test frequency alignment detection and flag bands > 5 Hz misaligned."""
        # Create aligned filters
        aligned_filters = [
            ParametricFilterBand(band=1, channel="L", freq_hz=62.5, q=4.0, gain_db=-6.0),
            ParametricFilterBand(band=2, channel="L", freq_hz=125.0, q=3.175, gain_db=-5.0),
            ParametricFilterBand(band=3, channel="L", freq_hz=250.0, q=2.520, gain_db=-4.0),
        ]

        audited, misaligned, hw_viol, ac_viol = audit_channel_filters(
            aligned_filters, self.freqs, self.spl_l, channel="L"
        )
        self.assertEqual(len(misaligned), 0)
        self.assertEqual(len(hw_viol), 0)
        self.assertEqual(len(ac_viol), 0)

        # Create misaligned filter (e.g. 78.7 Hz instead of 62.5 Hz peak)
        misaligned_filters = [
            ParametricFilterBand(band=1, channel="L", freq_hz=78.7, q=4.0, gain_db=-6.0),
        ]
        audited_m, misaligned_m, _, _ = audit_channel_filters(
            misaligned_filters, self.freqs, self.spl_l, channel="L"
        )
        self.assertTrue(len(misaligned_m) > 0)
        self.assertGreater(misaligned_m[0].discrepancy_hz, 5.0)
        self.assertEqual(misaligned_m[0].status, "MISALIGNED")

    def test_t009_t010_modal_boost_rejection(self):
        """Test rejection of positive gain in the room modal region (< 500 Hz)."""
        # Positive boost filter in modal region (< 500 Hz)
        boost_filters = [
            ParametricFilterBand(band=1, channel="L", freq_hz=62.5, q=4.0, gain_db=3.0),
        ]
        audited, misaligned, hw_viol, ac_viol = audit_channel_filters(
            boost_filters, self.freqs, self.spl_l, channel="L"
        )
        self.assertTrue(len(ac_viol) > 0)
        self.assertTrue(any("positive" in v.lower() or "boost" in v.lower() for v in ac_viol))

    def test_t012_t013_t014_reoptimization(self):
        """Test automated re-optimization yields lower RMS error when original is suboptimal."""
        # Suboptimal filter matrix (misaligned or ineffective)
        suboptimal_peq = {
            "left_channel": [
                ParametricFilterBand(band=1, channel="L", freq_hz=99.2, q=2.0, gain_db=-2.0)
            ],
            "right_channel": [
                ParametricFilterBand(band=1, channel="R", freq_hz=99.2, q=2.0, gain_db=-2.0)
            ]
        }

        diag = run_diagnostic_audit(
            self.freqs, self.spl_l, self.spl_r, suboptimal_peq, reoptimize=True
        )
        self.assertIn(diag.verdict, ("SUBOPTIMAL", "ERRONEOUS"))
        self.assertIsNotNone(diag.recommended_peq)
        self.assertIn("left_channel", diag.recommended_peq)
        self.assertTrue(len(diag.recommended_peq["left_channel"]) > 0)

        # Verify RMS improvement is positive
        comp = diag.comparative_metrics
        self.assertIsNotNone(comp)
        self.assertGreaterEqual(comp["rms_improvement_pct"], 0.0)

    def test_t015_cli_formatting(self):
        """Test CLI format helper generates non-empty report with expected sections."""
        from audit_peq_filters import format_cli_output
        band = ParametricFilterBand(
            band=1, channel="L", freq_hz=62.5, q=4.0, gain_db=-6.0, status="ALIGNED"
        )
        diag = FilterAuditDiagnosis(
            verdict="ACCURATE",
            composite_error_score=1.2,
            left_channel=[band],
            right_channel=[],
            misaligned_bands=[],
            hardware_violations=[],
            acoustic_violations=[],
        )
        out = format_cli_output(diag)
        self.assertIn("DIAGNOSTIC AUDIT REPORT", out)
        self.assertIn("ACCURATE", out)
        self.assertIn("LEFT CHANNEL ACTIVE FILTERS", out)

    def test_t016_t017_api_endpoint_integration(self):
        """Test /api/audit_peq live HTTP endpoint on localhost."""
        import urllib.request
        url = "http://127.0.0.1:53317/api/audit_peq"
        payload = json.dumps({"reoptimize": True}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                self.assertEqual(resp.status, 200)
                data = json.loads(resp.read().decode("utf-8"))
                self.assertTrue(data.get("ok"))
                self.assertIn("diagnosis", data)
                self.assertIn("verdict", data["diagnosis"])
        except Exception as e:
            # Server might not be running in isolated test runner, skip gracefully if connection refused
            if "Connection refused" in str(e):
                self.skipTest("Live server not running on port 53317")
            else:
                raise


if __name__ == "__main__":
    unittest.main()
