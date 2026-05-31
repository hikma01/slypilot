"""Resource trace builder for filesystem intake."""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ResourceTrace:
    raw_input: str
    detected_paths: list[str]
    normalized_paths: list[str]
    existing_paths: list[str]
    missing_paths: list[str]
    blocked_paths: list[str]
    resource_types: list[str]
    selected_resource: dict[str, object]
    intake_status: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_resource_trace(
    raw_input: str,
    detected_paths: list[str],
    normalized_paths: list[str],
    existing_paths: list[str],
    missing_paths: list[str],
    blocked_paths: list[str],
    resource_types: list[str],
    selected_resource: dict[str, object],
    intake_status: str,
) -> ResourceTrace:
    return ResourceTrace(
        raw_input=raw_input,
        detected_paths=detected_paths,
        normalized_paths=normalized_paths,
        existing_paths=existing_paths,
        missing_paths=missing_paths,
        blocked_paths=blocked_paths,
        resource_types=resource_types,
        selected_resource=selected_resource,
        intake_status=intake_status,
    )
