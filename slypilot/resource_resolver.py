"""Resource intake for local paths referenced by the user."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from slypilot.tools.filesystem import (
    build_resource_trace,
    check_path_policy,
    classify_resource,
    detect_paths,
)


@dataclass(frozen=True)
class ResourceDescriptor:
    raw_path: str
    normalized_path: str
    exists: bool
    resource_type: str
    detail: str
    policy_status: str
    selected: bool = False


@dataclass(frozen=True)
class ResourceIntakeResult:
    raw_input: str
    detected_paths: list[str]
    normalized_paths: list[str]
    existing_paths: list[str]
    missing_paths: list[str]
    blocked_paths: list[str]
    resource_types: list[str]
    selected_resource: str | None
    intake_status: str
    resources: list[ResourceDescriptor]
    warnings: list[str]
    project_name: str | None = None
    project_root: str | None = None
    resource_trace: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "raw_input": self.raw_input,
            "detected_paths": list(self.detected_paths),
            "normalized_paths": list(self.normalized_paths),
            "existing_paths": list(self.existing_paths),
            "missing_paths": list(self.missing_paths),
            "blocked_paths": list(self.blocked_paths),
            "resource_types": list(self.resource_types),
            "selected_resource": self.selected_resource,
            "intake_status": self.intake_status,
            "resources": [
                {
                    "raw_path": descriptor.raw_path,
                    "normalized_path": descriptor.normalized_path,
                    "exists": descriptor.exists,
                    "resource_type": descriptor.resource_type,
                    "detail": descriptor.detail,
                    "policy_status": descriptor.policy_status,
                    "selected": descriptor.selected,
                }
                for descriptor in self.resources
            ],
            "warnings": list(self.warnings),
            "project_name": self.project_name,
            "project_root": self.project_root,
            "resource_trace": self.resource_trace,
        }


def resolve_resources(raw_input: str, cwd: Path) -> ResourceIntakeResult:
    detected = detect_paths(raw_input, cwd)
    resources: list[ResourceDescriptor] = []
    warnings: list[str] = []
    existing_paths: list[str] = []
    missing_paths: list[str] = []
    blocked_paths: list[str] = []
    resource_types: list[str] = []
    selected_resource: str | None = None
    intake_status = "no_resource"
    project_name: str | None = None
    project_root: str | None = None

    if "dernière capture" in raw_input.lower() and not detected:
        inbox = cwd.parent / "SlyPilot" / "inbox"
        if inbox.exists():
            selected_resource = str(inbox)
            existing_paths.append(str(inbox))
            resource_types.append("directory")
            resources.append(
                ResourceDescriptor(
                    raw_path="inbox",
                    normalized_path=str(inbox),
                    exists=True,
                    resource_type="project_directory",
                    detail="inbox_directory",
                    policy_status="allowed",
                    selected=True,
                )
            )
            intake_status = "success"
        else:
            warnings.append(f"inbox missing: {inbox}")
            intake_status = "missing_path"

    for detected_path in detected:
        policy = check_path_policy(detected_path.normalized_path, cwd=cwd)
        if not policy.allowed:
            blocked_paths.append(detected_path.normalized_path)
            resources.append(
                ResourceDescriptor(
                    raw_path=detected_path.raw_path,
                    normalized_path=detected_path.normalized_path,
                    exists=False,
                    resource_type="blocked_path",
                    detail=policy.reason,
                    policy_status="blocked",
                )
            )
            continue

        classification = classify_resource(detected_path.normalized_path)
        if classification.resource_type == "missing_path":
            missing_paths.append(detected_path.normalized_path)
            resources.append(
                ResourceDescriptor(
                    raw_path=detected_path.raw_path,
                    normalized_path=detected_path.normalized_path,
                    exists=False,
                    resource_type="missing_path",
                    detail=classification.detail,
                    policy_status="allowed",
                )
            )
            continue

        existing_paths.append(detected_path.normalized_path)
        resource_types.append(classification.resource_type)
        resources.append(
            ResourceDescriptor(
                raw_path=detected_path.raw_path,
                normalized_path=detected_path.normalized_path,
                exists=True,
                resource_type=classification.resource_type,
                detail=classification.detail,
                policy_status="allowed",
                selected=selected_resource is None,
            )
        )
        if selected_resource is None:
            selected_resource = detected_path.normalized_path
        intake_status = "success"
        if classification.resource_type in {"project_directory", "archiops_project", "git_repository"}:
            project_name = Path(detected_path.normalized_path).name.lower()
            project_root = detected_path.normalized_path
            contract = Path(detected_path.normalized_path) / "Documents" / "ARCHIOPS" / "project.yaml"
            if not contract.exists():
                warnings.append(f"project contract missing: {contract}")
                intake_status = "init_required"
        elif classification.resource_type in {"image_file"}:
            intake_status = "resource_selected"

    if blocked_paths and not selected_resource:
        intake_status = "blocked"
    elif missing_paths and not selected_resource:
        intake_status = "missing_path"
    elif not detected and intake_status == "no_resource":
        intake_status = "no_resource"

    resource_trace = build_resource_trace(
        raw_input=raw_input,
        detected_paths=[item.raw_path for item in detected],
        normalized_paths=[item.normalized_path for item in detected],
        existing_paths=existing_paths,
        missing_paths=missing_paths,
        blocked_paths=blocked_paths,
        resource_types=resource_types,
        selected_resource={
            "path": selected_resource or "",
            "type": resource_types[0] if resource_types else "",
            "exists": bool(selected_resource),
            "policy_status": "allowed" if selected_resource else "blocked" if blocked_paths else "none",
        },
        intake_status=intake_status,
    )

    return ResourceIntakeResult(
        raw_input=raw_input,
        detected_paths=[item.raw_path for item in detected],
        normalized_paths=[item.normalized_path for item in detected],
        existing_paths=existing_paths,
        missing_paths=missing_paths,
        blocked_paths=blocked_paths,
        resource_types=resource_types,
        selected_resource=selected_resource,
        intake_status=intake_status,
        resources=resources,
        warnings=warnings,
        project_name=project_name,
        project_root=project_root,
        resource_trace=resource_trace.to_dict(),
    )
