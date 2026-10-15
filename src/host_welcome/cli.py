"""Simulation-only command line. Never treats a caller's JSON as host authority."""
from __future__ import annotations

import argparse
import json
import sys
from importlib.resources import files
from pathlib import Path

from .model import SnapshotError, assess, load_snapshot, CATEGORIES
from .presentation import render_console, render_html

SCENARIOS = ("pending", "ready", "offline", "recovery", "interrupted")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="host-welcome", description="Preview simulated Zog readiness (no host changes)"
    )
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument("--scenario", choices=SCENARIOS, help="built-in simulated host")
    inputs.add_argument("--input", type=Path, help="simulation-only v1 JSON snapshot")
    parser.add_argument("--format", choices=("console", "html", "json"), default="console")
    parser.add_argument("--output", type=Path, help="write output to a file instead of stdout")
    args = parser.parse_args(argv)
    try:
        if args.scenario:
            content = files("host_welcome").joinpath(f"examples/{args.scenario}.json").read_text(encoding="utf-8")
        else:
            content = args.input.read_text(encoding="utf-8")
        snapshot = load_snapshot(json.loads(content), trusted=False)
        result = assess(snapshot)
        if args.format == "console":
            output = render_console(snapshot, result)
        elif args.format == "html":
            output = render_html(snapshot, result)
        else:
            output = json.dumps({
                "schema_version": snapshot.schema_version,
                "source_kind": snapshot.source_kind,
                "simulated": snapshot.source_kind == "fixture",
                "aggregate": result.aggregate, "fresh": result.fresh,
                "reason": result.reason,
                "observations": {c: {
                    "status": snapshot.observations[c].status,
                    "summary": snapshot.observations[c].summary,
                    "producer": snapshot.observations[c].producer,
                    "evidence_ref": snapshot.observations[c].evidence_ref,
                } for c in CATEGORIES},
            }, indent=2) + "\n"
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
        return 0
    except (SnapshotError, ValueError, OSError) as exc:
        print(f"host-welcome: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
