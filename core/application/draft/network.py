# ============================================================
# File: core/application/draft/network.py
# GridForge V2
# Author: Subhendu Mishra
# ============================================================
"""Application-owned SLD authoring state; never authoritative Core state."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class DraftEndpointReference:
    """Stable authoring identity for a draft terminal or a Bus attachment."""
    kind: str
    object_id: str
    terminal_role: str | None = None
    attachment_id: str | None = None
    equipment_type: str | None = None

    def __post_init__(self) -> None:
        if self.kind not in {"terminal", "bus"}:
            raise ValueError("Draft endpoint kind must be 'terminal' or 'bus'.")
        if not isinstance(self.object_id, str) or not self.object_id.strip():
            raise ValueError("Draft endpoint object_id must be non-empty.")
        object.__setattr__(self, "object_id", self.object_id.strip())
        if self.kind == "terminal":
            if not isinstance(self.terminal_role, str) or not self.terminal_role.strip():
                raise ValueError("Draft terminal endpoint requires terminal_role.")
            if not isinstance(self.equipment_type, str) or not self.equipment_type.strip():
                raise ValueError("Draft terminal endpoint requires equipment_type.")
            if self.attachment_id is not None:
                raise ValueError("Draft terminal endpoint cannot carry attachment_id.")
            object.__setattr__(self, "terminal_role", self.terminal_role.strip())
            object.__setattr__(self, "equipment_type", self.equipment_type.strip().lower())
        else:
            if not isinstance(self.attachment_id, str) or not self.attachment_id.strip():
                raise ValueError("Draft Bus endpoint requires attachment_id.")
            if self.terminal_role is not None or self.equipment_type is not None:
                raise ValueError("Draft Bus endpoint cannot carry terminal identity.")
            object.__setattr__(self, "attachment_id", self.attachment_id.strip())

    @classmethod
    def terminal(cls, *, draft_id: str, equipment_type: str, terminal_role: str) -> "DraftEndpointReference":
        return cls("terminal", draft_id, terminal_role=terminal_role, equipment_type=equipment_type)

    @classmethod
    def bus(cls, *, bus_id: str, attachment_id: str) -> "DraftEndpointReference":
        return cls("bus", bus_id, attachment_id=attachment_id)

    @property
    def is_terminal(self) -> bool: return self.kind == "terminal"
    @property
    def is_bus(self) -> bool: return self.kind == "bus"

    def to_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "object_id": self.object_id, "terminal_role": self.terminal_role,
                "attachment_id": self.attachment_id, "equipment_type": self.equipment_type}

    @classmethod
    def from_value(cls, value: Any) -> "DraftEndpointReference":
        if isinstance(value, cls): return value
        if not isinstance(value, Mapping): raise TypeError("Draft endpoint must be a mapping or DraftEndpointReference.")
        return cls(str(value["kind"]), str(value["object_id"]), value.get("terminal_role"), value.get("attachment_id"), value.get("equipment_type"))




@dataclass(frozen=True, slots=True)
class DraftEquipment:
    draft_id: str
    equipment_type: str
    display_name: str
    terminal_contract: tuple[str, ...]
    engineering_data: Mapping[str, Any] = field(default_factory=dict)
    endpoints: Mapping[str, DraftEndpointReference] = field(default_factory=dict)
    placement: tuple[float, float] | None = None
    presentation: Mapping[str, Any] = field(default_factory=dict)
    validation_state: Mapping[str, Any] = field(default_factory=dict)
    command_type: str = ""
    id_field: str = ""
    parameter_mapping: Mapping[str, str] = field(default_factory=dict)
    endpoint_mapping: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.draft_id.strip() or not self.equipment_type.strip(): raise ValueError("Draft equipment identity is required.")
        if not self.command_type.strip() or not self.id_field.strip(): raise ValueError("DraftEquipment requires its canonical command contract.")
        object.__setattr__(self, "terminal_contract", tuple(str(x) for x in self.terminal_contract))
        object.__setattr__(self, "engineering_data", MappingProxyType(dict(self.engineering_data)))
        object.__setattr__(self, "endpoints", MappingProxyType({str(k): DraftEndpointReference.from_value(v) for k, v in self.endpoints.items()}))
        object.__setattr__(self, "presentation", MappingProxyType(dict(self.presentation)))
        object.__setattr__(self, "validation_state", MappingProxyType(dict(self.validation_state)))
        object.__setattr__(self, "parameter_mapping", MappingProxyType(dict(self.parameter_mapping)))
        object.__setattr__(self, "endpoint_mapping", MappingProxyType(dict(self.endpoint_mapping)))

    def to_dict(self) -> dict[str, Any]:
        return {"draft_id": self.draft_id, "equipment_type": self.equipment_type, "display_name": self.display_name,
                "terminal_contract": list(self.terminal_contract), "engineering_data": deepcopy(dict(self.engineering_data)),
                "endpoints": {k: v.to_dict() for k, v in self.endpoints.items()},
                "placement": None if self.placement is None else list(self.placement),
                "presentation": deepcopy(dict(self.presentation)), "validation_state": deepcopy(dict(self.validation_state)),
                "command_type": self.command_type, "id_field": self.id_field,
                "parameter_mapping": dict(self.parameter_mapping), "endpoint_mapping": dict(self.endpoint_mapping)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DraftEquipment":
        placement = data.get("placement")
        return cls(str(data["draft_id"]), str(data["equipment_type"]), str(data.get("display_name", data["equipment_type"])),
                    tuple(str(x) for x in data.get("terminal_contract", ())), dict(data.get("engineering_data", {})),
                    {k: DraftEndpointReference.from_value(v) for k, v in dict(data.get("endpoints", {})).items()},
                    None if placement is None else (float(placement[0]), float(placement[1])), dict(data.get("presentation", {})),
                    dict(data.get("validation_state", {})), str(data["command_type"]), str(data["id_field"]),
                    dict(data.get("parameter_mapping", {})), dict(data.get("endpoint_mapping", {})))


@dataclass(frozen=True, slots=True)
class DraftConnection:
    """One immutable connection whose endpoints are the canonical draft identities."""
    connection_id: str
    source: DraftEndpointReference
    target: DraftEndpointReference
    connection_kind: str = "simple_wire"
    route: Mapping[str, Any] = field(default_factory=dict)
    validation_state: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.connection_id, str) or not self.connection_id.strip(): raise ValueError("Draft connection_id is required.")
        object.__setattr__(self, "source", DraftEndpointReference.from_value(self.source))
        object.__setattr__(self, "target", DraftEndpointReference.from_value(self.target))
        if self.source == self.target: raise ValueError("Draft connection endpoints must be distinct.")
        object.__setattr__(self, "connection_id", self.connection_id.strip())
        object.__setattr__(self, "connection_kind", str(self.connection_kind).strip().lower())
        object.__setattr__(self, "route", MappingProxyType(dict(self.route)))
        object.__setattr__(self, "validation_state", MappingProxyType(dict(self.validation_state)))

    @property
    def source_draft_id(self) -> str: return self.source.object_id
    @property
    def target_draft_id(self) -> str: return self.target.object_id
    @property
    def source_terminal(self) -> str | None: return self.source.terminal_role
    @property
    def target_terminal(self) -> str | None: return self.target.terminal_role

    def to_dict(self) -> dict[str, Any]:
        return {"connection_id": self.connection_id, "source": self.source.to_dict(), "target": self.target.to_dict(),
                "connection_kind": self.connection_kind, "route": deepcopy(dict(self.route)), "validation_state": deepcopy(dict(self.validation_state))}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DraftConnection":
        # Reject the former dual-source representation instead of silently
        # maintaining two independent endpoint identities.
        if "source" not in data or "target" not in data:
            raise ValueError("DraftConnection requires canonical source and target DraftEndpointReference values.")
        return cls(str(data["connection_id"]), DraftEndpointReference.from_value(data["source"]), DraftEndpointReference.from_value(data["target"]),
                    str(data.get("connection_kind", "simple_wire")), dict(data.get("route", {})), dict(data.get("validation_state", {})))


class DraftNetwork:
    SCHEMA = 2
    def __init__(self, project_id: str, activation_generation: int):
        if not str(project_id).strip() or int(activation_generation) < 1: raise ValueError("DraftNetwork requires valid project scope.")
        self.project_id = str(project_id); self.activation_generation = int(activation_generation)
        self._equipment: dict[str, DraftEquipment] = {}; self._connections: dict[str, DraftConnection] = {}; self.validation_state: dict[str, Any] = {}

    @property
    def equipment(self) -> tuple[DraftEquipment, ...]: return tuple(self._equipment.values())
    @property
    def connections(self) -> tuple[DraftConnection, ...]: return tuple(self._connections.values())
    def require_equipment(self, draft_id: str) -> DraftEquipment: return self._equipment[draft_id]

    def add_equipment(self, equipment: DraftEquipment) -> None:
        if equipment.draft_id in self._equipment: raise ValueError(f"Draft equipment already exists: {equipment.draft_id}")
        self._equipment[equipment.draft_id] = equipment; self.validation_state = {}

    def update_equipment(self, draft_id: str, **changes: Any) -> DraftEquipment:
        current = self.require_equipment(draft_id); allowed = {"display_name","engineering_data","endpoints","placement","presentation","validation_state"}
        unknown = set(changes) - allowed
        if unknown: raise ValueError(f"Unsupported DraftEquipment fields: {sorted(unknown)!r}")
        values = {name: getattr(current, name) for name in ("draft_id","equipment_type","display_name","terminal_contract","engineering_data","endpoints","placement","presentation","validation_state","command_type","id_field","parameter_mapping","endpoint_mapping")}
        values.update(changes); updated = DraftEquipment(**values); self._equipment[draft_id] = updated; self.validation_state = {}; return updated

    def remove_equipment(self, draft_id: str) -> DraftEquipment:
        equipment = self._equipment.pop(draft_id)
        for cid, connection in tuple(self._connections.items()):
            if (connection.source.is_terminal and connection.source.object_id == draft_id) or (connection.target.is_terminal and connection.target.object_id == draft_id):
                self._connections.pop(cid)
        self.validation_state = {}; return equipment

    def _validate_endpoint(self, endpoint: DraftEndpointReference, *, connection_id: str | None = None) -> None:
        prefix = f"{connection_id}: " if connection_id else ""
        if endpoint.is_bus:
            if not endpoint.attachment_id: raise ValueError(f"{prefix}Bus endpoint attachment is missing.")
            return
        equipment = self._equipment.get(endpoint.object_id)
        if equipment is None: raise ValueError(f"{prefix}unknown draft equipment {endpoint.object_id!r}.")
        if endpoint.terminal_role not in equipment.terminal_contract: raise ValueError(f"{prefix}unknown terminal role {endpoint.terminal_role!r} for {endpoint.object_id!r}.")
        declared = equipment.endpoints.get(endpoint.terminal_role)
        if declared is not None and declared != endpoint: raise ValueError(f"{prefix}terminal identity mapping is contradictory.")

    def add_connection(self, connection: DraftConnection) -> None:
        if connection.connection_id in self._connections: raise ValueError(f"Draft connection already exists: {connection.connection_id}")
        if connection.connection_kind != "simple_wire": raise ValueError("Only simple_wire DraftConnection is supported by the canonical authoring contract.")
        self._validate_endpoint(connection.source, connection_id=connection.connection_id)
        self._validate_endpoint(connection.target, connection_id=connection.connection_id)
        self._connections[connection.connection_id] = connection; self.validation_state = {}

    def remove_connection(self, connection_id: str) -> DraftConnection:
        return self._connections.pop(connection_id)

    def validate(self) -> tuple[str, ...]:
        errors: list[str] = []
        seen_pairs: set[tuple[DraftEndpointReference, DraftEndpointReference]] = set()
        for item in self._equipment.values():
            if item.placement is None: errors.append(f"{item.draft_id}: placement is required.")
            if len(set(item.terminal_contract)) != len(item.terminal_contract): errors.append(f"{item.draft_id}: duplicate terminal role in contract.")
            for role, endpoint in item.endpoints.items():
                if role not in item.terminal_contract: errors.append(f"{item.draft_id}: endpoint role {role!r} is not canonical.")
                if endpoint != DraftEndpointReference.terminal(draft_id=item.draft_id, equipment_type=item.equipment_type, terminal_role=role):
                    errors.append(f"{item.draft_id}: endpoint mapping for {role!r} is inconsistent with DraftEquipment identity.")
        for item in self._connections.values():
            try:
                self._validate_endpoint(item.source, connection_id=item.connection_id); self._validate_endpoint(item.target, connection_id=item.connection_id)
            except (KeyError, TypeError, ValueError) as exc: errors.append(str(exc)); continue
            pair = tuple(sorted((item.source, item.target), key=lambda x: x.to_dict().__repr__()))
            if pair in seen_pairs: errors.append(f"{item.connection_id}: duplicate endpoint pair.")
            seen_pairs.add(pair)
            if item.source == item.target: errors.append(f"{item.connection_id}: self-connection is invalid.")
        self.validation_state = {"errors": tuple(errors), "valid": not errors}
        return tuple(errors)

    def clear_after_commit(self) -> None: self._equipment.clear(); self._connections.clear(); self.validation_state = {}
    def restore_snapshot(self, snapshot: Mapping[str, Any]) -> None:
        restored = DraftNetwork.from_dict(snapshot, project_id=self.project_id, activation_generation=self.activation_generation)
        self._equipment = restored._equipment; self._connections = restored._connections; self.validation_state = restored.validation_state
    def to_dict(self) -> dict[str, Any]: return {"schema": self.SCHEMA, "project_id": self.project_id, "activation_generation": self.activation_generation, "equipment": [x.to_dict() for x in self.equipment], "connections": [x.to_dict() for x in self.connections], "validation_state": deepcopy(self.validation_state)}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any], *, project_id: str, activation_generation: int) -> "DraftNetwork":
        if data.get("project_id", project_id) != project_id: raise ValueError("DraftNetwork project_id does not match project metadata.")
        if data.get("activation_generation") is not None and int(data["activation_generation"]) > activation_generation: raise ValueError("DraftNetwork generation is newer than active project generation.")
        draft = cls(project_id, activation_generation)
        for item in data.get("equipment", ()): draft.add_equipment(DraftEquipment.from_dict(item))
        for item in data.get("connections", ()): draft.add_connection(DraftConnection.from_dict(item))
        draft.validation_state = dict(data.get("validation_state", {})); return draft

    @classmethod
    def empty(cls, project_id: str, activation_generation: int) -> "DraftNetwork": return cls(project_id, activation_generation)


__all__ = ["DraftEndpointReference", "DraftEquipment", "DraftConnection", "DraftNetwork"]
