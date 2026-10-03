"""Offline smoke tests for themed GitHub Streak and animated snake wrappers."""
from __future__ import annotations
import unittest
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
import generate_streak as streak
import glass_snake


class GlassProfileTests(unittest.TestCase):
    def test_current_streak_preserves_yesterday_then_resets(self):
        contributions = {date(2026, 10, 3): 2}
        self.assertEqual(streak.calculate_current_streak(contributions, date(2026, 10, 4)).days, 1)
        self.assertEqual(streak.calculate_current_streak(contributions, date(2026, 10, 5)).days, 0)

    def test_last_active_and_svg_render(self):
        data = {date(2026, 10, 3): 2}
        stats = streak.calculate_stats(data, date(2026, 10, 5))
        self.assertEqual(stats.last_active, date(2026, 10, 3))
        for theme in ("dark", "light"):
            svg = streak.render_svg(stats, "Barbaron86", 2026, theme=theme)
            ET.fromstring(svg)
            self.assertIn("LAST ACTIVE", svg)
            self.assertIn("Start a new streak", svg)
            self.assertIn('fill-opacity="0"', svg)

    def test_snake_preserves_css_animation(self):
        source = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-16 -32 880 192" width="880" height="192"><style>@keyframes move{to{opacity:1}}.snake{animation:move 20s infinite}</style><rect class="snake" width="12" height="12"/></svg>'
        for theme in ("dark", "light"):
            output = glass_snake.wrap_snake(source, theme)
            ET.fromstring(output)
            self.assertIn("animation:move 20s infinite", output)
            self.assertIn("glass-snake-bg", output)


if __name__ == "__main__":
    unittest.main()
