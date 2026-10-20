"""Proposed, non-executing local graphical transition acceptance gate.

The LocalSeatEvidence type is a SOURCE-TEST PLACEHOLDER, not an accepted
authentication envelope or a trusted socket adapter. No production caller
constructs one until box-control/root-control and host-install approve the
physical-seat/PAM/logind/browser-readiness observer contract.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from .post_install import validate_image_snapshot
from .progress import _controller, _date, _fresh

REQUIRED = ("xorg-server", "i3", "greetd")
BROWSERS = ("firefox-esr", "firefox", "chromium")


@dataclass(frozen=True)
class LocalSeatEvidence:
    """Synthetic evidence interface; cannot itself authenticate a local seat."""
    physical_seat: bool
    pam_grant_approved: bool
    logind_session_active: bool
    display_ready: bool
    browser_page_ready: bool
    boot_id: str
    selection_revision: str
    observed_at: str


@dataclass(frozen=True)
class TransitionDecision:
    eligible: bool
    retain_console: bool
    gates: tuple[str, ...]


def evaluate_graphical_transition(image, controller=None, local_seat=None,
                                  *, accepted_boot=None, browser="firefox-esr", now=None):
    """Decide only on provided source-level evidence; perform no lifecycle action.

    No built-in producer authenticates LocalSeatEvidence. Consequently this
    function must NOT be used to activate a real session until reviewed
    native authentication and rollback adapters have been accepted.
    """
    now = datetime.now(timezone.utc) if now is None else now
    if browser not in BROWSERS:
        raise ValueError("unsupported graphical kiosk browser")
    image = validate_image_snapshot(image, now=now)
    failed = []
    rows = {r["application"]: r for r in image["items"]}
    for name in (*REQUIRED, browser):
        row = rows.get(name)
        if row is None:
            failed.append(name + ": not observed")
            continue
        if row["requested"] is not True:
            failed.append(name + ": not selected for installation")
        publication = row["publication"]
        if (publication["state"] != "succeeded" or
                publication["message_code"] != "view-published-compatible" or
                not publication["compatibility_checked"] or
                publication["view_id"] is None or
                publication["binding_digest"] is None):
            failed.append(name + ": compatible immutable view not proven")
    if image["page"]["has_more"]:
        failed.append("image-build listing incomplete")
    revisions = {r["selection_revision"] for r in rows.values()}
    if len(revisions) != 1 or None in revisions:
        failed.append("selected application revision inconsistent")
    if controller is None:
        failed.append("controller runtimes not observed")
    else:
        controller = _controller(controller)
        if (accepted_boot is None or controller["boot_id"] != accepted_boot
                or not _fresh(_date(controller["observed_at"], "controller timestamp"),
                              now, boot=controller["boot_id"], expected_boot=accepted_boot)):
            failed.append("controller not bound to verified current boot")
        if controller["page"]["runtime_has_more"]:
            failed.append("controller runtime listing incomplete")
        runtimes = controller["items"]
        for name in (*REQUIRED, browser):
            row = rows.get(name)
            if row is None or row["publication"]["view_id"] is None:
                continue
            linked = [r for r in runtimes
                      if r["runtime_id"] is not None and r["application"] == name
                      and r["selected_software_id"] == row["publication"]["view_id"]
                      and r["state"] == "running"]
            if len(linked) != 1:
                failed.append(name + ": matching observed controller runtime unavailable")
    if not isinstance(local_seat, LocalSeatEvidence):
        failed.append("local-seat observer and greetd/PAM/logind policy unapproved")
    else:
        if (not local_seat.physical_seat or not local_seat.pam_grant_approved
                or not local_seat.logind_session_active):
            failed.append("approved physical seat and login session unavailable")
        if not local_seat.display_ready or not local_seat.browser_page_ready:
            failed.append("graphical display/browser readiness unverified")
        if (accepted_boot is None or local_seat.boot_id != accepted_boot
                or not _fresh(_date(local_seat.observed_at, "seat observation"),
                              now, boot=local_seat.boot_id, expected_boot=accepted_boot)):
            failed.append("local seat is not on the accepted boot")
        if len(revisions) != 1 or local_seat.selection_revision not in revisions:
            failed.append("local seat selection revision conflicts with image-build")
    # No GUI execution or TTY takeover, even when a test supplies all gates.
    return TransitionDecision(not failed, True, tuple(dict.fromkeys(failed)))
