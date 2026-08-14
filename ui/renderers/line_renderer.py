# ============================================================
# File: ui/renderers/line_renderer.py
# GridForge V2 — Line Renderer
# ============================================================
"""
Renderer for authoritative GridForge Line objects.

Architecture
------------

    Core / Application Line
              │
              ▼
         LineRenderer
              │
              ▼
           LineItem
              │
              ▼
         GridScene
              │
              ▼
        GraphicsView

Purpose
-------
LineRenderer is the presentation-layer adapter responsible for
creating and synchronizing the graphical projection of a Line.

The authoritative Line remains in Core/Application state.

LineRenderer does NOT:

    - modify the Core model;
    - create or delete Core objects;
    - determine electrical topology;
    - perform electrical calculations;
    - perform snapping;
    - implement LineTool behavior;
    - own selection state;
    - own navigation;
    - manage the scene lifecycle;
    - decide connection validity.

Geometry
--------
The renderer extracts presentation endpoints from the
authoritative Line.

The renderer does not perform viewport/scene coordinate
conversion.

Coordinate conversion belongs to CoordinateSystem.

Topology
--------
The authoritative electrical connection remains in Core.

LineItem is only a graphical projection of that connection.

A LineItem endpoint may visually correspond to a Bus or other
connection location, but LineRenderer does not establish or
validate that relationship.

Qt Architecture
---------------
All Qt dependencies must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.qt import (
    QPointF,
    QGraphicsScene,
)

from ui.items.line_item import LineItem


class LineRenderer:
    """
    Render and synchronize Line objects as LineItem instances.

    The renderer does not maintain a persistent model cache.

    The scene is the container for graphical projections.

    Parameters
    ----------
    scene:
        QGraphicsScene receiving LineItem projections.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        scene: QGraphicsScene,
    ) -> None:
        if scene is None:
            raise ValueError(
                "scene must not be None."
            )

        self._validate_scene(
            scene
        )

        self.scene = scene

    # ========================================================
    # RENDER
    # ========================================================

    def render(
        self,
        line: Any,
    ) -> LineItem:
        """
        Create or update the graphical projection of a Line.

        If a LineItem with the same object_id already exists,
        the existing projection is synchronized and returned.

        Otherwise a new LineItem is created and added to the
        scene.
        """

        object_id = self._get_object_id(
            line
        )

        existing = self.get_item(
            object_id
        )

        if existing is not None:
            return self.update(
                existing,
                line,
            )

        start, end = self.get_model_endpoints(
            line
        )

        item = LineItem(
            object_id=object_id,
            start=start,
            end=end,
            model=line,
        )

        self.scene.addItem(
            item
        )

        return item

    # ========================================================
    # CREATE
    # ========================================================

    def create_item(
        self,
        line: Any,
    ) -> LineItem:
        """
        Create a LineItem without adding it to the scene.

        This method is intended for explicit scene lifecycle
        management.

        Raises
        ------
        ValueError
            If a projection for the same object ID already
            exists in the scene.
        """

        object_id = self._get_object_id(
            line
        )

        if self.get_item(
            object_id
        ) is not None:
            raise ValueError(
                "A LineItem for "
                f"object_id={object_id!r} "
                "already exists."
            )

        start, end = self.get_model_endpoints(
            line
        )

        return LineItem(
            object_id=object_id,
            start=start,
            end=end,
            model=line,
        )

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        item: LineItem,
        line: Any,
    ) -> LineItem:
        """
        Synchronize an existing LineItem from the authoritative
        Line object.

        Only the graphical projection is modified.
        """

        if item is None:
            raise ValueError(
                "item must not be None."
            )

        if not isinstance(
            item,
            LineItem,
        ):
            raise TypeError(
                "item must be a LineItem."
            )

        object_id = self._get_object_id(
            line
        )

        if item.object_id != object_id:
            raise ValueError(
                "LineItem object_id does not match "
                "the supplied Line."
            )

        start, end = self.get_model_endpoints(
            line
        )

        item.set_model(
            line
        )

        item.set_endpoints(
            start,
            end,
        )

        return item

    # ========================================================
    # REMOVE
    # ========================================================

    def remove(
        self,
        object_id: Any,
    ) -> bool:
        """
        Remove the graphical Line projection identified by
        object_id.

        This does not delete the authoritative Line.
        """

        item = self.get_item(
            object_id
        )

        if item is None:
            return False

        self.scene.removeItem(
            item
        )

        return True

    # ========================================================
    # LOOKUP
    # ========================================================

    def get_item(
        self,
        object_id: Any,
    ) -> Optional[LineItem]:
        """
        Return the LineItem representing object_id.

        Returns None when no matching projection exists.
        """

        if object_id is None:
            return None

        for item in tuple(
            self.scene.items()
        ):
            if (
                isinstance(
                    item,
                    LineItem,
                )
                and item.object_id == object_id
            ):
                return item

        return None

    # ========================================================
    # BULK RENDERING
    # ========================================================

    def render_all(
        self,
        lines: Iterable[Any],
    ) -> tuple[LineItem, ...]:
        """
        Render a collection of authoritative Line objects.

        Existing projections are updated.

        New projections are created.

        Existing scene items not represented by the supplied
        collection are deliberately retained.

        Removal is explicit through remove().
        """

        if lines is None:
            raise ValueError(
                "lines must not be None."
            )

        result: list[LineItem] = []

        for line in lines:
            result.append(
                self.render(
                    line
                )
            )

        return tuple(
            result
        )

    # ========================================================
    # MODEL GEOMETRY
    # ========================================================

    @classmethod
    def get_model_endpoints(
        cls,
        line: Any,
    ) -> tuple[QPointF, QPointF]:
        """
        Extract presentation endpoints from an authoritative
        Line object.

        Supported endpoint representations are:

            line.start / line.end

        or:

            line.start_point / line.end_point

        or:

            line.from_point / line.to_point

        or:

            line.p1 / line.p2

        Callable attributes are also supported.

        No coordinate conversion is performed here.
        """

        if line is None:
            raise ValueError(
                "line must not be None."
            )

        start = cls._read_attribute(
            line,
            (
                "start",
                "start_point",
                "from_point",
                "p1",
            ),
        )

        end = cls._read_attribute(
            line,
            (
                "end",
                "end_point",
                "to_point",
                "p2",
            ),
        )

        if start is None:
            raise AttributeError(
                "Line must provide a start endpoint "
                "through start, start_point, "
                "from_point, or p1."
            )

        if end is None:
            raise AttributeError(
                "Line must provide an end endpoint "
                "through end, end_point, "
                "to_point, or p2."
            )

        return (
            cls._point_copy(
                start,
                "start",
            ),
            cls._point_copy(
                end,
                "end",
            ),
        )

    # ========================================================
    # MODEL IDENTITY
    # ========================================================

    @staticmethod
    def _get_object_id(
        line: Any,
    ) -> Any:
        """
        Extract the authoritative Line identifier.

        Supported forms:

            line.object_id
            line.id
        """

        if line is None:
            raise ValueError(
                "line must not be None."
            )

        object_id = getattr(
            line,
            "object_id",
            None,
        )

        if callable(object_id):
            object_id = object_id()

        if object_id is None:
            object_id = getattr(
                line,
                "id",
                None,
            )

            if callable(object_id):
                object_id = object_id()

        if object_id is None:
            raise AttributeError(
                "Line must provide object_id or id."
            )

        return object_id

    # ========================================================
    # ATTRIBUTE HELPERS
    # ========================================================

    @staticmethod
    def _read_attribute(
        obj: Any,
        names: tuple[str, ...],
    ) -> Any:
        """
        Return the first non-None attribute from names.

        Callable attributes are evaluated.
        """

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

        return None

    # --------------------------------------------------------

    @staticmethod
    def _point_copy(
        point: Any,
        name: str,
    ) -> QPointF:
        """
        Validate and copy a QPointF-compatible point.
        """

        if point is None:
            raise ValueError(
                f"{name} must not be None."
            )

        x = getattr(
            point,
            "x",
            None,
        )

        y = getattr(
            point,
            "y",
            None,
        )

        if not callable(x):
            raise TypeError(
                f"{name} must provide x()."
            )

        if not callable(y):
            raise TypeError(
                f"{name} must provide y()."
            )

        return QPointF(
            x(),
            y(),
        )

    # ========================================================
    # SCENE
    # ========================================================

    def set_scene(
        self,
        scene: QGraphicsScene,
    ) -> None:
        """
        Replace the target scene.

        Existing items are not migrated automatically.
        """

        if scene is None:
            raise ValueError(
                "scene must not be None."
            )

        self._validate_scene(
            scene
        )

        self.scene = scene

    # --------------------------------------------------------

    def get_scene(
        self,
    ) -> QGraphicsScene:
        """
        Return the target scene.
        """

        return self.scene

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic renderer state.
        """

        item_count = sum(
            1
            for item in tuple(
                self.scene.items()
            )
            if isinstance(
                item,
                LineItem,
            )
        )

        return {
            "renderer": type(self).__name__,
            "scene_attached": (
                self.scene is not None
            ),
            "line_item_count": item_count,
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_scene(
        scene: Any,
    ) -> None:
        """
        Validate the minimum scene contract required by the
        renderer.
        """

        required_methods = (
            "addItem",
            "removeItem",
            "items",
        )

        for method_name in required_methods:
            if not callable(
                getattr(
                    scene,
                    method_name,
                    None,
                )
            ):
                raise TypeError(
                    "scene must provide "
                    f"{method_name}()."
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

        state = self.get_state()

        return (
            "LineRenderer("
            f"line_items="
            f"{state['line_item_count']}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "LineRenderer",
]
