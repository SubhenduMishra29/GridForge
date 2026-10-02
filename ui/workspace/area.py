# ============================================================
# File: ui/workspace/area.py
# GridForge V2 — Engineering Area Contract
# Author: Subhendu Mishra
# ============================================================

"""Qt-independent Area composition primitive."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .editor import EditorDefinition


@dataclass(frozen=True, slots=True)
class AreaDefinition:
    """A UI composition area capable of hosting one editor."""

    area_id: str
    editor: EditorDefinition
    visible: bool = True
    order: int = 0
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.area_id, str) or not self.area_id.strip():
            raise ValueError("area_id must be a non-empty string.")
        if not isinstance(self.editor, EditorDefinition):
            raise TypeError("editor must be an EditorDefinition.")
        if not isinstance(self.visible, bool):
            raise TypeError("visible must be bool.")
        if not isinstance(self.order, int):
            raise TypeError("order must be int.")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping.")


Area = AreaDefinition


__all__ = ["AreaDefinition", "Area"]
