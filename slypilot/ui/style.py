"""Formatting helpers for the conversation UI."""

from __future__ import annotations
import os
import sys

# ANSI Escape Codes
DIM = "\033[2m"
RESET = "\033[0m"


def supports_color() -> bool:
    """Check if the terminal supports color."""
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    if sys.platform == "win32" and os.environ.get("TERM") != "xterm":
        return False
    return True


def dim(text: str) -> str:
    """Apply dimmed style (simulated 50% opacity) to text if supported."""
    if supports_color():
        return f"{DIM}{text}{RESET}"
    return text


def task_style(text: str) -> str:
    """Apply style for background tasks / process work."""
    return dim(text)


def hr(char: str = "─", width: int = 44) -> str:
    return char * width


def section(title: str, icon: str = "🤖") -> str:
    return "\n".join([hr(), f"{icon} {title}", hr()])
