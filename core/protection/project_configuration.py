"""Project-scoped protection configuration and runtime composition state."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
from types import MappingProxyType
from typing import Any, Mapping

from .protection_measurement_binding import ProtectionMeasurementBinding


def _freeze_value(value: Any) -> Any:
    """Recursively detach and freeze JSON-like configuration containers."""
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze_value(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_value(item) for item in value)
    return value


def _thaw_value(value: Any) -> Any:
    """Return detached plain containers suitable for persistence/serialization."""
    if isinstance(value, Mapping):
        return {key: _thaw_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_thaw_value(item) for item in value]
    return value


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
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a boolean.")
        if not isinstance(self.blocked, bool):
            raise TypeError("blocked must be a boolean.")
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
        for field_name in ("settings", "input_channel_ids", "metadata"):
            value = getattr(self, field_name)
            if not isinstance(value, Mapping):
                raise TypeError(f"{field_name} must be a mapping.")
        def validate_setting_value(value: Any, path: str) -> None:
            if value is None or isinstance(value, (str, bool, int)):
                return
            if isinstance(value, float):
                if not math.isfinite(value):
                    raise ValueError(f"{path} must not contain NaN or infinity.")
                return
            if isinstance(value, Mapping):
                for nested_key, nested_value in value.items():
                    if not isinstance(nested_key, str) or not nested_key.strip():
                        raise ValueError(f"{path} mapping keys must be non-empty strings.")
                    validate_setting_value(nested_value, f"{path}.{nested_key}")
                return
            if isinstance(value, (list, tuple)):
                for index, nested_value in enumerate(value):
                    validate_setting_value(nested_value, f"{path}[{index}]")
                return
            raise TypeError(f"{path} contains unsupported setting value type: {type(value).__name__}.")

        for setting_name, setting_value in self.settings.items():
            if not isinstance(setting_name, str) or not setting_name.strip():
                raise ValueError("setting names must be non-empty strings.")
            validate_setting_value(setting_value, f"settings.{setting_name}")
        for input_name, channel_id in self.input_channel_ids.items():
            if not isinstance(input_name, str) or not input_name.strip():
                raise ValueError("input_channel_ids keys must be non-empty strings.")
            if not isinstance(channel_id, str) or not channel_id.strip():
                raise ValueError("input_channel_ids values must be non-empty strings.")
            if channel_id != channel_id.strip():
                raise ValueError("input channel IDs must not contain surrounding whitespace.")
        for metadata_key in self.metadata:
            if not isinstance(metadata_key, str) or not metadata_key.strip():
                raise ValueError("metadata keys must be non-empty strings.")
        object.__setattr__(self, "settings", _freeze_value(self.settings))
        object.__setattr__(self, "input_channel_ids", MappingProxyType(dict(self.input_channel_ids)))
        object.__setattr__(self, "metadata", _freeze_value(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "element_id": self.element_id,
            "relay_id": self.relay_id,
            "function_code": self.function_code,
            "settings": _thaw_value(self.settings),
            "input_channel_ids": dict(self.input_channel_ids),
            "enabled": self.enabled,
            "blocked": self.blocked,
            "priority": self.priority,
            "name": self.name,
            "metadata": _thaw_value(self.metadata),
            "action_target_type": self.action_target_type,
            "action_target_id": self.action_target_id,
            "action_type": self.action_type,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProtectionFunctionConfiguration":
        if not isinstance(data, Mapping):
            raise TypeError("protection function configuration must be a mapping.")
        enabled = data.get("enabled", True)
        blocked = data.get("blocked", False)
        if not isinstance(enabled, bool):
            raise TypeError("enabled must be a boolean.")
        if not isinstance(blocked, bool):
            raise TypeError("blocked must be a boolean.")
        mapping_fields = ("settings", "input_channel_ids", "metadata")
        for field_name in mapping_fields:
            value = data.get(field_name)
            if value is not None and not isinstance(value, Mapping):
                raise TypeError(f"{field_name} must be a mapping.")
        return cls(
            element_id=data["element_id"], relay_id=data["relay_id"],
            function_code=data["function_code"], settings=dict(data.get("settings") or {}),
            input_channel_ids=dict(data.get("input_channel_ids") or {}), enabled=enabled,
            blocked=blocked, priority=data.get("priority", 0),
            name=str(data.get("name", "")), metadata=dict(data.get("metadata") or {}),
            action_target_type=data.get("action_target_type"),
            action_target_id=data.get("action_target_id"),
            action_type=data.get("action_type"),
        )


@dataclass(frozen=True, slots=True)
class DifferentialProtectionSchemeConfiguration:
    """Explicit differential-scheme membership, independent of CT placement."""

    scheme_id: str
    protected_object_type: str
    protected_object_id: str
    measurement_binding_ids: tuple[str, ...]
    phase_compensation_degrees: Mapping[str, float] = field(default_factory=dict)
    enabled: bool = True
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("scheme_id", "protected_object_type", "protected_object_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())
        object.__setattr__(self, "protected_object_type", self.protected_object_type.lower())
        if self.protected_object_type not in {"bus", "transformer", "line", "generator", "motor", "reactor"}:
            raise ValueError("Differential scheme protected_object_type is unsupported.")
        if not isinstance(self.measurement_binding_ids, (tuple, list)):
            raise TypeError("measurement_binding_ids must be a tuple or list.")
        binding_ids = tuple(self.measurement_binding_ids)
        if len(binding_ids) < 2:
            raise ValueError("A differential scheme requires at least two explicitly configured CT measurement bindings.")
        if any(not isinstance(item, str) or not item.strip() for item in binding_ids):
            raise ValueError("Every differential measurement binding ID must be non-empty.")
        binding_ids = tuple(item.strip() for item in binding_ids)
        if len(set(binding_ids)) != len(binding_ids):
            raise ValueError("Differential scheme measurement binding IDs must be unique.")
        object.__setattr__(self, "measurement_binding_ids", binding_ids)
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be a boolean.")
        if not isinstance(self.phase_compensation_degrees, Mapping):
            raise TypeError("phase_compensation_degrees must be a mapping.")
        compensation = {}
        for binding_id, degrees in self.phase_compensation_degrees.items():
            if binding_id not in binding_ids:
                raise ValueError("Phase compensation may reference only a member measurement binding.")
            value = float(degrees)
            if not math.isfinite(value):
                raise ValueError("Phase compensation degrees must be finite.")
            compensation[binding_id] = value
        object.__setattr__(self, "phase_compensation_degrees", MappingProxyType(compensation))
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", _freeze_value(self.metadata))

    def to_dict(self) -> dict[str, Any]:
        return {
            "scheme_id": self.scheme_id,
            "protected_object_type": self.protected_object_type,
            "protected_object_id": self.protected_object_id,
            "measurement_binding_ids": list(self.measurement_binding_ids),
            "phase_compensation_degrees": dict(self.phase_compensation_degrees),
            "enabled": self.enabled,
            "metadata": _thaw_value(self.metadata),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "DifferentialProtectionSchemeConfiguration":
        if not isinstance(data, Mapping):
            raise TypeError("differential protection scheme configuration must be a mapping.")
        return cls(
            scheme_id=data["scheme_id"],
            protected_object_type=data["protected_object_type"],
            protected_object_id=data["protected_object_id"],
            measurement_binding_ids=tuple(data["measurement_binding_ids"]),
            phase_compensation_degrees=dict(data.get("phase_compensation_degrees") or {}),
            enabled=data.get("enabled", True),
            metadata=dict(data.get("metadata") or {}),
        )


class ProtectionProjectConfiguration:
    """Project-owned configuration aggregate; it owns no physical equipment."""

    def __init__(self, project_id: str) -> None:
        if not isinstance(project_id, str) or not project_id.strip():
            raise ValueError("project_id must be a non-empty string.")
        self._project_id = project_id.strip()
        self._elements: dict[str, ProtectionFunctionConfiguration] = {}
        self._bindings: dict[str, ProtectionMeasurementBinding] = {}
        self._differential_schemes: dict[str, DifferentialProtectionSchemeConfiguration] = {}

    @property
    def project_id(self) -> str:
        return self._project_id

    @property
    def elements(self) -> tuple[ProtectionFunctionConfiguration, ...]:
        return tuple(self._elements.values())

    @property
    def measurement_bindings(self) -> tuple[ProtectionMeasurementBinding, ...]:
        return tuple(self._bindings.values())

    @property
    def differential_schemes(self) -> tuple[DifferentialProtectionSchemeConfiguration, ...]:
        return tuple(self._differential_schemes.values())

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
        for binding in self._bindings.values():
            if binding.protection_element_id == configuration.element_id:
                if configuration.input_channel_ids.get(binding.relay_input_id) != binding.channel_id:
                    raise ValueError(
                        "Cannot change an input channel while a canonical measurement binding references it."
                    )
        self._elements[configuration.element_id] = configuration

    def remove(self, element_id: str) -> ProtectionFunctionConfiguration:
        if any(binding.protection_element_id == element_id for binding in self._bindings.values()):
            raise ValueError(
                f"Cannot remove protection element {element_id!r} while measurement bindings reference it."
            )
        try:
            return self._elements.pop(element_id)
        except KeyError as exc:
            raise KeyError(f"Protection element is not configured: {element_id}") from exc

    def get(self, element_id: str) -> ProtectionFunctionConfiguration:
        try: return self._elements[element_id]
        except KeyError as exc: raise KeyError(f"Protection element is not configured: {element_id}") from exc

    def add_measurement_binding(self, binding: ProtectionMeasurementBinding) -> None:
        if not isinstance(binding, ProtectionMeasurementBinding):
            raise TypeError("binding must be ProtectionMeasurementBinding.")
        if binding.binding_id in self._bindings:
            raise ValueError(f"Protection measurement binding already exists: {binding.binding_id}")
        configuration = self.get(binding.protection_element_id)
        if configuration.input_channel_ids.get(binding.relay_input_id) != binding.channel_id:
            raise ValueError(
                "Protection measurement binding must match the configured element input channel."
            )
        if any(
            existing.protection_element_id == binding.protection_element_id
            and existing.relay_input_id == binding.relay_input_id
            for existing in self._bindings.values()
        ):
            raise ValueError(
                "A protection element input may have only one canonical measurement binding."
            )
        self._bindings[binding.binding_id] = binding

    def replace_measurement_binding(self, binding: ProtectionMeasurementBinding) -> None:
        if not isinstance(binding, ProtectionMeasurementBinding):
            raise TypeError("binding must be ProtectionMeasurementBinding.")
        if binding.binding_id not in self._bindings:
            raise KeyError(binding.binding_id)
        if (
            binding.measurement_type.strip().lower() != "current"
            and any(binding.binding_id in scheme.measurement_binding_ids for scheme in self._differential_schemes.values())
        ):
            raise ValueError("A differential scheme member must remain a current measurement binding.")
        configuration = self.get(binding.protection_element_id)
        if configuration.input_channel_ids.get(binding.relay_input_id) != binding.channel_id:
            raise ValueError(
                "Protection measurement binding must match the configured element input channel."
            )
        if any(
            key != binding.binding_id
            and existing.protection_element_id == binding.protection_element_id
            and existing.relay_input_id == binding.relay_input_id
            for key, existing in self._bindings.items()
        ):
            raise ValueError("A protection element input may have only one canonical measurement binding.")
        self._bindings[binding.binding_id] = binding

    def get_measurement_binding(self, binding_id: str) -> ProtectionMeasurementBinding:
        try:
            return self._bindings[binding_id]
        except KeyError as exc:
            raise KeyError(f"Protection measurement binding not found: {binding_id}") from exc

    def add_differential_scheme(self, scheme: DifferentialProtectionSchemeConfiguration) -> None:
        if not isinstance(scheme, DifferentialProtectionSchemeConfiguration):
            raise TypeError("scheme must be DifferentialProtectionSchemeConfiguration.")
        if scheme.scheme_id in self._differential_schemes:
            raise ValueError(f"Differential scheme already exists: {scheme.scheme_id}")
        for binding_id in scheme.measurement_binding_ids:
            binding = self.get_measurement_binding(binding_id)
            if binding.measurement_type.strip().lower() != "current":
                raise ValueError(f"Differential scheme member {binding_id!r} must be a current measurement binding.")
        self._differential_schemes[scheme.scheme_id] = scheme

    def replace_differential_scheme(self, scheme: DifferentialProtectionSchemeConfiguration) -> None:
        if not isinstance(scheme, DifferentialProtectionSchemeConfiguration):
            raise TypeError("scheme must be DifferentialProtectionSchemeConfiguration.")
        if scheme.scheme_id not in self._differential_schemes:
            raise KeyError(scheme.scheme_id)
        for binding_id in scheme.measurement_binding_ids:
            binding = self.get_measurement_binding(binding_id)
            if binding.measurement_type.strip().lower() != "current":
                raise ValueError("Differential scheme members must be current measurement bindings.")
        self._differential_schemes[scheme.scheme_id] = scheme

    def get_differential_scheme(self, scheme_id: str) -> DifferentialProtectionSchemeConfiguration:
        try:
            return self._differential_schemes[scheme_id]
        except KeyError as exc:
            raise KeyError(f"Differential protection scheme not found: {scheme_id}") from exc

    def remove_differential_scheme(self, scheme_id: str) -> DifferentialProtectionSchemeConfiguration:
        try:
            return self._differential_schemes.pop(scheme_id)
        except KeyError as exc:
            raise KeyError(f"Differential protection scheme not found: {scheme_id}") from exc

    def remove_measurement_binding(self, binding_id: str) -> ProtectionMeasurementBinding:
        if any(binding_id in scheme.measurement_binding_ids for scheme in self._differential_schemes.values()):
            raise ValueError(f"Cannot remove measurement binding {binding_id!r} while a differential scheme references it.")
        try:
            return self._bindings.pop(binding_id)
        except KeyError as exc:
            raise KeyError(f"Protection measurement binding not found: {binding_id}") from exc

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "elements": [item.to_dict() for item in self.elements],
            "measurement_bindings": [item.to_dict() for item in self.measurement_bindings],
            "differential_schemes": [item.to_dict() for item in self.differential_schemes],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ProtectionProjectConfiguration":
        if not isinstance(data, Mapping):
            raise TypeError("protection project configuration must be a mapping.")
        project_id = data["project_id"]
        elements = data.get("elements", ())
        if not isinstance(elements, (list, tuple)):
            raise TypeError("protection configuration elements must be a list or tuple.")
        result = cls(project_id)
        for item in elements:
            result.add(ProtectionFunctionConfiguration.from_dict(item))
        bindings = data.get("measurement_bindings", ())
        if not isinstance(bindings, (list, tuple)):
            raise TypeError("protection measurement bindings must be a list or tuple.")
        for item in bindings:
            result.add_measurement_binding(ProtectionMeasurementBinding.from_dict(item))
        schemes = data.get("differential_schemes", ())
        if not isinstance(schemes, (list, tuple)):
            raise TypeError("differential_schemes must be a list or tuple.")
        for item in schemes:
            result.add_differential_scheme(DifferentialProtectionSchemeConfiguration.from_dict(item))
        return result


__all__ = ["ProtectionFunctionConfiguration", "DifferentialProtectionSchemeConfiguration", "ProtectionProjectConfiguration"]
