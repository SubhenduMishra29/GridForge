# ============================================================
# File: ui/tools/tool_settings.py
# GridForge V2 — Canonical Typed Tool Settings
# ============================================================
"""Qt-independent schema and immutable values for contextual tool settings."""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ToolSettingDefinition:
    """Typed metadata for one interaction setting; never an equipment property."""

    label: str
    value_type: str
    default: Any
    editable: bool = True
    unit: str | None = None
    choices: tuple[Any, ...] = ()
    minimum: float | None = None
    maximum: float | None = None
    step: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("setting label must be a non-empty string.")
        if self.value_type not in {"bool", "int", "float", "str", "choice"}:
            raise ValueError("value_type must be bool, int, float, str or choice.")
        if not isinstance(self.editable, bool):
            raise TypeError("editable must be bool.")
        if self.unit is not None and (not isinstance(self.unit, str) or not self.unit.strip()):
            raise ValueError("unit must be None or a non-empty string.")
        choices = tuple(self.choices)
        object.__setattr__(self, "choices", choices)
        if self.value_type == "choice" and not choices:
            raise ValueError("choice settings require at least one choice.")
        if self.value_type != "choice" and choices:
            raise ValueError("choices are supported only for choice settings.")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("minimum cannot exceed maximum.")
        if self.step is not None and (not math.isfinite(float(self.step)) or self.step <= 0):
            raise ValueError("step must be finite and positive.")
        self.validate(self.default)

        for name in ("minimum", "maximum", "step"):
            bound = getattr(self, name)
            if bound is not None:
                if self.value_type not in {"int", "float"}:
                    raise ValueError(f"{name} is valid only for numeric settings.")
                if isinstance(bound, bool) or not isinstance(bound, (int, float)) or not math.isfinite(float(bound)):
                    raise ValueError(f"{name} must be a finite number.")
        if self.value_type == "int" and any(
            isinstance(getattr(self, name), float) and not float(getattr(self, name)).is_integer()
            for name in ("minimum", "maximum", "step") if getattr(self, name) is not None
        ):
            raise ValueError("integer setting bounds and step must be whole numbers.")

    def validate(self, value: Any) -> Any:
        """Return a normalized value or raise a precise validation error."""
        if self.value_type == "bool":
            if not isinstance(value, bool):
                raise TypeError(f"{self.label} must be boolean.")
            normalized = value
        elif self.value_type == "int":
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{self.label} must be an integer.")
            normalized = value
        elif self.value_type == "float":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise TypeError(f"{self.label} must be a finite number.")
            normalized = float(value)
        elif self.value_type == "str":
            if not isinstance(value, str):
                raise TypeError(f"{self.label} must be text.")
            normalized = value
        else:
            if value not in self.choices:
                raise ValueError(f"{self.label} must be one of the declared choices.")
            normalized = value
        if self.minimum is not None and normalized < self.minimum:
            raise ValueError(f"{self.label} must be at least {self.minimum}.")
        if self.maximum is not None and normalized > self.maximum:
            raise ValueError(f"{self.label} must be at most {self.maximum}.")
        return normalized

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "value_type": self.value_type,
            "default": self.default,
            "editable": self.editable,
            "unit": self.unit,
            "choices": self.choices,
            "minimum": self.minimum,
            "maximum": self.maximum,
            "step": self.step,
        }

@dataclass(frozen=True, slots=True)
class ToolSettings:
    """Immutable contextual settings for tool interaction, not engineering state."""

    tool_id: str
    values: Mapping[str, Any] = field(default_factory=dict)
    definitions: Mapping[str, ToolSettingDefinition] = field(default_factory=dict)
    revision: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.tool_id, str) or not self.tool_id.strip():
            raise ValueError("tool_id must be a non-empty string.")
        if not isinstance(self.values, Mapping):
            raise TypeError("values must be a mapping.")
        if not isinstance(self.definitions, Mapping):
            raise TypeError("definitions must be a mapping.")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision < 0:
            raise ValueError("revision must be a non-negative integer.")
        definitions = dict(self.definitions)
        if any(not isinstance(key, str) or not key.strip() or not isinstance(value, ToolSettingDefinition)
               for key, value in definitions.items()):
            raise TypeError("definitions must map non-empty setting IDs to ToolSettingDefinition values.")
        values = dict(self.values)
        if set(values).difference(definitions):
            raise ValueError("values contain settings absent from the declared schema.")
        for key, definition in definitions.items():
            if key not in values:
                values[key] = definition.default
            values[key] = definition.validate(values[key])
        object.__setattr__(self, "tool_id", self.tool_id.strip())
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "definitions", definitions)

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def with_updates(self, **changes: Any) -> "ToolSettings":
        updated = dict(self.values)
        for key, value in changes.items():
            definition = self.definitions.get(key)
            if definition is None:
                raise KeyError(f"Undeclared tool setting: {key!r}")
            if not definition.editable:
                raise PermissionError(f"Tool setting {key!r} is read-only.")
            updated[key] = definition.validate(value)
        return replace(self, values=updated, revision=self.revision + 1)

    def to_dict(self) -> dict[str, Any]:
        return {"tool_id": self.tool_id, "values": dict(self.values), "revision": self.revision}


__all__ = ["ToolSettingDefinition", "ToolSettings"]
