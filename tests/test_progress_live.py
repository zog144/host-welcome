"""Phase 2 protected integration tests; all producers are synthetic and injected."""
import contextlib
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from host_welcome import progress_live as live
from host_welcome.progress_cli import main
from host_welcome.progress_examples import BOOT, fixture
from host_welcome.progress_presentation import render_live_console


NOW = datetime.now(timezone.utc).isoformat()
def bootstrap(status="verified"):
    return {
        "schema": "zog-host-install-bootstrap-readiness-v1",
        "boot_id": BOOT, "observed_at": NOW,
        "headless_installation": {"status": status, "message_code": "demo-only", "evidence_ref": None},
    }


def controller():
    result = fixture("published")["controller"]
    result["observed_at"] = datetime.now(timezone.utc).isoformat()
    for item in result["items"]:
        item["observed_at"] = result["observed_at"]
    return result


class Phase2Tests(unittest.TestCase):
    def test_protected_bootstrap_only_without_controller(self):
        def missing(_boot):
            raise live.LiveProgressUnavailable("unavailable secret /etc/project")
        result = live.live_assessment(bootstrap_reader=bootstrap, controller_reader=missing)
        self.assertEqual(result.headless, "verified")
        self.assertEqual(result.graphics_request, "unknown")
        self.assertEqual(result.publication, "unobserved")
        self.assertEqual(result.graphical_session, "not-verified")
        self.assertEqual(result.controller_availability, "unavailable")
        out = render_live_console(result)
        self.assertIn("Headless installation: VERIFIED", out)
        self.assertNotIn("/etc/project", out)
        self.assertIn("NOT VERIFIED", out)

    def test_full_controller_does_not_claim_publication_or_install(self):
        observed = live.live_assessment(bootstrap_reader=bootstrap, controller_reader=lambda _: controller())
        self.assertEqual(observed.controller_availability, "observed")
        self.assertEqual(observed.lines[0].title, "Unassociated build command")
        self.assertEqual(observed.lines[0].state, "succeeded")
        self.assertEqual(observed.publication, "unobserved")
        self.assertEqual(observed.graphics_request, "unknown")
        self.assertEqual(observed.graphical_session, "not-verified")

    def test_wrong_boot_and_controller_timestamp_fail_closed(self):
        a = controller()
        a["boot_id"] = "22222222-2222-4222-8222-222222222222"
        result = live.live_assessment(bootstrap_reader=bootstrap, controller_reader=lambda _: a)
        self.assertEqual(result.controller_availability, "unavailable")
        a["boot_id"] = BOOT
        a["observed_at"] = "2026-10-16T12:00:00Z"
        a["items"][0]["observed_at"] = a["observed_at"]
        result = live.live_assessment(bootstrap_reader=bootstrap, controller_reader=lambda _: a)
        self.assertEqual(result.controller_availability, "unavailable")

    def test_invalid_or_missing_bootstrap_never_connects_controller(self):
        for producer in (
            lambda: (_ for _ in ()).throw(OSError("private state path")),
            lambda: {"boot_id": None, "headless_installation": {"status": "verified"}},
            lambda: {"boot_id": BOOT, "headless_installation": {"status": "root"}},
        ):
            with self.subTest(producer=producer):
                observed = live.live_assessment(
                    bootstrap_reader=producer,
                    controller_reader=lambda _: self.fail("must not read controller"),
                )
                self.assertEqual(observed.headless, "unknown")
                self.assertEqual(observed.controller_availability, "unavailable")

    def test_all_bootstrap_statuses_remain_distinct(self):
        for status in ("verified", "pending", "unknown", "degraded", "failed"):
            with self.subTest(status=status):
                assessment = live.live_assessment(
                    bootstrap_reader=lambda: bootstrap(status),
                    controller_reader=lambda _: (_ for _ in ()).throw(OSError()),
                )
                self.assertEqual(assessment.headless, status)
                self.assertIn(status.upper(), render_live_console(assessment))

    def test_new_live_cli_is_read_only_and_no_file_input(self):
        with patch("host_welcome.progress_cli.live_assessment", return_value=
                   live.live_assessment(bootstrap_reader=bootstrap,
                                        controller_reader=lambda _: (_ for _ in ()).throw(OSError()))):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["--live"]), 0)
                self.assertIn("PROTECTED READ-ONLY", output.getvalue())
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(main(["--live", "--format", "json"]), 0)
                data = json.loads(output.getvalue())
                self.assertFalse(data["simulated"])
                self.assertEqual(data["publication"], "unobserved")
                self.assertTrue(data["read_only"])
        with contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                main(["--live", "--output", "/tmp/private.json"])
            with self.assertRaises(SystemExit):
                main(["--live", "--input", "/tmp/fake.json"])

    def test_cli_defaults_to_unavailable_when_no_source_installed(self):
        with patch("host_welcome.progress_live.request_bootstrap",
                   side_effect=live.LiveProgressUnavailable("producer error /var/state")):
            with contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(main(["--live"]), 0)
            self.assertIn("Headless installation: UNKNOWN", out.getvalue())
            self.assertNotIn("/var/state", out.getvalue())

    def test_policy_schema_and_uid_are_fixed(self):
        valid = {
            "schema":"zog-host-welcome-progress-observer-v1", "enabled":True,
            "consumer_uid":12345, "controller_owner_uid":23456,
            "socket":live.CONTROLLER_SOCKET, "box_control_source_commit":"a"*40,
        }
        # The parser rejects duplicate keys before it can reach an owner policy.
        with self.assertRaisesRegex(ValueError, "duplicate"):
            json.loads('{"enabled":true,"enabled":false}', object_pairs_hook=live._no_duplicates)
        self.assertEqual(live.CONTROLLER_SOCKET, "/run/host-welcome/controller-progress.sock")
        self.assertNotIn("station-access", live.CONTROLLER_SOCKET)
        self.assertNotEqual(valid["consumer_uid"],valid["controller_owner_uid"])

    def test_policy_missing_or_wrong_permissions_means_unavailable(self):
        with patch("host_welcome.progress_live.os.open", side_effect=FileNotFoundError()):
            with self.assertRaises(live.LiveProgressUnavailable):
                live.read_controller_policy()
        with patch("host_welcome.progress_live.read_controller_policy",
                   side_effect=live.LiveProgressUnavailable("not installed")):
            with self.assertRaises(live.LiveProgressUnavailable):
                live.request_controller(BOOT)

    def test_actual_controller_client_is_not_called_on_wrong_user(self):
        with patch("host_welcome.progress_live.read_controller_policy",
                   return_value={"consumer_uid":12345,"controller_owner_uid":23456}), \
             patch("host_welcome.progress_live._welcome_uid", return_value=12345), \
             patch("host_welcome.progress_live.os.geteuid", return_value=99999, create=True):
            with self.assertRaises(live.LiveProgressUnavailable):
                live.request_controller(BOOT)

    def test_bounded_controller_pages_and_hostile_ids_fail_closed(self):
        bad = controller()
        bad["items"][0]["application"] = "/etc/shadow"
        observed = live.live_assessment(bootstrap_reader=bootstrap, controller_reader=lambda _: bad)
        self.assertEqual(observed.controller_availability, "unavailable")
        self.assertEqual(observed.publication, "unobserved")
        bad = controller()
        bad["page"]["build_has_more"] = True
        observed = live.live_assessment(bootstrap_reader=bootstrap, controller_reader=lambda _: bad)
        self.assertEqual(observed.controller_availability, "observed")
        self.assertTrue(any("non-atomic" in x for x in observed.warnings))

    def test_no_automatic_retries_or_app_launch(self):
        calls = []
        def boot():
            calls.append("bootstrap")
            return bootstrap()
        def ctl(boot_id):
            calls.append(("controller", boot_id))
            return controller()
        live.live_assessment(bootstrap_reader=boot, controller_reader=ctl)
        self.assertEqual(calls, ["bootstrap", ("controller", BOOT)])

    def test_staged_policy_is_exact_revision_and_distinct_uids(self):
        valid = {
            "schema": "zog-host-welcome-progress-observer-v1", "enabled": True,
            "consumer_uid": 12041, "controller_owner_uid": 11021,
            "socket": live.CONTROLLER_SOCKET,
            "box_control_source_commit": live.REVIEWED_BOX_CONTROL_COMMIT,
        }
        self.assertIs(live._validate_policy(valid), valid)
        for name, value in (
            ("box_control_source_commit", "03c847ec6adc55fd5e2268534d47b500d9f52ab9"),
            ("box_control_source_commit", "0" * 40),
            ("socket", "/run/zog-host-export/application-progress/application-progress.sock"),
            ("consumer_uid", 11021), ("consumer_uid", 0),
            ("controller_owner_uid", 0), ("enabled", False),
        ):
            with self.subTest(name=name, value=value):
                changed = dict(valid, **{name:value})
                with self.assertRaises(live.LiveProgressUnavailable):
                    live._validate_policy(changed)
        with self.assertRaises(live.LiveProgressUnavailable):
            live._validate_policy(dict(valid, extra="arbitrary"))

    def test_reviewed_box_control_client_invocation_and_frozen_role(self):
        """Verify the actual peer-checked client constructor and snapshot call."""
        import sys
        import types
        captured = []
        mock_client_mod = types.ModuleType("zog.box_control.application_progress_client")
        class Client:
            def __init__(self, path, *, controller_uid, timeout_seconds):
                captured.append(("client", path, controller_uid, timeout_seconds))
            def snapshot(self, *, limit):
                captured.append(("snapshot", limit))
                return controller()
        mock_client_mod.ApplicationProgressClient = Client
        mock_zog = types.ModuleType("zog")
        mock_zog.__path__ = []
        mock_box = types.ModuleType("zog.box_control")
        mock_box.__path__ = []
        modules = {
            "zog": mock_zog, "zog.box_control": mock_box,
            "zog.box_control.application_progress_client": mock_client_mod,
        }
        with patch.dict(sys.modules, modules), \
             patch("host_welcome.progress_live.read_controller_policy",
                   return_value={"consumer_uid": 12041, "controller_owner_uid": 11021}), \
             patch("host_welcome.progress_live._welcome_uid", return_value=12041), \
             patch("host_welcome.progress_live.os.geteuid", return_value=12041, create=True):
            snapshot = live.request_controller(BOOT)
        self.assertEqual(snapshot["boot_id"], BOOT)
        self.assertEqual(captured, [
            ("client", "/run/host-welcome/controller-progress.sock", 11021, 12),
            ("snapshot", 4),
        ])

    def test_simulation_import_requires_no_posix_pwd(self):
        """A user can run the simulation CLI on Windows without Linux pwd."""
        import builtins
        import importlib
        old_import = builtins.__import__
        def guarded_import(name, *args, **kwargs):
            if name == "pwd":
                raise ImportError("pwd is not installed")
            return old_import(name, *args, **kwargs)
        with patch("builtins.__import__", side_effect=guarded_import):
            importlib.reload(live)
        self.assertIsNotNone(live.live_assessment)
        self.assertEqual(live.REVIEWED_BOX_CONTROL_COMMIT,
                         "8249715708c6ef8a1fd30a3fb529b4034ffffe25")
