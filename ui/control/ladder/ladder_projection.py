"""Control read-model to Ladder canvas projection boundary."""

from __future__ import annotations

from typing import Any


class LadderProjection:
    """Adapt the immutable ControlProgramReadModel to the existing ControlCanvas."""

    def __init__(self, canvas: Any) -> None:
        if canvas is None or not callable(getattr(canvas, "project", None)):
            raise TypeError("canvas must expose project(read_model).")
        self._canvas = canvas

    def project(self, read_model: Any) -> None:
        self._canvas.project(read_model)


__all__ = ["LadderProjection"]
