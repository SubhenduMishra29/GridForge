# ============================================================
# File: ui/sld/items/sld_node_item.py
# GridForge V2 — SLD Node Graphics Projection
# Author: Subhendu Mishra
# ============================================================
"""Qt graphics projection for an SLD node.

The item owns presentation geometry only. Core identity is retained as an
immutable reference and no domain mutation is performed here.
"""

from __future__ import annotations

from ui.core.qt import QGraphicsEllipseItem, QPointF, QRectF


class SLDNodeItem(QGraphicsEllipseItem):
    """Render one SLD node as a lightweight graphics projection."""

    _SIZE = 12.0

    def __init__(self, object_id: str) -> None:
        if not isinstance(object_id, str) or not object_id:
            raise ValueError("SLD node object_id must be a non-empty string")
        half = self._SIZE / 2.0
        super().__init__(QRectF(-half, -half, self._SIZE, self._SIZE))
        self._object_id = object_id
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)

    @property
    def object_id(self) -> str:
        """Stable Core object ID represented by this graphics item."""
        return self._object_id

    def set_visual_position(self, x: float, y: float) -> None:
        """Set presentation position without modifying Core state."""
        self.setPos(QPointF(float(x), float(y)))

    def visual_position(self) -> tuple[float, float]:
        """Return the current presentation position."""
        position = self.pos()
        return (position.x(), position.y())
