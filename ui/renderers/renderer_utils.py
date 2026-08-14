# ============================================================
# File: ui/renderers/renderer_utils.py
# GridForge V2 — Renderer Utilities
# ============================================================
"""
Shared utilities for GridForge UI renderers.

Architecture
------------

    Core/Application Model
              │
              ▼
        Concrete Renderer
              │
              ▼
       renderer_utils
              │
              ▼
       Graphics Projection

Purpose
-------
This module contains small, renderer-layer utilities shared by
multiple concrete renderers.

Utilities here are presentation helpers only.

They do NOT:

    - own application state;
    - mutate Core objects;
    - create model objects;
    - perform electrical calculations;
    - implement tool behavior;
    - perform snapping;
    - perform selection;
    - perform navigation;
    - decide topology;
    - own QGraphicsScene;
    - register renderers.

Qt Architecture
---------------
All Qt dependencies must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.

Design Rule
-----------
Renderer utilities must remain stateless wherever practical.

They transform or validate presentation data.

They must not become a hidden renderer manager or a second
application-state container.
"""

from __future__ import annotations

from math import isfinite
from typing import Any, Iterable, Optional

from ui.core.qt import (
    QPointF,
    QRectF,
)


# ============================================================
# OBJECT ID
# ============================================================

def get_object_id(
    obj: Any,
) -> Any:
    """
    Return the authoritative object identifier.

    Supported forms are:

        object_id
        id

    Callable attributes are evaluated.

    Raises
    ------
    ValueError
        If obj is None.

    AttributeError
        If no supported identifier exists.
    """

    if obj is None:
        raise ValueError(
            "obj must not be None."
        )

    object_id = getattr(
        obj,
        "object_id",
        None,
    )

    if callable(object_id):
        object_id = object_id()

    if object_id is not None:
        return object_id

    object_id = getattr(
        obj,
        "id",
        None,
    )

    if callable(object_id):
        object_id = object_id()

    if object_id is None:
        raise AttributeError(
            "Object must provide object_id or id."
        )

    return object_id


# ============================================================
# ATTRIBUTE ACCESS
# ============================================================

def read_attribute(
    obj: Any,
    names: Iterable[str],
    *,
    default: Any = None,
) -> Any:
    """
    Return the first non-None attribute from names.

    Callable attributes are evaluated.

    Parameters
    ----------
    obj:
        Source object.

    names:
        Attribute names in priority order.

    default:
        Value returned when no usable attribute exists.
    """

    if obj is None:
        return default

    for name in names:

        value = getattr(
            obj,
            name,
            None,
        )

        if callable(value):
            value = value()

        if value is not None:
            return value

    return default


# ============================================================
# POINT CONVERSION
# ============================================================

def to_pointf(
    value: Any,
    *,
    name: str = "point",
) -> QPointF:
    """
    Convert a QPointF-compatible value to a detached QPointF.

    Supported forms include:

        QPointF

        object with x() / y()

        object with numeric x / y attributes

        (x, y)

        [x, y]

    No coordinate-system transformation is performed.

    The returned point remains in the coordinate system supplied
    by the caller.
    """

    if value is None:
        raise ValueError(
            f"{name} must not be None."
        )

    # --------------------------------------------------------
    # QPointF-compatible callable coordinates
    # --------------------------------------------------------

    x_attr = getattr(
        value,
        "x",
        None,
    )

    y_attr = getattr(
        value,
        "y",
        None,
    )

    if callable(x_attr) and callable(y_attr):

        return QPointF(
            _finite_number(
                x_attr(),
                name=f"{name}.x",
            ),
            _finite_number(
                y_attr(),
                name=f"{name}.y",
            ),
        )

    # --------------------------------------------------------
    # Numeric x / y attributes
    # --------------------------------------------------------

    if (
        x_attr is not None
        and y_attr is not None
        and not callable(x_attr)
        and not callable(y_attr)
    ):

        return QPointF(
            _finite_number(
                x_attr,
                name=f"{name}.x",
            ),
            _finite_number(
                y_attr,
                name=f"{name}.y",
            ),
        )

    # --------------------------------------------------------
    # Two-value sequence
    # --------------------------------------------------------

    if isinstance(
        value,
        (tuple, list),
    ):

        if len(value) != 2:
            raise ValueError(
                f"{name} sequence must contain exactly "
                "two values."
            )

        return QPointF(
            _finite_number(
                value[0],
                name=f"{name}[0]",
            ),
            _finite_number(
                value[1],
                name=f"{name}[1]",
            ),
        )

    raise TypeError(
        f"{name} must be QPointF-compatible or "
        "contain exactly two numeric coordinates."
    )


# ============================================================
# POINT PAIR
# ============================================================

def to_point_pair(
    start: Any,
    end: Any,
) -> tuple[QPointF, QPointF]:
    """
    Convert two endpoint values into detached QPointF objects.
    """

    return (
        to_pointf(
            start,
            name="start",
        ),
        to_pointf(
            end,
            name="end",
        ),
    )


# ============================================================
# RECTANGLE CONVERSION
# ============================================================

def to_rectf(
    value: Any,
    *,
    name: str = "rect",
) -> QRectF:
    """
    Convert a QRectF-compatible value to a detached QRectF.

    Supported forms include:

        QRectF

        object with x(), y(), width(), height()

        object with x, y, width, height attributes

        (x, y, width, height)

        [x, y, width, height]

    No coordinate-system transformation is performed.
    """

    if value is None:
        raise ValueError(
            f"{name} must not be None."
        )

    x = getattr(
        value,
        "x",
        None,
    )

    y = getattr(
        value,
        "y",
        None,
    )

    width = getattr(
        value,
        "width",
        None,
    )

    height = getattr(
        value,
        "height",
        None,
    )

    if all(
        callable(attribute)
        for attribute in (
            x,
            y,
            width,
            height,
        )
    ):

        return QRectF(
            _finite_number(
                x(),
                name=f"{name}.x",
            ),
            _finite_number(
                y(),
                name=f"{name}.y",
            ),
            _finite_number(
                width(),
                name=f"{name}.width",
            ),
            _finite_number(
                height(),
                name=f"{name}.height",
            ),
        )

    if all(
        attribute is not None
        and not callable(attribute)
        for attribute in (
            x,
            y,
            width,
            height,
        )
    ):

        return QRectF(
            _finite_number(
                x,
                name=f"{name}.x",
            ),
            _finite_number(
                y,
                name=f"{name}.y",
            ),
            _finite_number(
                width,
                name=f"{name}.width",
            ),
            _finite_number(
                height,
                name=f"{name}.height",
            ),
        )

    if isinstance(
        value,
        (tuple, list),
    ):

        if len(value) != 4:
            raise ValueError(
                f"{name} sequence must contain exactly "
                "four values."
            )

        return QRectF(
            _finite_number(
                value[0],
                name=f"{name}[0]",
            ),
            _finite_number(
                value[1],
                name=f"{name}[1]",
            ),
            _finite_number(
                value[2],
                name=f"{name}[2]",
            ),
            _finite_number(
                value[3],
                name=f"{name}[3]",
            ),
        )

    raise TypeError(
        f"{name} must be QRectF-compatible or "
        "contain four numeric values."
    )


# ============================================================
# RECTANGLE FROM POINTS
# ============================================================

def rect_from_points(
    start: Any,
    end: Any,
    *,
    padding: float = 0.0,
) -> QRectF:
    """
    Construct a bounding QRectF from two points.

    Parameters
    ----------
    start:
        First point.

    end:
        Second point.

    padding:
        Uniform expansion around the resulting rectangle.
    """

    if padding < 0:
        raise ValueError(
            "padding must be non-negative."
        )

    p1, p2 = to_point_pair(
        start,
        end,
    )

    left = min(
        p1.x(),
        p2.x(),
    )

    right = max(
        p1.x(),
        p2.x(),
    )

    top = min(
        p1.y(),
        p2.y(),
    )

    bottom = max(
        p1.y(),
        p2.y(),
    )

    return QRectF(
        left - padding,
        top - padding,
        (right - left)
        + (2.0 * padding),
        (bottom - top)
        + (2.0 * padding),
    )


# ============================================================
# MIDPOINT
# ============================================================

def midpoint(
    start: Any,
    end: Any,
) -> QPointF:
    """
    Return the midpoint between two presentation coordinates.
    """

    p1, p2 = to_point_pair(
        start,
        end,
    )

    return QPointF(
        (p1.x() + p2.x()) / 2.0,
        (p1.y() + p2.y()) / 2.0,
    )


# ============================================================
# DISTANCE SQUARED
# ============================================================

def distance_squared(
    start: Any,
    end: Any,
) -> float:
    """
    Return squared Euclidean distance between two points.

    Squared distance avoids an unnecessary square root and is
    suitable for renderer-side geometric comparisons.
    """

    p1, p2 = to_point_pair(
        start,
        end,
    )

    dx = (
        p2.x()
        - p1.x()
    )

    dy = (
        p2.y()
        - p1.y()
    )

    return (
        dx * dx
        + dy * dy
    )


# ============================================================
# LINE LENGTH
# ============================================================

def distance(
    start: Any,
    end: Any,
) -> float:
    """
    Return Euclidean distance between two points.
    """

    return distance_squared(
        start,
        end,
    ) ** 0.5


# ============================================================
# ITEM LOOKUP
# ============================================================

def find_item_by_object_id(
    scene: Any,
    object_id: Any,
    item_type: Optional[type] = None,
) -> Optional[Any]:
    """
    Find the first graphics item in scene representing
    object_id.

    Parameters
    ----------
    scene:
        Graphics scene.

    object_id:
        Authoritative application object identifier.

    item_type:
        Optional graphics-item type restriction.

    Returns
    -------
    object | None
        Matching item.
    """

    if scene is None:
        raise ValueError(
            "scene must not be None."
        )

    if object_id is None:
        return None

    items_method = getattr(
        scene,
        "items",
        None,
    )

    if not callable(
        items_method
    ):
        raise TypeError(
            "scene must provide items()."
        )

    for item in tuple(
        items_method()
    ):

        if (
            item_type is not None
            and not isinstance(
                item,
                item_type,
            )
        ):
            continue

        item_id = getattr(
            item,
            "object_id",
            None,
        )

        if item_id == object_id:
            return item

    return None


# ============================================================
# ITEM COLLECTION LOOKUP
# ============================================================

def find_items_by_object_ids(
    scene: Any,
    object_ids: Iterable[Any],
    item_type: Optional[type] = None,
) -> tuple[Any, ...]:
    """
    Find graphical projections representing object_ids.

    Scene iteration order is preserved.
    """

    if scene is None:
        raise ValueError(
            "scene must not be None."
        )

    if object_ids is None:
        raise ValueError(
            "object_ids must not be None."
        )

    requested = set(
        object_ids
    )

    if not requested:
        return ()

    items_method = getattr(
        scene,
        "items",
        None,
    )

    if not callable(
        items_method
    ):
        raise TypeError(
            "scene must provide items()."
        )

    result = []

    for item in tuple(
        items_method()
    ):

        if (
            item_type is not None
            and not isinstance(
                item,
                item_type,
            )
        ):
            continue

        item_id = getattr(
            item,
            "object_id",
            None,
        )

        if item_id in requested:
            result.append(
                item
            )

    return tuple(
        result
    )


# ============================================================
# SELECTION PROJECTION
# ============================================================

def set_item_selected(
    item: Any,
    selected: bool,
) -> None:
    """
    Set the visual selection state of a graphics item.

    This function performs only the visual operation.

    It does not modify application selection state.
    """

    if item is None:
        raise ValueError(
            "item must not be None."
        )

    if not isinstance(
        selected,
        bool,
    ):
        raise TypeError(
            "selected must be a bool."
        )

    setter = getattr(
        item,
        "setSelected",
        None,
    )

    if not callable(
        setter
    ):
        raise TypeError(
            "item must provide setSelected()."
        )

    setter(
        selected
    )


# ============================================================
# GEOMETRY VALIDATION
# ============================================================

def validate_pointf(
    point: Any,
    *,
    name: str = "point",
) -> QPointF:
    """
    Validate and return a QPointF-compatible coordinate.
    """

    return to_pointf(
        point,
        name=name,
    )


# ============================================================
# NUMERIC VALIDATION
# ============================================================

def _finite_number(
    value: Any,
    *,
    name: str,
) -> float:
    """
    Convert value to float and ensure it is finite.
    """

    if isinstance(
        value,
        bool,
    ):
        raise TypeError(
            f"{name} must be numeric."
        )

    try:
        result = float(
            value
        )
    except (
        TypeError,
        ValueError,
    ) as exc:

        raise TypeError(
            f"{name} must be numeric."
        ) from exc

    if not isfinite(
        result
    ):
        raise ValueError(
            f"{name} must be finite."
        )

    return result


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "distance",
    "distance_squared",
    "find_item_by_object_id",
    "find_items_by_object_ids",
    "get_object_id",
    "midpoint",
    "read_attribute",
    "rect_from_points",
    "set_item_selected",
    "to_point_pair",
    "to_pointf",
    "to_rectf",
    "validate_pointf",
]
