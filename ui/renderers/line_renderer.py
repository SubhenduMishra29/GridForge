# ============================================================
# File: ui/renderers/line_renderer.py
# GridForge V2 — Line Renderer
# ============================================================
"""
Concrete renderer for authoritative GridForge Line objects.

Architecture
------------

    Authoritative Core/Application Line
                    │
                    ▼
              LineRenderer
                    │
                    ▼
                 LineItem
                    │
                    ▼
              QGraphicsScene

Purpose
-------
LineRenderer converts authoritative Line state into its
graphical presentation.

The Line object remains the single source of engineering truth.

LineRenderer is a presentation-layer adapter only.

It does NOT:

    - create or mutate Core engineering objects;
    - determine electrical topology;
    - perform electrical calculations;
    - perform snapping;
    - implement tools;
    - own application selection state;
    - perform navigation;
    - own the Canvas;
    - own the QGraphicsScene;
    - persist project state;
    - maintain an independent engineering-state cache.

Rendering direction
-------------------

    Core/Application State
            ↓
        LineRenderer
            ↓
          LineItem
            ↓
       Graphics Scene

The reverse direction is prohibited:

    LineItem
       ↓
    LineRenderer
       ↓
    Core engineering state

Geometry
--------
The renderer reads presentation geometry from the authoritative
Line model.

No viewport/scene/grid transformation is performed here.

Coordinate conversion belongs to CoordinateSystem.

Topology
--------
The renderer does not determine electrical connectivity.

Any relationship between a Line and its terminals remains
authoritative in the Core/network layer.

Qt Architecture
----------------
All Qt dependencies pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.qt import (
    QGraphicsScene,
    QPointF,
)

from ui.items.line_item import LineItem
from ui.renderers.renderer_base import RendererBase
from ui.renderers.renderer_utils import (
    find_item_by_object_id,
    get_object_id,
    read_attribute,
    to_pointf,
    to_point_pair,
)


class LineRenderer(RendererBase):
    """
    Render authoritative Line objects as LineItem projections.

    The renderer does not maintain a persistent application-model
    cache.

    The graphics scene is the container for graphical
    projections.

    Parameters
    ----------
    scene:
        Target QGraphicsScene-compatible object.
    """

    # ========================================================
    # RENDER
    # ========================================================

    def render(
        self,
        model: Any,
    ) -> LineItem:
        """
        Create or update the graphical projection of a Line.

        Existing projections are synchronized.

        Missing projections are created and attached to the
        renderer scene.

        The authoritative Line is never modified.
        """

        object_id = self._get_object_id(
            model
        )

        existing = self.get_item(
            object_id
        )

        if existing is not None:
            return self.update(
                existing,
                model,
            )

        item = self.create_item(
            model
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
        model: Any,
    ) -> LineItem:
        """
        Create a LineItem projection without adding it to the
        scene.

        Raises
        ------
        ValueError
            If a projection for the same object_id already
            exists.
        """

        object_id = self._get_object_id(
            model
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
            model
        )

        return LineItem(
            object_id=object_id,
            start=start,
            end=end,
            model=model,
        )

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        item: LineItem,
        model: Any,
    ) -> LineItem:
        """
        Synchronize an existing LineItem from authoritative
        Line state.

        Only the graphical projection is modified.

        The authoritative Line is never modified.
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
            model
        )

        if item.object_id != object_id:
            raise ValueError(
                "LineItem object_id does not match "
                "the supplied Line."
            )

        start, end = self.get_model_endpoints(
            model
        )

        item.set_model(
            model
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

        This removes only the graphical representation.

        The authoritative Core Line is never deleted or modified.
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
        Return the LineItem projection for object_id.

        Returns None when no matching projection exists.
        """

        if object_id is None:
            return None

        item = find_item_by_object_id(
            self.scene,
            object_id,
            LineItem,
        )

        if item is None:
            return None

        return item

    # ========================================================
    # BULK SYNCHRONIZATION
    # ========================================================

    def render_all(
        self,
        models: Iterable[Any],
    ) -> tuple[LineItem, ...]:
        """
        Render a collection of authoritative Line objects.

        Existing projections are updated.

        Missing projections are created.

        Existing scene projections not represented by the supplied
        collection are retained.

        Removal remains explicit through remove().
        """

        if models is None:
            raise ValueError(
                "models must not be None."
            )

        result: list[LineItem] = []

        for model in models:
            result.append(
                self.render(
                    model
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
        model: Any,
    ) -> tuple[QPointF, QPointF]:
        """
        Extract presentation endpoints from the authoritative
        Line model.

        Supported public endpoint representations are:

            start / end

            start_point / end_point

            from_point / to_point

            p1 / p2

        Callable attributes are supported.

        No coordinate transformation or snapping is performed.
        """

        if model is None:
            raise ValueError(
                "model must not be None."
            )

        start = read_attribute(
            model,
            (
                "start",
                "start_point",
                "from_point",
                "p1",
            ),
        )

        end = read_attribute(
            model,
            (
                "end",
                "end_point",
                "to_point",
                "p2",
            ),
        )

        if start is None:
            raise AttributeError(
                "Line must provide a start endpoint through "
                "start, start_point, from_point, or p1."
            )

        if end is None:
            raise AttributeError(
                "Line must provide an end endpoint through "
                "end, end_point, to_point, or p2."
            )

        return to_point_pair(
            start,
            end,
        )

    # ========================================================
    # MODEL IDENTITY
    # ========================================================

    @staticmethod
    def _get_object_id(
        model: Any,
    ) -> Any:
        """
        Extract the authoritative Line identifier using the
        shared renderer identity contract.
        """

        return get_object_id(
            model
        )

    # ========================================================
    # SCENE
    # ========================================================

    def set_scene(
        self,
        scene: QGraphicsScene,
    ) -> None:
        """
        Replace the target graphics scene.

        Existing graphical items are not migrated automatically.

        RendererBase owns scene validation.
        """

        super().set_scene(
            scene
        )

    # --------------------------------------------------------

    def get_scene(
        self,
    ) -> QGraphicsScene:
        """
        Return the currently attached graphics scene.
        """

        return super().get_scene()

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic renderer state.
        """

        state = super().get_state()

        line_item_count = sum(
            1
            for item in tuple(
                self.scene.items()
            )
            if isinstance(
                item,
                LineItem,
            )
        )

        state.update(
            {
                "line_item_count": line_item_count,
            }
        )

        return state

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
