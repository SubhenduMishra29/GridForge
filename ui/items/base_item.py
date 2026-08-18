# ============================================================

# File: ui/items/base_item.py

# GridForge V2 — Base Graphics Item

# ============================================================

"""
GridForge V2 Base Graphics Item.

The BaseItem is the common presentation-layer foundation for
GridForge QGraphicsItem implementations.

## Architectural Role

BaseItem provides the shared graphical representation contract
for UI items that correspond to authoritative GridForge objects.

```
Core Object
     │
     │ object identity
     ▼
  BaseItem
     │
     ├── graphical state
     ├── selection projection
     ├── interaction flags
     └── presentation lifecycle
          │
          ▼
     QGraphicsScene
```

BaseItem does NOT own engineering truth.

The authoritative engineering object remains in GridForge Core.
The graphics item is only its UI representation.

## Responsibilities

BaseItem:

```
- stores the authoritative object identifier;
- provides a common QGraphicsObject foundation;
- establishes common graphics-item behavior;
- exposes object identity to UI infrastructure;
- provides presentation-level selection behavior;
- provides controlled position access;
- provides diagnostic state;
- provides a common item contract for concrete items.
```

BaseItem does NOT:

```
- own Core model objects;
- modify Core model state directly;
- perform engineering calculations;
- determine electrical topology;
- perform snapping;
- perform rendering policy;
- implement tool behavior;
- manage application selection;
- manage plugins;
- manage controllers;
- perform navigation;
- become an engineering authority.
```

## Selection

Graphics selection is a projection of application selection.

The authoritative direction is:

```
Controller.selected_ids
        │
        ▼
SelectionManager
        │
        ▼
BaseItem.setSelected()
```

BaseItem must never treat its QGraphicsItem selection state as
the authoritative application selection.

## Qt Boundary

All Qt dependencies pass through:

```
ui.core.qt
```

No direct PySide6/PyQt imports are permitted.

## Subclass Contract

Concrete graphics items such as:

```
BusItem
LineItem
```

inherit from BaseItem.

Concrete items are responsible for:

```
- their own bounding geometry;
- their own visual painting;
- item-specific presentation behavior.
```

Rendering policy remains outside the item where the renderer
architecture requires it.

## Identity

Every BaseItem represents an application object through a
stable object_id.

object_id is an identity reference only.

It must not be interpreted as:

```
- a QGraphicsItem memory identity;
- a numerical network index;
- an electrical topology index.
```

The BaseItem does not copy or duplicate engineering state.
"""

from **future** import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from ui.core.qt import (
QGraphicsObject,
QRectF,
)

# ============================================================

# BASE ITEM

# ============================================================

class BaseItem(QGraphicsObject, ABC):
"""
Common presentation-layer base class for GridForge graphics
items.

```
BaseItem provides graphical infrastructure while keeping
engineering ownership in GridForge Core.
"""

# ========================================================
# INITIALIZATION
# ========================================================

def __init__(
    self,
    object_id: Any,
    parent: Optional[QGraphicsObject] = None,
) -> None:
    """
    Initialize a BaseItem.

    Parameters
    ----------
    object_id:
        Stable identifier of the authoritative application
        object represented by this graphics item.

    parent:
        Optional Qt graphics parent.

    Raises
    ------
    ValueError
        If object_id is None.
    """

    if object_id is None:
        raise ValueError(
            "object_id must not be None."
        )

    super().__init__(parent)

    self._object_id = object_id

    # ----------------------------------------------------
    # Common interaction configuration
    # ----------------------------------------------------

    self.setFlag(
        self.GraphicsItemFlag.ItemIsSelectable,
        True,
    )

    self.setFlag(
        self.GraphicsItemFlag.ItemIsFocusable,
        False,
    )

# ========================================================
# IDENTITY
# ========================================================

@property
def object_id(self) -> Any:
    """
    Return the authoritative application object identifier.

    The returned identifier is an identity reference only.
    """

    return self._object_id

# --------------------------------------------------------

def get_object_id(self) -> Any:
    """
    Return the represented application object identifier.
    """

    return self._object_id

# ========================================================
# SELECTION
# ========================================================

def is_selected(self) -> bool:
    """
    Return the current graphical selection state.

    This reflects QGraphicsItem presentation state only.

    It does not establish application-level selection
    authority.
    """

    return bool(
        self.isSelected()
    )

# --------------------------------------------------------

def set_graphical_selected(
    self,
    selected: bool,
) -> None:
    """
    Set the graphical selection state.

    This method changes presentation state only.

    Application selection must be changed through the
    SelectionManager / Controller path.
    """

    if not isinstance(
        selected,
        bool,
    ):
        raise TypeError(
            "selected must be a bool."
        )

    self.setSelected(
        selected
    )

# ========================================================
# POSITION
# ========================================================

def get_scene_position(self) -> tuple[float, float]:
    """
    Return the item's scene position.

    This is presentation geometry and is not an electrical
    coordinate or topology authority.
    """

    position = self.scenePos()

    return (
        float(position.x()),
        float(position.y()),
    )

# --------------------------------------------------------

def set_scene_position(
    self,
    x: float,
    y: float,
) -> None:
    """
    Set the item's scene position.

    This changes graphical presentation state only.

    Validation of whether a position is appropriate for an
    engineering object belongs outside BaseItem.
    """

    if isinstance(x, bool) or not isinstance(
        x,
        (int, float),
    ):
        raise TypeError(
            "x must be a numeric value."
        )

    if isinstance(y, bool) or not isinstance(
        y,
        (int, float),
    ):
        raise TypeError(
            "y must be a numeric value."
        )

    self.setPos(
        float(x),
        float(y),
    )

# ========================================================
# GEOMETRY
# ========================================================

@abstractmethod
def boundingRect(self) -> QRectF:
    """
    Return the item's local bounding rectangle.

    Concrete graphics items must implement their own
    presentation geometry.
    """

    raise NotImplementedError

# --------------------------------------------------------

def scene_bounding_rect(self) -> QRectF:
    """
    Return the item's scene-space bounding rectangle.

    This is a convenience accessor for UI infrastructure.
    """

    return self.mapToScene(
        self.boundingRect()
    ).boundingRect()

# ========================================================
# VISIBILITY
# ========================================================

def is_visible(self) -> bool:
    """
    Return whether the graphics item is currently visible.
    """

    return bool(
        self.isVisible()
    )

# --------------------------------------------------------

def set_graphical_visible(
    self,
    visible: bool,
) -> None:
    """
    Set graphical visibility.

    Visibility is presentation state only.
    """

    if not isinstance(
        visible,
        bool,
    ):
        raise TypeError(
            "visible must be a bool."
        )

    self.setVisible(
        visible
    )

# ========================================================
# ENABLEMENT
# ========================================================

def is_enabled(self) -> bool:
    """
    Return whether the graphics item is enabled.
    """

    return bool(
        self.isEnabled()
    )

# --------------------------------------------------------

def set_graphical_enabled(
    self,
    enabled: bool,
) -> None:
    """
    Set graphical enabled state.

    Enabled state controls graphical interaction only.
    """

    if not isinstance(
        enabled,
        bool,
    ):
        raise TypeError(
            "enabled must be a bool."
        )

    self.setEnabled(
        enabled
    )

# ========================================================
# DIAGNOSTICS
# ========================================================

def get_state(self) -> dict[str, Any]:
    """
    Return a diagnostic snapshot of the graphics item.

    The state contains presentation information and stable
    object identity only.
    """

    position = self.scenePos()

    return {
        "object_id": self._object_id,
        "selected": bool(
            self.isSelected()
        ),
        "visible": bool(
            self.isVisible()
        ),
        "enabled": bool(
            self.isEnabled()
        ),
        "x": float(
            position.x()
        ),
        "y": float(
            position.y()
        ),
    }

# ========================================================
# REPRESENTATION
# ========================================================

def __repr__(self) -> str:
    """
    Return a concise diagnostic representation.
    """

    return (
        f"{self.__class__.__name__}("
        f"object_id={self._object_id!r}, "
        f"selected={self.isSelected()}"
        ")"
    )
```

# ============================================================

# PUBLIC API

# ============================================================

**all** = [
"BaseItem",
]
