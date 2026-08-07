#!/usr/bin/env python3
"""Dependency-free student environment check for the first hands-on class."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def run(command: list[str], timeout: int = 10) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, str(exc)
    output = (result.stdout or result.stderr).strip().splitlines()
    return result.returncode == 0, output[0] if output else f"exit={result.returncode}"


def check_environment(root: Path) -> tuple[list[str], list[str]]:
    passes: list[str] = []
    failures: list[str] = []

    if sys.version_info >= (3, 11):
        passes.append(f"Python {sys.version.split()[0]}")
    else:
        failures.append(f"Python 3.11+ required; found {sys.version.split()[0]}")

    for command, label in (("git", "Git"), ("codex", "Codex")):
        executable = shutil.which(command)
        if not executable:
            failures.append(f"{label} command not found")
            continue
        ok, output = run([executable, "--version"])
        if ok:
            passes.append(f"{label}: {output}")
        else:
            failures.append(f"{label} version check failed: {output}")

    git = shutil.which("git")
    if git:
        for key in ("user.name", "user.email"):
            ok, output = run([git, "config", "--global", "--get", key])
            if ok and output:
                passes.append(f"Git {key} configured")
            else:
                failures.append(f"Git {key} is empty")

        ok, output = run([git, "-C", str(root), "rev-parse", "--is-inside-work-tree"])
        if ok and output == "true":
            passes.append("Current folder is a Git repository")
        else:
            failures.append("Current folder is not a Git repository")

    for relative in ("AGENTS.md", "README.md"):
        if (root / relative).is_file():
            passes.append(f"Found {relative}")
        else:
            failures.append(f"Missing {relative}")

    return passes, failures


def main() -> int:
    passes, failures = check_environment(Path.cwd())
    for item in passes:
        print(f"PASS: {item}")
    for item in failures:
        print(f"FAIL: {item}")

    if failures:
        print(f"NOT READY: {len(failures)} check(s) need attention")
        return 1
    print("READY: core environment checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
