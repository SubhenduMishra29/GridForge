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


\n\n@dataclass(frozen=True, slots=True)\nclass ProjectSnapshot:\n    """Immutable Application study boundary for one activated project generation."""\n\n    project_id: str\n    activation_generation: int\n    revision: Any\n    network: Any\n    dynamic_models: tuple[Any, ...] = ()\n\n    def __post_init__(self) -> None:\n        if not isinstance(self.project_id, str) or not self.project_id.strip():\n            raise ValueError("project_id must be a non-empty string.")\n        if not isinstance(self.activation_generation, int) or isinstance(self.activation_generation, bool) or self.activation_generation < 1:\n            raise ValueError("activation_generation must be a positive integer.")\n        if self.network is None:\n            raise ValueError("ProjectSnapshot requires a network snapshot.")\n        object.__setattr__(self, "project_id", self.project_id.strip())\n        object.__setattr__(self, "dynamic_models", tuple(self.dynamic_models))\n\n\n__all__ = ["ProjectContext", "ProjectSnapshot"]
