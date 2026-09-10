"""Canonical ``.gridforge`` project package persistence boundary.

Author: Subhendu Mishra

Persistence is deliberately outside the authoritative Core model. The package
stores a semantic project envelope plus authoritative Network engineering
objects. Object references are encoded by stable IDs so collection position
never becomes an engineering identity.
"""

from __future__ import annotations

import importlib
import json
import zipfile
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from core.network.network import Network


FORMAT_VERSION = 1


@dataclass
class Project:
    """Persistence root: metadata, authoritative Network and SLD data."""

    network: Network
    metadata: dict[str, Any] = field(default_factory=dict)
    sld_layout: dict[str, Any] = field(default_factory=dict)


class GridForgePackage:
    """Save/load the canonical ``project.gridforge`` package."""

    MANIFEST = "manifest.json"
    PROJECT = "project.json"

    @classmethod
    def save(cls, project: Project, path: str | Path) -> None:
        if not isinstance(project, Project):
            raise TypeError("project must be a Project.")
        if not isinstance(project.network, Network):
            raise TypeError("project.network must be a Network.")

        objects: dict[str, dict[str, Any]] = {}
        collections: dict[str, list[str]] = {}
        for element_type, values in cls._network_collections(project.network):
            ids: list[str] = []
            for element in values:
                object_id = cls._require_id(element)
                if object_id in objects:
                    raise ValueError(f"Duplicate persisted object ID: {object_id}")
                objects[object_id] = {
                    "type": element_type,
                    "class": f"{type(element).__module__}:{type(element).__qualname__}",
                    "state": cls._encode_state(cls._attributes(element)),
                }
                ids.append(object_id)
            collections[element_type] = ids

        payload = {
            "format_version": FORMAT_VERSION,
            "root": "Project",
            "metadata": cls._json_value(project.metadata),
            "sld_layout": cls._json_value(project.sld_layout),
            "network": {"collections": collections, "objects": objects},
        }
        manifest = {
            "format": "GridForge Project Package",
            "format_version": FORMAT_VERSION,
            "root": "Project",
            "engineering_units": "canonical model units; no unit inference",
        }

        target = Path(path)
        with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr(cls.MANIFEST, json.dumps(manifest, sort_keys=True, indent=2))
            archive.writestr(cls.PROJECT, json.dumps(payload, sort_keys=True, indent=2))

    @classmethod
    def load(cls, path: str | Path) -> Project:
        target = Path(path)
        with zipfile.ZipFile(target, "r") as archive:
            manifest = json.loads(archive.read(cls.MANIFEST).decode("utf-8"))
            payload = json.loads(archive.read(cls.PROJECT).decode("utf-8"))

        if manifest.get("root") != "Project" or payload.get("root") != "Project":
            raise ValueError("GridForge package root must be Project.")
        if manifest.get("format_version") != FORMAT_VERSION or payload.get("format_version") != FORMAT_VERSION:
            raise ValueError("Unsupported GridForge package format version.")

        object_specs = payload.get("network", {}).get("objects", {})
        if not isinstance(object_specs, dict):
            raise ValueError("project.json network.objects must be an object mapping.")

        objects: dict[str, Any] = {}
        for object_id, spec in object_specs.items():
            if not isinstance(spec, dict) or not isinstance(spec.get("class"), str):
                raise ValueError(f"Invalid persisted object specification: {object_id}")
            objects[str(object_id)] = cls._allocate(spec["class"])

        for object_id, spec in object_specs.items():
            state = cls._decode_state(spec.get("state", {}), objects)
            cls._restore_state(objects[str(object_id)], state)

        network = Network()
        collections = payload.get("network", {}).get("collections", {})
        for element_type, ids in collections.items():
            add_method = getattr(network, f"add_{element_type}", None)
            if add_method is None:
                raise ValueError(f"Unsupported persisted Network collection: {element_type}")
            for object_id in ids:
                if str(object_id) not in objects:
                    raise ValueError(f"Persisted object reference is missing: {object_id}")
                add_method(objects[str(object_id)])

        # Topology and indexing are derived from authoritative objects and are
        # deliberately rebuilt rather than persisted as another source of truth.
        network.rebuild_topology()
        network.ensure_bus_index()
        return Project(
            network=network,
            metadata=dict(payload.get("metadata", {})),
            sld_layout=dict(payload.get("sld_layout", {})),
        )

    @staticmethod
    def _attributes(value: Any) -> dict[str, Any]:
        attributes: dict[str, Any] = {}
        if hasattr(value, "__dict__"):
            attributes.update(vars(value))
        for base in type(value).__mro__:
            slots = getattr(base, "__slots__", ())
            if isinstance(slots, str):
                slots = (slots,)
            for name in slots:
                if name in {"__dict__", "__weakref__"}:
                    continue
                try:
                    attributes[name] = getattr(value, name)
                except AttributeError:
                    pass
        return attributes

    @staticmethod
    def _restore_state(value: Any, state: Mapping[str, Any]) -> None:
        for name, item in state.items():
            setattr(value, name, item)

    @staticmethod
    def _require_id(element: Any) -> str:
        object_id = getattr(element, "id", None)
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValueError("Persisted Network elements require a non-empty string id.")
        return object_id

    @staticmethod
    def _network_collections(network: Network):
        names = (
            "bus", "grid", "generator", "synchronous_machine", "load", "motor",
            "shunt", "capacitor", "reactor", "solar", "battery", "current_transformer",
            "potential_transformer", "capacitive_voltage_transformer", "line", "cable",
            "transformer", "breaker", "switch", "disconnector", "fuse",
        )
        for name in names:
            yield name, getattr(network, f"{name}s", ())

    @classmethod
    def _encode_state(cls, value: Any) -> Any:
        if isinstance(value, Enum):
            return {"$enum": f"{type(value).__module__}:{type(value).__qualname__}", "value": value.value}
        if hasattr(value, "id") and isinstance(getattr(value, "id"), str):
            return {"$ref": value.id}
        if isinstance(value, dict):
            return {"$dict": [[cls._encode_state(k), cls._encode_state(v)] for k, v in value.items()]}
        if isinstance(value, (list, tuple)):
            return {"$tuple": [cls._encode_state(v) for v in value]}
        if isinstance(value, set):
            return {"$set": [cls._encode_state(v) for v in sorted(value, key=str)]}
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if hasattr(value, "__dict__") or hasattr(type(value), "__slots__"):
            return {
                "$object": f"{type(value).__module__}:{type(value).__qualname__}",
                "state": cls._encode_state(cls._attributes(value)),
            }
        raise TypeError(f"Unsupported persisted value type: {type(value)!r}")

    @classmethod
    def _decode_state(cls, value: Any, objects: Mapping[str, Any]) -> Any:
        if isinstance(value, dict):
            if "$ref" in value:
                try:
                    return objects[str(value["$ref"])]
                except KeyError as exc:
                    raise ValueError(f"Unknown persisted object reference: {value['$ref']}") from exc
            if "$enum" in value:
                enum_type = cls._resolve_type(value["$enum"])
                return enum_type(value["value"])
            if "$dict" in value:
                return {cls._decode_state(k, objects): cls._decode_state(v, objects) for k, v in value["$dict"]}
            if "$tuple" in value:
                return tuple(cls._decode_state(v, objects) for v in value["$tuple"])
            if "$set" in value:
                return set(cls._decode_state(v, objects) for v in value["$set"])
            if "$object" in value:
                obj = cls._allocate(value["$object"])
                cls._restore_state(obj, cls._decode_state(value.get("state", {}), objects))
                return obj
            return {k: cls._decode_state(v, objects) for k, v in value.items()}
        return value

    @staticmethod
    def _allocate(class_path: str) -> Any:
        cls = GridForgePackage._resolve_type(class_path)
        return cls.__new__(cls)

    @staticmethod
    def _resolve_type(class_path: str) -> type[Any]:
        module_name, separator, qualname = class_path.partition(":")
        if not separator or not module_name or not qualname:
            raise ValueError(f"Invalid persisted class path: {class_path!r}")
        value: Any = importlib.import_module(module_name)
        for part in qualname.split("."):
            value = getattr(value, part)
        if not isinstance(value, type):
            raise TypeError(f"Persisted class path is not a type: {class_path!r}")
        return value

    @staticmethod
    def _json_value(value: Any) -> Any:
        try:
            json.dumps(value)
        except TypeError as exc:
            raise TypeError("Project metadata and SLD layout must be JSON-compatible.") from exc
        return value


__all__ = ["FORMAT_VERSION", "GridForgePackage", "Project"]
