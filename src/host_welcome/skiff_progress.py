"""Read-only semantic mapping for the pinned Skiff v0.3 presenter.

No animation/event can change host status; the source-to-state transform only
reads an already accepted progress assessment. The graphical UI remains gated
separately from this module.
"""
from .progress import ProgressAssessment


def skiff_state_for_progress(progress: ProgressAssessment) -> str:
    """Select a visual state, never an installation or session authorization."""
    if progress.headless == "failed" or any(x.state == "failed" for x in progress.lines):
        return "error"
    if progress.headless == "degraded" or any(
            x.state in ("blocked", "cancelled") for x in progress.lines):
        return "warning"
    if any(x.state in ("uncertain", "unknown") for x in progress.lines):
        return "thinking"
    if progress.headless == "unknown" or progress.controller_availability == "unavailable":
        return "thinking"
    if any(x.state == "running" for x in progress.lines):
        return "working"
    # Software publication/animation completion never establishes host/login
    # readiness; the separate host-readiness aggregate owns visual "ready".
    return "waiting"
