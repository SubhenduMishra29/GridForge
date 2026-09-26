# ============================================================
# GridForge V2 — Canonical SLD Bus presentation definition
# ============================================================
"""Renderer-neutral Bus-bar presentation geometry shared by preview and commit."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SLDBusPresentationDefinition:
    """Canonical default geometry for a presentation-only SLD Bus bar."""

    half_length: float = 80.0
    attachment_count: int = 9

    def __post_init__(self) -> None:
        if self.half_length <= 0:
            raise ValueError("half_length must be positive")
        if self.attachment_count < 2:
            raise ValueError("attachment_count must be at least two")

    @property
    def start(self) -> tuple[float, float]:
        return (-self.half_length, 0.0)

    @property
    def end(self) -> tuple[float, float]:
        return (self.half_length, 0.0)


DEFAULT_SLD_BUS_PRESENTATION = SLDBusPresentationDefinition()


__all__ = ["SLDBusPresentationDefinition", "DEFAULT_SLD_BUS_PRESENTATION"]
