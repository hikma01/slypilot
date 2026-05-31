"""Bounded filesystem access helpers."""

from __future__ import annotations

from pathlib import Path


def exists(path: str | Path) -> bool:
    return Path(path).expanduser().exists()


def stat(path: str | Path) -> dict[str, object]:
    p = Path(path).expanduser()
    st = p.stat()
    return {
        "exists": p.exists(),
        "is_file": p.is_file(),
        "is_dir": p.is_dir(),
        "is_symlink": p.is_symlink(),
        "size": st.st_size,
    }


def is_file(path: str | Path) -> bool:
    return Path(path).expanduser().is_file()


def is_dir(path: str | Path) -> bool:
    return Path(path).expanduser().is_dir()


def is_symlink(path: str | Path) -> bool:
    return Path(path).expanduser().is_symlink()


def list_dir(path: str | Path, max_depth: int = 1, max_entries: int = 100) -> list[str]:
    root = Path(path).expanduser()
    if max_depth < 0 or not root.is_dir():
        return []
    results: list[str] = []
    _walk_dir(root, max_depth=max_depth, max_entries=max_entries, results=results, current_depth=0)
    return results


def _walk_dir(root: Path, max_depth: int, max_entries: int, results: list[str], current_depth: int) -> None:
    if len(results) >= max_entries or current_depth > max_depth:
        return
    for child in sorted(root.iterdir()):
        if len(results) >= max_entries:
            return
        results.append(str(child))
        if child.is_dir() and current_depth < max_depth:
            _walk_dir(child, max_depth=max_depth, max_entries=max_entries, results=results, current_depth=current_depth + 1)


def read_text(path: str | Path, max_bytes: int = 200_000) -> str:
    p = Path(path).expanduser()
    data = p.read_bytes()
    if len(data) > max_bytes:
        data = data[:max_bytes]
    return data.decode("utf-8", errors="replace")
