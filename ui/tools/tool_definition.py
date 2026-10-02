# ============================================================
# File: ui/tools/tool_definition.py
# GridForge V2 — Canonical Tool Definition
# Author: Subhendu Mishra
# ============================================================
"""Qt-independent immutable metadata describing an editor tool."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ToolDefinition:
    """Immutable interaction-capability metadata.

    ToolDefinition describes a tool; it never owns its runtime instance,
    lifecycle, widgets, commands, or domain state.
    """

    tool_id: str
    display_name: str
    description: str = ""
    icon_id: str | None = None
    editor_types: tuple[str, ...] = ()
    capabilities: tuple[str, ...] = ()
    supported_modes: tuple[str, ...] = ()
    default_mode: str | None = None
    shortcuts: tuple[str, ...] = ()
    settings: Mapping[str, object] = field(default_factory=dict)
    applicability: Mapping[str, object] = field(default_factory=dict)
    category: str = "general"
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("tool_id", "display_name"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())

        for name in ("description", "category"):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string.")
            object.__setattr__(self, name, value.strip())

        if self.icon_id is not None:
            if not isinstance(self.icon_id, str) or not self.icon_id.strip():
                raise ValueError("icon_id must be None or a non-empty string.")
            object.__setattr__(self, "icon_id", self.icon_id.strip())

        for name in ("editor_types", "capabilities", "supported_modes", "shortcuts"):
            values = tuple(str(value).strip() for value in getattr(self, name))
            if any(not value for value in values):
                raise ValueError(f"{name} cannot contain empty values.")
            object.__setattr__(self, name, values)

        if self.default_mode is not None:
            if not isinstance(self.default_mode, str) or not self.default_mode.strip():
                raise ValueError("default_mode must be None or a non-empty string.")
            object.__setattr__(self, "default_mode", self.default_mode.strip())

        for name in ("settings", "applicability", "metadata"):
            value = getattr(self, name)
            if not isinstance(value, Mapping):
                raise TypeError(f"{name} must be a mapping.")
            object.__setattr__(self, name, dict(value))

    def supports_editor(self, editor_type: str) -> bool:
        return not self.editor_types or editor_type in self.editor_types

    def supports_mode(self, mode: str) -> bool:
        return not self.supported_modes or mode in self.supported_modes

    def to_dict(self) -> dict[str, object]:
        return {
            "tool_id": self.tool_id,
            "display_name": self.display_name,
            "description": self.description,
            "icon_id": self.icon_id,
            "editor_types": self.editor_types,
            "capabilities": self.capabilities,
            "supported_modes": self.supported_modes,
            "default_mode": self.default_mode,
            "shortcuts": self.shortcuts,
            "settings": dict(self.settings),
            "applicability": dict(self.applicability),
            "category": self.category,
            "metadata": dict(self.metadata),
        }



def contextual_tool_definitions(tool_ids: tuple[str, ...] | list[str], *, editor_type: str) -> tuple[ToolDefinition, ...]:
    """Build presentation metadata from an authoritative runtime tool-ID set.

    This is an adapter, not a catalogue: ToolManager remains the runtime
    authority and callers may replace these definitions with richer metadata.
    """
    if not isinstance(editor_type, str) or not editor_type.strip():
        raise ValueError("editor_type must be a non-empty string.")
    definitions: list[ToolDefinition] = []
    seen: set[str] = set()
    for raw_id in tool_ids:
        tool_id = str(raw_id).strip()
        if not tool_id or tool_id in seen:
            continue
        seen.add(tool_id)
        definitions.append(
            ToolDefinition(
                tool_id=tool_id,
                display_name=tool_id.replace("_", " ").replace(".", " ").title(),
                icon_id=tool_id,
                editor_types=(editor_type,),
                category="engineering",
            )
        )
    return tuple(definitions)


__all__ = ["ToolDefinition", "contextual_tool_definitions"]
