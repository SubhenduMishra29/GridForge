"""Project-scoped protection configuration and runtime composition state."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ProtectionFunctionConfiguration:
    """Immutable project association for one configured protection function."""

    element_id: str
    relay_id: str
    function_code: str
    settings: Mapping[str, Any] = field(default_factory=dict)
    input_channel_ids: Mapping[str, str] = field(default_factory=dict)
    enabled: bool = True
    blocked: bool = False
    priority: int = 0
    name: str = ""
    metadata: Mapping[str, Any] = field(default_factory=dict)
    action_target_type: str | None = None
    action_target_id: str | None = None
    action_type: str | None = None

    def __post_init__(self) -> None:
        for field_name in ("element_id", "relay_id", "function_code"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string.")
            object.__setattr__(self, field_name, value.strip())
        object.__setattr__(self, "function_code", self.function_code.upper())
        mapping_values = (self.action_target_type, self.action_target_id, self.action_type)
        if any(value is not None for value in mapping_values) and any(
            not isinstance(value, str) or not value.strip() for value in mapping_values
        ):
            raise ValueError("Protection action mapping requires target type, target ID, and action type together.")
        if all(value is not None for value in mapping_values):
            target_type = self.action_target_type.strip().lower()
            action_type = self.action_type.strip().lower()
            if target_type not in {"breaker", "switch", "disconnector", "fuse", "motor"}:
                raise ValueError(f"Unsupported protection action target type: {target_type!r}.")
            if action_type not in {"trip", "open", "close", "start", "stop", "blow", "reset", "put_in_service", "take_out_of_service"}:
                raise ValueError(f"Unsupported protection action type: {action_type!r}.")
            object.__setattr__(self, "action_target_type", target_type)
            object.__setattr__(self, "action_target_id", self.action_target_id.strip())
            object.__setattr__(self, "action_type", action_type)
        if isinstance(self.priority, bool) or not isinstance(self.priority, int):
            raise TypeError("priority must be an integer.")
        object.__setattr__(self, "settings", MappingProxyType(dict(self.settings)))
        object.__setattr__(self, "input_channel_ids", MappingProxyType(dict(self.input_channel_ids)))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_id": self.element_id,
            "relay_id": self.relay_id,
            "function_code": self.function_code,
            "settings": dict(self.settings),
            "input_channel_ids": dict(self.input_channel_ids),
            "enabled": self.enabled,
            "blocked": self.blocked,
            "priority": self.priority,
            "name": self.name,
            "metadata": dict(self.metadata),
            "action_target_type": self.action_target_type,
            "action_target_id": self.action_target_id,
            "action_type": self.action_type,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProtectionFunctionConfiguration":
        return cls(
            element_id=str(data["element_id"]), relay_id=str(data["relay_id"]),
            function_code=str(data["function_code"]), settings=dict(data.get("settings") or {}),
            input_channel_ids=dict(data.get("input_channel_ids") or {}), enabled=bool(data.get("enabled", True)),
            blocked=bool(data.get("blocked", False)), priority=int(data.get("priority", 0)),
            name=str(data.get("name", "")), metadata=dict(data.get("metadata") or {}),
            action_target_type=data.get("action_target_type"),
            action_target_id=data.get("action_target_id"),
            action_type=data.get("action_type"),
        )


class ProtectionProjectConfiguration:
    """Project-owned configuration aggregate; it owns no physical equipment."""

    def __init__(self, project_id: str) -> None:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id must be a non-empty string.")
        self._project_id = project_id.strip()
        self._elements: dict[str, ProtectionFunctionConfiguration] = {}

    @property
    def project_id(self) -> str:
        return self._project_id

    @property
    def elements(self) -> tuple[ProtectionFunctionConfiguration, ...]:
        return tuple(self._elements.values())

    def add(self, configuration: ProtectionFunctionConfiguration) -> None:
        if not isinstance(configuration, ProtectionFunctionConfiguration):
            raise TypeError("configuration must be ProtectionFunctionConfiguration.")
        if configuration.element_id in self._elements:
            raise ValueError(f"Protection element already configured: {configuration.element_id}")
        self._elements[configuration.element_id] = configuration

    def replace(self, configuration: ProtectionFunctionConfiguration) -> None:
        if not isinstance(configuration, ProtectionFunctionConfiguration):
            raise TypeError("configuration must be ProtectionFunctionConfiguration.")
        if configuration.element_id not in self._elements:
            raise KeyError(configuration.element_id)
        self._elements[configuration.element_id] = configuration

    def remove(self, element_id: str) -> ProtectionFunctionConfiguration:
        try: return self._elements.pop(element_id)
        except KeyError as exc: raise KeyError(f"Protection element is not configured: {element_id}") from exc

    def get(self, element_id: str) -> ProtectionFunctionConfiguration:
        try: return self._elements[element_id]
        except KeyError as exc: raise KeyError(f"Protection element is not configured: {element_id}") from exc

    def to_dict(self) -> dict[str, Any]:
        return {"project_id": self.project_id, "elements": [item.to_dict() for item in self.elements]}

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProtectionProjectConfiguration":
        result = cls(str(data["project_id"]))
        for item in data.get("elements", ()):
            result.add(ProtectionFunctionConfiguration.from_dict(item))
        return result


__all__ = ["ProtectionFunctionConfiguration", "ProtectionProjectConfiguration"]
