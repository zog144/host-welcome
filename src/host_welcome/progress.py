"""Simulation-only join of independently attributed application progress observations.

The controller subset matches zog-application-progress-v1. The other two slices
are explicitly host-welcome-owned *fixture formats*, NOT image-build or
host-install live producer contracts. In particular this module contains no
socket reader, privilege escalation, scheduler or execution method.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any
import re

SCHEMA = "host-welcome.progress-fixture/v1"
CONTROLLER_SCHEMA = "zog-application-progress-v1"
HEX = re.compile(r"[0-9a-f]{32}\Z")
BOOT = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9-]{0,63}\Z")
TOKEN = re.compile(r"[A-Za-z0-9-]{1,200}\Z")
RUNTIME = re.compile(r"[A-Za-z0-9-]{1,80}\Z")
VIEW = re.compile(r"sha256:[0-9a-f]{64}\Z")
CONTROLLER_PHASES = frozenset({"queued", "building", "launching"})
BUILD_PHASES = frozenset({"queued", "acquiring", "building", "testing", "verifying", "publishing"})
STATES = frozenset({"waiting", "running", "succeeded", "blocked", "failed", "cancelled", "uncertain", "unknown"})
CODES = frozenset({
    "build-awaiting-start", "build-job-running", "build-command-succeeded",
    "build-command-cancelled", "build-command-failed", "build-outcome-uncertain",
    "build-state-unrecognized", "build-state-unobserved", "build-evidence-unavailable",
    "runtime-observation-unavailable", "runtime-observed-active",
    "runtime-terminated-successfully", "runtime-terminal-unverified",
    "runtime-failed", "runtime-cleanup-or-state-uncertain",
})
ITEM_FIELDS = frozenset({
    "application", "producer", "operation_id", "attempt_id", "stage_id",
    "package", "command_index", "build_job_id", "controller_request_id",
    "runtime_id", "selected_software_id", "phase", "state", "observed_at",
    "evidence_ref", "progress", "message_code",
})
AGE_SECONDS = 120


class ProgressError(ValueError):
    """Invalid or untrusted simulation progress input."""


@dataclass(frozen=True)
class ProgressFixture:
    reference_time: datetime
    installation: dict[str, Any]
    controller: dict[str, Any] | None
    image_build: dict[str, Any] | None


@dataclass(frozen=True)
class ProgressLine:
    title: str
    phase: str
    state: str
    description: str


@dataclass(frozen=True)
class ProgressAssessment:
    headless: str
    graphics_request: str
    publication: str
    graphical_session: str
    controller_availability: str
    lines: tuple[ProgressLine, ...]
    warnings: tuple[str, ...]


def _object(value: Any, keys: set[str] | frozenset[str], where: str) -> dict[str, Any]:
    if type(value) is not dict or set(value) != set(keys):
        raise ProgressError(f"{where}: unexpected or missing fields")
    return value


def _id(value: Any, pattern: re.Pattern, where: str, nullable: bool = False) -> str | None:
    if nullable and value is None:
        return None
    if type(value) is not str or not pattern.fullmatch(value):
        raise ProgressError(f"{where}: invalid identifier")
    return value


def _enum(value: Any, allowed: frozenset[str] | set[str], where: str) -> str:
    if type(value) is not str or value not in allowed:
        raise ProgressError(f"{where}: unsupported value")
    return value


def _date(value: Any, where: str) -> datetime:
    if type(value) is not str or len(value) > 40:
        raise ProgressError(f"{where}: timestamp required")
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None or dt.utcoffset() is None:
            raise ValueError("naive timestamp")
        return dt.astimezone(timezone.utc)
    except (ValueError, OverflowError) as exc:
        raise ProgressError(f"{where}: timezone-aware timestamp required") from exc


def _fresh(stamp: datetime, now: datetime, *, boot: str | None, expected_boot: str | None) -> bool:
    delta = now - stamp
    return (timedelta(seconds=-AGE_SECONDS) <= delta <= timedelta(seconds=AGE_SECONDS)
            and (boot is None or expected_boot is None or boot == expected_boot))


def _controller(data: Any) -> dict[str, Any]:
    value = _object(data, {"schema", "host_id", "installation_id", "snapshot_id",
                           "observed_at", "boot_id", "items", "page"}, "controller")
    if value["schema"] != CONTROLLER_SCHEMA or value["host_id"] is not None or value["installation_id"] is not None:
        raise ProgressError("controller: identity cannot be inferred")
    _id(value["snapshot_id"], HEX, "controller.snapshot_id")
    _date(value["observed_at"], "controller.observed_at")
    _id(value["boot_id"], BOOT, "controller.boot_id", nullable=True)
    items = value["items"]
    if type(items) is not list or len(items) > 8:
        raise ProgressError("controller: maximum four build jobs and four runtimes")
    builds, runtimes = set(), set()
    for item in items:
        row = _object(item, ITEM_FIELDS, "controller.item")
        if row["producer"] != "box-control" or row["progress"] is not None or row["observed_at"] != value["observed_at"]:
            raise ProgressError("controller: invalid producer or progress evidence")
        _enum(row["phase"], CONTROLLER_PHASES, "controller.phase")
        _enum(row["state"], STATES, "controller.state")
        _enum(row["message_code"], CODES, "controller.message_code")
        _id(row["controller_request_id"], TOKEN, "controller.request_id", nullable=True)
        if row["build_job_id"] is not None:
            job = _id(row["build_job_id"], HEX, "controller.job")
            if (job in builds or row["operation_id"] != "build:" + job
                    or row["evidence_ref"] != "build-job:" + job
                    or any(row[key] is not None for key in ("application", "attempt_id",
                            "stage_id", "package", "command_index", "runtime_id",
                            "selected_software_id"))
                    or row["phase"] not in ("queued", "building")
                    or not row["message_code"].startswith("build-")):
                raise ProgressError("controller: invalid build-job association")
            builds.add(job)
        else:
            rid = _id(row["runtime_id"], RUNTIME, "controller.runtime")
            _id(row["application"], NAME, "controller.application")
            _id(row["selected_software_id"], VIEW, "controller.software_view", nullable=True)
            if (rid in runtimes or row["operation_id"] != "runtime:" + rid
                    or row["evidence_ref"] != "runtime:" + rid or row["phase"] != "launching"
                    or any(row[key] is not None for key in ("attempt_id", "stage_id",
                        "package", "command_index"))
                    or not row["message_code"].startswith("runtime-")):
                raise ProgressError("controller: invalid runtime identity")
            runtimes.add(rid)
    if len(builds) > 4 or len(runtimes) > 4:
        raise ProgressError("controller: page bound exceeded")
    page = _object(value["page"], {"build_has_more", "runtime_has_more",
                                  "next_build", "next_runtime"}, "controller.page")
    for field in ("build_has_more", "runtime_has_more"):
        if type(page[field]) is not bool:
            raise ProgressError("controller: invalid paging flag")
    _id(page["next_build"], HEX, "controller.next_build", nullable=True)
    _id(page["next_runtime"], RUNTIME, "controller.next_runtime", nullable=True)
    if (page["build_has_more"] and page["next_build"] is None or
            page["runtime_has_more"] and page["next_runtime"] is None):
        raise ProgressError("controller: cannot continue an unanchored page")
    return value


def load_progress_fixture(data: Any) -> ProgressFixture:
    """Validate ONLY explicitly simulated progress; never enable host authority."""
    root = _object(data, {"schema", "source_kind", "reference_time",
                          "installation", "controller", "image_build"}, "fixture")
    if root["schema"] != SCHEMA or root["source_kind"] != "fixture":
        raise ProgressError("only simulated progress fixtures are accepted")
    now = _date(root["reference_time"], "fixture.reference_time")
    install = _object(root["installation"], {"observed_at", "boot_id", "headless",
                                             "graphics_request"}, "installation fixture")
    _date(install["observed_at"], "installation.observed_at")
    _id(install["boot_id"], BOOT, "installation.boot_id", nullable=True)
    _enum(install["headless"], {"verified", "pending", "failed", "unknown"}, "installation.headless")
    _enum(install["graphics_request"], {"requested", "not-requested", "unknown"}, "installation.graphics_request")
    control = None if root["controller"] is None else _controller(root["controller"])
    image = root["image_build"]
    if image is not None:
        image = _object(image, {"schema", "observed_at", "boot_id", "operations"}, "image_build fixture")
        if image["schema"] != "host-welcome.image-build-fixture/v1":
            raise ProgressError("image-build fixture schema mismatch")
        _date(image["observed_at"], "image_build.observed_at")
        _id(image["boot_id"], BOOT, "image_build.boot_id", nullable=True)
        operations = image["operations"]
        if type(operations) is not list or len(operations) > 8:
            raise ProgressError("image-build fixture: too many operations")
        seen = set()
        for op in operations:
            _object(op, {"application", "attempt_id", "build_job_id", "phase", "state",
                         "publication", "published_view", "publication_evidence_ref"}, "image_build.operation")
            _id(op["application"], NAME, "image_build.application")
            attempt = _id(op["attempt_id"], TOKEN, "image_build.attempt_id")
            if attempt in seen:
                raise ProgressError("image-build fixture: duplicate attempt")
            seen.add(attempt)
            _id(op["build_job_id"], HEX, "image_build.build_job_id", nullable=True)
            _enum(op["phase"], BUILD_PHASES, "image_build.phase")
            _enum(op["state"], STATES, "image_build.state")
            _enum(op["publication"], {"unobserved", "verified", "failed", "uncertain"}, "image_build.publication")
            _id(op["published_view"], VIEW, "image_build.published_view", nullable=True)
            _id(op["publication_evidence_ref"], TOKEN, "image_build.publication_evidence_ref", nullable=True)
            if (op["publication"] == "verified") != (
                    op["published_view"] is not None and op["publication_evidence_ref"] is not None):
                raise ProgressError("image-build fixture: publication requires its own view and evidence")
            if op["publication"] == "verified" and (op["phase"] != "publishing" or op["state"] != "succeeded"):
                raise ProgressError("image-build fixture: publication must be independently completed")
    return ProgressFixture(now, install, control, image)


def assess_progress(fixture: ProgressFixture, *, now: datetime | None = None) -> ProgressAssessment:
    """Merge *display evidence*, never phase-success into publication or login."""
    now = now or fixture.reference_time
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")
    now = now.astimezone(timezone.utc)
    install = fixture.installation
    expected_boot = install["boot_id"]
    inst_ok = _fresh(_date(install["observed_at"], "installation.observed_at"),
                     now, boot=expected_boot, expected_boot=expected_boot)
    headless = install["headless"] if inst_ok else "unknown"
    requested = install["graphics_request"] if inst_ok else "unknown"
    warnings = []
    if not inst_ok:
        warnings.append("Installation observation is stale or future-dated.")
    lines = []
    controller = fixture.controller
    controller_ok = controller is not None and _fresh(
        _date(controller["observed_at"], "controller.observed_at"),
        now, boot=controller["boot_id"], expected_boot=expected_boot)
    jobs = {}
    if controller_ok:
        for item in controller["items"]:
            if item["build_job_id"] is not None:
                jobs[item["build_job_id"]] = item
            else:
                lines.append(ProgressLine(
                    "Runtime " + item["application"], item["phase"], item["state"],
                    "Controller runtime only; not a login session or browser readiness proof."))
        if controller["page"]["build_has_more"] or controller["page"]["runtime_has_more"]:
            warnings.append("Controller listing has more non-atomic pages; this page is incomplete.")
    else:
        warnings.append("Controller progress unavailable, stale or on a different boot.")
    image = fixture.image_build
    image_ok = image is not None and _fresh(
        _date(image["observed_at"], "image_build.observed_at"),
        now, boot=image["boot_id"], expected_boot=expected_boot)
    publication = "unobserved"
    if not image_ok:
        warnings.append("Authoritative image-build mapping/publication is unavailable.")
    else:
        for op in image["operations"]:
            label = op["application"]
            description = "Simulation-only image-build operation."
            state = op["state"]
            # Matched job IDs are evidence about a command only. Missing,
            # pruned or contradictory jobs may not become positive progress.
            jid = op["build_job_id"]
            if jid is not None and controller_ok:
                job = jobs.get(jid)
                if job is None:
                    description = "Controller command association not observed on this page."
                    if state in ("running", "succeeded"):
                        state = "unknown"
                elif job["state"] in ("failed", "cancelled", "uncertain", "unknown"):
                    description = "Controller command needs reconciliation."
                    if state in ("running", "succeeded"):
                        state = "uncertain"
                elif job["state"] == "succeeded" and op["phase"] == "building":
                    description = "Build command succeeded; publication is independent."
            elif jid is not None:
                if state in ("running", "succeeded"):
                    state = "unknown"
                description = "Controller job evidence currently unavailable."
            lines.append(ProgressLine(label, op["phase"], state, description))
            if op["publication"] == "verified":
                if state in ("unknown", "uncertain") and jid is not None:
                    warnings.append("Publication receipt needs controller association review for " + label + ".")
                else:
                    publication = "verified"
            elif op["publication"] in ("failed", "uncertain"):
                publication = op["publication"] if publication != "verified" else "mixed"
        # The per-row publication state is the only producer of a published claim.
    associated = set(op["build_job_id"] for op in image["operations"]) if image_ok else set()
    if controller_ok:
        for job_id, job in jobs.items():
            if job_id not in associated:
                lines.append(ProgressLine("Unassociated build job " + job_id,
                                          job["phase"], job["state"],
                                          "Controller command only; application and publication unknown."))
    if requested == "not-requested":
        # A verified *request authority* can establish that optional graphics
        # were not selected; absence of controller jobs cannot.
        warnings.append("Graphical applications were not requested in the installation fixture.")
    if requested != "requested" and publication == "verified":
        warnings.append("Published software does not imply requested graphical start.")
    return ProgressAssessment(headless, requested, publication, "not-verified",
                              "observed" if controller_ok else "unavailable",
                              tuple(lines), tuple(warnings))
