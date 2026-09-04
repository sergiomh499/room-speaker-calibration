#!/usr/bin/env python3
"""Unit tests for multi-format filter export (REW, EqualizerAPO, CSV)."""

import unittest
from pathlib import Path
import tempfile
import zipfile
import csv

REPO_DIR = Path(__file__).resolve().parent.parent

class TestFilterExport(unittest.TestCase):
    def setUp(self):
        self.mock_bands_l = [
            {"band": 1, "freq_hz": 2520.0, "q": 1.260, "gain_db": 1.5, "type": "PK"},
            {"band": 2, "freq_hz": 125.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 3, "freq_hz": 315.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 4, "freq_hz": 793.7, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 5, "freq_hz": 2000.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 6, "freq_hz": 5040.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 7, "freq_hz": 12700.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
        ]
        self.mock_bands_r = [
            {"band": 1, "freq_hz": 198.4, "q": 0.500, "gain_db": -2.0, "type": "PK"},
            {"band": 2, "freq_hz": 2520.0, "q": 1.260, "gain_db": 2.0, "type": "PK"},
            {"band": 3, "freq_hz": 315.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 4, "freq_hz": 793.7, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 5, "freq_hz": 2000.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 6, "freq_hz": 5040.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
            {"band": 7, "freq_hz": 12700.0, "q": 1.000, "gain_db": 0.0, "type": "PK"},
        ]
        self.mock_hardware = {
            "microphone": "pixel_9_pro_calibrated",
            "amplifier": "yamaha_rx_v673",
            "speakers": "q_acoustics_3020i",
        }

    def test_format_rew_syntax(self):
        from scripts.export_filters import format_rew
        out = format_rew(self.mock_bands_l, channel="L", profile="harman_wide_room", hardware=self.mock_hardware)
        self.assertIn("Filter Settings file", out)
        self.assertIn("Room EQ V5.20", out)
        self.assertIn("Equaliser: Generic", out)
        self.assertIn("Filter  1: ON  PK", out)
        self.assertIn("2520.0 Hz", out)
        self.assertIn("+1.5 dB", out)
        self.assertIn("1.260", out)

    def test_format_equalizer_apo_syntax(self):
        from scripts.export_filters import format_equalizer_apo
        out = format_equalizer_apo(self.mock_bands_l, self.mock_bands_r, profile="harman_wide_room", hardware=self.mock_hardware)
        self.assertIn("Preamp: -2.0 dB", out)
        self.assertIn("Channel: L", out)
        self.assertIn("Channel: R", out)
        self.assertIn("Filter 1: ON PK Fc 2520.0 Hz Gain +1.5 dB Q 1.260", out)
        self.assertIn("Filter 1: ON PK Fc 198.4 Hz Gain -2.0 dB Q 0.500", out)

    def test_format_csv_structure(self):
        from scripts.export_filters import format_csv
        out = format_csv(self.mock_bands_l, self.mock_bands_r, profile="harman_wide_room", hardware=self.mock_hardware)
        reader = list(csv.reader(out.strip().splitlines()))
        self.assertEqual(reader[0], [
            "channel", "band", "frequency_hz", "gain_db", "q", "filter_type",
            "profile", "hardware_mic", "hardware_amp", "hardware_speakers"
        ])
        # 1 header + 7 L bands + 7 R bands = 15 rows
        self.assertEqual(len(reader), 15)
        # Check first L band
        self.assertEqual(reader[1][0], "L")
        self.assertEqual(reader[1][1], "1")
        self.assertEqual(reader[1][2], "2520.0")
        self.assertEqual(reader[1][3], "1.5")

    def test_build_export_bundle_zip(self):
        from scripts.export_filters import build_export_bundle
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = build_export_bundle("harman_wide_room", out_dir=tmpdir)
            self.assertIn("rew_l", bundle)
            self.assertIn("rew_r", bundle)
            self.assertIn("equalizer_apo", bundle)
            self.assertIn("csv", bundle)
            self.assertIn("zip_bytes", bundle)

            # Test ZIP archive content
            zip_path = Path(tmpdir) / "filters_harman_wide_room_all.zip"
            self.assertTrue(zip_path.exists())
            with zipfile.ZipFile(zip_path, "r") as z:
                names = z.namelist()
                self.assertIn("filters_harman_wide_room_L.req", names)
                self.assertIn("filters_harman_wide_room_R.req", names)
                self.assertIn("equalizer_apo_harman_wide_room.txt", names)
                self.assertIn("peq_filters_harman_wide_room.csv", names)

if __name__ == "__main__":
    unittest.main()
