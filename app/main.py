#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.deployer import Deployer, create_project_from_sample
from tools.validate_manifest import ValidationError, validate_manifest


def cmd_validate(manifest: Path) -> int:
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
        validate_manifest(data)
    except FileNotFoundError:
        print(f"ERROR: file not found: {manifest}")
        return 2
    except (json.JSONDecodeError, ValidationError) as exc:
        print(f"INVALID: {exc}")
        return 1
    print("VALID")
    return 0


def cmd_init(output: Path) -> int:
    p = create_project_from_sample(output)
    print(f"Created manifest: {p}")
    return 0


def cmd_install(manifest: Path, runtime_dir: Path, resume: bool) -> int:
    try:
        engine = Deployer.from_file(manifest, runtime_dir)
    except FileNotFoundError:
        print(f"ERROR: file not found: {manifest}")
        return 2
    except (json.JSONDecodeError, ValidationError) as exc:
        print(f"INVALID: {exc}")
        return 1

    report = engine.run(resume=resume)
    failed = [s for s in report["steps"] if s["status"] == "failed"]
    print(f"Finished steps={len(report['steps'])}, failed={len(failed)}")
    print(f"Report: {runtime_dir / 'report.json'}")
    return 1 if failed else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Windows one-click deployer runnable prototype")
    sub = parser.add_subparsers(dest="command", required=True)

    p_init = sub.add_parser("init", help="Create a manifest from sample template")
    p_init.add_argument("--output", default="runtime/manifest.json", type=Path)

    p_validate = sub.add_parser("validate", help="Validate manifest JSON")
    p_validate.add_argument("manifest", type=Path)

    p_install = sub.add_parser("install", help="Execute deployment pipeline")
    p_install.add_argument("manifest", type=Path)
    p_install.add_argument("--runtime-dir", default=Path("runtime"), type=Path)
    p_install.add_argument("--resume", action="store_true")

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init":
        return cmd_init(args.output)
    if args.command == "validate":
        return cmd_validate(args.manifest)
    if args.command == "install":
        return cmd_install(args.manifest, args.runtime_dir, args.resume)

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
