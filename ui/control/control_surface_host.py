"""Presentation-only host for GridForge engineering workspace surfaces."""

from __future__ import annotations

from collections.abc import Mapping

from ui.core.qt import QVBoxLayout, QWidget


class ControlSurfaceHost(QWidget):
    """Host mutually exclusive engineering surfaces without owning domain state."""

    def __init__(self, *, surfaces: Mapping[str, QWidget], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if not surfaces:
            raise ValueError("At least one workspace surface is required.")
        normalized = dict(surfaces)
        if any(not isinstance(key, str) or not key.strip() for key in normalized):
            raise TypeError("Workspace surface IDs must be non-empty strings.")
        if any(not isinstance(widget, QWidget) for widget in normalized.values()):
            raise TypeError("All workspace surfaces must be QWidget instances.")
        self._surfaces = normalized
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        for widget in normalized.values():
            layout.addWidget(widget)
        self.activate(next(iter(normalized)))

    @property
    def surface_ids(self) -> tuple[str, ...]:
        return tuple(self._surfaces)

    def activate(self, surface_id: str) -> None:
        if surface_id not in self._surfaces:
            raise KeyError(f"Unknown workspace surface: {surface_id!r}")
        for key, widget in self._surfaces.items():
            widget.setVisible(key == surface_id)


__all__ = ["ControlSurfaceHost"]
