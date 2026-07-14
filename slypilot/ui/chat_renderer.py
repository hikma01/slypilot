"""Render user-facing chat messages."""

from __future__ import annotations

from .style import hr, section, dim


def render_user_message(message: str) -> str:
    return "\n".join(
        [
            hr("─", 44),
            "👤 Utilisateur",
            hr("─", 44),
            "",
            message,
        ]
    )


def render_slypilot_header() -> str:
    """Render the official 🤖 SlyPilot header."""
    return section("SlyPilot")


def render_slypilot_message(title: str, lines: list[str], include_header: bool = True) -> str:
    """Render a conversational message from SlyPilot."""
    body = "\n".join(lines)
    parts = []
    if include_header:
        parts.extend([render_slypilot_header(), ""])
    
    # STI: Unified identity. Don't show internal titles/labels.
    if title and title not in {"SlyPilot", "Coordinateur", "Interface Cognitive", "", "None"}:
        parts.extend([title, "", body])
    else:
        parts.append(body)
    return "\n".join(parts)


def render_technical_block(title: str, lines: list[str]) -> str:
    """Render a non-intrusive technical block (dimmed, no header)."""
    body = "\n".join([f"  › {line}" for line in lines])
    return dim(f"› {title}\n{body}")


def render_technical_info(message: str) -> str:
    """Render a single-line technical information (dimmed)."""
    return dim(f"  › {message}")
