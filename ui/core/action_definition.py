# ============================================================
# GridForge V2 — Canonical Presentation Action Definition
# Author: Subhendu Mishra
# ============================================================
"""Qt-independent immutable metadata for presentation actions."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True, slots=True)
class ActionDefinition:
    """Immutable metadata shared by menus, toolbars, shortcuts and shelves."""

    action_id: str
    title: str
    description: str = ""
    icon_id: str | None = None
    shortcut: str | None = None
    category: str = "general"
    enabled: bool = True
    checkable: bool = False
    checked: bool = False
    scope: str = "global"
    tool_id: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("action_id", "title", "category", "scope"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
            object.__setattr__(self, name, value.strip())
        for name in ("description",):
            value = getattr(self, name)
            if not isinstance(value, str):
                raise TypeError(f"{name} must be a string.")
            object.__setattr__(self, name, value.strip())
        if self.icon_id is not None:
            if not isinstance(self.icon_id, str) or not self.icon_id.strip():
                raise ValueError("icon_id must be None or a non-empty string.")
            object.__setattr__(self, "icon_id", self.icon_id.strip())
        if self.shortcut is not None:
            if not isinstance(self.shortcut, str) or not self.shortcut.strip():
                raise ValueError("shortcut must be None or a non-empty string.")
            object.__setattr__(self, "shortcut", self.shortcut.strip())
        if self.tool_id is not None:
            if not isinstance(self.tool_id, str) or not self.tool_id.strip():
                raise ValueError("tool_id must be None or a non-empty string.")
            object.__setattr__(self, "tool_id", self.tool_id.strip())
        if not isinstance(self.enabled, bool):
            raise TypeError("enabled must be bool.")
        if not isinstance(self.checkable, bool) or not isinstance(self.checked, bool):
            raise TypeError("checkable and checked must be bool.")
        if self.checked and not self.checkable:
            raise ValueError("checked actions must be checkable.")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))

    def to_dict(self) -> dict[str, object]:
        return {
            "action_id": self.action_id,
            "title": self.title,
            "description": self.description,
            "icon_id": self.icon_id,
            "shortcut": self.shortcut,
            "category": self.category,
            "enabled": self.enabled,
            "checkable": self.checkable,
            "checked": self.checked,
            "scope": self.scope,
            "tool_id": self.tool_id,
            "metadata": dict(self.metadata),
        }


__all__ = ["ActionDefinition"]
