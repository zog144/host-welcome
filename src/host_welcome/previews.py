"""Offline HTML preview bundle for viewing all Skiff states without Python on Windows."""
from __future__ import annotations

import argparse
from html import escape
from pathlib import Path

from .cli import SCENARIOS, main as preview_main

DESCRIPTIONS = {
    "pending": "Setup pending · patient welcome",
    "ready": "Ready · greeting",
    "offline": "Degraded · network unavailable",
    "recovery": "Attention · STATE recovery",
    "interrupted": "Degraded · interrupted installation",
}


def build_previews(output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    generated = []
    for name in SCENARIOS:
        target = output_dir / f"welcome-{name}.html"
        result = preview_main(["--scenario", name, "--format", "html", "--output", str(target)])
        if result != 0:
            raise RuntimeError(f"could not render scenario {name}")
        generated.append(target)
    links = "\n".join(
        f'<a href="welcome-{escape(name)}.html"><strong>{escape(name.title())}</strong>'
        f'<small>{escape(DESCRIPTIONS[name])}</small></a>'
        for name in SCENARIOS
    )
    index = f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Zog · Welcome previews</title>
<style>
:root{{color-scheme:dark;font-family:system-ui,-apple-system,sans-serif}}
body{{margin:0;min-height:100vh;background:radial-gradient(circle at 25% 20%,#1d4b75,#08192c 75%);color:#e9f9ff}}
main{{max-width:680px;margin:5rem auto;padding:0 1.3rem}}
h1{{font-size:2.5rem;letter-spacing:-.05em;margin-bottom:.25em}}
p{{color:#b1cde0;line-height:1.6}}
a{{display:block;background:#102d49;border:1px solid #326384;border-radius:10px;
padding:1rem 1.25rem;color:#e7f9ff;text-decoration:none;margin:.65rem 0}}
a:hover,a:focus-visible{{outline:2px solid #7ce4f5;outline-offset:2px}}
small{{display:block;color:#99c9de;margin-top:.35rem}}
.notice{{border:1px solid #ac8751;color:#ffdba9;padding:1rem;border-radius:9px}}
</style></head>
<body><main><h1>Welcome aboard.</h1>
<p>Explore Skiff's five offline first-boot presentations. Click any scenario to open its
self-contained HTML file in your browser. No installation, server, or internet connection is needed.</p>
<p class="notice"><strong>SIMULATED EXAMPLES</strong> — these pages do not report the readiness of your computer or any Zog host.</p>
<nav aria-label="Simulated scenarios">{links}</nav>
<p>Built from the pinned pose-animate renderer and host-welcome readiness fixtures.</p>
</main></body></html>"""
    target = output_dir / "index.html"
    target.write_text(index, encoding="utf-8")
    return [target, *generated]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="host-welcome-previews")
    parser.add_argument("--output-dir", type=Path, default=Path("welcome-previews"))
    args = parser.parse_args(argv)
    try:
        paths = build_previews(args.output_dir)
    except (OSError, RuntimeError) as exc:
        parser.exit(2, f"host-welcome-previews: {exc}\n")
    for path in paths:
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
