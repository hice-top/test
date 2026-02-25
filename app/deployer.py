from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from tools.validate_manifest import ValidationError, validate_manifest


@dataclass
class StepResult:
    step: str
    status: str
    start_at: str
    end_at: str
    detail: str = ""


class Deployer:
    """Manifest-driven installer engine (cross-platform simulation)."""

    def __init__(self, manifest: dict[str, Any], output_dir: Path) -> None:
        self.manifest = manifest
        self.output_dir = output_dir
        self.logs_dir = output_dir / "logs"
        self.state_file = output_dir / "state.json"
        self.report_file = output_dir / "report.json"
        self.results: list[StepResult] = []

    @classmethod
    def from_file(cls, manifest_path: Path, output_dir: Path) -> "Deployer":
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        validate_manifest(data)
        return cls(data, output_dir)

    def run(self, resume: bool = False) -> dict[str, Any]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

        done_steps: set[str] = set()
        if resume and self.state_file.exists():
            state = json.loads(self.state_file.read_text(encoding="utf-8"))
            done_steps = set(state.get("done_steps", []))

        sequence = [
            ("init", self._init),
            ("prechecks", self._prechecks),
            ("install_components", self._install_components),
            ("deploy_artifacts", self._deploy_artifacts),
            ("health_check", self._health_check),
            ("finish", self._finish),
        ]

        stop_on_failure = self.manifest["execution"]["stopOnFailure"]

        for step_name, fn in sequence:
            if step_name in done_steps:
                continue

            started = self._now()
            status = "success"
            detail = ""
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 - process boundary
                status = "failed"
                detail = str(exc)
                self._append_log(f"[ERROR] {step_name}: {exc}")
                self._save_state(done_steps)
                self._record_step(step_name, status, started, self._now(), detail)
                if stop_on_failure:
                    break
            else:
                done_steps.add(step_name)
                self._append_log(f"[OK] {step_name}")
                self._save_state(done_steps)
                self._record_step(step_name, status, started, self._now(), detail)

        summary = {
            "project": self.manifest["project"]["name"],
            "version": self.manifest["project"]["version"],
            "finishedAt": self._now(),
            "steps": [asdict(x) for x in self.results],
        }
        self.report_file.write_text(
            json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return summary

    def _init(self) -> None:
        self._append_log("Initialize runtime and manifest")
        self._sleep()

    def _prechecks(self) -> None:
        self._append_log("Run global prechecks: permission, disk, service, ports")
        self._sleep()

    def _install_components(self) -> None:
        components = [c for c in self.manifest["components"] if c.get("enabled")]
        for comp in components:
            name = comp["name"]
            policy = comp["conflictPolicy"]
            self._append_log(f"Install component={name}, conflictPolicy={policy}")
            if policy == "ask_user":
                # non-interactive default: continue with overwrite policy
                self._append_log(
                    f"Policy ask_user detected for {name}; non-interactive fallback=overwrite"
                )
            self._sleep()

    def _deploy_artifacts(self) -> None:
        artifacts = self.manifest["artifacts"]
        root = Path(self.manifest["project"]["installRoot"]) if self.manifest["project"].get("installRoot") else self.output_dir / "install"
        sandbox_root = self.output_dir / "sandbox_install"
        sandbox_root.mkdir(exist_ok=True)

        if artifacts.get("jar"):
            target = sandbox_root / "app" / Path(artifacts["jar"]).name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("simulated jar payload", encoding="utf-8")
            self._append_log(f"jar deployed -> {target}")

        if artifacts.get("war"):
            target = sandbox_root / "tomcat" / "webapps" / Path(artifacts["war"]).name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text("simulated war payload", encoding="utf-8")
            self._append_log(f"war deployed -> {target}")

        if artifacts.get("frontendZip"):
            priority = artifacts.get("webTargetPriority", ["tomcat"])
            first = priority[0]
            if first == "nginx":
                target = sandbox_root / "nginx" / "html" / "dist"
            else:
                target = sandbox_root / "tomcat" / "webapps" / "dist"
            target.mkdir(parents=True, exist_ok=True)
            (target / "index.html").write_text("<html>simulated dist</html>", encoding="utf-8")
            self._append_log(f"dist.zip deployed -> {target}")

        self._append_log(f"installRoot configured: {root}")
        self._sleep()

    def _health_check(self) -> None:
        self._append_log("Run health checks for services and files")
        self._sleep()

    def _finish(self) -> None:
        self._append_log("Deployment finished")
        self._sleep()

    def _append_log(self, message: str) -> None:
        ts = self._now()
        (self.logs_dir / "install.log").open("a", encoding="utf-8").write(f"{ts} {message}\n")

    def _record_step(self, step: str, status: str, start_at: str, end_at: str, detail: str) -> None:
        self.results.append(
            StepResult(step=step, status=status, start_at=start_at, end_at=end_at, detail=detail)
        )

    def _save_state(self, done_steps: set[str]) -> None:
        self.state_file.write_text(
            json.dumps({"done_steps": sorted(done_steps)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _now() -> str:
        return datetime.utcnow().isoformat(timespec="seconds") + "Z"

    @staticmethod
    def _sleep() -> None:
        time.sleep(0.01)


def create_project_from_sample(output_manifest: Path) -> Path:
    sample = Path("examples/manifest.sample.json")
    if not sample.exists():
        raise FileNotFoundError("examples/manifest.sample.json not found")
    output_manifest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(sample, output_manifest)
    return output_manifest
