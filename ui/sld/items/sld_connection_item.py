# ============================================================
# File: ui/sld/items/sld_connection_item.py
# GridForge V2 — SLD Connection Graphics Projection
# Author: Subhendu Mishra
# ============================================================
"""Qt graphics projection for an SLD connection.

The item owns presentation endpoints only. It does not resolve topology or
mutate authoritative Core network state.
"""

from __future__ import annotations

from ui.core.qt import QGraphicsLineItem, QLineF, QPointF


class SLDConnectionItem(QGraphicsLineItem):
    """Render one SLD connection between two projected endpoints."""

    def __init__(
        self,
        object_id: str,
        source_object_id: str,
        target_object_id: str,
    ) -> None:
        for name, value in (
            ("object_id", object_id),
            ("source_object_id", source_object_id),
            ("target_object_id", target_object_id),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string")

        super().__init__()
        self._object_id = object_id
        self._source_object_id = source_object_id
        self._target_object_id = target_object_id

    @property
    def object_id(self) -> str:
        """Stable Core connection ID represented by this graphics item."""
        return self._object_id

    @property
    def source_object_id(self) -> str:
        """Stable ID of the source projected object."""
        return self._source_object_id

    @property
    def target_object_id(self) -> str:
        """Stable ID of the target projected object."""
        return self._target_object_id

    def set_visual_endpoints(
        self,
        source_x: float,
        source_y: float,
        target_x: float,
        target_y: float,
    ) -> None:
        """Set presentation endpoints without changing Core topology."""
        self.setLine(
            QLineF(
                QPointF(float(source_x), float(source_y)),
                QPointF(float(target_x), float(target_y)),
            )
        )

    def visual_endpoints(self) -> tuple[tuple[float, float], tuple[float, float]]:
        """Return the current presentation endpoints."""
        line = self.line()
        return (
            (line.p1().x(), line.p1().y()),
            (line.p2().x(), line.p2().y()),
        )
