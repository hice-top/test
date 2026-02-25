from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path


class CliTests(unittest.TestCase):
    def run_cmd(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", "-m", "app.main", *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def test_validate_sample_ok(self) -> None:
        r = self.run_cmd("validate", "examples/manifest.sample.json")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("VALID", r.stdout)

    def test_install_generates_report(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            manifest = base / "manifest.json"
            runtime = base / "runtime"

            init = self.run_cmd("init", "--output", str(manifest))
            self.assertEqual(init.returncode, 0, msg=init.stderr)

            install = self.run_cmd("install", str(manifest), "--runtime-dir", str(runtime))
            self.assertEqual(install.returncode, 0, msg=install.stderr)

            report = runtime / "report.json"
            self.assertTrue(report.exists())
            data = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(data["project"], "demo-enterprise-app")


if __name__ == "__main__":
    unittest.main()
