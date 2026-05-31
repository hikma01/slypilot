"""Bounded policy checks for local filesystem access."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ALLOWED_PREFIXES = [
    "/Users/",
]

BLOCKED_PREFIXES = [
    "/System",
    "/Library",
    "/private",
    "/etc",
    "/bin",
    "/sbin",
    "/usr/bin",
]

SENSITIVE_NAMES = {".env", "id_rsa", "credentials", "secrets", "token"}


@dataclass(frozen=True)
class PathPolicyResult:
    allowed: bool
    reason: str


def check_path_policy(path: str | Path, cwd: Path | None = None) -> PathPolicyResult:
    candidate = Path(path).expanduser()
    candidate_str = str(candidate)
    if any(name in candidate.parts for name in SENSITIVE_NAMES):
        return PathPolicyResult(False, "sensitive_path")
    if any(candidate_str.startswith(prefix) for prefix in BLOCKED_PREFIXES):
        return PathPolicyResult(False, "sensitive_path")
    if candidate_str.startswith(str(Path.home() / ".ssh")) or candidate_str.startswith(str(Path.home() / ".gnupg")):
        return PathPolicyResult(False, "sensitive_path")
    if any(candidate_str.startswith(prefix) for prefix in ALLOWED_PREFIXES):
        return PathPolicyResult(True, "allowed")
    if cwd is not None:
        try:
            cwd_resolved = cwd.resolve()
            candidate_resolved = candidate.resolve(strict=False)
            if str(candidate_resolved).startswith(str(cwd_resolved)):
                return PathPolicyResult(True, "allowed")
        except Exception:
            pass
    return PathPolicyResult(False, "outside_allowed_scope")
