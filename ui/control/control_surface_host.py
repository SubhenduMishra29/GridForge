"""Presentation-only host for switching the existing SLD and Control surfaces."""

from __future__ import annotations

from ui.core.qt import QVBoxLayout, QWidget


class ControlSurfaceHost(QWidget):
    """Host mutually exclusive engineering surfaces without owning domain state."""

    def __init__(self, *, sld_surface: QWidget, control_surface: QWidget, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        if not isinstance(sld_surface, QWidget) or not isinstance(control_surface, QWidget):
            raise TypeError("Both workspace surfaces must be QWidget instances.")
        self._surfaces = {"sld": sld_surface, "control": control_surface}
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(sld_surface)
        layout.addWidget(control_surface)
        self.activate("sld")

    @property
    def surface_ids(self) -> tuple[str, ...]:
        return tuple(self._surfaces)

    def activate(self, surface_id: str) -> None:
        if surface_id not in self._surfaces:
            raise KeyError(f"Unknown workspace surface: {surface_id!r}")
        for key, widget in self._surfaces.items():
            widget.setVisible(key == surface_id)


__all__ = ["ControlSurfaceHost"]
