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
from ui.styling.presentation_style import VisualState, visual_brush, visual_pen


class SLDNodeItem(QGraphicsEllipseItem):
    """Render one SLD node as a lightweight graphics projection."""

    _SIZE = 12.0

    def __init__(self, object_id: str) -> None:
        if not isinstance(object_id, str) or not object_id:
            raise ValueError("SLD node object_id must be a non-empty string")
        half = self._SIZE / 2.0
        super().__init__(QRectF(-half, -half, self._SIZE, self._SIZE))
        self._object_id = object_id
        self._visual_state = VisualState.NORMAL
        self.setAcceptHoverEvents(True)
        self.setPen(visual_pen("terminal", VisualState.NORMAL, width=1.5))
        self.setBrush(visual_brush("terminal", VisualState.NORMAL))
        self.setFlag(QGraphicsEllipseItem.GraphicsItemFlag.ItemIsSelectable, True)

    @property
    def object_id(self) -> str:
        """Stable Core object ID represented by this graphics item."""
        return self._object_id

    def set_visual_position(self, x: float, y: float) -> None:
        """Apply only the position supplied by the canonical canvas snapshot.

        This method is a renderer operation, not an edit API. Persistent node
        movement must use SetSLDNodePositionCommand; this item never decides
        whether a position change is accepted.
        """
        self.setPos(QPointF(float(x), float(y)))

    def visual_position(self) -> tuple[float, float]:
        """Return the current presentation position."""
        position = self.pos()
        return (position.x(), position.y())


    def set_visual_state(self, state: VisualState | str) -> None:
        self._visual_state = state if isinstance(state, VisualState) else VisualState(str(state).lower())
        self.setPen(visual_pen("terminal", self._visual_state, width=1.5))
        self.setBrush(visual_brush("terminal", self._visual_state))

    def hoverEnterEvent(self, event) -> None:
        self.set_visual_state(VisualState.HOVER)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event) -> None:
        self.set_visual_state(VisualState.SELECTED if self.isSelected() else VisualState.NORMAL)
        super().hoverLeaveEvent(event)
