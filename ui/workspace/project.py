# ============================================================
# File: ui/workspace/project.py
# GridForge V2 — Project Descriptor
# Author: Subhendu Mishra
# ============================================================
"""Persistent project identity boundary for the Presentation workspace.

A Project identifies the engineering container to which documents belong.
It is deliberately not the authoritative Core electrical model.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping


@dataclass(frozen=True, slots=True)
class Project:
    """Stable project identity and presentation-level configuration."""

    project_id: str
    name: str = "Untitled Project"
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise ValueError("project_id must be a non-empty string")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("metadata must be a mapping")


__all__ = ["Project"]
