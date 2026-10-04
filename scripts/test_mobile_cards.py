"""Regression checks for desktop-faithful mobile activity cards."""
import re
import sys
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import mobile_cards as cards  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
NS = "{http://www.w3.org/2000/svg}"


class MobileCardTests(unittest.TestCase):
    def test_desktop_streak_details_remain(self):
        source = (ROOT / "assets/streak-glass-template.svg").read_text()
        for theme in ("dark", "light"):
            result = cards.mobile_streak(source, theme)
            svg = ET.fromstring(result)
            self.assertEqual((svg.get("width"), svg.get("height")), ("600", "224"))
            self.assertEqual(svg.get("preserveAspectRatio"), "none")
            self.assertNotIn("Every day counts", result)
            for token in ("{{TOTAL}}", "{{LONGEST}}", "{{THIS_YEAR}}",
                          "{{ACTIVE_DAYS}}", "{{BEST_DAY_COUNT}}", "{{LAST_ACTIVE}}",
                          "{{FIRST_CONTRIBUTION}}", "{{LONGEST_RANGE}}"):
                self.assertIn(token, result)
            self.assertEqual(result.count("<text"), source.count("<text"))

    def test_tagline_is_removed_from_published_desktop_source(self):
        source = (ROOT / "assets/streak-glass-template.svg").read_text()
        source = source.replace("</g></svg>", '<text x="36" y="230">Every day counts</text></g></svg>')
        result = cards.mobile_streak(source, "dark")
        self.assertNotIn("Every day counts", result)
        self.assertIn("{{TOTAL}}", result)

    def test_wrong_dimensions_rejected(self):
        with self.assertRaisesRegex(ValueError, "dimensions"):
            cards.mobile_streak('<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"/>', "dark")

    def test_snake_keeps_keyframes_and_desktop_style(self):
        source = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="-16 -56 880 235" '
                  'width="880" height="235"><style>@keyframes move{to{opacity:1}}</style>'
                  '<rect x="832" y="50" width="12" height="12"/></svg>')
        for theme in ("dark", "light"):
            result = cards.mobile_snake(source, theme)
            svg = ET.fromstring(result)
            self.assertEqual((svg.get("width"), svg.get("height")), ("600", "224"))
            self.assertEqual(svg.get("preserveAspectRatio"), "none")
            self.assertIn("@keyframes move", result)
            self.assertIn('x="832"', result)
            self.assertIn("glass-snake-bg", result)


if __name__ == "__main__":
    unittest.main()
