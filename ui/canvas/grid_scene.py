# ============================================================
# File: ui/canvas/grid_scene.py
# GridForge V2 — Canvas Scene
# ============================================================
"""
GridForge V2 canvas scene.

QGraphicsScene is the scene boundary between the canvas viewport
and the permanent graphical projection managed by RenderSystem.

Responsibilities
----------------
GridScene:

    - owns the canvas scene rectangle;
    - provides a stable QGraphicsScene boundary;
    - maintains scene-level presentation configuration;
    - provides controlled scene clearing/reset operations;
    - exposes diagnostic scene state;
    - provides a stable place for canvas-level scene metadata.

GridScene does NOT:

    - own the Core model;
    - create electrical model objects;
    - implement electrical topology;
    - implement tool behavior;
    - perform selection logic;
    - perform snapping;
    - perform navigation;
    - calculate electrical quantities;
    - own concrete renderers;
    - decide what domain objects should be rendered.

Rendering
---------

Permanent graphical objects are created and managed by the
RenderSystem and renderer layer.

GridScene is therefore deliberately passive.

Architecture
------------

                    GraphicsView
                         │
                         ▼
                     GridScene
                         │
                ┌────────┴────────┐
                ▼                 ▼
          RenderSystem       UI services
                │
                ▼
             Renderers
                │
                ▼
        QGraphicsItems

Qt Boundary
-----------

All Qt dependencies must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import (
    QGraphicsScene,
    QRectF,
)


class GridScene(QGraphicsScene):
    """
    GridForge canvas scene.

    GridScene is intentionally a thin scene container.

    Domain state remains outside the scene and graphical items
    remain projections of authoritative application state.
    """

    # ========================================================
    # DEFAULT SCENE CONFIGURATION
    # ========================================================

    DEFAULT_SCENE_RECT = QRectF(
        -5000.0,
        -5000.0,
        10000.0,
        10000.0,
    )

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        parent: Optional[Any] = None,
    ) -> None:
        """
        Initialize the GridForge canvas scene.

        Parameters
        ----------
        parent:
            Optional Qt parent object.
        """

        super().__init__(parent)

        self._configured_scene_rect = QRectF(
            self.DEFAULT_SCENE_RECT
        )

        self.setSceneRect(
            self._configured_scene_rect
        )

    # ========================================================
    # SCENE RECTANGLE
    # ========================================================

    def set_canvas_rect(
        self,
        rect: QRectF,
    ) -> None:
        """
        Set the logical canvas scene rectangle.

        This controls the available scene coordinate extent.

        It does not move or modify graphical items.
        """

        if rect is None:
            raise ValueError(
                "rect must not be None."
            )

        if not isinstance(
            rect,
            QRectF,
        ):
            raise TypeError(
                "rect must be a QRectF."
            )

        if rect.isNull():
            raise ValueError(
                "rect must not be null."
            )

        if rect.width() <= 0:
            raise ValueError(
                "rect width must be greater than zero."
            )

        if rect.height() <= 0:
            raise ValueError(
                "rect height must be greater than zero."
            )

        self._configured_scene_rect = QRectF(
            rect
        )

        self.setSceneRect(
            self._configured_scene_rect
        )

    # --------------------------------------------------------

    def get_canvas_rect(
        self,
    ) -> QRectF:
        """
        Return the configured logical canvas rectangle.
        """

        return QRectF(
            self._configured_scene_rect
        )

    # ========================================================
    # CONTENT RECTANGLE
    # ========================================================

    def get_content_rect(
        self,
    ) -> QRectF:
        """
        Return the bounding rectangle of all scene content.

        This is a graphical projection query only.

        It does not imply ownership of the objects represented
        by the scene items.
        """

        return QRectF(
            self.itemsBoundingRect()
        )

    # --------------------------------------------------------

    def has_content(
        self,
    ) -> bool:
        """
        Return True when the scene contains graphical items.
        """

        return bool(
            self.items()
        )

    # ========================================================
    # SCENE CLEARING
    # ========================================================

    def clear_items(
        self,
    ) -> None:
        """
        Remove all graphical items from the scene.

        This operation affects only the UI projection.

        It does not modify the Core model or application state.
        """

        self.clear()

    # --------------------------------------------------------

    def reset_scene(
        self,
    ) -> None:
        """
        Clear all graphical items and restore the default
        logical canvas rectangle.
        """

        self.clear()

        self._configured_scene_rect = QRectF(
            self.DEFAULT_SCENE_RECT
        )

        self.setSceneRect(
            self._configured_scene_rect
        )

    # ========================================================
    # ITEM ACCESS
    # ========================================================

    def get_items(
        self,
    ) -> tuple[Any, ...]:
        """
        Return a snapshot of all scene items.

        The returned tuple does not expose mutable scene
        ownership semantics.
        """

        return tuple(
            self.items()
        )

    # --------------------------------------------------------

    def get_item_count(
        self,
    ) -> int:
        """
        Return the number of graphical items in the scene.
        """

        return len(
            self.items()
        )

    # ========================================================
    # OBJECT-ID LOOKUP
    # ========================================================

    def find_item_by_object_id(
        self,
        object_id: Any,
    ) -> Optional[Any]:
        """
        Find the first graphical item exposing the requested
        application object ID.

        Graphics items may expose:

            object_id

        This is a projection lookup only.
        """

        if object_id is None:
            return None

        for item in tuple(
            self.items()
        ):
            item_id = getattr(
                item,
                "object_id",
                None,
            )

            if item_id == object_id:
                return item

        return None

    # --------------------------------------------------------

    def find_items_by_object_id(
        self,
        object_id: Any,
    ) -> tuple[Any, ...]:
        """
        Find all graphical items exposing the requested
        application object ID.
        """

        if object_id is None:
            return ()

        result = []

        for item in tuple(
            self.items()
        ):
            item_id = getattr(
                item,
                "object_id",
                None,
            )

            if item_id == object_id:
                result.append(
                    item
                )

        return tuple(
            result
        )

    # ========================================================
    # SELECTION PROJECTION SUPPORT
    # ========================================================

    def clear_graphical_selection(
        self,
    ) -> None:
        """
        Clear QGraphicsItem selection state.

        This does NOT modify authoritative application
        selection stored by Controller.
        """

        for item in tuple(
            self.items()
        ):
            set_selected = getattr(
                item,
                "setSelected",
                None,
            )

            if callable(
                set_selected
            ):
                set_selected(False)

    # ========================================================
    # SCENE COORDINATE HELPERS
    # ========================================================

    def contains_scene_point(
        self,
        point: Any,
    ) -> bool:
        """
        Return whether a scene point lies inside the configured
        canvas rectangle.
        """

        if point is None:
            raise ValueError(
                "point must not be None."
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

        if not callable(x) or not callable(y):
            raise TypeError(
                "point must provide x() and y()."
            )

        return self.sceneRect().contains(
            point
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of the scene.
        """

        rect = self.sceneRect()

        return {
            "item_count": len(
                self.items()
            ),
            "scene_rect": rect,
            "content_rect": (
                self.itemsBoundingRect()
            ),
            "has_content": bool(
                self.items()
            ),
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        rect = self.sceneRect()

        return (
            "GridScene("
            f"items={len(self.items())}, "
            f"rect=("
            f"{rect.x():.1f}, "
            f"{rect.y():.1f}, "
            f"{rect.width():.1f}, "
            f"{rect.height():.1f}"
            ")"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "GridScene",
]
