"""Deterministic, explicitly simulated examples for console progress review."""
from __future__ import annotations

from copy import deepcopy
from .progress import SCHEMA

NOW = "2026-10-16T12:00:00Z"
BOOT = "11111111-1111-4111-8111-111111111111"
JOB = "a" * 32
VIEW = "sha256:" + "b" * 64
RUNTIME = "firefox-demo-01"


def fixture(name: str) -> dict:
    if name not in {"building", "blocked", "uncertain", "published", "headless", "unavailable"}:
        raise ValueError("unknown simulated progress scenario")
    controller = {
        "schema": "zog-application-progress-v1",
        "host_id": None, "installation_id": None,
        "snapshot_id": "c" * 32, "observed_at": NOW, "boot_id": BOOT,
        "items": [{
            "application": None, "producer": "box-control",
            "operation_id": "build:" + JOB, "attempt_id": None, "stage_id": None,
            "package": None, "command_index": None, "build_job_id": JOB,
            "controller_request_id": "demo-req-1", "runtime_id": None,
            "selected_software_id": None, "phase": "building", "state": "unknown",
            "observed_at": NOW, "evidence_ref": "build-job:" + JOB, "progress": None,
            "message_code": "build-state-unobserved",
        }],
        "page": {"build_has_more": False, "runtime_has_more": False,
                 "next_build": JOB, "next_runtime": None},
    }
    image_build = {
        "schema": "host-welcome.image-build-fixture/v1", "observed_at": NOW,
        "boot_id": BOOT,
        "operations": [{
            "application": "firefox", "attempt_id": "demo-attempt-1",
            "build_job_id": JOB, "phase": "building", "state": "unknown",
            "publication": "unobserved", "published_view": None,
            "publication_evidence_ref": None,
        }],
    }
    result = {
        "schema": SCHEMA, "source_kind": "fixture", "reference_time": NOW,
        "installation": {"observed_at": NOW, "boot_id": BOOT,
                         "headless": "verified", "graphics_request": "requested"},
        "controller": controller, "image_build": image_build,
    }
    job = controller["items"][0]
    op = image_build["operations"][0]
    if name == "building":
        # Persisted 'running' alone is not a live kernel observation.
        # Show only that a source operation is in the building phase.
        job["state"] = "unknown"
        op["state"] = "running"
    elif name == "blocked":
        op["state"], op["phase"] = "blocked", "acquiring"
        job.update(phase="queued", state="waiting", message_code="build-awaiting-start")
    elif name == "uncertain":
        job.update(state="uncertain", message_code="build-outcome-uncertain")
        op["state"] = "uncertain"
    elif name == "published":
        job.update(state="succeeded", message_code="build-command-succeeded")
        op.update(phase="publishing", state="succeeded", publication="verified",
                  published_view=VIEW, publication_evidence_ref="receipt-demo-1")
    elif name == "headless":
        result["installation"]["graphics_request"] = "not-requested"
        result["controller"] = None
        result["image_build"] = None
    elif name == "unavailable":
        result["installation"]["headless"] = "unknown"
        result["controller"] = None
        result["image_build"] = None
    return deepcopy(result)
