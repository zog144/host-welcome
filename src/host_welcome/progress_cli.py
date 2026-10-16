"""Safe, simulation-only entrypoint for application progress console examples."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .progress import ProgressError, assess_progress, load_progress_fixture
from .progress_examples import fixture
from .progress_presentation import render_progress_console

SCENARIOS = ("building", "blocked", "uncertain", "published", "headless", "unavailable")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="host-welcome-progress",
        description="Simulated read-only post-install application progress (never live)",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--scenario", choices=SCENARIOS)
    source.add_argument("--input", type=Path, help="untrusted simulation JSON; live input is denied")
    parser.add_argument("--format", choices=("console", "json"), default="console")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        raw = fixture(args.scenario) if args.scenario else json.loads(args.input.read_text(encoding="utf-8"))
        loaded = load_progress_fixture(raw)
        assessment = assess_progress(loaded)
        if args.format == "console":
            output = render_progress_console(loaded, assessment)
        else:
            output = json.dumps({
                "schema": loaded_schema(), "simulated": True,
                "headless": assessment.headless,
                "graphics_request": assessment.graphics_request,
                "publication": assessment.publication,
                "graphical_session": assessment.graphical_session,
                "controller_availability": assessment.controller_availability,
                "items": [vars(item) for item in assessment.lines],
                "warnings": list(assessment.warnings),
            }, indent=2) + "\n"
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        return 0
    except (ProgressError, ValueError, OSError, TypeError) as exc:
        print(f"host-welcome-progress: {exc}", file=sys.stderr)
        return 2


def loaded_schema() -> str:
    return "host-welcome.progress-view-fixture/v1"


if __name__ == "__main__":
    raise SystemExit(main())
