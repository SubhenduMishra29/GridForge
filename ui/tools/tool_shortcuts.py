# ============================================================
# File: ui/tools/tool_shortcuts.py
# GridForge V2 — Contextual Tool Keymaps
# Author: Subhendu Mishra
# ============================================================
"""Qt-independent contextual keymap definitions.

The registry contains semantic shortcuts only. It does not own the tool
catalogue or activate tools; ToolManager remains the runtime authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Optional


class ToolShortcutAction(str, Enum):
    """Compatibility semantic actions; not a tool catalogue."""
    SELECT_TOOL = "select_tool"
    BUS_TOOL = "bus_tool"
    LINE_TOOL = "line_tool"


@dataclass(frozen=True, slots=True)
class ToolShortcut:
    sequence: str
    action: ToolShortcutAction | str | None
    tool_id: str
    description: str
    context: str = "global"

    def __post_init__(self) -> None:
        if not isinstance(self.sequence, str) or not self.sequence.strip():
            raise ValueError("sequence must be a non-empty string.")
        if not isinstance(self.tool_id, str) or not self.tool_id.strip():
            raise ValueError("tool_id must be a non-empty string.")
        if self.action is not None and not isinstance(self.action, (ToolShortcutAction, str)):
            raise TypeError("action must be a ToolShortcutAction, string, or None.")
        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("description must be a non-empty string.")
        if not isinstance(self.context, str) or not self.context.strip():
            raise ValueError("context must be a non-empty string.")


class ToolShortcutRegistry:
    """Contextual keymap registry with no embedded tool catalogue."""

    def __init__(self, shortcuts: Optional[Iterable[ToolShortcut]] = None) -> None:
        self._shortcuts: dict[tuple[str, str], ToolShortcut] = {}
        for shortcut in shortcuts or ():
            self.register(shortcut)

    def register(self, shortcut: ToolShortcut) -> None:
        if not isinstance(shortcut, ToolShortcut):
            raise TypeError("shortcut must be a ToolShortcut.")
        context = shortcut.context.strip().lower()
        sequence = self.normalize(shortcut.sequence)
        key = (context, sequence)
        if key in self._shortcuts:
            raise ValueError(f"Shortcut {sequence!r} is already registered in {context!r}.")
        self._shortcuts[key] = ToolShortcut(sequence, shortcut.action, shortcut.tool_id.strip(), shortcut.description.strip(), context)

    def unregister(self, sequence: str, *, context: str = "global") -> ToolShortcut:
        key = (context.strip().lower(), self.normalize(sequence))
        try:
            return self._shortcuts.pop(key)
        except KeyError as exc:
            raise KeyError(f"Shortcut {sequence!r} is not registered in {context!r}.") from exc

    def get(self, sequence: str, *, context: str = "global") -> ToolShortcut:
        value = self.get_optional(sequence, context=context)
        if value is None:
            raise KeyError(f"Shortcut {sequence!r} is not registered in {context!r}.")
        return value

    def get_optional(self, sequence: str, *, context: str = "global") -> Optional[ToolShortcut]:
        return self._shortcuts.get((context.strip().lower(), self.normalize(sequence)))

    def for_tool(self, tool_id: str, *, context: str | None = None) -> Optional[ToolShortcut]:
        for shortcut in self._shortcuts.values():
            if shortcut.tool_id != tool_id:
                continue
            if context is None or shortcut.context == context.strip().lower():
                return shortcut
        return None

    def sequence_for_tool(self, tool_id: str, *, context: str | None = None) -> Optional[str]:
        shortcut = self.for_tool(tool_id, context=context)
        return shortcut.sequence if shortcut is not None else None

    def shortcuts(self, *, context: str | None = None) -> tuple[ToolShortcut, ...]:
        if context is None:
            return tuple(self._shortcuts.values())
        normalized = context.strip().lower()
        return tuple(item for item in self._shortcuts.values() if item.context == normalized)

    def contexts(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(item.context for item in self._shortcuts.values()))

    def sequences(self, *, context: str | None = None) -> tuple[str, ...]:
        return tuple(item.sequence for item in self.shortcuts(context=context))

    @staticmethod
    def normalize(sequence: str) -> str:
        if not isinstance(sequence, str):
            raise TypeError("Shortcut sequence must be a string.")
        value = sequence.strip().upper()
        if not value:
            raise ValueError("Shortcut sequence must not be empty.")
        return value

    def validate_unique(self) -> None:
        keys = [(item.context, item.sequence) for item in self._shortcuts.values()]
        if len(keys) != len(set(keys)):
            raise RuntimeError("Contextual keymap contains duplicate shortcuts.")

    def action_for(self, sequence: str, *, context: str = "global") -> Optional[str]:
        shortcut = self.get_optional(sequence, context=context)
        return shortcut.action if shortcut is not None else None

    def tool_id_for(self, sequence: str, *, context: str = "global") -> Optional[str]:
        shortcut = self.get_optional(sequence, context=context)
        return shortcut.tool_id if shortcut is not None else None

    def get_state(self) -> dict[str, object]:
        return {
            "count": len(self._shortcuts),
            "contexts": self.contexts(),
            "sequences": self.sequences(),
            "tools": tuple(item.tool_id for item in self._shortcuts.values()),
        }


ContextualKeymapRegistry = ToolShortcutRegistry
GlobalKeymap = ToolShortcutRegistry
SLDKeymap = ToolShortcutRegistry
ControlKeymap = ToolShortcutRegistry
ProtectionKeymap = ToolShortcutRegistry


__all__ = [
    "ToolShortcutAction",
    "ToolShortcut",
    "ToolShortcutRegistry",
    "ContextualKeymapRegistry",
    "GlobalKeymap",
    "SLDKeymap",
    "ControlKeymap",
    "ProtectionKeymap",
]
