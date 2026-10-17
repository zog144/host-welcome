"""Authenticated, fail-closed one-shot host application progress reader.

Boot readiness uses the official host-install peer-checked client. Controller
progress needs a separate UID-gated socket and reviewed root-owned policy.
Never reuse station-access listener or accept caller-controlled transport paths.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import pwd
import re
import stat

from .progress import ProgressAssessment, ProgressLine, _controller, _date, _fresh

POLICY = Path("/etc/zog/host-welcome-progress-observer.json")
CONTROLLER_SOCKET = "/run/host-welcome/controller-progress.sock"
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
BOOT = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\Z")
MAX_CONFIG = 2048


class LiveProgressUnavailable(RuntimeError):
    """The protected producer or its reviewed installation is unavailable."""


def _no_duplicates(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate protected policy member")
        result[key] = value
    return result


def read_controller_policy() -> dict:
    """Read fixed administrator-owned policy, rejecting symlinks/writable ancestor."""
    if not hasattr(os, "O_NOFOLLOW"):
        raise LiveProgressUnavailable("safe policy open not available")
    try:
        d = os.open(str(POLICY.parent), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            directory = os.fstat(d)
            if (not stat.S_ISDIR(directory.st_mode) or directory.st_uid != 0
                    or stat.S_IMODE(directory.st_mode) & 0o022):
                raise LiveProgressUnavailable("unsafe progress policy directory")
            fd = os.open(POLICY.name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=d)
            try:
                record = os.fstat(fd)
                if (not stat.S_ISREG(record.st_mode) or record.st_uid != 0
                        or stat.S_IMODE(record.st_mode) & 0o022
                        or record.st_size <= 0 or record.st_size > MAX_CONFIG):
                    raise LiveProgressUnavailable("unsafe progress policy file")
                raw = os.read(fd, MAX_CONFIG + 1)
            finally:
                os.close(fd)
        finally:
            os.close(d)
        if len(raw) > MAX_CONFIG:
            raise LiveProgressUnavailable("overlong progress policy")
        config = json.loads(raw, object_pairs_hook=_no_duplicates)
        if (type(config) is not dict or set(config) != {
                "schema", "enabled", "consumer_uid", "controller_owner_uid",
                "socket", "box_control_source_commit"}
                or config["schema"] != "zog-host-welcome-progress-observer-v1"
                or config["enabled"] is not True
                or config["socket"] != CONTROLLER_SOCKET
                or type(config["consumer_uid"]) is not int
                or type(config["controller_owner_uid"]) is not int
                or not 1 <= config["consumer_uid"] < 2**31
                or not 1 <= config["controller_owner_uid"] < 2**31
                or config["consumer_uid"] == config["controller_owner_uid"]
                or type(config["box_control_source_commit"]) is not str
                or not HEX40.fullmatch(config["box_control_source_commit"])):
            raise LiveProgressUnavailable("invalid reviewed progress policy")
        return config
    except (OSError, ValueError, UnicodeError, TypeError) as exc:
        raise LiveProgressUnavailable("progress observer policy not installed or invalid") from exc


def request_bootstrap() -> dict:
    """host-install verifies fixed socket, root peer UID, nonce, boot and freshness."""
    try:
        from zog.host_install.welcome_readiness import request_live
        result = request_live()
    except Exception as exc:
        raise LiveProgressUnavailable("authenticated bootstrap observation unavailable") from exc
    if (type(result) is not dict
            or result.get("schema") != "zog-host-install-bootstrap-readiness-v1"
            or type(result.get("headless_installation")) is not dict
            or result["headless_installation"].get("status") not in
            ("verified", "pending", "unknown", "degraded", "failed")
            or type(result.get("observed_at")) is not str
            or type(result.get("boot_id")) is not str
            or not BOOT.fullmatch(result["boot_id"])):
        raise LiveProgressUnavailable("invalid bootstrap observation")
    return result


def request_controller(expected_boot: str) -> dict:
    """Controller progress is optional until a distinct observer is deployed."""
    config = read_controller_policy()
    try:
        account_uid = pwd.getpwnam("host-welcome").pw_uid
        if not (os.geteuid() == account_uid == config["consumer_uid"]):
            raise LiveProgressUnavailable("wrong dedicated console observer UID")
        # The deployment owner separately verifies that the loaded package bytes
        # match the reviewed source commit specified in the protected policy.
        from zog.box_control.application_progress_client import ApplicationProgressClient
        client = ApplicationProgressClient(
            CONTROLLER_SOCKET, controller_uid=config["controller_owner_uid"],
            timeout_seconds=12,
        )
        response = client.snapshot(limit=4)
        parsed = _controller(response)
        if parsed["boot_id"] != expected_boot:
            raise LiveProgressUnavailable("controller boot mismatch")
        if not _fresh(_date(parsed["observed_at"], "controller.observed_at"),
                      datetime.now(timezone.utc), boot=parsed["boot_id"],
                      expected_boot=expected_boot):
            raise LiveProgressUnavailable("stale controller observation")
        return parsed
    except Exception as exc:
        raise LiveProgressUnavailable("authenticated controller observation unavailable") from exc


def live_assessment(*, bootstrap_reader=None, controller_reader=None) -> ProgressAssessment:
    """One bounded observation. Injectable readers are for source tests only."""
    bootstrap_reader = bootstrap_reader or request_bootstrap
    controller_reader = controller_reader or request_controller
    warnings = []
    try:
        bootstrap = bootstrap_reader()
        if type(bootstrap) is not dict:
            raise LiveProgressUnavailable("invalid bootstrap")
        boot = bootstrap.get("boot_id")
        if type(boot) is not str or not BOOT.fullmatch(boot):
            raise LiveProgressUnavailable("no verified current boot")
        item = bootstrap.get("headless_installation")
        if type(item) is not dict or item.get("status") not in (
                "verified", "pending", "degraded", "failed", "unknown"):
            raise LiveProgressUnavailable("invalid headless status")
        headless = item["status"]
    except Exception:
        warnings.append("Authenticated host-install bootstrap readiness unavailable.")
        return ProgressAssessment("unknown", "unknown", "unobserved",
                                  "not-verified", "unavailable", (),
                                  tuple(warnings))
    try:
        controller = controller_reader(boot)
        controller = _controller(controller)
        if (controller["boot_id"] != boot or not _fresh(
                _date(controller["observed_at"], "controller.observed_at"),
                datetime.now(timezone.utc), boot=controller["boot_id"], expected_boot=boot)):
            raise LiveProgressUnavailable("controller observation not current")
        lines = []
        for record in controller["items"]:
            if record["build_job_id"] is not None:
                lines.append(ProgressLine(
                    "Unassociated build command", record["phase"], record["state"],
                    "Controller job outcome only; application/publication not independently observed."
                ))
            else:
                lines.append(ProgressLine(
                    "Runtime " + record["application"], record["phase"], record["state"],
                    "Controller runtime; graphical session and browser readiness unverified."
                ))
        if controller["page"]["build_has_more"] or controller["page"]["runtime_has_more"]:
            warnings.append("Controller observation is one non-atomic page; more entries exist.")
        availability = "observed"
    except Exception:
        lines = []
        availability = "unavailable"
        warnings.append("Authenticated controller progress unavailable or not authorized for host-welcome.")
    warnings.append("Image-build application request intent and publication not independently observed.")
    return ProgressAssessment(headless, "unknown", "unobserved", "not-verified",
                              availability, tuple(lines), tuple(warnings))
