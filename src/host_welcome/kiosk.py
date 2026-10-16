"""Optional local Linux graphical kiosk for simulated host-welcome snapshots.

No browser engine is bundled; Firefox is preferred, Chromium is an alternative.
The launcher does not elevate privileges, mutate host state, fetch remotely, or
try to install a missing browser.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

from .cli import SCENARIOS, main as preview_main

BROWSER_CANDIDATES = {
    "firefox": ("firefox", "firefox-esr"),
    "chromium": ("chromium", "chromium-browser"),
}
BROWSER_ORDER = ("firefox", "chromium")


class KioskError(RuntimeError):
    """The optional kiosk presentation cannot be started safely."""


def resolve_browser(choice: str) -> tuple[str, str]:
    """Resolve only known browsers from the caller's executable search path."""
    if choice not in ("auto", *BROWSER_ORDER):
        raise KioskError("unsupported browser")
    choices = BROWSER_ORDER if choice == "auto" else (choice,)
    for kind in choices:
        for candidate in BROWSER_CANDIDATES[kind]:
            executable = shutil.which(candidate)
            if executable:
                return kind, executable
    raise KioskError("no supported browser available; install Firefox or Chromium, or use console mode")


def kiosk_command(kind: str, executable: str, html: Path, profile: Path, *, wayland_only: bool = False) -> list[str]:
    """Build an argument vector; never shell-interpolate a URL or executable."""
    url = html.resolve().as_uri()
    if kind == "firefox":
        return [executable, "--no-remote", "--profile", str(profile), "--kiosk", url]
    if kind == "chromium":
        return [
            executable,
            "--user-data-dir=" + str(profile),
            "--no-first-run",
            "--no-default-browser-check",
            *(["--ozone-platform=wayland"] if wayland_only else []),
            "--kiosk",
            url,
        ]
    raise KioskError("unsupported browser")


def _check_graphical_session() -> None:
    if sys.platform != "linux":
        raise KioskError("live kiosk launch requires Linux; use --dry-run or download HTML previews")
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise KioskError("refusing to start a kiosk browser as root")
    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        raise KioskError("no X11/Wayland display detected; use the console presentation")


def run_kiosk(args: argparse.Namespace) -> int:
    # The existing CLI owns the validation and the factual assessment. It will
    # reject source_kind=host input from an untrusted file.
    with TemporaryDirectory(prefix="zog-host-welcome-") as directory:
        base = Path(directory)
        html = base / "welcome.html"
        selected = ["--scenario", args.scenario] if args.scenario else ["--input", str(args.input)]
        if preview_main([*selected, "--format", "html", "--output", str(html)]) != 0:
            return 2
        if args.dry_run:
            kind = "firefox" if args.browser == "auto" else args.browser
            example = kiosk_command(
                kind, BROWSER_CANDIDATES[kind][0],
                Path("/tmp/zog-host-welcome/welcome.html"),
                Path("/tmp/zog-host-welcome/browser-profile"),
            )
            print("SIMULATED KIOSK PLAN -- no browser started")
            print("Browser preference:", args.browser, "(Firefox first)" if args.browser == "auto" else "")
            print("HTML: generated from an explicitly simulated readiness snapshot")
            print("Command template:", shlex.join(example))
            print("At launch, file and isolated profile paths are temporary.")
            return 0
        _check_graphical_session()
        kind, executable = resolve_browser(args.browser)
        profile = base / "browser-profile"
        profile.mkdir(mode=0o700)
        wayland_only = bool(os.environ.get("WAYLAND_DISPLAY")) and not bool(os.environ.get("DISPLAY"))
        command = kiosk_command(kind, executable, html, profile, wayland_only=wayland_only)
        env = os.environ.copy()
        if kind == "firefox" and wayland_only:
            env.setdefault("MOZ_ENABLE_WAYLAND", "1")
        print(f"Launching {kind} kiosk; this remains a simulated status display.", flush=True)
        try:
            process = subprocess.Popen(command, env=env, cwd=str(base))
        except OSError as exc:
            raise KioskError(f"could not start {kind}: {exc}") from exc
        try:
            return process.wait()
        except KeyboardInterrupt:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            return 130


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="host-welcome-kiosk",
        description="Launch a simulated Zog welcome in an existing Linux browser (no installer authority)",
    )
    selected = parser.add_mutually_exclusive_group(required=True)
    selected.add_argument("--scenario", choices=SCENARIOS)
    selected.add_argument("--input", type=Path, help="untrusted simulation-only snapshot JSON")
    parser.add_argument("--browser", choices=("auto", "firefox", "chromium"), default="auto")
    parser.add_argument("--dry-run", action="store_true", help="validate and show command plan; never launch")
    args = parser.parse_args(argv)
    try:
        return run_kiosk(args)
    except KioskError as exc:
        print(f"host-welcome-kiosk: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
