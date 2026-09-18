import json
import unittest
import urllib.request
import urllib.error
import numpy as np
from unittest.mock import patch, MagicMock

BASE_URL = "http://127.0.0.1:53317"

class TestPresetPreloaderAndHistoryEndpoints(unittest.TestCase):
    def test_get_sessions_history_endpoint(self):
        req = urllib.request.Request(f"{BASE_URL}/api/sessions/history")
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("ok"))
            self.assertIn("sessions", data)
            self.assertIsInstance(data["sessions"], list)

    def test_preload_preset_endpoint_validation(self):
        # Missing profile_id should return 400 or error
        req = urllib.request.Request(
            f"{BASE_URL}/api/calibration/preload_preset",
            data=json.dumps({}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.assertFalse(data.get("ok"))
        except urllib.error.HTTPError as e:
            self.assertEqual(e.code, 400)

    def test_preload_preset_endpoint_valid_profile(self):
        req = urllib.request.Request(
            f"{BASE_URL}/api/calibration/preload_preset",
            data=json.dumps({"profile_id": "bk_1974"}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("ok"))
            self.assertEqual(data.get("deployed_profile"), "bk_1974")
            self.assertEqual(data.get("bands_fl"), 7)
            self.assertEqual(data.get("bands_fr"), 7)

if __name__ == "__main__":
    unittest.main()
