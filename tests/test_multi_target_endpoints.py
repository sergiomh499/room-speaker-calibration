import unittest
import urllib.request
import json

class TestMultiTargetEndpoints(unittest.TestCase):
    BASE_URL = "http://127.0.0.1:53317"

    @classmethod
    def setUpClass(cls):
        try:
            req = urllib.request.Request(f"{cls.BASE_URL}/api/targets")
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                cls.server_online = (resp.status == 200)
        except Exception:
            cls.server_online = False

    def setUp(self):
        if not self.server_online:
            self.skipTest("Web calibration server offline on port 53317")

    def test_get_targets_endpoint(self):
        url = f"{self.BASE_URL}/api/targets"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("ok"))
            self.assertIn("targets", data)
            self.assertGreaterEqual(len(data["targets"]), 5)
            # Verify structure of target objects
            first = data["targets"][0]
            self.assertIn("id", first)
            self.assertIn("name", first)
            self.assertIn("category", first)

    def test_post_multi_target_eval_endpoint(self):
        url = f"{self.BASE_URL}/api/calibration/multi_target_eval"
        payload = json.dumps({
            "measurement_file": "medicion_verificacion_manual.npz"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            self.assertEqual(resp.status, 200)
            data = json.loads(resp.read().decode("utf-8"))
            self.assertTrue(data.get("ok"))
            self.assertIn("results", data)
            self.assertIn("best_fit", data)

if __name__ == "__main__":
    unittest.main()
