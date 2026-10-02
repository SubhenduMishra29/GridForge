# ============================================================
# File: ui/tools/tool_settings.py
# GridForge V2 — Canonical Tool Settings
# Author: Subhendu Mishra
# ============================================================
"""Qt-independent settings describing how the active tool operates."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class ToolSettings:
    """Immutable contextual settings for tool interaction.

    These are interaction preferences, not engineering properties of the
    selected object and not runtime lifecycle state.
    """

    tool_id: str
    values: Mapping[str, Any] = field(default_factory=dict)
    revision: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.tool_id, str) or not self.tool_id.strip():
            raise ValueError("tool_id must be a non-empty string.")
        if not isinstance(self.values, Mapping):
            raise TypeError("values must be a mapping.")
        if not isinstance(self.revision, int) or self.revision < 0:
            raise ValueError("revision must be a non-negative integer.")
        object.__setattr__(self, "tool_id", self.tool_id.strip())
        object.__setattr__(self, "values", dict(self.values))

    def get(self, key: str, default: Any = None) -> Any:
        return self.values.get(key, default)

    def with_updates(self, **changes: Any) -> "ToolSettings":
        updated = dict(self.values)
        updated.update(changes)
        return replace(self, values=updated, revision=self.revision + 1)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_id": self.tool_id,
            "values": dict(self.values),
            "revision": self.revision,
        }


__all__ = ["ToolSettings"]
