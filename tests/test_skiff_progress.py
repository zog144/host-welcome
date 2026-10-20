"""Producer-derived presentation only; Skiff events remain non-authoritative."""
from dataclasses import replace
import unittest

from host_welcome.progress import ProgressAssessment, ProgressLine
from host_welcome.skiff_progress import skiff_state_for_progress
from host_welcome.model import load_snapshot, assess
from host_welcome.presentation import render_html
from host_welcome.progress_examples import fixture
from host_welcome.progress import load_progress_fixture, assess_progress


def assessment(**kwargs):
    return ProgressAssessment(headless="verified", graphics_request="requested",
        publication="unobserved", graphical_session="not-verified",
        controller_availability="observed", lines=(), warnings=(), **kwargs)


class SkiffProgressTests(unittest.TestCase):
    def test_publication_never_sets_ready(self):
        for state in ("unobserved","partial","compatible"):
            with self.subTest(state=state):
                p=replace(assessment(), publication=state)
                self.assertEqual(skiff_state_for_progress(p),"waiting")

    def test_build_failure_blocked_and_unknown_have_honest_semantics(self):
        for state,expect in (("failed","error"),("blocked","warning"),
                             ("uncertain","thinking"),("running","working")):
            with self.subTest(state=state):
                p=replace(assessment(),lines=(
                    ProgressLine("firefox-esr","building",state,"producer observation"),))
                self.assertEqual(skiff_state_for_progress(p),expect)

    def test_reconnection_cannot_replay_a_fake_ready_transition(self):
        p=assessment()
        disconnected=replace(p,controller_availability="unavailable")
        self.assertEqual(skiff_state_for_progress(disconnected),"thinking")
        reconnected=replace(p,controller_availability="observed",publication="compatible")
        self.assertEqual(skiff_state_for_progress(reconnected),"waiting")
        reboot_uncertain=replace(reconnected,lines=(ProgressLine(
            "firefox-esr","building","uncertain","reboot"),))
        self.assertEqual(skiff_state_for_progress(reboot_uncertain),"thinking")

    def test_approved_html_still_cleans_up_and_supports_reduced_motion(self):
        from importlib.resources import files
        import json
        example=files("host_welcome").joinpath("examples/pending.json")
        raw=json.loads(example.read_text(encoding="utf-8"))
        page=render_html(load_snapshot(raw),assess(load_snapshot(raw)))
        self.assertIn('createSkiffPresenter(container,{palette:"blue",reducedMotion:"auto"})',page)
        self.assertIn("skiff.destroy()",page)
        self.assertIn("pagehide",page)
        self.assertIn("@media(prefers-reduced-motion:reduce)",page)
        self.assertIn("aria-label=",page)
        self.assertIn("role=\"img\"",page)
        self.assertNotIn("skiff.playSequence(",page)
        self.assertNotIn("window.fetch(",page)
        self.assertIn("SIMULATED EXAMPLE",page)
