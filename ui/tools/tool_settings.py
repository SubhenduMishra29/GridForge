from __future__ import annotations

import math
from dataclasses import dataclass, field, replace
from types import MappingProxyType
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ToolSettingDefinition:
    """Typed metadata for one contextual interaction setting."""
    label: str
    value_type: str
    default: Any
    editable: bool = True
    unit: str | None = None
    choices: tuple[Any, ...] = ()
    minimum: int | float | None = None
    maximum: int | float | None = None
    step: int | float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("setting label must be non-empty.")
        if self.value_type not in {"bool", "int", "float", "str", "choice"}:
            raise ValueError("unsupported setting value_type.")
        if not isinstance(self.editable, bool):
            raise TypeError("editable must be bool.")
        if self.unit is not None and (not isinstance(self.unit, str) or not self.unit.strip()):
            raise ValueError("unit must be None or non-empty.")
        choices = tuple(self.choices)
        object.__setattr__(self, "choices", choices)
        if any(type(v) not in (str, int, float, bool) for v in choices):
            raise TypeError("choices must be scalar immutable values.")
        if self.value_type == "choice" and not choices:
            raise ValueError("choice settings require choices.")
        if self.value_type != "choice" and choices:
            raise ValueError("choices apply only to choice settings.")
        for name in ("minimum", "maximum", "step"):
            value = getattr(self, name)
            if value is not None:
                if self.value_type not in {"int", "float"} or isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                    raise ValueError(f"{name} must be a finite numeric setting constraint.")
                if self.value_type == "int" and type(value) is not int:
                    raise ValueError(f"{name} for integer settings must be an integer.")
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("minimum cannot exceed maximum.")
        if self.step is not None and self.step <= 0:
            raise ValueError("step must be positive.")
        self.validate(self.default)

    def validate(self, value: Any) -> Any:
        if self.value_type == "bool":
            if type(value) is not bool: raise TypeError(f"{self.label} must be boolean.")
            result = value
        elif self.value_type == "int":
            if type(value) is not int: raise TypeError(f"{self.label} must be an integer.")
            result = value
        elif self.value_type == "float":
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                raise TypeError(f"{self.label} must be finite numeric data.")
            result = float(value)
        elif self.value_type == "str":
            if not isinstance(value, str): raise TypeError(f"{self.label} must be text.")
            result = value
        else:
            if not any(type(value) is type(choice) and value == choice for choice in self.choices):
                raise ValueError(f"{self.label} must match a declared choice.")
            result = value
        if self.minimum is not None and result < self.minimum:
            raise ValueError(f"{self.label} must be at least {self.minimum}.")
        if self.maximum is not None and result > self.maximum:
            raise ValueError(f"{self.label} must be at most {self.maximum}.")
        if self.step is not None:
            anchor = self.minimum if self.minimum is not None else 0
            q = (float(result) - float(anchor)) / float(self.step)
            if not math.isclose(q, round(q), rel_tol=1e-9, abs_tol=1e-9):
                raise ValueError(f"{self.label} must align to increments of {self.step} from {anchor}.")
        return result

    def to_dict(self) -> dict[str, Any]:
        return {"label": self.label, "value_type": self.value_type, "default": self.default,
                "editable": self.editable, "unit": self.unit, "choices": self.choices,
                "minimum": self.minimum, "maximum": self.maximum, "step": self.step}


@dataclass(frozen=True, slots=True)
class ToolSettings:
    """Immutable interaction preferences, separate from equipment engineering state."""
    tool_id: str
    values: Mapping[str, Any] = field(default_factory=dict)
    definitions: Mapping[str, ToolSettingDefinition] = field(default_factory=dict)
    revision: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.tool_id, str) or not self.tool_id.strip():
            raise ValueError("tool_id must be non-empty.")
        if not isinstance(self.values, Mapping) or not isinstance(self.definitions, Mapping):
            raise TypeError("values and definitions must be mappings.")
        if isinstance(self.revision, bool) or not isinstance(self.revision, int) or self.revision < 0:
            raise ValueError("revision must be a non-negative integer.")
        definitions = dict(self.definitions)
        if any(not isinstance(k, str) or not k.strip() or not isinstance(v, ToolSettingDefinition) for k, v in definitions.items()):
            raise TypeError("definitions must map non-empty IDs to ToolSettingDefinition values.")
        values = dict(self.values)
        unknown = set(values).difference(definitions)
        if unknown: raise ValueError("values contain undeclared setting IDs: " + ", ".join(sorted(unknown)))
        for key, definition in definitions.items():
            values[key] = definition.validate(values.get(key, definition.default))
        object.__setattr__(self, "tool_id", self.tool_id.strip())
        object.__setattr__(self, "values", MappingProxyType(values))
        object.__setattr__(self, "definitions", MappingProxyType(definitions))

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def with_updates(self, **changes: Any) -> "ToolSettings":
        if not changes: raise ValueError("at least one setting change is required.")
        updated = dict(self.values)
        for key, value in changes.items():
            definition = self.definitions.get(key)
            if definition is None: raise KeyError(f"Undeclared tool setting: {key!r}")
            if not definition.editable: raise PermissionError(f"Tool setting {key!r} is read-only.")
            updated[key] = definition.validate(value)
        return replace(self, values=updated, revision=self.revision + 1)

    def to_dict(self) -> dict[str, Any]:
        return {"tool_id": self.tool_id, "values": dict(self.values), "revision": self.revision}


__all__ = ["ToolSettingDefinition", "ToolSettings"]
