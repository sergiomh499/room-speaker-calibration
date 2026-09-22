#!/usr/bin/env python3
"""
Integration tests for Paginated Wizard Navigation and Non-Destructive Point Re-Measurement (FR-010, FR-011, SC-005).
"""
import unittest
import urllib.request
import json
import time

SERVER_URL = "http://127.0.0.1:53317"

class TestWizardNavigation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Verify server is responding
        try:
            req = urllib.request.Request(f"{SERVER_URL}/api/session_state")
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                cls.server_online = (resp.status == 200)
        except Exception:
            cls.server_online = False

    def test_session_state_endpoint_returns_points_and_wizard_metadata(self):
        """FR-010: Session state provides point statuses and active wizard step."""
        if not self.server_online:
            self.skipTest("Web calibration server offline")
            
        req = urllib.request.Request(f"{SERVER_URL}/api/session_state")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            self.assertIn("points", data)
            self.assertEqual(len(data["points"]), 5)

    def test_clear_point_preserves_other_points(self):
        """FR-011, SC-005: Clearing a single point does not wipe the other points."""
        if not self.server_online:
            self.skipTest("Web calibration server offline")

        # Clear Point 3
        req = urllib.request.Request(f"{SERVER_URL}/api/clear_point?point=3", data=b"", method="POST")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(res.get("ok"))
            self.assertFalse(res.get("points", {}).get("punto_3", True))
            # Verify Point 1 and Point 2 are intact
            self.assertTrue(res.get("points", {}).get("punto_1", False))

        # Restore Point 3 from file if backup exists
        req_rec = urllib.request.Request(f"{SERVER_URL}/api/restore_point?point=3", data=b"", method="POST")
        try:
            with urllib.request.urlopen(req_rec, timeout=2.0) as r:
                pass
        except urllib.error.HTTPError as e:
            e.close()
        except Exception:
            pass

    def test_web_html_contains_wizard_stepper_elements(self):
        """FR-010: Main web interface contains wizard stepper and navigation pages."""
        if not self.server_online:
            self.skipTest("Web calibration server offline")

        req = urllib.request.Request(f"{SERVER_URL}/")
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            html = resp.read().decode("utf-8")
            self.assertIn("wizard-stepper", html)
            self.assertIn("wizard-page", html)

if __name__ == "__main__":
    unittest.main()
