"""Filesystem tool namespace."""

from .filesystem_tool import exists, stat, is_file, is_dir, is_symlink, list_dir, read_text
from .path_detector import detect_paths
from .resource_classifier import classify_resource, ResourceClassification
from .filesystem_policy import check_path_policy, PathPolicyResult
from .resource_trace import build_resource_trace, ResourceTrace

__all__ = [
    "exists",
    "stat",
    "is_file",
    "is_dir",
    "is_symlink",
    "list_dir",
    "read_text",
    "detect_paths",
    "classify_resource",
    "ResourceClassification",
    "check_path_policy",
    "PathPolicyResult",
    "build_resource_trace",
    "ResourceTrace",
]
