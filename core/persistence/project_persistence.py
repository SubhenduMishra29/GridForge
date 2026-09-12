# ============================================================
# File: core/persistence/project_persistence.py
# GridForge V2 — Canonical Project Persistence
# Author: Subhendu Mishra
# ============================================================

"""Canonical ``.gridforge`` project loader/saver."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.analysis.dynamic_model_association import DynamicMachineModelAssociation
from core.application.project import ProjectContext
from core.network import Network

from .network_serializer import deserialize_network, serialize_network
from .project_package import MANIFEST_NAME, PACKAGE_VERSION, manifest_path, normalize_package_path, project_path


@dataclass(frozen=True)
class LoadedProject:
    """Explicit in-memory representation of a loaded project package."""
    context: ProjectContext
    network: Network
    presentation: Mapping[str, Any] | None = None
    dynamic_models: tuple[DynamicMachineModelAssociation, ...] = ()


class ProjectPersistenceError(RuntimeError):
    """Raised when a project package is invalid or cannot be persisted."""


class ProjectPersistenceService:
    """Load and save the canonical GridForge engineering project package."""

    def load(self, path: str | Path) -> LoadedProject:
        package = normalize_package_path(path)
        if not package.is_dir():
            raise ProjectPersistenceError(f"Project package does not exist: {package}")
        manifest = self._read_json(manifest_path(package))
        if manifest.get("package_version") != PACKAGE_VERSION:
            raise ProjectPersistenceError(f"Unsupported GridForge package version: {manifest.get('package_version')!r}")
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
        presentation = project.get("sld")
        if presentation is not None and not isinstance(presentation, dict):
            raise ProjectPersistenceError("project.json sld payload must be a JSON object.")

        dynamic_models_data = project.get("dynamic_models", ())
        if not isinstance(dynamic_models_data, list):
            raise ProjectPersistenceError("project.json dynamic_models payload must be an array.")
        try:
            dynamic_models = tuple(
                DynamicMachineModelAssociation.from_dict(item)
                for item in dynamic_models_data
            )
        except (TypeError, ValueError, KeyError) as exc:
            raise ProjectPersistenceError(f"Invalid dynamic machine model association: {exc}") from exc

        context = ProjectContext(project_id=project_id, name=name, path=package)
        return LoadedProject(
            context=context,
            network=network,
            presentation=presentation,
            dynamic_models=dynamic_models,
        )

    def save(self, context: ProjectContext, network: Network,
             presentation: Mapping[str, Any] | str | Path | None = None,
             path: str | Path | None = None,
             *, dynamic_models: Sequence[DynamicMachineModelAssociation] = ()) -> None:
        """Save a project with optional persistent presentation and dynamic-model state."""
        if path is None:
            path = presentation
            presentation = None
        if path is None:
            raise TypeError("path is required.")
        if not isinstance(context, ProjectContext):
            raise TypeError("context must be a ProjectContext.")
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        if presentation is not None and not isinstance(presentation, Mapping):
            raise TypeError("presentation must be a mapping or None.")
        if not isinstance(dynamic_models, Sequence):
            raise TypeError("dynamic_models must be a sequence.")
        if any(not isinstance(item, DynamicMachineModelAssociation) for item in dynamic_models):
            raise TypeError("dynamic_models contains an invalid association.")

        target = normalize_package_path(path)
        parent = target.parent
        parent.mkdir(parents=True, exist_ok=True)
        network_data = serialize_network(network)
        presentation_data = None if presentation is None else dict(presentation)
        dynamic_models_data = [item.to_dict() for item in dynamic_models]
        manifest = {
            "format": "GridForgeProject",
            "package_version": PACKAGE_VERSION,
            "project_id": context.project_id,
            "name": context.name,
            "engineering_state": "project.json",
        }
        project = {
            "schema": 1,
            "project": {"project_id": context.project_id, "name": context.name},
            "network": network_data,
            "dynamic_models": dynamic_models_data,
        }
        if presentation_data is not None:
            project["sld"] = presentation_data

        temp_dir = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=parent))
        backup_dir: Path | None = None
        try:
            self._write_json(temp_dir / MANIFEST_NAME, manifest)
            self._write_json(temp_dir / "project.json", project)
            if target.exists():
                backup_dir = Path(tempfile.mkdtemp(prefix=f".{target.name}.backup.", dir=parent))
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
            raise ProjectPersistenceError(f"Unable to save GridForge project to {target}: {exc}") from exc

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
        except (OSError, TypeError, ValueError) as exc:
            raise ProjectPersistenceError(f"Unable to write {path.name}: {exc}") from exc


__all__ = ["LoadedProject", "ProjectPersistenceError", "ProjectPersistenceService"]
