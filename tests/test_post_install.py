"""Strict consumer of the exact image-build post-install producer, no live transport."""
import copy
from datetime import datetime, timezone
import unittest

from host_welcome.post_install import validate_image_snapshot, join_image_progress, PRODUCER_PIN
from host_welcome.progress import ProgressError
from host_welcome.progress_examples import fixture

NOW = lambda: datetime.now(timezone.utc).isoformat()
REV = "sha256:" + "a" * 64
V = "sha256:" + "b" * 64
P = "sha256:" + "c" * 64

def item(name="firefox", requested=True, published="view-published-compatible"):
    pub = dict(state="succeeded", message_code=published, artifact_id=REV,
               view_id=V, receipt=P, compatibility_checked=True,
               rootfs_generation="e" * 64,
               binding_digest=P, artifact_revision="git-" + "d" * 40,
               artifact_source_identity=REV)
    if published == "publication-unobserved":
        pub = dict(state="unknown", message_code=published, artifact_id=None,
                   view_id=None, receipt=None, compatibility_checked=False,
                   rootfs_generation=None, binding_digest=None, artifact_revision=None,
                   artifact_source_identity=None)
    if published == "artifact-published":
        pub.update(view_id=None, compatibility_checked=False, binding_digest=None,
                   rootfs_generation=None)
    if published == "view-published-compatibility-unchecked":
        pub.update(state="uncertain", compatibility_checked=False, binding_digest=None,
                   rootfs_generation=None)
    result = dict(application=name, producer="image-build", selection_owner="host-install",
        selection_revision=REV, selection_sequence=7,
        operation_revision=V if requested else None, requested=requested,
        pipeline_id=None, pipeline_state=None, source_pin_identity=None,
        commands=[], commands_truncated=False, publication=pub,
        runtime_admission="unobserved", phase="publishing", state="succeeded",
        message_code=published, progress=None, observed_at=None)
    if not requested:
        result.update(phase="intent", state="not-requested",
                      message_code="application-not-requested",
                      publication=item(published="publication-unobserved")["publication"])
    return result

def snapshot(rows=None):
    date=NOW()
    rows=[item()] if rows is None else rows
    for row in rows:
        row["observed_at"]=date
    return dict(schema="image-build-post-install-progress-v2",
        producer_source={"contract":"image-build-post-install-source-v1",
          "repository":"zog144/image-build","revision":PRODUCER_PIN},
        boot_id="11111111-1111-4111-8111-111111111111",
        snapshot_id="e"*32, observed_at=date, producer="image-build",
        selection_owner="host-install", items=rows,
        page=dict(has_more=False, next_after=rows[-1]["application"] if rows else None))

class ImageProducerTests(unittest.TestCase):
    def test_compatible_view_and_no_local_seat_claim(self):
        snap=validate_image_snapshot(snapshot())
        request, pub, lines, warnings=join_image_progress(snap)
        self.assertEqual(request, "requested")
        self.assertEqual(pub, "compatible")
        self.assertEqual(lines[0].state, "succeeded")
        self.assertIn("selected-rootfs binding verified", lines[0].description)

    def test_publication_steps_are_not_graphical_session(self):
        for label, expected in (("publication-unobserved","unobserved"),
                                 ("artifact-published","partial"),
                                 ("view-published-compatibility-unchecked","partial")):
            with self.subTest(label=label):
                data=snapshot([item(published=label)])
                if label == "publication-unobserved":
                    data["items"][0].update(state="running", phase="building",
                                               message_code="pipeline-running")
                obs=validate_image_snapshot(data)
                self.assertEqual(join_image_progress(obs)[1],expected)

    def test_explicit_not_requested_and_unknown_are_distinct(self):
        data=snapshot([item(requested=False)])
        self.assertEqual(join_image_progress(validate_image_snapshot(data))[0],"not-requested")
        data["items"][0].update(selection_revision=None, selection_sequence=None,
                                requested=None, operation_revision=None,
                                state="unknown", message_code="selection-unobserved")
        self.assertEqual(join_image_progress(validate_image_snapshot(data))[0],"unknown")
        data["page"]["has_more"]=True
        self.assertEqual(join_image_progress(validate_image_snapshot(data))[0],"unknown")

    def test_stale_wrong_producer_and_extra_fields_rejected(self):
        for transform in (
            lambda d: d.update(producer="station-access"),
            lambda d: d.update(schema="host-welcome.progress-fixture/v1"),
            lambda d: d.update(observed_at="2025-01-01T00:00:00Z"),
            lambda d: d["items"][0].update(progress={"completed":99,"total":100}),
            lambda d: d["items"][0].update(runtime_admission="ready"),
            lambda d: d["items"][0].update(secret="/etc/shadow"),
            lambda d: d["items"][0].update(application="../root"),
            lambda d: d["items"][0]["publication"].update(
                artifact_id="sha256:"+"f"*64, compatibility_checked=False),
        ):
            data=snapshot();transform(data)
            with self.subTest(str(transform)),self.assertRaises(ProgressError):
                validate_image_snapshot(data)

    def test_conflicting_selection_revisions_and_duplicate_apps(self):
        data=snapshot([item(name="firefox"),item(name="xorg-server")])
        data["items"][1]["selection_revision"]="sha256:"+"f"*64
        with self.assertRaises(ProgressError):
            validate_image_snapshot(data)
        data=snapshot([item(),item()])
        with self.assertRaises(ProgressError):
            validate_image_snapshot(data)

    def test_controller_command_success_is_not_publication(self):
        producer=snapshot([item(published="publication-unobserved")])
        producer["items"][0].update(phase="building",state="succeeded",
                                     message_code="pipeline-complete-publication-unobserved")
        producer=validate_image_snapshot(producer)
        controller=fixture("published")["controller"]
        request, pub, _, _=join_image_progress(producer,controller)
        self.assertEqual(request,"requested")
        self.assertEqual(pub,"unobserved")

    def test_missing_or_incomplete_page_never_proves_nonselection(self):
        data=snapshot([item(name="firefox",requested=False)])
        data["page"]["has_more"]=True
        self.assertEqual(join_image_progress(validate_image_snapshot(data))[0],"unknown")
        data=snapshot([])
        self.assertEqual(join_image_progress(validate_image_snapshot(data))[0],"unknown")

    def test_commands_are_identity_checked(self):
        data=snapshot([item(published="publication-unobserved")])
        row=data["items"][0]
        row.update(pipeline_id="d"*32,pipeline_state="running",
                   source_pin_identity="a"*64,phase="building",
                   state="uncertain",message_code="command-observation-missing")
        command=dict(attempt_id="image-"+"f"*32,stage_id="firefox-final",
            package="firefox",phase="build",command_index=0,
            controller_request_id="req-123",build_job_id="c"*32,
            recipe_identity="e"*64,source_pin_identity="a"*64,
            state="uncertain",message_code="command-observation-missing",progress=None)
        row["commands"]=[command]
        validated=validate_image_snapshot(data)
        self.assertEqual(validated["items"][0]["commands"][0]["build_job_id"],"c"*32)
        command["source_pin_identity"]="b"*64
        with self.assertRaises(ProgressError):
            validate_image_snapshot(data)

    def test_rootfs_and_producer_source_replay_rejected(self):
        good=snapshot()
        validate_image_snapshot(good, expected_boot=good["boot_id"])
        for change in (
            lambda d: d["producer_source"].update(revision="0"*40),
            lambda d: d.update(boot_id="22222222-2222-4222-8222-222222222222"),
            lambda d: d["items"][0]["publication"].update(rootfs_generation="f"*63),
        ):
            bad=snapshot()
            change(bad)
            with self.subTest(change=str(change)),self.assertRaises(ProgressError):
                validate_image_snapshot(bad, expected_boot="11111111-1111-4111-8111-111111111111")
