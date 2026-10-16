"""Plain-text, accessible presentation of the read-only progress assessment."""
from __future__ import annotations
from .progress import ProgressAssessment, ProgressFixture

LABEL = {
    "verified": "VERIFIED", "pending": "PENDING", "failed": "FAILED",
    "unknown": "UNKNOWN", "requested": "REQUESTED", "not-requested": "NOT REQUESTED",
    "unobserved": "UNOBSERVED", "uncertain": "UNCERTAIN", "mixed": "MIXED",
}


def render_progress_console(fixture: ProgressFixture, result: ProgressAssessment) -> str:
    lines = [
        "ZOG / APPLICATION PROGRESS",
        "SIMULATED EXAMPLE -- NOT LIVE HOST OR INSTALLATION STATUS",
        "Read-only: no downloads, compilation, authorization or runtime changes.",
        "",
        "Headless installation: " + LABEL[result.headless],
        "Optional graphical applications: " + LABEL[result.graphics_request],
        "Software publication: " + LABEL[result.publication],
        "Local login / graphical session: NOT VERIFIED",
        "Controller observations: " + result.controller_availability.upper(),
        "",
    ]
    if result.lines:
        for row in result.lines:
            lines.append(f"[{row.state.upper():<9}] {row.title}: {row.phase}")
            lines.append("             " + row.description)
    else:
        lines.append("No associated application work in this simulated view.")
        lines.append("An empty controller page does not prove applications were not requested.")
    if result.warnings:
        lines.append("")
        lines.append("Notes:")
        lines.extend(" - " + warning for warning in result.warnings)
    lines.extend([
        "",
        "A completed build command is not an installed or published application.",
        "A published browser is not proof of X11/Wayland, PAM login or a ready desktop.",
        "The console remains usable while optional applications are unavailable.",
    ])
    return "\n".join(lines) + "\n"
