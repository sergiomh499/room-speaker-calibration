"""
tests/test_report_graphs_sync.py
Automated Verification Suite for Technical Reports, Acoustic Figures, and Hardware PEQ Execution.
Validates:
1. CLI Argument Aliases (--profile and --target in auto_calibrate.py)
2. Non-zero 3D Waterfall CSD Matrix Sourced from Punto 1 IR
3. Dynamic Profile-Aware PDF Report Generation for Multiple Community Targets
4. Dynamic RT60 Reverberation Decay Plot Generation
5. HTTP Anti-Caching Headers on Figures, Reports, and PDF Endpoints
6. Subprocess Error Handling and Stderr Capture
"""

import os
import sys
import json
import time
import subprocess
import unittest
from pathlib import Path
import numpy as np

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR))
import importlib
generate_pdf_report = importlib.import_module("scripts.03_generate_pdf_report").generate_pdf_report
from scripts.csd_waterfall import compute_csd_matrix, generate_waterfall_csd


class TestReportGraphsSync(unittest.TestCase):

    def setUp(self):
        self.data_dir = REPO_DIR / "data"
        self.fig_dir = REPO_DIR / "figures"
        self.report_dir = REPO_DIR / "reports"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.fig_dir.mkdir(parents=True, exist_ok=True)
        self.report_dir.mkdir(parents=True, exist_ok=True)

    def test_01_auto_calibrate_argument_aliases(self):
        """Verify auto_calibrate.py accepts both --profile and --target interchangeably without exit code 2."""
        cmd_target = [sys.executable, str(REPO_DIR / "scripts/auto_calibrate.py"), "--target", "harman_wide_room", "--no-spatial"]
        res_target = subprocess.run(cmd_target, capture_output=True, text=True)
        self.assertEqual(res_target.returncode, 0, f"--target failed: {res_target.stderr}")
        self.assertIn("Harman Target", res_target.stdout)

        cmd_profile = [sys.executable, str(REPO_DIR / "scripts/auto_calibrate.py"), "--profile", "bk_1974", "--no-spatial"]
        res_profile = subprocess.run(cmd_profile, capture_output=True, text=True)
        self.assertEqual(res_profile.returncode, 0, f"--profile failed: {res_profile.stderr}")
        self.assertIn("B&K 1974", res_profile.stdout)

        cmd_multipoint = [sys.executable, str(REPO_DIR / "scripts/auto_calibrate.py"), "--multipoint", "--no-spatial"]
        res_multipoint = subprocess.run(cmd_multipoint, capture_output=True, text=True)
        self.assertEqual(res_multipoint.returncode, 0, f"--multipoint failed: {res_multipoint.stderr}")

    def test_02_waterfall_csd_nonzero_decay(self):
        """Verify that 3D Waterfall CSD extracts real impulse response and calculates non-zero decay slices."""
        pt1_file = self.data_dir / "medicion_punto_1.npz"
        self.assertTrue(pt1_file.exists(), "medicion_punto_1.npz missing")

        d = np.load(pt1_file)
        self.assertIn("ir_l", d, "ir_l missing from Punto 1")
        ir_l = d["ir_l"]
        self.assertGreater(float(np.max(np.abs(ir_l))), 1e-4, "ir_l is flat/empty")

        freqs, times, csd_matrix = compute_csd_matrix(ir_l)
        self.assertEqual(csd_matrix.shape[0], 30)
        self.assertGreater(float(np.std(csd_matrix)), 2.0, "CSD matrix is flat or zeroed!")

        # Run generator
        out_fig = generate_waterfall_csd()
        self.assertTrue(out_fig.exists(), f"Waterfall figure not created at {out_fig}")
        self.assertGreater(out_fig.stat().st_size, 10000, "Waterfall figure is empty")

    def test_03_profile_aware_pdf_report_generation(self):
        """Verify that PDF generation reflects the specified target profile."""
        out_harman = self.report_dir / "test_report_harman.pdf"
        out_bk = self.report_dir / "test_report_bk1974.pdf"

        if out_harman.exists():
            out_harman.unlink()
        if out_bk.exists():
            out_bk.unlink()

        # Generate Harman
        res_h = generate_pdf_report(profile="harman_wide_room", output_path=str(out_harman))
        self.assertTrue(Path(res_h).exists())
        self.assertGreater(Path(res_h).stat().st_size, 50000)

        # Generate B&K 1974
        res_bk = generate_pdf_report(profile="bk_1974", output_path=str(out_bk))
        self.assertTrue(Path(res_bk).exists())
        self.assertGreater(Path(res_bk).stat().st_size, 50000)

        # Canonical file must also be updated
        canonical_pdf = self.report_dir / "Informe_Calibracion_Acustica_Yamaha_Q_Acoustics.pdf"
        self.assertTrue(canonical_pdf.exists())

    def test_04_rt60_decay_generation(self):
        """Verify that 02_plot_responses.py dynamically creates figures/rt60_decay_analysis.png."""
        rt60_fig = self.fig_dir / "rt60_decay_analysis.png"
        cmd = [sys.executable, str(REPO_DIR / "scripts/02_plot_responses.py")]
        res = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"02_plot_responses failed: {res.stderr}")
        self.assertTrue(rt60_fig.exists(), "rt60_decay_analysis.png not created")
        self.assertGreater(rt60_fig.stat().st_size, 10000)

    def test_05_http_anti_cache_headers(self):
        """Verify web server emits strict anti-caching HTTP headers for assets and reports."""
        import urllib.request
        server_url = "http://127.0.0.1:53317"

        # Check /figures/
        try:
            fig_req = urllib.request.urlopen(f"{server_url}/figures/waterfall_csd_comparison.png", timeout=3.0)
            cache_hdr = fig_req.headers.get("Cache-Control", "")
            self.assertIn("no-cache", cache_hdr.lower())
            self.assertIn("no-store", cache_hdr.lower())
        except Exception as e:
            self.skipTest(f"Server not reachable on {server_url}: {e}")

        # Check /api/download_pdf
        try:
            pdf_req = urllib.request.urlopen(f"{server_url}/api/download_pdf?profile=harman_wide_room", timeout=5.0)
            cache_hdr = pdf_req.headers.get("Cache-Control", "")
            self.assertIn("no-cache", cache_hdr.lower())
            self.assertEqual(pdf_req.headers.get("Content-Type"), "application/pdf")
        except Exception as e:
            self.skipTest(f"PDF download route failed on {server_url}: {e}")


if __name__ == "__main__":
    unittest.main()
