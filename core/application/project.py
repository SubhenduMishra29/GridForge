# ============================================================
# File: core/application/project.py
# GridForge V2 — Immutable Application Project Context
# Author: Subhendu Mishra
# ============================================================

"""Value object describing the authoritative Application project context."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class ProjectContext:
    """Immutable identity and location context for the active GridForge project."""

    project_id: str
    name: str
    path: Path | None

    def __post_init__(self) -> None:
        project_id = self._validated_text(self.project_id, "project_id")
        name = self._validated_text(self.name, "name")

        object.__setattr__(self, "project_id", project_id)
        object.__setattr__(self, "name", name)

        if self.path is not None:
            if not isinstance(self.path, (str, Path)):
                raise TypeError("path must be a string, Path, or None.")
            path = Path(self.path)
            if not str(path):
                raise ValueError("path must not be empty.")
            object.__setattr__(self, "path", path)

    @staticmethod
    def _validated_text(value: Any, field_name: str) -> str:
        if not isinstance(value, str):
            raise TypeError(f"{field_name} must be a string.")
        value = value.strip()
        if not value:
            raise ValueError(f"{field_name} must not be empty.")
        return value


__all__ = ["ProjectContext"]
