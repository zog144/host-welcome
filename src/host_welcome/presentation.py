"""Console and self-contained HTML renderers of the same assessed snapshot."""
from __future__ import annotations

from html import escape
from importlib.resources import files
from .model import CATEGORIES, LABELS, Assessment, Snapshot

HEADLINES = {
    "ready": ("Welcome aboard!", "All required readiness checks are verified."),
    "setup_pending": ("Your Zog host is taking shape.", "There are still steps to complete."),
    "unknown": ("Let's check a few things.", "Some readiness facts are not yet known."),
    "degraded": ("Something needs attention.", "Your host has a degraded readiness check."),
    "attention": ("Let's get this sorted.", "A readiness check reported a failure."),
}
MARKERS = {
    "verified": "OK", "pending": "WAIT", "unknown": "?",
    "degraded": "WARN", "failed": "FAIL",
}


def render_console(snapshot: Snapshot, assessment: Assessment) -> str:
    headline, subline = HEADLINES[assessment.aggregate]
    lines = [
        "ZOG / HOST-WELCOME", "Skiff: Welcome aboard!",
        f"HOST: {snapshot.host_label}",
        "SIMULATED EXAMPLE -- NOT LIVE HOST READINESS" if snapshot.source_kind == "fixture"
        else "VERIFIED PRODUCER SNAPSHOT",
        "", headline, subline, "",
    ]
    for category in CATEGORIES:
        item = snapshot.observations[category]
        lines.append(f"[{MARKERS[item.status]:<4}] {LABELS[category]:<17} {item.summary}")
    lines += ["", f"Readiness: {assessment.aggregate} ({assessment.reason})",
              "Read-only presentation: no installation, enrollment or recovery actions."]
    return "\n".join(lines) + "\n"


def render_html(snapshot: Snapshot, assessment: Assessment) -> str:
    title, subline = HEADLINES[assessment.aggregate]
    rows = []
    for category in CATEGORIES:
        item = snapshot.observations[category]
        rows.append(
            f'<li class="check"><span class="marker {item.status}">'
            f'{escape(MARKERS[item.status])}</span>'
            f'<span><strong>{escape(LABELS[category])}</strong>'
            f'<small>{escape(item.summary)}</small></span></li>'
        )
    # Assets are reproducibly compiled from the pinned pose-animate revision,
    # never redrawn or independently posed by host-welcome.
    skiff_state = {
        "ready": "ready",
        "setup_pending": "waiting",
        "unknown": "thinking",
        "degraded": "warning",
        "attention": "error",
    }[assessment.aggregate]
    assets = files("host_welcome").joinpath("assets")
    skiff = assets.joinpath(f"skiff-{assessment.aggregate}.svg").read_text(encoding="utf-8")
    skiff_runtime = assets.joinpath("pose_animate.js").read_text(encoding="utf-8")
    # The state name is selected from the fixed mapping above, not user input.
    skiff_script = (
        '<script type="module">\n'
        + skiff_runtime
        + '\nconst container=document.getElementById("skiff-stage");\n'
        + 'const skiff=createSkiffPresenter(container,{palette:"blue",reducedMotion:"auto"});\n'
        + f'skiff.setState("{skiff_state}");\n'
        + 'window.addEventListener("pagehide",()=>skiff.destroy(),{once:true});\n'
        + '</script>'
    )
    demo = '<div class="demo" role="note">SIMULATED EXAMPLE · NO LIVE HOST CONNECTION</div>' if snapshot.source_kind == "fixture" else ""
    css = """
:root{color-scheme:dark;font-family:system-ui,-apple-system,sans-serif}
*{box-sizing:border-box}body{margin:0;min-height:100vh;color:#eaf8ff;background:radial-gradient(circle at 25% 40%,#1b4e78 0%,#092343 52%,#071428 100%)}
main{max-width:1160px;margin:auto;padding:30px 26px 22px}.bar{display:flex;justify-content:space-between;align-items:center;gap:14px}
.brand{font-size:20px;font-weight:900;letter-spacing:2px}.brand span{display:block;font-size:10px;color:#a0cbe0;letter-spacing:2px;font-weight:600}
.tag{border:1px solid #44708c;color:#b3d5ea;border-radius:25px;padding:9px 13px;font-size:11px;letter-spacing:1px}
.layout{display:grid;grid-template-columns:1fr 1fr;gap:42px;align-items:center;padding:38px 0}
.welcome{text-align:center}.mascot{max-width:440px;width:95%;height:auto;filter:drop-shadow(0 15px 20px #0005);margin:auto}.mascot svg{display:block;width:100%;height:auto;image-rendering:pixelated}
.eyebrow{font-size:11px;color:#a0ebfc;font-weight:800;letter-spacing:2.5px}
h1{font-size:clamp(32px,4vw,54px);line-height:1.1;letter-spacing:-1.8px;margin:18px 0;color:#fff}
.welcome p{font-size:16px;color:#b8d6ea;line-height:1.7;max-width:400px;margin:0 auto}
.panel{background:#081d36ee;border:1px solid #3a6684;border-radius:15px;padding:24px;box-shadow:0 22px 38px #0005}
.panel-top{font-size:11px;letter-spacing:1.5px;color:#9fcee8;font-weight:800}
.state{float:right;border-radius:5px;padding:6px 8px;background:#493e35;color:#f9d09a;font-size:10px;letter-spacing:.5px}
.state.ready{background:#184e4b;color:#8ae6c2}.state.attention,.state.degraded{background:#59363d;color:#ffb7ba}
h2{font-size:27px;margin:21px 0 5px}.intro{color:#b1cee2;font-size:13px;line-height:1.5;margin:0 0 18px}
.checks{list-style:none;margin:0;padding:0}.check{display:flex;align-items:center;gap:13px;border-top:1px solid #244661;padding:10px 0}
.marker{width:43px;min-width:43px;text-align:center;border-radius:6px;padding:7px 3px;font-size:11px;font-weight:900;background:#324354;color:#d6e7f3}
.marker.verified{background:#155052;color:#9df0cc}.marker.pending{background:#55432d;color:#ffdc9e}
.marker.failed,.marker.degraded{background:#633a45;color:#ffb8be}
.check strong{display:block;font-size:13px}.check small{display:block;color:#98bad3;font-size:11px;line-height:1.6;margin-top:2px}
.next{background:#163a56;border:1px solid #32627e;padding:15px;border-radius:9px;margin-top:15px}
.next b{display:block;font-size:10px;letter-spacing:1px;color:#8de7fa;margin-bottom:5px}
.next span{font-size:12px;line-height:1.6}.demo{font-size:11px;font-weight:800;color:#ffd59c;border:1px solid #9c7140;border-radius:7px;padding:12px 16px;text-align:center;letter-spacing:1px}
footer{border-top:1px solid #315873;padding-top:18px;display:flex;justify-content:space-between;gap:14px;flex-wrap:wrap;color:#92bcd6;font-size:11px}
@media(prefers-reduced-motion:reduce){.mascot{animation:none}}
@media(max-width:750px){.layout{grid-template-columns:1fr;gap:16px;padding:15px 0 25px}.mascot{max-width:285px}.panel{padding:17px}main{padding:20px 16px}}
"""
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>Zog · Host Welcome</title><style>' + css + '</style></head><body>'
        '<main><header class="bar"><div class="brand">ZOG<span>HOST-WELCOME</span></div>'
        '<div class="tag">✦ FIRST BOOT</div></header>'
        '<div class="layout"><section class="welcome" aria-labelledby="welcome-title">'
        '<div id="skiff-stage" class="mascot" role="img" aria-label="Skiff, the eight-tentacled blue pixel octopus">' + skiff + '</div>'
        '<div class="eyebrow">✦ A NEW BEGINNING</div><h1 id="welcome-title">' + escape(title) + '</h1>'
        '<p>Hi, I\'m Skiff! I\'ll help you find your way while your machine gets ready.</p></section>'
        '<section class="panel" aria-labelledby="status-title"><div class="panel-top">HOST READINESS'
        f'<span class="state {assessment.aggregate}">{escape(assessment.aggregate.replace("_", " ").upper())}</span>'
        '</div><h2 id="status-title">' + escape(snapshot.host_label) + '</h2>'
        '<p class="intro">' + escape(subline) + '</p><ul class="checks">' + ''.join(rows) + '</ul>'
        '<div class="next"><b>WHAT THIS MEANS</b><span>' + escape(assessment.reason) +
        '</span></div></section></div>' + demo +
        '<footer><span>✧ Made for curious explorers</span>'
        '<span>Read-only · host-welcome v1</span></footer></main>' + skiff_script + '</body></html>'
    )
