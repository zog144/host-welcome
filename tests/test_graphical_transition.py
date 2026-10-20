import copy
from datetime import datetime, timezone
import unittest

from host_welcome.graphical_transition import (
    LocalSeatEvidence, evaluate_graphical_transition,
)
from host_welcome.post_install import validate_image_snapshot
from host_welcome.progress_examples import fixture
from test_post_install import item, snapshot

BOOT = "11111111-1111-4111-8111-111111111111"

def parts(browser="firefox-esr"):
    im=snapshot([item(name=n) for n in ("firefox-esr","greetd","i3","xorg-server")])
    # Canonical order as required by the publisher.
    im["items"].sort(key=lambda r:r["application"])
    controller=fixture("published")["controller"]
    t=datetime.now(timezone.utc).isoformat()
    controller["observed_at"]=t
    controller["boot_id"]=BOOT
    controller["items"]=[]
    for i,n in enumerate(("xorg-server","i3","greetd","firefox-esr")):
        controller["items"].append(dict(application=n,producer="box-control",
            operation_id="runtime:graphical-"+str(i),
            attempt_id=None,stage_id=None,package=None,command_index=None,
            build_job_id=None,controller_request_id=None,
            runtime_id="graphical-"+str(i),
            selected_software_id=im["items"][0]["publication"]["view_id"],
            phase="launching",state="running",observed_at=t,
            evidence_ref="runtime:graphical-"+str(i),progress=None,
            message_code="runtime-observed-active"))
    seat=LocalSeatEvidence(True,True,True,True,True,BOOT,
                           im["items"][0]["selection_revision"],t,"e"*64)
    return im,controller,seat

class GateTests(unittest.TestCase):
    def test_no_local_seat_means_always_console(self):
        im,controller,_=parts()
        result=evaluate_graphical_transition(im,controller,accepted_boot=BOOT)
        self.assertFalse(result.eligible)
        self.assertTrue(result.retain_console)
        self.assertIn("local-seat observer", " ".join(result.gates))

    def test_synthetic_all_gates_not_execution(self):
        im,controller,seat=parts()
        decision=evaluate_graphical_transition(im,controller,seat,accepted_boot=BOOT)
        self.assertTrue(decision.eligible,decision.gates)
        self.assertTrue(decision.retain_console)

    def test_remote_vnc_does_not_satisfy_physical_seat(self):
        im,controller,seat=parts()
        seat=LocalSeatEvidence(False,True,True,True,True,BOOT,
                               seat.selection_revision,seat.observed_at,seat.rootfs_generation)
        decision=evaluate_graphical_transition(im,controller,seat,accepted_boot=BOOT)
        self.assertFalse(decision.eligible)
        self.assertIn("physical seat", " ".join(decision.gates))

    def test_greetd_grant_browser_and_display_crash(self):
        im,controller,seat=parts()
        for key in ("pam_grant_approved","display_ready","browser_page_ready"):
            with self.subTest(key=key):
                data=dict(vars(seat))
                data[key]=False
                d=evaluate_graphical_transition(im,controller,
                       LocalSeatEvidence(**data),accepted_boot=BOOT)
                self.assertFalse(d.eligible)
                self.assertTrue(d.retain_console)

    def test_publication_without_runtime_remains_console(self):
        im,controller,seat=parts()
        controller["items"]=[]
        decision=evaluate_graphical_transition(im,controller,seat,accepted_boot=BOOT)
        self.assertFalse(decision.eligible)
        self.assertIn("controller runtime", " ".join(decision.gates))

    def test_published_artifact_not_compatible_view(self):
        im,controller,seat=parts()
        im["items"][0]["publication"].update(message_code="artifact-published",
                    view_id=None,binding_digest=None,compatibility_checked=False,
                    rootfs_generation=None)
        result=evaluate_graphical_transition(im,controller,seat,accepted_boot=BOOT)
        self.assertFalse(result.eligible)
        self.assertIn("compatible immutable view", " ".join(result.gates))

    def test_rootfs_view_mismatch_and_wrong_boot(self):
        im,controller,seat=parts()
        controller["items"][0]["selected_software_id"]="sha256:"+"f"*64
        result=evaluate_graphical_transition(im,controller,seat,accepted_boot=BOOT)
        self.assertFalse(result.eligible)
        controller["items"][0]["selected_software_id"]=im["items"][0]["publication"]["view_id"]
        result=evaluate_graphical_transition(im,controller,seat,
            accepted_boot="22222222-2222-4222-8222-222222222222")
        self.assertFalse(result.eligible)
        self.assertTrue(result.retain_console)

    def test_reboot_compilation_fails_conservatively(self):
        im,controller,seat=parts()
        im["items"][0].update(phase="building", state="uncertain",
                               message_code="pipeline-pending")
        im["items"][0]["publication"]=item(published="publication-unobserved")["publication"]
        result=evaluate_graphical_transition(im,controller,seat,accepted_boot=BOOT)
        self.assertFalse(result.eligible)

    def test_partial_controller_page_cannot_be_readiness(self):
        im,controller,seat=parts()
        controller["page"]["runtime_has_more"]=True
        controller["page"]["next_runtime"]="graphical-3"
        result=evaluate_graphical_transition(im,controller,seat,accepted_boot=BOOT)
        self.assertFalse(result.eligible)

    def test_rejection_does_not_modify_producer_evidence(self):
        im,controller,seat=parts()
        prior=copy.deepcopy((im,controller,seat))
        evaluate_graphical_transition(im,controller,seat,accepted_boot=BOOT)
        self.assertEqual((im,controller,seat),prior)

    def test_seat_selected_generation_must_match_publisher(self):
        im,controller,seat=parts()
        changed=dict(vars(seat),rootfs_generation="f"*64)
        result=evaluate_graphical_transition(im,controller,
            LocalSeatEvidence(**changed),accepted_boot=BOOT)
        self.assertFalse(result.eligible)
        self.assertIn("rootfs generation", " ".join(result.gates))
