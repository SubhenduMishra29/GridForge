# ============================================================

# File: ui/items/bus_item.py

# GridForge V2 — Bus Graphics Item

# ============================================================

"""
GridForge V2 Bus Graphics Item.

BusItem is the presentation-layer graphics representation of an
authoritative GridForge Bus.

## Architectural Role

The authoritative Bus remains in GridForge Core.

```
Core Bus
   │
   ▼
BusItem
   │
   ▼
```

QGraphicsScene
│
▼
GraphicsView

BusItem provides graphical representation and interaction
metadata only.

## Responsibilities

BusItem:

```
- represents one authoritative Bus visually;
- exposes the stable object_id;
- provides bus-specific graphical geometry;
- supports graphical selection;
- supports graphical movement;
- reports graphical position changes;
- provides presentation diagnostics;
- optionally retains a non-owning reference to the projected
  model object.
```

BusItem does NOT:

```
- own the Bus model;
- modify the Core model directly;
- perform engineering calculations;
- determine electrical topology;
- perform snapping;
- own application selection;
- create Lines or other engineering objects;
- implement tool behavior;
- manage controllers;
- manage plugins;
- perform navigation;
- become an engineering authority.
```

## Identity

object_id identifies the authoritative application/Core object.

It is not:

```
- a QGraphicsItem memory identity;
- a numerical network index;
- an electrical topology index.
```

## Selection

QGraphicsItem selection is presentation state only.

Persistent application selection remains owned by Controller
through SelectionManager.

## Movement

BusItem is movable at the graphics level so UI interaction can
provide immediate visual feedback.

Position changes are exposed through `position_changed`.

Changing graphical position does not directly modify the Core.
A controller/command workflow is responsible for committing any
application-level position change.

## Rendering

BusItem provides only its own minimal graphics painting.

Renderer infrastructure may configure its presentation through
the item's Qt painting properties.

No engineering semantics are encoded in the visual rendering.

## Qt Boundary

All Qt dependencies are imported through:

```
ui.core.qt
```

No direct PySide6 or PyQt imports are permitted.
"""

from __future__ import annotations
from typing import Any, Optional

from ui.core.qt import (
QBrush,
QGraphicsItem,
QPainter,
QGraphicsObject,
QPen,
QPointF,
Qt,
Signal,
)

from .base_item import BaseItem

# ============================================================

# BUS ITEM

# ============================================================

class BusItem(BaseItem):
"""
Graphical representation of one GridForge Bus.

```
BusItem inherits the common UI graphics contract from
BaseItem and adds only Bus-specific presentation behavior.
"""

# ========================================================
# VISUAL DEFAULTS
# ========================================================

DEFAULT_RADIUS = 8.0

DEFAULT_LINE_WIDTH = 1.5

# ========================================================
# SIGNALS
# ========================================================

position_changed = Signal(object)

# ========================================================
# INITIALIZATION
# ========================================================

def __init__(
    self,
    object_id: Any,
    position: Optional[QPointF] = None,
    radius: float = DEFAULT_RADIUS,
    model: Optional[Any] = None,
    parent: Optional[QGraphicsObject] = None,
) -> None:
    """
    Initialize a BusItem.

    Parameters
    ----------
    object_id:
        Stable identifier of the represented Bus.

    position:
        Optional initial scene position.

    radius:
        Visual radius of the bus symbol.

    model:
        Optional non-owning reference to the projected
        authoritative Bus object.

    parent:
        Optional Qt graphics parent.
    """

    super().__init__(
        object_id=object_id,
        parent=parent,
    )

    self._validate_radius(
        radius
    )

    self.radius = float(
        radius
    )

    # ----------------------------------------------------
    # Projection reference.
    #
    # This is not owned by BusItem and is never mutated
    # by BusItem.
    # ----------------------------------------------------

    self._model = model

    # ----------------------------------------------------
    # Graphics configuration.
    # ----------------------------------------------------

    self.setFlag(
        QGraphicsItem.GraphicsItemFlag.ItemIsSelectable,
        True,
    )

    self.setFlag(
        QGraphicsItem.GraphicsItemFlag.ItemIsMovable,
        True,
    )

    self.setFlag(
        QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges,
        True,
    )

    # ----------------------------------------------------
    # Default presentation.
    #
    # Renderers may replace these properties.
    # ----------------------------------------------------

    self.setPen(
        QPen(
            Qt.GlobalColor.black,
            self.DEFAULT_LINE_WIDTH,
        )
    )

    self.setBrush(
        QBrush(
            Qt.GlobalColor.white
        )
    )

    if position is not None:
        self.set_scene_position(
            position,
            emit=False,
        )

# ========================================================
# MODEL PROJECTION
# ========================================================

def get_model(
    self,
) -> Optional[Any]:
    """
    Return the optional projected model reference.

    BusItem does not own or mutate the returned object.
    """

    return self._model

# --------------------------------------------------------

def set_model(
    self,
    model: Optional[Any],
) -> None:
    """
    Replace the projected model reference.

    This changes only the UI projection reference.
    """

    self._model = model

# ========================================================
# POSITION
# ========================================================

def get_scene_position(
    self,
) -> QPointF:
    """
    Return the current Qt scene position.

    QGraphicsItem remains the sole owner of graphical
    position state.
    """

    position = self.pos()

    return QPointF(
        position.x(),
        position.y(),
    )

# --------------------------------------------------------

def set_scene_position(
    self,
    position: QPointF,
    *,
    emit: bool = True,
) -> None:
    """
    Set the graphical scene position.

    Parameters
    ----------
    position:
        Target scene position.

    emit:
        Whether a position_changed notification should be
        emitted when the position actually changes.

    The operation modifies graphical state only.
    """

    self._validate_point(
        position,
        "position",
    )

    old_position = self.get_scene_position()

    new_position = QPointF(
        position.x(),
        position.y(),
    )

    self.setPos(
        new_position
    )

    if (
        emit
        and self._positions_differ(
            old_position,
            new_position,
        )
    ):
        self.position_changed.emit(
            new_position
        )

# ========================================================
# QT GEOMETRY CHANGE
# ========================================================

def itemChange(
    self,
    change: Any,
    value: Any,
) -> Any:
    """
    Observe Qt graphics-item position changes.

    This method reports presentation changes only.

    It never modifies the Core model.
    """

    result = super().itemChange(
        change,
        value,
    )

    position_change = (
        QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged
    )

    if change == position_change:
        if value is not None:
            self._validate_point(
                value,
                "position change",
            )

            self.position_changed.emit(
                QPointF(
                    value.x(),
                    value.y(),
                )
            )

    return result

# ========================================================
# GEOMETRY
# ========================================================

def boundingRect(self) -> Any:
    """
    Return the local bounding rectangle of the Bus symbol.
    """

    radius = self.radius

    return self._make_rect(
        -radius,
        -radius,
        radius * 2.0,
        radius * 2.0,
    )

# --------------------------------------------------------

def paint(
    self,
    painter: QPainter,
    option: Any,
    widget: Optional[Any] = None,
) -> None:
    """
    Paint the graphical Bus representation.

    No engineering calculations or domain decisions occur
    here.
    """

    del option
    del widget

    if painter is None:
        return

    painter.setPen(
        self.pen()
    )

    painter.setBrush(
        self.brush()
    )

    painter.drawEllipse(
        self.boundingRect()
    )

# ========================================================
# VISUAL CONFIGURATION
# ========================================================

def set_radius(
    self,
    radius: float,
) -> None:
    """
    Change the visual Bus radius.

    This modifies presentation geometry only.
    """

    self._validate_radius(
        radius
    )

    radius = float(
        radius
    )

    if radius == self.radius:
        return

    self.prepareGeometryChange()

    self.radius = radius

    self.update()

# --------------------------------------------------------

def get_radius(
    self,
) -> float:
    """
    Return the current visual radius.
    """

    return self.radius

# --------------------------------------------------------

def set_pen(
    self,
    pen: QPen,
) -> None:
    """
    Set the Bus outline presentation.
    """

    if pen is None:
        raise ValueError(
            "pen must not be None."
        )

    super().setPen(
        pen
    )

# --------------------------------------------------------

def set_brush(
    self,
    brush: QBrush,
) -> None:
    """
    Set the Bus fill presentation.
    """

    if brush is None:
        raise ValueError(
            "brush must not be None."
        )

    super().setBrush(
        brush
    )

# ========================================================
# SELECTION PRESENTATION
# ========================================================

def set_visual_selected(
    self,
    selected: bool,
) -> None:
    """
    Set the graphical selection projection.

    Persistent application selection remains owned by
    Controller / SelectionManager.
    """

    self.set_graphical_selected(
        selected
    )

# --------------------------------------------------------

def is_visual_selected(
    self,
) -> bool:
    """
    Return the current graphical selection state.
    """

    return self.is_selected()

# ========================================================
# DIAGNOSTICS
# ========================================================

def get_state(
    self,
) -> dict[str, Any]:
    """
    Return diagnostic presentation state.
    """

    state = super().get_state()

    state.update(
        {
            "radius": self.radius,
            "movable": bool(
                self.flags()
                & QGraphicsItem.GraphicsItemFlag.ItemIsMovable
            ),
            "selectable": bool(
                self.flags()
                & QGraphicsItem.GraphicsItemFlag.ItemIsSelectable
            ),
            "has_model": self._model is not None,
        }
    )

    return state

# ========================================================
# VALIDATION
# ========================================================

@staticmethod
def _validate_radius(
    radius: Any,
) -> None:
    """
    Validate a visual radius.
    """

    if (
        isinstance(radius, bool)
        or not isinstance(
            radius,
            (int, float),
        )
    ):
        raise TypeError(
            "radius must be a numeric value."
        )

    if radius <= 0:
        raise ValueError(
            "radius must be greater than zero."
        )

# --------------------------------------------------------

@staticmethod
def _validate_point(
    point: Any,
    name: str,
) -> None:
    """
    Validate a QPointF-compatible value.
    """

    if point is None:
        raise ValueError(
            f"{name} must not be None."
        )

    if not callable(
        getattr(
            point,
            "x",
            None,
        )
    ):
        raise TypeError(
            f"{name} must provide x()."
        )

    if not callable(
        getattr(
            point,
            "y",
            None,
        )
    ):
        raise TypeError(
            f"{name} must provide y()."
        )

# --------------------------------------------------------

@staticmethod
def _positions_differ(
    first: QPointF,
    second: QPointF,
) -> bool:
    """
    Return whether two positions differ.
    """

    return (
        first.x() != second.x()
        or first.y() != second.y()
    )

# --------------------------------------------------------

@staticmethod
def _make_rect(
    x: float,
    y: float,
    width: float,
    height: float,
) -> Any:
    """
    Create a QRectF without expanding the public Qt
    abstraction beyond the current requirement.
    """

    from ui.core.qt import QRectF

    return QRectF(
        x,
        y,
        width,
        height,
    )

# ========================================================
# REPRESENTATION
# ========================================================

def __repr__(
    self,
) -> str:
    """
    Return a concise diagnostic representation.
    """

    position = self.get_scene_position()

    return (
        "BusItem("
        f"object_id={self.object_id!r}, "
        f"position=("
        f"{position.x():.2f}, "
        f"{position.y():.2f}"
        "), "
        f"radius={self.radius:.2f}, "
        f"selected={self.is_selected()}"
        ")"
    )
```

# ============================================================

# PUBLIC API

# ============================================================

**all** = [
"BusItem",
]
