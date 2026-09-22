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




@dataclass(frozen=True, slots=True)
class ProjectSnapshot:
    """Immutable Application study boundary for one activated project generation."""

    project_id: str
    activation_generation: int
    revision: Any
    network: Any
    dynamic_models: tuple[Any, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id must be a non-empty string.")
        if not isinstance(self.activation_generation, int) or isinstance(self.activation_generation, bool) or self.activation_generation < 1:
            raise ValueError("activation_generation must be a positive integer.")
        if self.network is None:
            raise ValueError("ProjectSnapshot requires a network snapshot.")
        object.__setattr__(self, "project_id", self.project_id.strip())
        object.__setattr__(self, "dynamic_models", tuple(self.dynamic_models))


__all__ = ["ProjectContext", "ProjectSnapshot"]
