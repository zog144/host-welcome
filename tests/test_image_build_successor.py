"""Receipt-only publication successor: pure injected fixtures, never live authority.

The reviewed image-build source now verifies immutable publication before
looking for a post-install pipeline. No missing build history is fabricated.
"""
import copy
import unittest

from host_welcome.post_install import (
    PRODUCER_PIN, WIRE, validate_image_snapshot, join_image_progress,
)
from host_welcome.progress import ProgressError
from host_welcome.progress_live import live_assessment
from host_welcome.progress_examples import BOOT
from test_post_install import item, snapshot


SUCCESSOR = "7b653e8be3f89730a52688d71df28513456f9cf3"
PREDECESSOR = "7348ec730a3181f1a8ecc62a6e4d633ce191674a"


class ReceiptOnlySuccessorTests(unittest.TestCase):
    def test_publication_with_no_pipeline_has_no_invented_history(self):
        for status, expected in (
            ("artifact-published", "partial"),
            ("view-published-compatibility-unchecked", "partial"),
            ("view-published-compatible", "compatible"),
        ):
            with self.subTest(publication=status):
                data = snapshot([item(name="firefox-esr", published=status)])
                data["items"][0]["state"] = data["items"][0]["publication"]["state"]
                row = validate_image_snapshot(data, expected_boot=data["boot_id"])["items"][0]
                self.assertEqual((row["phase"], row["message_code"]), ("publishing", status))
                self.assertEqual(row["state"], row["publication"]["state"])
                self.assertIsNone(row["pipeline_id"])
                self.assertIsNone(row["pipeline_state"])
                self.assertIsNone(row["source_pin_identity"])
                self.assertEqual(row["commands"], [])
                self.assertFalse(row["commands_truncated"])
                self.assertEqual(row["runtime_admission"], "unobserved")
                selection, publication, lines, _ = join_image_progress(data)
                self.assertEqual(selection, "requested")
                self.assertEqual(publication, expected)
                self.assertEqual(lines[0].phase, "publishing")
                self.assertNotIn("running", lines[0].description.lower())

    def test_no_receipt_no_pipeline_is_still_waiting(self):
        row = item(name="firefox-esr", published="publication-unobserved")
        row.update(phase="queued", state="waiting", message_code="intent-awaiting-pipeline")
        data = snapshot([row])
        validate_image_snapshot(data, expected_boot=data["boot_id"])
        selection, published, lines, _ = join_image_progress(data)
        self.assertEqual(selection, "requested")
        self.assertEqual(published, "unobserved")
        self.assertEqual(lines[0].state, "waiting")
        self.assertEqual(row["commands"], [])

    def test_corrupt_publication_conflicts_fail_closed(self):
        row = item(name="firefox-esr", published="publication-unobserved")
        row.update(phase="publishing", state="unknown",
                   message_code="publication-evidence-conflict")
        row["publication"]["message_code"] = "publication-evidence-conflict"
        data = snapshot([row])
        validate_image_snapshot(data, expected_boot=data["boot_id"])
        self.assertEqual(join_image_progress(data)[1], "uncertain")
        damaged = copy.deepcopy(data)
        damaged["items"][0]["publication"]["receipt"] = "sha256:" + "c" * 64
        with self.assertRaises(ProgressError):
            validate_image_snapshot(damaged, expected_boot=damaged["boot_id"])

    def test_pipeline_conflict_does_not_disappear_when_view_published(self):
        row = item(name="firefox-esr")
        row.update(phase="building", state="uncertain", message_code="pipeline-conflict")
        data = snapshot([row])
        validate_image_snapshot(data, expected_boot=data["boot_id"])
        selection, pub, lines, _ = join_image_progress(data)
        self.assertEqual(selection, "requested")
        self.assertEqual(pub, "compatible")
        self.assertEqual(lines[0].state, "uncertain")
        self.assertEqual(data["items"][0]["message_code"], "pipeline-conflict")
        self.assertIsNone(data["items"][0]["pipeline_id"])

    def test_exact_source_successor_and_stale_pins_rejected(self):
        self.assertEqual(PRODUCER_PIN, SUCCESSOR)
        self.assertEqual(WIRE, "image-build-post-install-progress-rpc-v2")
        for stale in (PREDECESSOR, "fcc12f3db959afe395b1adfb5b0b4dc1f16a3258"):
            with self.subTest(stale=stale):
                data = snapshot([item(name="firefox-esr")])
                data["producer_source"]["revision"] = stale
                with self.assertRaises(ProgressError):
                    validate_image_snapshot(data, expected_boot=data["boot_id"])

    def test_boot_and_generation_bound_even_without_pipeline(self):
        data = snapshot([item(name="firefox-esr")])
        with self.assertRaises(ProgressError):
            validate_image_snapshot(data, expected_boot="22222222-2222-4222-8222-222222222222")
        damaged = copy.deepcopy(data)
        damaged["items"][0]["publication"]["rootfs_generation"] = None
        with self.assertRaises(ProgressError):
            validate_image_snapshot(damaged, expected_boot=data["boot_id"])

    def test_authenticated_source_can_be_observed_without_controller(self):
        # Dependency injection is only for tests. Production calls its fixed,
        # SCM_CREDENTIALS-authenticated read-only observer.
        data = snapshot([item(name="firefox-esr")])
        data["boot_id"] = BOOT
        bootstrap = lambda: {
            "boot_id": BOOT,
            "headless_installation": {"status": "verified"},
        }
        def controller(_boot):
            raise OSError("controller not installed")
        result = live_assessment(
            bootstrap_reader=bootstrap,
            controller_reader=controller,
            image_reader=lambda: data,
        )
        self.assertEqual(result.headless, "verified")
        self.assertEqual(result.controller_availability, "unavailable")
        self.assertEqual(result.graphics_request, "requested")
        self.assertEqual(result.publication, "compatible")
        self.assertEqual(result.graphical_session, "not-verified")
        self.assertTrue(all(line.phase == "publishing" for line in result.lines))
