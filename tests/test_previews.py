import tempfile
import unittest
from pathlib import Path

from host_welcome.cli import SCENARIOS
from host_welcome.previews import build_previews


class PreviewTests(unittest.TestCase):
    def test_every_scenario_is_standalone_and_indexed(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            generated = build_previews(output)
            self.assertEqual(len(generated), len(SCENARIOS) + 1)
            chooser = (output / "index.html").read_text(encoding="utf-8")
            self.assertIn("SIMULATED EXAMPLES", chooser)
            for scenario in SCENARIOS:
                filename = f"welcome-{scenario}.html"
                self.assertIn(filename, chooser)
                html = (output / filename).read_text(encoding="utf-8")
                self.assertIn("SIMULATED EXAMPLE", html)
                self.assertIn('<script type="module">', html)
                self.assertIn('id="skiff-head"', html)
                self.assertNotIn('src="https://', html)
                self.assertNotIn('href="https://', html)
