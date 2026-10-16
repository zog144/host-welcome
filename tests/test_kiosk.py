import contextlib
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

from host_welcome.kiosk import (
    KioskError, kiosk_command, main, resolve_browser
)


class KioskTests(unittest.TestCase):
    def test_firefox_first_with_chromium_fallback(self):
        def which(candidate):
            return {
                "firefox": "/usr/bin/firefox",
                "chromium": "/usr/bin/chromium",
            }.get(candidate)
        with patch("host_welcome.kiosk.shutil.which", side_effect=which):
            self.assertEqual(resolve_browser("auto"), ("firefox", "/usr/bin/firefox"))
            self.assertEqual(resolve_browser("chromium"), ("chromium", "/usr/bin/chromium"))

    def test_missing_browser_is_clear_and_does_not_autoinstall(self):
        with patch("host_welcome.kiosk.shutil.which", return_value=None):
            with self.assertRaisesRegex(KioskError, "no supported browser"):
                resolve_browser("auto")

    def test_explicit_firefox_uses_esr(self):
        with patch("host_welcome.kiosk.shutil.which",
                   side_effect=lambda name: "/usr/bin/firefox-esr" if name == "firefox-esr" else None):
            self.assertEqual(resolve_browser("firefox"), ("firefox", "/usr/bin/firefox-esr"))

    def test_safe_commands_and_wayland_selection(self):
        html = Path("/tmp/zog preview/hello.html")
        profile = Path("/tmp/zog preview/profile")
        ff = kiosk_command("firefox", "/usr/bin/firefox", html, profile)
        self.assertEqual(ff[:5], ["/usr/bin/firefox", "--no-remote", "--profile", str(profile), "--kiosk"])
        self.assertTrue(ff[-1].startswith("file:///"))
        self.assertIn("%20", ff[-1])
        ch = kiosk_command("chromium", "/usr/bin/chromium", html, profile, wayland_only=True)
        self.assertIn("--ozone-platform=wayland", ch)
        self.assertIn("--user-data-dir=" + str(profile), ch)
        self.assertNotIn("--no-sandbox", ch)

    def test_dry_run_without_browser_or_display(self):
        out = io.StringIO()
        with patch("host_welcome.kiosk.shutil.which", side_effect=AssertionError("browser must not be resolved")), \\
             patch("host_welcome.kiosk.subprocess.Popen", side_effect=AssertionError("must not launch")), \\
             patch.dict(os.environ, {"DISPLAY": "", "WAYLAND_DISPLAY": ""}), \\
             contextlib.redirect_stdout(out):
            code = main(["--scenario", "pending", "--dry-run"])
        self.assertEqual(code, 0)
        self.assertIn("SIMULATED KIOSK PLAN", out.getvalue())
        self.assertIn("firefox", out.getvalue())

    def test_live_refuses_missing_display_without_launch(self):
        if not hasattr(os, "geteuid"):
            self.skipTest("Linux-only launcher")
        with patch("host_welcome.kiosk.sys.platform", "linux"), \\
             patch("host_welcome.kiosk.os.geteuid", return_value=1000), \\
             patch.dict(os.environ, {"DISPLAY": "", "WAYLAND_DISPLAY": ""}), \\
             patch("host_welcome.kiosk.subprocess.Popen", side_effect=AssertionError("should not launch")), \\
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--scenario", "ready"]), 2)

    def test_live_refuses_root_even_with_display(self):
        if not hasattr(os, "geteuid"):
            self.skipTest("Linux-only launcher")
        with patch("host_welcome.kiosk.sys.platform", "linux"), \\
             patch("host_welcome.kiosk.os.geteuid", return_value=0), \\
             patch.dict(os.environ, {"DISPLAY": ":0"}), \\
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(main(["--scenario", "ready"]), 2)

    def test_live_launch_wait_and_temporary_files_removed(self):
        if not hasattr(os, "geteuid"):
            self.skipTest("Linux-only launcher")
        recorded = {}
        process = Mock()
        process.wait.return_value = 0
        def popen(args, **kwargs):
            recorded["command"] = args
            recorded["cwd"] = kwargs["cwd"]
            recorded["html"] = Path(kwargs["cwd"]) / "welcome.html"
            recorded["profile"] = Path(kwargs["cwd"]) / "browser-profile"
            self.assertTrue(recorded["html"].exists())
            self.assertTrue(recorded["profile"].is_dir())
            return process
        with patch("host_welcome.kiosk.sys.platform", "linux"), \\
             patch("host_welcome.kiosk.os.geteuid", return_value=1000), \\
             patch.dict(os.environ, {"DISPLAY": ":0", "WAYLAND_DISPLAY": ""}), \\
             patch("host_welcome.kiosk.shutil.which", side_effect=lambda n: "/usr/bin/firefox" if n == "firefox" else None), \\
             patch("host_welcome.kiosk.subprocess.Popen", side_effect=popen):
            self.assertEqual(main(["--scenario", "ready"]), 0)
        self.assertFalse(recorded["html"].exists())
        self.assertFalse(recorded["profile"].exists())
        self.assertIn("--kiosk", recorded["command"])

    def test_rejects_host_source_even_for_dry_run(self):
        import json
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "untrusted.json"
            target.write_text(json.dumps({"source_kind":"host"}), encoding="utf-8")
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(main(["--input", str(target), "--dry-run"]), 2)
