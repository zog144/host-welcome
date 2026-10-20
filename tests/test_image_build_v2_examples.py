"""Pinned image-build v2 cross-repo examples: source fixtures never acquire live authority."""
import json
from pathlib import Path
from datetime import datetime, timezone
import unittest

from host_welcome.post_install import PRODUCER_PIN, validate_image_snapshot, join_image_progress
from host_welcome.progress import ProgressError

ROOT=Path(__file__).resolve().parent / "fixtures" / "image-build-v2"
BOOT="11111111-2222-3333-4444-555555555555"
EXAMPLES=("successful","in-progress","failed","interrupted","unknown","published")


def example(name):
    snapshot=json.loads((ROOT / (name+".json")).read_text(encoding="utf-8"))
    now=datetime.now(timezone.utc).isoformat()
    snapshot["producer_source"]["revision"]=PRODUCER_PIN
    snapshot["observed_at"]=now
    for row in snapshot["items"]:
        row["observed_at"]=now
    return snapshot


class PinnedImageBuildExamples(unittest.TestCase):
    def test_exact_six_image_build_examples(self):
        expected={"successful":"unobserved","in-progress":"unobserved",
                  "failed":"unobserved","interrupted":"unobserved",
                  "unknown":"unobserved","published":"compatible"}
        for name in EXAMPLES:
            with self.subTest(name=name):
                raw=example(name)
                validated=validate_image_snapshot(raw,expected_boot=BOOT)
                request,pub,lines,warnings=join_image_progress(validated)
                self.assertEqual(pub,expected[name])
                self.assertEqual(len(lines),1)
                if name=="unknown":
                    self.assertEqual(request,"unknown")
                else:
                    self.assertEqual(request,"requested")
                self.assertNotIn("ETA",str(lines))
                self.assertNotIn("percent",str(lines).lower())

    def test_terminal_history_from_old_boot_is_not_current_claim(self):
        raw=example("published")
        current=raw["boot_id"]
        command=raw["items"][0]["commands"][0]
        self.assertNotEqual(command["controller_boot_id"],current)
        self.assertEqual(command["state"],"succeeded")
        validate_image_snapshot(raw,expected_boot=current)
        command["build_record"]=None
        with self.assertRaises(ProgressError):
            validate_image_snapshot(raw,expected_boot=current)

    def test_no_fake_publication_from_command_receipt(self):
        for name in ("successful","in-progress","failed","interrupted"):
            with self.subTest(name=name):
                raw=example(name)
                self.assertEqual(join_image_progress(
                    validate_image_snapshot(raw, expected_boot=BOOT))[1],
                    "unobserved")

    def test_pipeline_running_is_not_live_job_proof(self):
        raw = example("in-progress")
        validated = validate_image_snapshot(raw, expected_boot=BOOT)
        _, publication, lines, warnings = join_image_progress(validated)
        self.assertEqual(publication, "unobserved")
        self.assertEqual(lines[0].phase, "building")
        self.assertEqual(lines[0].state, "uncertain")
        self.assertTrue(any("not independently verified" in x for x in warnings))

    def test_mismatched_rootfs_and_source_fail_closed(self):
        raw=example("published")
        raw["items"][0]["publication"]["rootfs_generation"]="../old"
        with self.assertRaises(ProgressError):
            validate_image_snapshot(raw,expected_boot=BOOT)
        raw=example("published")
        raw["producer_source"]["repository"]="other/producer"
        with self.assertRaises(ProgressError):
            validate_image_snapshot(raw,expected_boot=BOOT)
