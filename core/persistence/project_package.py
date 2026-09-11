# ============================================================
# File: core/persistence/project_package.py
# GridForge V2 — Canonical Project Package
# Author: Subhendu Mishra
# ============================================================

"""Canonical on-disk ``.gridforge`` project package contract."""

from __future__ import annotations

from pathlib import Path


PACKAGE_SUFFIX = ".gridforge"
MANIFEST_NAME = "manifest.json"
PROJECT_NAME = "project.json"
PACKAGE_VERSION = 1


def normalize_package_path(path: str | Path) -> Path:
    """Normalize a project package path and require the canonical suffix."""
    if not isinstance(path, (str, Path)):
        raise TypeError("Project path must be a string or Path.")
    target = Path(path)
    if not str(target):
        raise ValueError("Project path must not be empty.")
    if target.suffix.lower() != PACKAGE_SUFFIX:
        target = target.with_name(target.name + PACKAGE_SUFFIX)
    return target


def manifest_path(package: Path) -> Path:
    return package / MANIFEST_NAME


def project_path(package: Path) -> Path:
    return package / PROJECT_NAME


__all__ = [
    "MANIFEST_NAME",
    "PACKAGE_SUFFIX",
    "PACKAGE_VERSION",
    "PROJECT_NAME",
    "manifest_path",
    "normalize_package_path",
    "project_path",
]
