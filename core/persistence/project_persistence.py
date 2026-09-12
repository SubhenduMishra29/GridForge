# ============================================================
# File: core/persistence/project_persistence.py
# GridForge V2 — Canonical Project Persistence
# Author: Subhendu Mishra
# ============================================================

"""Canonical ``.gridforge`` project loader/saver.

The persistence service is the sole representation boundary for project
packages. It does not own application lifecycle or revision state.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any

from core.application.project import ProjectContext
from core.network import Network

from .network_serializer import deserialize_network, serialize_network
from .project_package import (
    MANIFEST_NAME,
    PACKAGE_VERSION,
    manifest_path,
    normalize_package_path,
    project_path,
)


class ProjectPersistenceError(RuntimeError):
    """Raised when a project package is invalid or cannot be persisted."""


class ProjectPersistenceService:
    """Load and save the canonical GridForge engineering project package."""

    def load(self, path: str | Path) -> tuple[ProjectContext, Network]:
        package = normalize_package_path(path)
        if not package.is_dir():
            raise ProjectPersistenceError(f"Project package does not exist: {package}")

        manifest = self._read_json(manifest_path(package))
        if manifest.get("package_version") != PACKAGE_VERSION:
            raise ProjectPersistenceError(
                f"Unsupported GridForge package version: {manifest.get('package_version')!r}"
            )
        if manifest.get("format") != "GridForgeProject":
            raise ProjectPersistenceError("Invalid GridForge project manifest.")

        project = self._read_json(project_path(package))
        context_data = project.get("project")
        if not isinstance(context_data, dict):
            raise ProjectPersistenceError("project.json is missing project metadata.")

        project_id = context_data.get("project_id")
        name = context_data.get("name")
        if not isinstance(project_id, str) or not project_id.strip():
            raise ProjectPersistenceError("project_id must be a non-empty string.")
        if not isinstance(name, str) or not name.strip():
            raise ProjectPersistenceError("project name must be a non-empty string.")

        network = deserialize_network(project.get("network", {}))
        context = ProjectContext(
            project_id=project_id,
            name=name,
            path=package,
        )
        return context, network

    def save(self, context: ProjectContext, network: Network, path: str | Path) -> None:
        if not isinstance(context, ProjectContext):
            raise TypeError("context must be a ProjectContext.")
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")

        target = normalize_package_path(path)
        parent = target.parent
        parent.mkdir(parents=True, exist_ok=True)

        # Serialize completely before touching the destination. Any model or
        # topology serialization failure therefore leaves the active package
        # untouched.
        network_data = serialize_network(network)
        manifest = {
            "format": "GridForgeProject",
            "package_version": PACKAGE_VERSION,
            "project_id": context.project_id,
            "name": context.name,
            "engineering_state": "project.json",
        }
        project = {
            "schema": 1,
            "project": {
                "project_id": context.project_id,
                "name": context.name,
            },
            "network": network_data,
        }

        temp_dir = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=parent))
        backup_dir: Path | None = None
        try:
            self._write_json(temp_dir / MANIFEST_NAME, manifest)
            self._write_json(temp_dir / "project.json", project)

            # Complete the replacement transaction only after the entire temp
            # package is present and parseable JSON has been written.
            if target.exists():
                backup_dir = Path(
                    tempfile.mkdtemp(prefix=f".{target.name}.backup.", dir=parent)
                )
                backup_dir.rmdir()
                os.replace(target, backup_dir)
            os.replace(temp_dir, target)

            if backup_dir is not None:
                shutil.rmtree(backup_dir)
                backup_dir = None
            temp_dir = Path()
        except Exception as exc:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            if backup_dir is not None and backup_dir.exists() and not target.exists():
                os.replace(backup_dir, target)
            raise ProjectPersistenceError(
                f"Unable to save GridForge project to {target}: {exc}"
            ) from exc

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        if not path.is_file():
            raise ProjectPersistenceError(f"Required project file is missing: {path.name}")
        try:
            with path.open("r", encoding="utf-8") as handle:
                value = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ProjectPersistenceError(f"Unable to read {path.name}: {exc}") from exc
        if not isinstance(value, dict):
            raise ProjectPersistenceError(f"{path.name} must contain a JSON object.")
        return value

    @staticmethod
    def _write_json(path: Path, value: dict[str, Any]) -> None:
        try:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise ProjectPersistenceError(f"Unable to write {path.name}: {exc}") from exc


__all__ = ["ProjectPersistenceError", "ProjectPersistenceService"]
