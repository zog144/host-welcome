import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from host_welcome.cli import main


class CLITests(unittest.TestCase):
    def test_all_formats(self):
        for fmt in ("console", "html", "json"):
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                self.assertEqual(main(["--scenario", "pending", "--format", fmt]), 0)
            self.assertTrue(out.getvalue())
            if fmt == "json":
                self.assertTrue(json.loads(out.getvalue())["simulated"])
            elif fmt == "html":
                self.assertIn("eight-tentacled", out.getvalue())
                self.assertIn('skiff.setState("waiting")', out.getvalue())

    def test_output_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "preview.html"
            self.assertEqual(main(["--scenario", "recovery", "--format", "html", "--output", str(target)]), 0)
            self.assertIn("ATTENTION", target.read_text())

    def test_reject_live_claim_via_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "untrusted.json"
            target.write_text(json.dumps({
                "schema_version": "host-welcome.readiness/v1",
                "source_kind": "host", "observed_at": "2026-10-15T12:00:00Z",
                "host_label": "test", "observations": {}
            }))
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--input", str(target)]), 2)
