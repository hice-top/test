#!/usr/bin/env python3
"""Minimal manifest checker for local CI without external dependencies."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED_ROOT = {"project", "advanced", "components", "artifacts", "execution"}
REQUIRED_PROJECT = {"name", "version", "installRoot"}
REQUIRED_ADVANCED = {"enableLogs", "showProgress", "smartExtract"}
REQUIRED_EXECUTION = {"stopOnFailure", "allowResume", "requireAdmin"}


class ValidationError(Exception):
    pass


def ensure_keys(obj: dict, required: set[str], path: str) -> None:
    missing = required - set(obj)
    if missing:
        raise ValidationError(f"{path} missing keys: {sorted(missing)}")


def validate_manifest(data: dict) -> None:
    ensure_keys(data, REQUIRED_ROOT, "root")
    ensure_keys(data["project"], REQUIRED_PROJECT, "project")
    ensure_keys(data["advanced"], REQUIRED_ADVANCED, "advanced")
    ensure_keys(data["execution"], REQUIRED_EXECUTION, "execution")

    components = data["components"]
    if not isinstance(components, list) or len(components) == 0:
        raise ValidationError("components must be a non-empty list")

    for i, comp in enumerate(components):
        for key in [
            "name",
            "enabled",
            "installer",
            "installPath",
            "silentArgs",
            "preChecks",
            "conflictPolicy",
            "postActions",
        ]:
            if key not in comp:
                raise ValidationError(f"components[{i}] missing key: {key}")

    artifacts = data["artifacts"]
    priority = artifacts.get("webTargetPriority", [])
    if not isinstance(priority, list) or len(priority) == 0:
        raise ValidationError("artifacts.webTargetPriority must be a non-empty list")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: validate_manifest.py <manifest.json>")
        return 2

    p = Path(sys.argv[1])
    if not p.exists():
        print(f"ERROR: file not found: {p}")
        return 2

    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        validate_manifest(data)
    except (json.JSONDecodeError, ValidationError) as exc:
        print(f"INVALID: {exc}")
        return 1

    print("VALID")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
