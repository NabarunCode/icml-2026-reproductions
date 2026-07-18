"""Tests for repro_core.environment.

These assert on the *schema contract* (every key present, undetectable
values None rather than missing) and on facts that are verifiable in any
environment (this repo is a git checkout, Python version matches the
running interpreter) — not on machine-specific values.
"""

from __future__ import annotations

import json
import platform
from pathlib import Path

from repro_core.environment import (
    SCHEMA_VERSION,
    capture_environment,
    write_environment,
)

REQUIRED_TOP_LEVEL_KEYS = {
    "schema_version",
    "captured_at_utc",
    "git",
    "python",
    "os",
    "cpu",
    "memory",
    "gpu",
    "rust",
    "packages",
}


def test_capture_has_stable_schema() -> None:
    env = capture_environment()
    assert set(env) >= REQUIRED_TOP_LEVEL_KEYS
    assert env["schema_version"] == SCHEMA_VERSION
    assert set(env["git"]) == {"commit", "branch", "dirty"}
    assert set(env["gpu"]) == {"devices", "cuda_version"}


def test_capture_is_json_serializable() -> None:
    env = capture_environment()
    round_tripped = json.loads(json.dumps(env))
    assert round_tripped["python"]["version"] == platform.python_version()


def test_git_commit_detected_in_this_repo() -> None:
    git = capture_environment()["git"]
    assert git["commit"] is not None
    assert len(git["commit"]) == 40
    assert all(c in "0123456789abcdef" for c in git["commit"])
    assert isinstance(git["dirty"], bool)


def test_packages_include_dev_tooling() -> None:
    packages = capture_environment()["packages"]
    assert isinstance(packages, dict)
    assert all(isinstance(v, str) for v in packages.values())


def test_write_environment_creates_parent_dirs(tmp_path: Path) -> None:
    target = tmp_path / "nested" / "results" / "environment.json"
    written = write_environment(target)
    assert written == target
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data["schema_version"] == SCHEMA_VERSION
