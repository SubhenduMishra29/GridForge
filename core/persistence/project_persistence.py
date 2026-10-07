# ============================================================
# File: core/persistence/project_persistence.py
# GridForge V2 — Project Persistence Service
# Author: Subhendu Mishra
# ============================================================

"""Canonical ``.gridforge`` project loader/saver."""

from __future__ import annotations
# Author: Subhendu Mishra

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.analysis.dynamic_model_association import DynamicMachineModelAssociation
from core.application.project import ProjectContext
from core.application.draft import DraftNetwork
from core.control.configuration import ControlConfiguration
from core.network import Network
from core.protection.project_configuration import ProtectionProjectConfiguration
from core.application.services.validation_service import ValidationService

from .network_serializer import deserialize_network, serialize_network
from .migration import ProjectPersistenceMigration, ProjectMigrationError, SLDMigrationError
from .project_package import (
    MANIFEST_NAME,
    PACKAGE_VERSION,
    PROJECT_SCHEMA_VERSION,
    PRESENTATION_SCHEMA_VERSION,
    SLD_SCHEMA_VERSION,
    CORE_SERIALIZATION_VERSION,
    manifest_path,
    normalize_package_path,
    project_path,
)


@dataclass(frozen=True)
class LoadedProject:
    """Explicit in-memory representation of a loaded project package."""
    context: ProjectContext
    network: Network
    presentation: Mapping[str, Any] | None = None
    presentation_collection: Mapping[str, Any] | None = None
    dynamic_models: tuple[DynamicMachineModelAssociation, ...] = ()
    protection_configuration: ProtectionProjectConfiguration | None = None
    measurement_definitions: tuple[Mapping[str, Any], ...] = ()
    control_configuration: ControlConfiguration | None = None
    draft_network: DraftNetwork | None = None
    protection_presentation: Mapping[str, Any] | None = None


class ProjectPersistenceError(RuntimeError):
    """Raised when a project package is invalid or cannot be persisted."""


class ProjectPersistenceService:
    """Load and save the canonical GridForge engineering project package.

    The temporary-directory replacement strategy writes a complete candidate
    package before installation. An interrupted directory replacement leaves
    the previous package in a recoverable sibling backup; load-time recovery
    restores that checkpoint before parsing. File contents are fsync'd before
    replacement. Directory-entry durability remains platform-specific.
    """

    def __init__(self, migration: ProjectPersistenceMigration | None = None) -> None:
        self._migration = migration or ProjectPersistenceMigration()

    def load(self, path: str | Path) -> LoadedProject:
        package = normalize_package_path(path)
        self._recover_interrupted_save(package)
        if not package.is_dir():
            raise ProjectPersistenceError(f"Project package does not exist: {package}")
        manifest = self._read_json(manifest_path(package))
        package_version = manifest.get("package_version")
        if package_version != PACKAGE_VERSION:
            raise ProjectPersistenceError(
                f"Unsupported GridForge package version: {package_version!r}; "
                f"supported package version is {PACKAGE_VERSION}."
            )
        if manifest.get("format") != "GridForgeProject":
            raise ProjectPersistenceError("Invalid GridForge project manifest.")

        raw_project = self._read_json(project_path(package))
        try:
            project = self._migration.migrate_project(raw_project)
            self._validate_canonical_project_data(project)
        except (ProjectMigrationError, SLDMigrationError, TypeError, ValueError) as exc:
            raise ProjectPersistenceError(f"Project migration/validation failed: {exc}") from exc

        context_data = project["project"]
        project_id, name = context_data["project_id"], context_data["name"]
        try:
            network = deserialize_network(project["network"])
        except (TypeError, ValueError, KeyError) as exc:
            raise ProjectPersistenceError(f"Invalid persisted Network: {exc}") from exc

        presentation_collection = self._normalize_presentation_collection(
            project["presentations"], project_id
        )
        active_id = presentation_collection["active_document_id"]
        documents = presentation_collection["documents"]
        presentation = next(
            (item for item in documents if item["document_id"] == active_id),
            documents[0] if documents else None,
        )
        try:
            dynamic_models = tuple(
                DynamicMachineModelAssociation.from_dict(item, project_id=project_id)
                for item in project["dynamic_models"]
            )
        except (TypeError, ValueError, KeyError) as exc:
            raise ProjectPersistenceError(f"Invalid dynamic machine model association: {exc}") from exc

        measurement_definitions = project["measurement"]["channels"]
        draft_data = project.get("draft_network")
        draft_network = (
            DraftNetwork.from_dict(draft_data, project_id=project_id, activation_generation=1)
            if draft_data is not None else DraftNetwork.empty(project_id, 1)
        )

        control_data = project.get("control")
        try:
            control_configuration = (
                ControlConfiguration.from_dict(control_data)
                if control_data is not None else ControlConfiguration.empty(project_id)
            )
        except (TypeError, ValueError, KeyError) as exc:
            raise ProjectPersistenceError(f"Invalid Control configuration: {exc}") from exc
        if control_configuration.project_id != project_id:
            raise ProjectPersistenceError("Control configuration project_id does not match project metadata.")
        control_configuration.validate()

        protection_data = project.get("protection")
        protection_presentation = project.get("protection_presentation")
        protection_configuration = None
        if protection_data is not None:
            try:
                protection_configuration = ProtectionProjectConfiguration.from_dict(protection_data)
            except (TypeError, ValueError, KeyError) as exc:
                raise ProjectPersistenceError(f"Invalid protection configuration: {exc}") from exc

        context = ProjectContext(project_id=project_id, name=name, path=package)
        self._validate_project_state(
            context, network, presentation, presentation_collection,
            dynamic_models, protection_configuration, control_configuration,
        )
        return LoadedProject(
            context=context,
            network=network,
            presentation=presentation,
            presentation_collection=presentation_collection,
            dynamic_models=dynamic_models,
            protection_configuration=protection_configuration,
            measurement_definitions=tuple(dict(item) for item in measurement_definitions),
            control_configuration=control_configuration,
            draft_network=draft_network,
            protection_presentation=protection_presentation,
        )

    def save(self, context: ProjectContext, network: Network,
             presentation: Mapping[str, Any] | str | Path | None = None,
             path: str | Path | None = None,
             *, dynamic_models: Sequence[DynamicMachineModelAssociation] = (),
             protection_configuration: ProtectionProjectConfiguration | None = None,
             measurement_definitions: Sequence[Mapping[str, Any]] = (),
             control_configuration: ControlConfiguration | None = None,
             draft_network: DraftNetwork | None = None,
             protection_presentation: Mapping[str, Any] | None = None,
             presentation_collection: Mapping[str, Any] | None = None) -> None:
        if path is None:
            path = presentation
            presentation = None
        if path is None:
            raise TypeError("path is required.")
        if not isinstance(context, ProjectContext):
            raise TypeError("context must be a ProjectContext.")
        if not isinstance(network, Network):
            raise TypeError("network must be a Network.")
        if draft_network is not None:
            if not isinstance(draft_network, DraftNetwork):
                raise TypeError("draft_network must be DraftNetwork or None.")
            if draft_network.project_id != context.project_id:
                raise ProjectPersistenceError("DraftNetwork project_id does not match the project.")
        if presentation is not None and not isinstance(presentation, Mapping):
            raise TypeError("presentation must be a mapping or None.")
        if presentation_collection is not None and not isinstance(presentation_collection, Mapping):
            raise TypeError("presentation_collection must be a mapping or None.")
        if protection_presentation is not None and not isinstance(protection_presentation, Mapping):
            raise TypeError("protection_presentation must be a mapping or None.")
        if not isinstance(dynamic_models, Sequence):
            raise TypeError("dynamic_models must be a sequence.")
        if any(not isinstance(item, DynamicMachineModelAssociation) for item in dynamic_models):
            raise TypeError("dynamic_models contains an invalid association.")
        if any(item.project_id != context.project_id for item in dynamic_models):
            raise ProjectPersistenceError("dynamic_models contains an association for a different project.")
        if len({(item.project_id, item.activation_generation) for item in dynamic_models}) > 1:
            raise ProjectPersistenceError("dynamic_models contains mixed project-generation provenance.")
        if protection_configuration is not None and not isinstance(
            protection_configuration, ProtectionProjectConfiguration
        ):
            raise TypeError("protection_configuration must be ProtectionProjectConfiguration or None.")
        if not isinstance(measurement_definitions, Sequence) or any(
            not isinstance(item, Mapping) for item in measurement_definitions
        ):
            raise TypeError("measurement_definitions must be a sequence of mappings.")
        if control_configuration is not None:
            if not isinstance(control_configuration, ControlConfiguration):
                raise TypeError("control_configuration must be ControlConfiguration or None.")
            if control_configuration.project_id != context.project_id:
                raise ProjectPersistenceError("Control configuration project_id does not match the project.")
            control_configuration.validate()

        target = normalize_package_path(path)
        parent = target.parent
        parent.mkdir(parents=True, exist_ok=True)
        try:
            if network.topology_dirty:
                network.rebuild_topology()
            network.validate()
        except Exception as exc:
            raise ProjectPersistenceError(
                f"Project Network failed the persistence validation gate: {exc}"
            ) from exc

        if presentation_collection is not None:
            canonical_collection = self._normalize_presentation_collection(
                presentation_collection, context.project_id
            )
        elif presentation is not None:
            canonical_collection = self._normalize_presentation_collection(
                {
                    "schema": PRESENTATION_SCHEMA_VERSION,
                    "documents": [dict(presentation)],
                    "active_document_id": presentation.get("document_id"),
                },
                context.project_id,
            )
        else:
            canonical_collection = {
                "schema": PRESENTATION_SCHEMA_VERSION,
                "documents": [],
                "active_document_id": None,
            }

        active_id = canonical_collection["active_document_id"]
        documents = canonical_collection["documents"]
        active_presentation = next(
            (item for item in documents if item["document_id"] == active_id),
            documents[0] if documents else None,
        )
        self._validate_project_state(
            context, network, active_presentation, canonical_collection,
            tuple(dynamic_models), protection_configuration, control_configuration,
        )

        project: dict[str, Any] = {
            "schema": PROJECT_SCHEMA_VERSION,
            "project": {"project_id": context.project_id, "name": context.name},
            "network": serialize_network(network),
            "presentations": canonical_collection,
            "dynamic_models": [item.to_dict() for item in dynamic_models],
            "measurement": {"channels": [dict(item) for item in measurement_definitions]},
        }
        if protection_configuration is not None:
            project["protection"] = protection_configuration.to_dict()
        if protection_presentation is not None:
            project["protection_presentation"] = dict(protection_presentation)
        if control_configuration is not None:
            project["control"] = control_configuration.to_dict()
        if draft_network is not None:
            project["draft_network"] = draft_network.to_dict()

        manifest = {"format": "GridForgeProject", "package_version": PACKAGE_VERSION}
        temp_dir = Path(tempfile.mkdtemp(prefix=f".{target.name}.", dir=parent))
        backup_dir: Path | None = None
        replacement_installed = False
        try:
            self._write_json(temp_dir / MANIFEST_NAME, manifest)
            self._write_json(temp_dir / "project.json", project)
            if target.exists():
                backup_dir = Path(tempfile.mkdtemp(prefix=f".{target.name}.backup.", dir=parent))
                backup_dir.rmdir()
                os.replace(target, backup_dir)
            os.replace(temp_dir, target)
            replacement_installed = True
            temp_dir = Path()
            if backup_dir is not None:
                shutil.rmtree(backup_dir)
                backup_dir = None
        except Exception as exc:
            if temp_dir and temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            if backup_dir is not None and backup_dir.exists():
                if replacement_installed and target.exists():
                    shutil.rmtree(target, ignore_errors=True)
                if not target.exists():
                    os.replace(backup_dir, target)
            raise ProjectPersistenceError(
                f"Unable to save GridForge project to {target}: {exc}"
            ) from exc

    @staticmethod
    def _normalize_presentation_collection(data: Mapping[str, Any], project_id: str) -> dict[str, Any]:
        if not isinstance(data, Mapping):
            raise ProjectPersistenceError("Persistent presentation collection must be a mapping.")
        if data.get("schema") != PRESENTATION_SCHEMA_VERSION:
            raise ProjectPersistenceError(
                f"Non-canonical presentation collection schema: {data.get('schema')!r}; "
                f"expected {PRESENTATION_SCHEMA_VERSION}."
            )
        documents = data.get("documents")
        if not isinstance(documents, list):
            raise ProjectPersistenceError("Presentation collection documents must be an array.")

        normalized: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in documents:
            if not isinstance(item, Mapping):
                raise ProjectPersistenceError("Every persisted presentation document must be an object.")
            document_id = item.get("document_id")
            if not isinstance(document_id, str) or not document_id.strip():
                raise ProjectPersistenceError("Persisted presentation document_id must be a non-empty string.")
            if item.get("document_type") != "sld":
                raise ProjectPersistenceError(
                    f"Unsupported persisted presentation document_type: {item.get('document_type')!r}"
                )
            if item.get("schema") != SLD_SCHEMA_VERSION:
                raise ProjectPersistenceError(
                    f"Non-canonical SLD schema in document {document_id!r}: "
                    f"{item.get('schema')!r}; expected {SLD_SCHEMA_VERSION}."
                )
            item_project_id = item.get("project_id")
            if item_project_id not in (None, project_id):
                raise ProjectPersistenceError(
                    f"Presentation document {document_id!r} belongs to another project."
                )
            if document_id in seen:
                raise ProjectPersistenceError(f"Duplicate persisted document_id: {document_id}")
            seen.add(document_id)
            normalized.append(dict(item))

        active_id = data.get("active_document_id")
        if active_id is not None and not isinstance(active_id, str):
            raise ProjectPersistenceError("active_document_id must be a string or null.")
        if active_id not in seen:
            active_id = normalized[0]["document_id"] if normalized else None
        return {
            "schema": PRESENTATION_SCHEMA_VERSION,
            "documents": normalized,
            "active_document_id": active_id,
        }

    @staticmethod
    def _deserialize_control_configuration(data: Mapping[str, Any], project_id: str) -> ControlConfiguration:
        configuration = ControlConfiguration.from_dict(data)
        if configuration.project_id != project_id:
            raise ValueError("Control configuration project_id does not match the project.")
        configuration.validate()
        return configuration

    @staticmethod
    def _validate_canonical_project_data(project: Mapping[str, Any]) -> None:
        """Validate the current persistence representation before deserialization."""
        if not isinstance(project, Mapping):
            raise ProjectPersistenceError("Canonical project representation must be an object.")
        allowed = {
            "schema", "project", "network", "presentations", "dynamic_models",
            "measurement", "control", "protection", "protection_presentation",
            "draft_network",
        }
        unknown = sorted(set(project) - allowed)
        if unknown:
            raise ProjectPersistenceError(
                "Unknown canonical project fields are rejected to prevent silent data loss: "
                + ", ".join(str(item) for item in unknown)
            )
        if project.get("schema") != PROJECT_SCHEMA_VERSION:
            raise ProjectPersistenceError(
                f"Canonical project schema must be {PROJECT_SCHEMA_VERSION}, got {project.get('schema')!r}."
            )
        metadata = project.get("project")
        if not isinstance(metadata, Mapping):
            raise ProjectPersistenceError("Canonical project metadata must be an object.")
        project_id, name = metadata.get("project_id"), metadata.get("name")
        if not isinstance(project_id, str) or not project_id.strip():
            raise ProjectPersistenceError("project_id must be a non-empty string.")
        if not isinstance(name, str) or not name.strip():
            raise ProjectPersistenceError("project name must be a non-empty string.")

        network = project.get("network")
        if not isinstance(network, Mapping) or network.get("schema") != CORE_SERIALIZATION_VERSION:
            raise ProjectPersistenceError(
                f"Canonical Core serialization schema must be {CORE_SERIALIZATION_VERSION}."
            )
        if not isinstance(network.get("elements"), list):
            raise ProjectPersistenceError("Canonical network elements must be an array.")
        connectivity = network.get("connectivity")
        if not isinstance(connectivity, Mapping) or connectivity.get("schema") != CORE_SERIALIZATION_VERSION:
            raise ProjectPersistenceError(
                f"Canonical connectivity serialization schema must be {CORE_SERIALIZATION_VERSION}."
            )
        if not isinstance(connectivity.get("simple_wires"), list):
            raise ProjectPersistenceError("Canonical simple_wires must be an array.")

        collection = project.get("presentations")
        if not isinstance(collection, Mapping):
            raise ProjectPersistenceError("Canonical presentations collection is required.")
        ProjectPersistenceService._normalize_presentation_collection(collection, project_id)

        dynamic_models = project.get("dynamic_models")
        if not isinstance(dynamic_models, list):
            raise ProjectPersistenceError("Canonical dynamic_models must be an array.")
        measurement = project.get("measurement")
        if not isinstance(measurement, Mapping):
            raise ProjectPersistenceError("Canonical measurement must be an object.")
        channels = measurement.get("channels")
        if not isinstance(channels, list) or any(not isinstance(item, Mapping) for item in channels):
            raise ProjectPersistenceError("Canonical measurement.channels must be an array of objects.")
        for key in ("control", "protection", "protection_presentation", "draft_network"):
            if key in project and project[key] is not None and not isinstance(project[key], Mapping):
                raise ProjectPersistenceError(f"Canonical {key} payload must be an object.")

    @staticmethod
    def _validate_project_state(context: ProjectContext, network: Network, presentation: Mapping[str, Any] | None, presentation_collection: Mapping[str, Any] | None, dynamic_models: Sequence[DynamicMachineModelAssociation], protection_configuration: ProtectionProjectConfiguration | None, control_configuration: ControlConfiguration | None = None) -> None:
        """Validate cross-domain project invariants at load/save boundaries."""
        if not isinstance(context, ProjectContext) or not isinstance(network, Network):
            raise ProjectPersistenceError("Project context or Network is invalid.")
        if presentation_collection is not None:
            normalized_collection = ProjectPersistenceService._normalize_presentation_collection(
                presentation_collection,
                context.project_id,
            )
            for document in normalized_collection["documents"]:
                document_schema = document.get("schema")
                if document_schema != SLD_SCHEMA_VERSION:
                    raise ProjectPersistenceError(
                        f"Non-canonical SLD representation schema: {document_schema!r}; expected {SLD_SCHEMA_VERSION}"
                    )
                document_validation = ValidationService.validate_sld_associations(
                    context,
                    network,
                    document,
                )
                for issue in document_validation.issues:
                    if issue.code != "SLD_EQUIPMENT_REFERENCE_UNRESOLVED":
                        raise ProjectPersistenceError(issue.message)
        if presentation is not None:
            if not isinstance(presentation, Mapping):
                raise ProjectPersistenceError("Persistent SLD representation must be a mapping.")
            sld_schema = presentation.get("schema")
            if sld_schema != SLD_SCHEMA_VERSION:
                raise ProjectPersistenceError(
                    f"Non-canonical SLD representation schema: {sld_schema!r}; expected {SLD_SCHEMA_VERSION}"
                )
            sld_validation = ValidationService.validate_sld_associations(
                context,
                network,
                presentation,
            )
            for issue in sld_validation.issues:
                # Structural/project-identity errors are persistence-contract
                # failures. An unresolved equipment reference is deliberately
                # diagnostic only until the repository establishes an orphan
                # policy; persistence must not silently delete, rewrite, or
                # synthesize either side of the association.
                if issue.code != "SLD_EQUIPMENT_REFERENCE_UNRESOLVED":
                    raise ProjectPersistenceError(issue.message)
        for association in dynamic_models:
            if association.project_id != context.project_id:
                raise ProjectPersistenceError(f"Dynamic model association '{association.machine_id}' belongs to another project.")
            try:
                machine = network.get_by_identity(association.machine_id)
                bus = network.get_by_identity(association.bus_id)
            except KeyError as exc:
                raise ProjectPersistenceError(f"Dynamic model association references a missing Core object: {exc}") from exc
            if machine.element_type != "SYNCHRONOUS_MACHINE":
                raise ProjectPersistenceError(f"Dynamic model association '{association.machine_id}' does not reference a SynchronousMachine.")
            if bus.element_type != "BUS":
                raise ProjectPersistenceError(f"Dynamic model association '{association.bus_id}' does not reference a Bus.")
        if control_configuration is not None:
            if control_configuration.project_id != context.project_id: raise ProjectPersistenceError("Control configuration project_id does not match active project.")
            try: control_configuration.validate()
            except (TypeError,ValueError) as exc: raise ProjectPersistenceError(f"Invalid Control configuration: {exc}") from exc
        if protection_configuration is not None:
            if protection_configuration.project_id != context.project_id:
                raise ProjectPersistenceError("Protection configuration project_id does not match the active project.")
            for item in protection_configuration.elements:
                try:
                    protected_element = network.get_by_identity(item.element_id)
                    relay = network.get_by_identity(item.relay_id)
                except KeyError as exc:
                    raise ProjectPersistenceError(
                        f"Protection configuration '{item.element_id}' references a missing Core object: {exc}"
                    ) from exc
                if relay.element_type != "RELAY":
                    raise ProjectPersistenceError(
                        f"Protection configuration '{item.element_id}' relay_id does not reference a Relay."
                    )
                if not getattr(protected_element, "id", None):
                    raise ProjectPersistenceError(
                        f"Protection configuration '{item.element_id}' references an invalid protected object."
                    )

    @staticmethod
    def _recover_interrupted_save(package: Path) -> None:
        """Recover a previous valid package after an interrupted replacement."""
        parent = package.parent
        backup_candidates = sorted(
            parent.glob(f".{package.name}.backup.*"),
            key=lambda item: item.stat().st_mtime_ns,
            reverse=True,
        )
        if package.is_dir():
            # A completed replacement may leave its old backup behind if the
            # process stopped before cleanup. The installed package remains
            # authoritative; stale backups are safe to discard.
            for backup in backup_candidates:
                shutil.rmtree(backup, ignore_errors=True)
            return
        if not backup_candidates:
            return

        backup = backup_candidates[0]
        try:
            os.replace(backup, package)
        except OSError as exc:
            raise ProjectPersistenceError(
                f"Unable to recover the previous persisted project package: {package}"
            ) from exc
        for stale in backup_candidates[1:]:
            shutil.rmtree(stale, ignore_errors=True)

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        if not path.is_file(): raise ProjectPersistenceError(f"Required project file is missing: {path.name}")
        try:
            with path.open("r", encoding="utf-8") as handle: value = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc: raise ProjectPersistenceError(f"Unable to read {path.name}: {exc}") from exc
        if not isinstance(value, dict): raise ProjectPersistenceError(f"{path.name} must contain a JSON object.")
        return value

    @staticmethod
    def _write_json(path: Path, value: dict[str, Any]) -> None:
        try:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
        except (OSError, TypeError, ValueError) as exc: raise ProjectPersistenceError(f"Unable to write {path.name}: {exc}") from exc


__all__ = ["LoadedProject", "ProjectPersistenceError", "ProjectPersistenceService"]
