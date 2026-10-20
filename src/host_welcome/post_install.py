"""Strict consumer of image-build's post-install-progress-v1 producer projection.

Pure schema validation and display-only joining. This module is NOT an
authenticated transport; callers must only supply a snapshot obtained through
the independently protected broker and verified producer peer identity.
"""
from __future__ import annotations

from datetime import datetime, timezone
import re

from .progress import ProgressError, ProgressLine, _controller, _date, _fresh

SCHEMA = "image-build-post-install-progress-v2"
PRODUCER_PIN = "fcc12f3db959afe395b1adfb5b0b4dc1f16a3258"
PRODUCER_SOURCE = "image-build-post-install-source-v1"
WIRE = "image-build-post-install-progress-rpc-v1"
REV = re.compile(r"sha256:[0-9a-f]{64}\Z")
HEX32 = re.compile(r"[0-9a-f]{32}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
APP = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
TOKEN = re.compile(r"[A-Za-z0-9-]{1,200}\Z")
ATTEMPT = re.compile(r"[a-z0-9-]+-[0-9a-f]{32}\Z")
SAFE = re.compile(r"[a-zA-Z0-9_.-]{1,128}\Z")
STATES = frozenset(("not-requested", "waiting", "running", "succeeded",
                    "blocked", "failed", "cancelled", "uncertain", "unknown"))
CODES = frozenset(("selection-unobserved", "application-not-requested",
    "intent-awaiting-pipeline", "pipeline-conflict", "pipeline-prepared",
    "pipeline-running", "pipeline-pending", "pipeline-complete-publication-unobserved",
    "pipeline-released", "pipeline-state-unknown", "command-awaiting-controller-request",
    "command-observation-missing", "command-running-unobserved", "command-succeeded",
    "command-failed", "command-cancelled", "command-outcome-uncertain",
    "command-evidence-conflict", "publication-unobserved", "artifact-published",
    "view-published-compatibility-unchecked", "view-published-compatible",
    "publication-evidence-conflict"))
PUB_CODES = frozenset(("publication-unobserved", "artifact-published",
    "view-published-compatibility-unchecked", "view-published-compatible",
    "publication-evidence-conflict"))
COMMAND_CODES = frozenset(("command-awaiting-controller-request",
    "command-observation-missing", "command-running-unobserved", "command-succeeded",
    "command-failed", "command-cancelled", "command-outcome-uncertain",
    "command-evidence-conflict"))
PHASES = frozenset(("intent", "queued", "building", "publishing"))
COMMAND_PHASES = frozenset(("prepare", "configure", "build", "test", "install"))
GRAPHICAL = frozenset(("firefox", "firefox-esr", "chromium", "greetd", "agreety",
                       "xorg-server", "i3", "turbovnc", "weston"))
FIELDS = frozenset(("application", "producer", "selection_owner", "selection_revision",
    "selection_sequence", "operation_revision", "requested", "pipeline_id",
    "pipeline_state", "source_pin_identity", "commands", "commands_truncated",
    "publication", "runtime_admission", "phase", "state", "message_code",
    "progress", "observed_at"))
PUBLICATION = frozenset(("state", "message_code", "artifact_id", "view_id", "receipt",
                         "compatibility_checked", "rootfs_generation", "binding_digest",
                         "artifact_revision", "artifact_source_identity"))
COMMAND = frozenset(("attempt_id", "stage_id", "package", "phase", "command_index",
    "controller_request_id", "build_job_id", "recipe_identity", "source_pin_identity",
    "state", "message_code", "progress"))


def _shape(obj, fields, label):
    if type(obj) is not dict or set(obj) != fields:
        raise ProgressError(label + ": unsupported producer shape")
    return obj


def _token(obj, pattern, label, nullable=False):
    if nullable and obj is None:
        return
    if type(obj) is not str or not pattern.fullmatch(obj):
        raise ProgressError(label + ": invalid identity")


def _value(item, values, label):
    if type(item) is not str or item not in values:
        raise ProgressError(label + ": unsupported value")


def validate_image_snapshot(raw, *, now=None, expected_boot=None):
    """Validate exactly one bounded producer page, without granting host authority."""
    _shape(raw, frozenset(("schema", "snapshot_id", "observed_at", "producer",
                          "producer_source", "boot_id", "selection_owner", "items", "page")), "image-build")
    if (raw["schema"] != SCHEMA or raw["producer"] != "image-build"
            or raw["selection_owner"] != "host-install"):
        raise ProgressError("invalid image-build producer/selection authority")
    source = _shape(raw["producer_source"],
        frozenset(("contract", "repository", "revision")), "producer source")
    if (source["contract"] != PRODUCER_SOURCE or source["repository"] != "zog144/image-build"
            or source["revision"] != PRODUCER_PIN):
        raise ProgressError("image-build producer source not reviewed")
    _token(raw["boot_id"], re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\\Z"), "producer boot")
    _token(raw["snapshot_id"], HEX32, "snapshot")
    if expected_boot is not None and raw["boot_id"] != expected_boot:
        raise ProgressError("image-build producer boot does not match verified installation")
    stamp = _date(raw["observed_at"], "image-build observation")
    now = datetime.now(timezone.utc) if now is None else now
    if now.tzinfo is None or now.utcoffset() is None or not _fresh(
            stamp, now.astimezone(timezone.utc), boot=None, expected_boot=None):
        raise ProgressError("stale/future image-build response")
    items = raw["items"]
    if type(items) is not list or len(items) > 4:
        raise ProgressError("image-build page exceeds consumer bound")
    seen = set()
    selections = set()
    for item in items:
        _shape(item, FIELDS, "image-build item")
        name = item["application"]
        _token(name, APP, "application")
        if name in seen:
            raise ProgressError("duplicate application")
        seen.add(name)
        if (item["producer"] != "image-build" or item["selection_owner"] != "host-install"
                or item["runtime_admission"] != "unobserved" or item["progress"] is not None
                or item["observed_at"] != raw["observed_at"]):
            raise ProgressError("unsupported application attestation")
        _value(item["phase"], PHASES, "phase")
        _value(item["state"], STATES, "state")
        _value(item["message_code"], CODES, "message code")
        requested = item["requested"]
        if requested is not None and type(requested) is not bool:
            raise ProgressError("invalid request intent")
        sequence, sel = item["selection_sequence"], item["selection_revision"]
        if sel is None:
            if sequence is not None or requested is not None or item["operation_revision"] is not None:
                raise ProgressError("unverified selection receipt")
        else:
            _token(sel, REV, "selection revision")
            if type(sequence) is not int or not 0 <= sequence < 2**63 or requested is None:
                raise ProgressError("invalid owner selection sequence")
            selections.add((sequence, sel))
        operation = item["operation_revision"]
        if requested is True:
            _token(operation, REV, "operation revision")
        elif operation is not None:
            raise ProgressError("unrequested operation revision")
        if requested is False and (item["state"] != "not-requested"
                                   or item["message_code"] != "application-not-requested"):
            raise ProgressError("incorrect nonselection claim")
        if requested is None and (item["state"] != "unknown"
                                  or item["message_code"] != "selection-unobserved"):
            raise ProgressError("selection not established")
        pipeline = item["pipeline_id"]
        _token(pipeline, HEX32, "pipeline", nullable=True)
        _token(item["source_pin_identity"], HEX64, "source pins", nullable=True)
        if pipeline is None and (item["source_pin_identity"] is not None
                                 or item["pipeline_state"] is not None):
            raise ProgressError("unbound pipeline state")
        if pipeline is not None:
            if requested is not True:
                raise ProgressError("unrequested pipeline")
            _value(item["pipeline_state"],
                   frozenset(("prepared", "running", "pending", "released", "complete")),
                   "pipeline state")
        commands = item["commands"]
        if type(commands) is not list or len(commands) > 16 or type(item["commands_truncated"]) is not bool:
            raise ProgressError("unbounded command list")
        if commands and pipeline is None:
            raise ProgressError("commands with no verified pipeline")
        ids = set()
        for cmd in commands:
            _shape(cmd, COMMAND, "image-build command")
            _token(cmd["attempt_id"], ATTEMPT, "attempt")
            _token(cmd["stage_id"], SAFE, "stage")
            _token(cmd["package"], APP, "package")
            _token(cmd["recipe_identity"], HEX64, "recipe")
            _token(cmd["source_pin_identity"], HEX64, "command source pins")
            _token(cmd["controller_request_id"], TOKEN, "controller request", nullable=True)
            _token(cmd["build_job_id"], HEX32, "controller job", nullable=True)
            if cmd["source_pin_identity"] != item["source_pin_identity"]:
                raise ProgressError("source pin mismatch")
            _value(cmd["phase"], COMMAND_PHASES, "command phase")
            _value(cmd["state"], STATES, "command state")
            _value(cmd["message_code"], COMMAND_CODES, "command message")
            if cmd["progress"] is not None or type(cmd["command_index"]) is not int or cmd["command_index"] < 0:
                raise ProgressError("unsupported command progress/index")
            key = (cmd["attempt_id"], cmd["stage_id"], cmd["package"],
                   cmd["phase"], cmd["command_index"])
            if key in ids:
                raise ProgressError("duplicate command identity")
            ids.add(key)
        pub = _shape(item["publication"], PUBLICATION, "publication")
        _value(pub["state"], frozenset(("unknown", "uncertain", "succeeded")), "publication state")
        _value(pub["message_code"], PUB_CODES, "publication code")
        for key in ("artifact_id", "view_id", "receipt", "binding_digest", "artifact_source_identity"):
            _token(pub[key], REV, key, nullable=True)
        if pub["artifact_revision"] is not None:
            _token(pub["artifact_revision"], SAFE, "artifact revision")
        _token(pub["rootfs_generation"], HEX64, "published rootfs generation", nullable=True)
        if type(pub["compatibility_checked"]) is not bool:
            raise ProgressError("publication compatibility flag")
        code = pub["message_code"]
        if code == "publication-unobserved" or code == "publication-evidence-conflict":
            if (pub["state"] != "unknown" or any(pub[k] is not None for k in
                 ("artifact_id", "view_id", "receipt", "binding_digest", "rootfs_generation",
                  "artifact_revision", "artifact_source_identity"))
                    or pub["compatibility_checked"]):
                raise ProgressError("invalid unknown publication")
        else:
            if (requested is not True or pub["artifact_id"] is None
                    or pub["receipt"] is None or pub["artifact_source_identity"] is None
                    or pub["artifact_revision"] is None):
                raise ProgressError("publication lacks owner artifact receipt")
            if code == "artifact-published":
                if (pub["state"] != "succeeded" or pub["view_id"] is not None
                        or pub["binding_digest"] is not None or pub["rootfs_generation"] is not None
                        or pub["compatibility_checked"]):
                    raise ProgressError("artifact-only publication invalid")
            elif code == "view-published-compatibility-unchecked":
                if (pub["state"] != "uncertain" or pub["view_id"] is None
                        or pub["compatibility_checked"] or pub["binding_digest"] is not None
                        or pub["rootfs_generation"] is not None):
                    raise ProgressError("unverified view compatibility")
            elif code == "view-published-compatible":
                if (pub["state"] != "succeeded" or pub["view_id"] is None
                        or not pub["compatibility_checked"] or pub["binding_digest"] is None
                        or pub["rootfs_generation"] is None):
                    raise ProgressError("missing verified rootfs binding")
        # Image-build can independently publish even after build-job retention expires.
        # Never let producer publication be silently replaced with controller success.
    if len(selections) > 1:
        raise ProgressError("conflicting selection revisions on one page")
    page = _shape(raw["page"], frozenset(("has_more", "next_after")), "page")
    if type(page["has_more"]) is not bool:
        raise ProgressError("image-build paging flag invalid")
    _token(page["next_after"], APP, "next application", nullable=True)
    if (page["has_more"] and (not items or page["next_after"] != items[-1]["application"])):
        raise ProgressError("unbound image-build page cursor")
    if [x["application"] for x in items] != sorted(seen):
        raise ProgressError("noncanonical image-build page order")
    return raw


def join_image_progress(snapshot, controller=None):
    """Join one authenticated image page to independently observed controller jobs.

    Controller success is never used to establish a publication receipt, nor
    absence on one non-atomic controller page to deny producer-owned history.
    """
    observed = {}
    warning = []
    if controller is not None:
        controller = _controller(controller)
        observed = {c["build_job_id"]: c for c in controller["items"] if c["build_job_id"]}
        if controller["page"]["build_has_more"] or controller["page"]["runtime_has_more"]:
            warning.append("Controller listing is partial; unmatched jobs are not absence proof.")
    lines = []
    graphics = []
    pubs = []
    for item in snapshot["items"]:
        name = item["application"]
        state, phase = item["state"], item["phase"]
        publication = item["publication"]
        code = publication["message_code"]
        desc = {
            "publication-unobserved": "No verified immutable software publication receipt.",
            "publication-evidence-conflict": "Publication evidence inconsistent; investigation required.",
            "artifact-published": "Artifact receipt published; application view not verified.",
            "view-published-compatibility-unchecked": "Application view published; selected-rootfs compatibility not checked.",
            "view-published-compatible": "Application software view and selected-rootfs binding verified.",
        }[code]
        contradictory = False
        for cmd in item["commands"]:
            jid = cmd["build_job_id"]
            if jid is None or controller is None:
                continue
            row = observed.get(jid)
            if row is None:
                warning.append(name + ": controller job not visible on this bounded page.")
            elif (cmd["controller_request_id"] is not None
                  and row["controller_request_id"] not in (None, cmd["controller_request_id"])):
                contradictory = True
            elif row["state"] in ("failed", "cancelled", "uncertain", "unknown"):
                if cmd["state"] == "succeeded":
                    contradictory = True
            elif row["state"] == "succeeded" and cmd["state"] in ("failed", "cancelled"):
                contradictory = True
        if contradictory:
            state = "uncertain"
            warning.append(name + ": controller execution evidence conflicts with image-build command.")
        if item["commands_truncated"]:
            warning.append(name + ": command evidence was truncated; history is incomplete.")
        lines.append(ProgressLine(name, phase, state, desc))
        if name in GRAPHICAL:
            graphics.append(item["requested"])
            pubs.append(code)
    request = "requested" if True in graphics else (
        "not-requested" if graphics and all(v is False for v in graphics)
        and not snapshot["page"]["has_more"] else "unknown")
    # Aggregate graphical software readiness is deliberately conservative.
    if not pubs or snapshot["page"]["has_more"] or request != "requested":
        pub_state = "unobserved"
    elif all(code == "view-published-compatible" for code, r in zip(pubs, graphics) if r):
        pub_state = "compatible" if any(graphics) and all(
            not r or code == "view-published-compatible" for code, r in zip(pubs, graphics)) else "unobserved"
    elif any(code == "publication-evidence-conflict" for code in pubs):
        pub_state = "uncertain"
    elif any(code in ("artifact-published", "view-published-compatibility-unchecked",
                     "view-published-compatible") for code in pubs):
        pub_state = "partial"
    else:
        pub_state = "unobserved"
    return request, pub_state, tuple(lines), tuple(warning)
