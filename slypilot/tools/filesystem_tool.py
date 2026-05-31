"""Compatibility wrapper for the new filesystem tool package."""

from __future__ import annotations

from pathlib import Path

from slypilot.tools.filesystem.filesystem_tool import (
    exists,
    is_dir,
    is_file,
    is_symlink,
    list_dir,
    read_text,
    stat,
)


def stat_path(path: str | Path) -> dict[str, object]:
    return stat(path)


def read_text_file(path: str | Path, max_bytes: int = 200_000) -> str:
    return read_text(path, max_bytes=max_bytes)


def detect_file_type(path: str | Path):
    suffix = Path(path).suffix.lower()
    if suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return type("FileTypeInfo", (), {"kind": "image", "mimetype": "image/*"})()
    if suffix == ".pdf":
        return type("FileTypeInfo", (), {"kind": "pdf", "mimetype": "application/pdf"})()
    if suffix in {".txt", ".md", ".yaml", ".yml", ".json", ".toml", ".py", ".js", ".ts", ".mjs", ".html", ".css"}:
        return type("FileTypeInfo", (), {"kind": "text", "mimetype": "text/plain"})()
    if Path(path).is_dir():
        return type("FileTypeInfo", (), {"kind": "directory", "mimetype": "inode/directory"})()
    return type("FileTypeInfo", (), {"kind": "unknown", "mimetype": "application/octet-stream"})()


__all__ = [
    "exists",
    "is_dir",
    "is_file",
    "is_symlink",
    "list_dir",
    "read_text",
    "stat",
    "stat_path",
    "read_text_file",
    "detect_file_type",
]
