import copy
import contextlib
import io
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from host_welcome.progress import (
    ProgressError, assess_progress, load_progress_fixture,
)
from host_welcome.progress_examples import BOOT, JOB, NOW, VIEW, fixture
from host_welcome.progress_presentation import render_progress_console
from host_welcome.progress_cli import main


def loaded(scenario="building"):
    return load_progress_fixture(fixture(scenario))


class ProgressTests(unittest.TestCase):
    def test_scenarios_and_separation_of_authority(self):
        expected = {
            "building": ("verified", "requested", "unobserved"),
            "blocked": ("verified", "requested", "unobserved"),
            "uncertain": ("verified", "requested", "unobserved"),
            "published": ("verified", "requested", "verified"),
            "headless": ("verified", "not-requested", "unobserved"),
            "unavailable": ("unknown", "requested", "unobserved"),
        }
        for name, outcome in expected.items():
            with self.subTest(name=name):
                result = assess_progress(loaded(name))
                self.assertEqual(
                    (result.headless, result.graphics_request, result.publication), outcome
                )
                self.assertEqual(result.graphical_session, "not-verified")
                output = render_progress_console(loaded(name), result)
                self.assertIn("SIMULATED EXAMPLE", output)
                self.assertIn("Local login / graphical session: NOT VERIFIED", output)
                self.assertNotIn("% complete", output)
                self.assertNotIn("ETA", output)

    def test_command_success_is_not_publication(self):
        raw = fixture("published")
        row = raw["image_build"]["operations"][0]
        row.update(phase="building", state="succeeded", publication="unobserved",
                   published_view=None, publication_evidence_ref=None)
        assessment = assess_progress(load_progress_fixture(raw))
        self.assertEqual(assessment.publication, "unobserved")
        self.assertEqual(assessment.lines[0].state, "succeeded")
        self.assertIn("publication is independent", assessment.lines[0].description)

    def test_published_software_never_claims_greetd_login(self):
        result = assess_progress(loaded("published"))
        self.assertEqual(result.publication, "verified")
        self.assertEqual(result.graphical_session, "not-verified")
        self.assertTrue(all("LOGIN READY" not in x.title for x in result.lines))

    def test_unassociated_job_retains_unknown_application(self):
        raw = fixture("published")
        raw["image_build"] = None
        result = assess_progress(load_progress_fixture(raw))
        self.assertEqual(result.publication, "unobserved")
        self.assertEqual(result.lines[0].title, "Unassociated build job " + JOB)
        self.assertIn("application and publication unknown", result.lines[0].description)

    def test_unknown_or_pruned_job_never_confirms_build(self):
        raw = fixture("published")
        raw["controller"]["items"].clear()
        assessment = assess_progress(load_progress_fixture(raw))
        self.assertEqual(assessment.lines[0].state, "unknown")
        self.assertEqual(assessment.publication, "unobserved")
        self.assertIn("association", " ".join(assessment.warnings))

    def test_conflicting_controller_job_does_not_claim_publication(self):
        raw = fixture("published")
        raw["controller"]["items"][0].update(
            state="failed", message_code="build-command-failed")
        result = assess_progress(load_progress_fixture(raw))
        self.assertEqual(result.lines[0].state, "uncertain")
        self.assertEqual(result.publication, "unobserved")

    def test_unrequested_only_from_separate_intent_fixture(self):
        result = assess_progress(loaded("headless"))
        self.assertEqual(result.graphics_request, "not-requested")
        raw = fixture("headless")
        raw["installation"]["graphics_request"] = "unknown"
        result = assess_progress(load_progress_fixture(raw))
        self.assertEqual(result.graphics_request, "unknown")
        self.assertNotIn("NOT REQUESTED", render_progress_console(load_progress_fixture(raw), result))

    def test_stale_future_and_wrong_boot_fail_closed(self):
        for bad in (
            lambda d: d["controller"].update(observed_at="2026-10-15T12:00:00Z"),
            lambda d: d["controller"].update(observed_at="2026-10-17T12:00:00Z"),
            lambda d: d["controller"].update(boot_id="22222222-2222-4222-8222-222222222222"),
        ):
            raw = fixture("published")
            bad(raw)
            # Keep the controller's own item timestamp consistent with the
            # envelope; otherwise the validator correctly rejects the input
            # before the stale/future assessment can be exercised.
            raw["controller"]["items"][0]["observed_at"] = raw["controller"]["observed_at"]
            result = assess_progress(load_progress_fixture(raw))
            self.assertEqual(result.controller_availability, "unavailable")
            self.assertEqual(result.publication, "unobserved")
            self.assertEqual(result.lines[0].state, "unknown")
        raw = fixture("published")
        raw["image_build"]["observed_at"] = "2026-10-15T12:00:00Z"
        self.assertEqual(assess_progress(load_progress_fixture(raw)).publication, "unobserved")
        raw = fixture("headless")
        raw["installation"]["observed_at"] = "2026-10-15T12:00:00Z"
        result = assess_progress(load_progress_fixture(raw))
        self.assertEqual(result.headless, "unknown")
        self.assertEqual(result.graphics_request, "unknown")

    def test_explicit_now_after_reboot_is_not_fixture_reference_time(self):
        data = loaded("published")
        later = datetime(2026, 10, 17, tzinfo=timezone.utc)
        result = assess_progress(data, now=later)
        self.assertEqual(result.publication, "unobserved")
        self.assertEqual(result.headless, "unknown")
        self.assertEqual(result.controller_availability, "unavailable")

    def test_bounded_non_atomic_controller_paging(self):
        raw = fixture("building")
        page = raw["controller"]["page"]
        page.update(build_has_more=True, next_build=JOB)
        result = assess_progress(load_progress_fixture(raw))
        self.assertIn("non-atomic pages", " ".join(result.warnings))
        page["next_build"] = None
        with self.assertRaises(ProgressError):
            load_progress_fixture(raw)

    def test_defensive_exact_schema_and_no_live_input(self):
        mutations = [
            lambda d: d.update(source_kind="host"),
            lambda d: d.update(schema="zog-application-progress-v1"),
            lambda d: d.update(extra=True),
            lambda d: d["controller"].update(host_id="pretend-host"),
            lambda d: d["controller"].update(extra=True),
            lambda d: d["controller"]["items"][0].update(application="firefox"),
            lambda d: d["controller"]["items"][0].update(phase="publishing"),
            lambda d: d["controller"]["items"][0].update(progress={"completed":99,"total":100}),
            lambda d: d["controller"]["items"][0].update(message_code="secret-file"),
            lambda d: d["controller"]["items"][0].update(evidence_ref="/etc/shadow"),
            lambda d: d["controller"]["items"][0].update(state="ready"),
            lambda d: d["installation"].update(extra="trust-me"),
            lambda d: d["image_build"]["operations"][0].update(application="bad\x1b[31m"),
            lambda d: d["image_build"]["operations"][0].update(build_job_id="../secrets"),
            lambda d: d["image_build"]["operations"][0].update(published_view=VIEW),
            lambda d: d["image_build"]["operations"][0].update(
                publication="verified", published_view=VIEW),
            lambda d: d["image_build"]["operations"][0].update(
                publication="verified", published_view=VIEW,
                publication_evidence_ref="receipt-demo-1"),
        ]
        for change in mutations:
            data = fixture("building")
            change(data)
            with self.subTest(change=str(change)), self.assertRaises(ProgressError):
                load_progress_fixture(data)

    def test_non_atomic_page_has_no_auto_cross_page_merge(self):
        page1 = fixture("building")
        page2 = copy.deepcopy(page1)
        page2["controller"]["snapshot_id"] = "d" * 32
        page2["controller"]["items"] = []
        self.assertTrue(load_progress_fixture(page1))
        result2 = assess_progress(load_progress_fixture(page2))
        self.assertEqual(result2.lines[0].state, "unknown")
        self.assertEqual(result2.publication, "unobserved")

    def test_non_schema_or_timestamp_tricks_rejected(self):
        tests = [
            lambda d: d.update(reference_time="2026-10-16T12:00:00"),
            lambda d: d["controller"].update(snapshot_id=True),
            lambda d: d["controller"].update(items="all done"),
            lambda d: d["image_build"].update(operations=[{}]),
            lambda d: d["image_build"].update(boot_id="prior boot"),
            lambda d: d["controller"]["items"][0].update(controller_request_id="go\nroot"),
        ]
        for fn in tests:
            raw = fixture("building")
            fn(raw)
            with self.assertRaises(ProgressError):
                load_progress_fixture(raw)

    def test_cli_console_json_and_output(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(main(["--scenario", "building"]), 0)
        self.assertIn("Uncertain", out.getvalue().title())
        with contextlib.redirect_stdout(io.StringIO()) as stream:
            self.assertEqual(main(["--scenario", "published", "--format", "json"]), 0)
            value = json.loads(stream.getvalue())
        self.assertTrue(value["simulated"])
        self.assertEqual(value["publication"], "verified")
        self.assertEqual(value["graphical_session"], "not-verified")
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "progress.txt"
            self.assertEqual(main(["--scenario", "headless", "--output", str(target)]), 0)
            self.assertIn("NOT REQUESTED", target.read_text(encoding="utf-8"))

    def test_external_fixture_is_never_live(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "input.json"
            value = fixture("published")
            target.write_text(json.dumps(value), encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(["--input", str(target)]), 0)
            self.assertIn("SIMULATED EXAMPLE", out.getvalue())
            value["source_kind"] = "host"
            target.write_text(json.dumps(value), encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--input", str(target)]), 2)
