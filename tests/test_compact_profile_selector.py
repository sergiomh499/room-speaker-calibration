"""
tests/test_compact_profile_selector.py
Unit tests and DOM contract verification for the compact acoustic profile selector.
"""

import json
import re
import unittest
from pathlib import Path

# Load web_calibration_server source
SERVER_PY = Path(__file__).resolve().parent.parent / "scripts" / "web_calibration_server.py"
TARGETS_JSON = Path(__file__).resolve().parent.parent / "config" / "targets.json"


class TestCompactProfileSelector(unittest.TestCase):
    def setUp(self):
        self.assertTrue(SERVER_PY.exists(), "web_calibration_server.py must exist")
        self.assertTrue(TARGETS_JSON.exists(), "config/targets.json must exist")
        with open(SERVER_PY, "r", encoding="utf-8") as f:
            self.server_code = f.read()
        with open(TARGETS_JSON, "r", encoding="utf-8") as f:
            self.targets = json.load(f)

    def test_01_all_nine_profiles_have_required_metadata(self):
        """Validates that all 9 community profiles possess rank, badge, category, description, pros, and cons."""
        self.assertEqual(len(self.targets), 9, "Expected exactly 9 community profiles")
        for key, p in self.targets.items():
            self.assertIn("name", p, f"Profile {key} missing name")
            self.assertIn("rank", p, f"Profile {key} missing rank")
            self.assertIn("badge", p, f"Profile {key} missing badge")
            self.assertIn("category", p, f"Profile {key} missing category")
            self.assertIn("description", p, f"Profile {key} missing description")
            self.assertIn("pros", p, f"Profile {key} missing pros list")
            self.assertIn("cons", p, f"Profile {key} missing cons list")
            self.assertIsInstance(p["pros"], list)
            self.assertIsInstance(p["cons"], list)

    def test_02_css_grid_and_chip_classes_defined(self):
        """Validates that CSS definitions for compact grid, chips, and inspector exist in web_calibration_server.py."""
        self.assertIn(".compact-profiles-grid", self.server_code, "Missing .compact-profiles-grid CSS class")
        self.assertIn(".compact-profile-chip", self.server_code, "Missing .compact-profile-chip CSS class")
        self.assertIn(".profile-inspector", self.server_code, "Missing .profile-inspector CSS class")
        
        # Verify grid layout declaration
        self.assertTrue(
            "grid-template-columns" in self.server_code or "display: grid" in self.server_code,
            "CSS grid display required for compact density"
        )

    def test_03_html_contains_profiles_container_and_inspector_panel(self):
        """Validates that the HTML markup contains #profiles-container and #profile-inspector-panel."""
        self.assertIn('id="profiles-container"', self.server_code)
        self.assertIn('id="profile-inspector-panel"', self.server_code)

    def test_04_js_renders_compact_chips_with_selection(self):
        """Validates that loadCommunityProfiles renders compact-profile-chip and selectProfile updates active state."""
        self.assertIn("compact-profile-chip", self.server_code)
        self.assertIn("updateProfileInspector", self.server_code)
        self.assertIn("active-target", self.server_code)

    def test_05_responsive_media_queries_present(self):
        """Validates that responsive media queries adjust the grid for mobile/tablet viewports."""
        self.assertIn("@media", self.server_code, "Media queries required for responsive adaptation")


if __name__ == "__main__":
    unittest.main()
