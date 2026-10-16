"""Check the standalone Skiff consumer stays on the documented presenter API."""
from importlib.resources import files
import unittest

from host_welcome.cli import SCENARIOS
from host_welcome.model import load_snapshot, assess
from host_welcome.presentation import render_html
import json


class SkiffPresenterTests(unittest.TestCase):
    def test_generated_inline_runtime_is_presenter_based(self):
        assets = files("host_welcome").joinpath("assets")
        runtime = assets.joinpath("pose_animate.js").read_text(encoding="utf-8")
        self.assertIn("createSkiffPresenter(", runtime)
        self.assertIn("BSD-3-Clause OR GPL-3.0-only", runtime)
        self.assertIn("ec5e8986be294a187e4d257df883dccfabea1034", runtime)
        self.assertNotIn("from './index.js'", runtime)
        self.assertNotIn('from "./index.js"', runtime)
        license_text = assets.joinpath("pose-animate-BSD-3-Clause.txt").read_text(encoding="utf-8")
        self.assertIn("Redistribution and use in source and binary forms", license_text)

    def test_all_scenarios_select_semantics_and_no_recovery_choreography(self):
        expected = {"pending":"waiting", "ready":"ready", "offline":"warning",
                    "recovery":"error", "interrupted":"warning"}
        for name in SCENARIOS:
            with self.subTest(name=name):
                fixture = files("host_welcome").joinpath("examples",name+".json")
                snapshot = load_snapshot(json.loads(fixture.read_text(encoding="utf-8")))
                html = render_html(snapshot, assess(snapshot))
                self.assertIn('createSkiffPresenter(container,{palette:"blue",reducedMotion:"auto"})', html)
                self.assertIn('skiff.setState("'+expected[name]+'")', html)
                self.assertIn('skiff.destroy()', html)
                self.assertNotIn('skiff.playSequence(', html)
                self.assertIn("SIMULATED EXAMPLE", html)
