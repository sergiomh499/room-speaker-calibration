"""
tests/test_compact_profile_selector.py
Unit tests and DOM contract verification for the compact acoustic profile selector.
"""

import json
import re
import unittest
from pathlib import Path

# Load template source
TEMPLATE_HTML = Path(__file__).resolve().parent.parent / "templates" / "octave.html"
TARGETS_JSON = Path(__file__).resolve().parent.parent / "config" / "targets.json"


class TestCompactProfileSelector(unittest.TestCase):
    def setUp(self):
        self.assertTrue(TEMPLATE_HTML.exists(), "templates/octave.html must exist")
        self.assertTrue(TARGETS_JSON.exists(), "config/targets.json must exist")
        with open(TEMPLATE_HTML, "r", encoding="utf-8") as f:
            self.html_code = f.read()
        with open(TARGETS_JSON, "r", encoding="utf-8") as f:
            self.targets = json.load(f)

    def test_01_all_nine_profiles_have_required_metadata(self):
        """Validates that community profiles possess rank, badge, category, description, pros, and cons."""
        self.assertGreaterEqual(len(self.targets), 9, "Expected at least 9 community profiles")
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
        """Validates that CSS definitions for carousel, tabs, and inspector exist."""
        self.assertIn(".profiles-carousel", self.html_code)
        self.assertIn(".cat-pill", self.html_code)
        self.assertIn(".profile-detail-panel", self.html_code)

    def test_03_html_contains_profiles_container_and_inspector_panel(self):
        """Validates that the HTML markup contains #profiles-carousel and #profile-detail-panel."""
        self.assertIn('id="profiles-carousel"', self.html_code)
        self.assertIn('id="profile-detail-panel"', self.html_code)

    def test_04_js_renders_compact_chips_with_selection(self):
        """Validates that profile selection and rendering functions exist in template."""
        self.assertIn("renderProfiles", self.html_code)
        self.assertIn("selectProfile", self.html_code)

    def test_05_responsive_media_queries_present(self):
        """Validates that responsive media queries adjust layout for mobile viewports."""
        self.assertIn("@media", self.html_code, "Media queries required for responsive adaptation")

if __name__ == "__main__":
    unittest.main()
