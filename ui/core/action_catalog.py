# ============================================================
# GridForge V2 — Canonical Presentation Action Catalog
# Author: Subhendu Mishra
# ============================================================
"""Single source of presentation action metadata."""

from __future__ import annotations

from collections.abc import Iterable
from types import MappingProxyType
from typing import Mapping

from ui.core.action_definition import ActionDefinition
from ui.tools.tool_definition import ToolDefinition


_COMMON: tuple[ActionDefinition, ...] = (
    ActionDefinition("select", "Select", "Select and inspect engineering objects.", "select", None, "selection", True, True, True, "editor", "select"),
    ActionDefinition("move", "Move", "Move the current selection.", "move", None, "selection", True, False, False, "editor", "move"),
    ActionDefinition("pan", "Pan", "Pan the active engineering view.", "pan", None, "navigation"),
    ActionDefinition("zoom_in", "Zoom In", "Zoom into the active view.", "zoom_in", "Ctrl+=", "navigation"),
    ActionDefinition("zoom_out", "Zoom Out", "Zoom out of the active view.", "zoom_out", "Ctrl+-", "navigation"),
    ActionDefinition("fit_view", "Fit", "Fit the active engineering view.", "fit_view", "F", "navigation"),
    ActionDefinition("copy", "Copy", "Copy the current semantic selection.", "copy", "Ctrl+C", "edit"),
    ActionDefinition("paste", "Paste", "Paste the current semantic clipboard.", "paste", "Ctrl+V", "edit"),
    ActionDefinition("delete", "Delete", "Delete the current selection.", "delete", "Delete", "edit"),
    ActionDefinition("undo", "Undo", "Undo the last Application command.", "undo", "Ctrl+Z", "history"),
    ActionDefinition("redo", "Redo", "Redo the last Application command.", "redo", "Ctrl+Y", "history"),
    ActionDefinition("sld_select", "SLD Select", "Select SLD objects.", "select", None, "sld", True, True, True, "sld", "select"),
    ActionDefinition("sld_move", "SLD Move", "Move selected SLD objects.", "move", None, "sld", True, False, False, "sld", "move"),
    ActionDefinition("sld_wire", "SLD Wire", "Create a terminal-to-terminal SLD connection.", "wire", None, "sld", True, True, False, "sld", "wire"),
)


def build_action_definitions(tool_definitions: Iterable[ToolDefinition] = ()) -> tuple[ActionDefinition, ...]:
    """Build one immutable action definition set from common actions plus canonical tools."""
    result: list[ActionDefinition] = list(_COMMON)
    seen = {item.action_id for item in result}
    for definition in tool_definitions:
        if not isinstance(definition, ToolDefinition):
            raise TypeError("tool_definitions must contain ToolDefinition objects.")
        action_id = f"tool.{definition.tool_id}"
        if action_id in seen:
            continue
        result.append(
            ActionDefinition(
                action_id=action_id,
                title=definition.display_name,
                description=definition.description or definition.display_name,
                icon_id=definition.icon_id,
                shortcut=definition.shortcuts[0] if definition.shortcuts else None,
                category=definition.category or "engineering",
                checkable=True,
                scope=definition.editor_types[0] if definition.editor_types else "editor",
                tool_id=definition.tool_id,
                metadata={
                    "tool_definition": definition.tool_id,
                    "editor_types": tuple(definition.editor_types),
                    "capabilities": tuple(definition.capabilities),
                },
            )
        )
        seen.add(action_id)
    return tuple(result)


def index_action_definitions(definitions: Iterable[ActionDefinition]) -> Mapping[str, ActionDefinition]:
    values = tuple(definitions)
    result: dict[str, ActionDefinition] = {}
    for definition in values:
        if not isinstance(definition, ActionDefinition):
            raise TypeError("definitions must contain ActionDefinition objects.")
        if definition.action_id in result:
            raise ValueError(f"Duplicate action definition: {definition.action_id!r}")
        result[definition.action_id] = definition
    return MappingProxyType(result)


__all__ = ["build_action_definitions", "index_action_definitions"]
