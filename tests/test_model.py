import copy
import json
import unittest
from datetime import datetime, timedelta, timezone
from importlib.resources import files

from host_welcome.model import CATEGORIES, SnapshotError, assess, load_snapshot
from host_welcome.presentation import render_console, render_html


def fixture(name="pending"):
    return json.loads(files("host_welcome").joinpath(f"examples/{name}.json").read_text())


class ModelTests(unittest.TestCase):
    def test_all_scenarios_aggregate(self):
        for name, expected in {
            "ready": "ready", "pending": "setup_pending", "offline": "degraded",
            "recovery": "attention", "interrupted": "degraded"
        }.items():
            with self.subTest(name=name):
                snapshot = load_snapshot(fixture(name))
                self.assertEqual(assess(snapshot).aggregate, expected)
                self.assertEqual(len(snapshot.observations), len(CATEGORIES))
                self.assertIn("SIMULATED EXAMPLE", render_console(snapshot, assess(snapshot)))
                self.assertIn("SIMULATED EXAMPLE", render_html(snapshot, assess(snapshot)))

    def test_fail_closed_on_missing_and_unrecognized_fields(self):
        for alteration in (
            lambda x: x["observations"].pop("recovery"),
            lambda x: x.update(schema_version="host-welcome.readiness/v2"),
            lambda x: x.update(extra=True),
            lambda x: x["observations"]["network"].update(status="healthy"),
            lambda x: x["observations"]["network"].update(extra=True),
        ):
            data = fixture()
            alteration(data)
            with self.assertRaises(SnapshotError):
                load_snapshot(data)

    def test_verified_requires_evidence(self):
        data = fixture("ready")
        data["observations"]["network"]["evidence_ref"] = None
        with self.assertRaisesRegex(SnapshotError, "requires an evidence_ref"):
            load_snapshot(data)

    def test_caller_does_not_gain_host_authority(self):
        data = fixture("ready")
        data["source_kind"] = "host"
        with self.assertRaisesRegex(SnapshotError, "protected trusted adapter"):
            load_snapshot(data)

    def test_host_expiry_and_future_clock_fail_closed(self):
        data = fixture("ready")
        data["source_kind"] = "host"
        now = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)
        snapshot = load_snapshot(data, trusted=True)
        self.assertEqual(assess(snapshot, now=now).aggregate, "ready")
        self.assertEqual(assess(snapshot, now=now + timedelta(minutes=6)).aggregate, "unknown")
        self.assertFalse(assess(snapshot, now=now + timedelta(minutes=6)).fresh)
        self.assertEqual(assess(snapshot, now=now - timedelta(minutes=2)).aggregate, "unknown")

    def test_unknown_and_pending_are_not_ready(self):
        data = fixture("ready")
        data["observations"]["network"]["status"] = "unknown"
        self.assertEqual(assess(load_snapshot(data)).aggregate, "unknown")
        data["observations"]["network"]["status"] = "pending"
        self.assertEqual(assess(load_snapshot(data)).aggregate, "setup_pending")

    def test_escape_host_content_and_forbid_terminal_control(self):
        data = fixture()
        data["host_label"] = "<script>alert(1)</script>"
        snap = load_snapshot(data)
        output = render_html(snap, assess(snap))
        self.assertIn("&lt;script&gt;", output)
        self.assertNotIn("<script>alert(1)</script>", output)
        data["host_label"] = "bad\nterminal"
        with self.assertRaises(SnapshotError):
            load_snapshot(data)

    def test_read_only_no_secret_fields(self):
        data = fixture()
        data["private_key"] = "not-permitted"
        with self.assertRaises(SnapshotError):
            load_snapshot(data)
