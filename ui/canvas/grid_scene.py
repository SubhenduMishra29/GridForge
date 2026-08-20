# ============================================================
# File: ui/canvas/grid_scene.py
# GridForge V2 — Canvas Scene
# ============================================================
"""
GridForge V2 canvas scene.

GridScene is the QGraphicsScene boundary of the SLD canvas.

Architectural role
------------------
GridScene is a passive graphical scene container.

The authoritative application/model state remains outside the
scene. Graphical objects placed in the scene are projections of
that state and are managed by the rendering layer.

Responsibilities
----------------
GridScene owns only scene-level canvas concerns:

    - canvas scene rectangle;
    - scene-level presentation boundary;
    - graphical item access;
    - controlled graphical clearing/reset;
    - projection-oriented object-ID lookup;
    - graphical selection-state clearing;
    - diagnostic scene state.

GridScene does NOT:

    - own Core state;
    - create electrical model objects;
    - validate electrical topology;
    - implement tools;
    - implement snapping;
    - implement navigation;
    - own authoritative selection;
    - perform electrical calculations;
    - own renderers;
    - decide which domain objects are rendered.

Rendering boundary
------------------
Permanent graphical projection is managed by RenderSystem and
the renderer layer.

    Domain/Application State
              |
              v
        RenderSystem
              |
              v
          Renderer
              |
              v
          GridScene
              |
              v
       QGraphicsItem

GridScene therefore remains passive.

Qt boundary
-----------
All Qt dependencies pass through:

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
    Passive QGraphicsScene boundary for the GridForge canvas.

    GridScene contains graphical projection state only. It does
    not become the owner of application or electrical-domain
    state.
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
        Initialize the canvas scene.
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

        This changes only the scene coordinate extent. Existing
        graphical items are not modified or repositioned.
        """

        self._validate_rect(
            rect,
            "rect",
        )

        if rect.isNull():
            raise ValueError(
                "rect must not be null."
            )

        if rect.width() <= 0.0:
            raise ValueError(
                "rect width must be greater than zero."
            )

        if rect.height() <= 0.0:
            raise ValueError(
                "rect height must be greater than zero."
            )

        configured = QRectF(
            rect
        )

        self._configured_scene_rect = configured

        self.setSceneRect(
            configured
        )

    # --------------------------------------------------------

    def get_canvas_rect(
        self,
    ) -> QRectF:
        """
        Return a copy of the configured canvas rectangle.
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
        Return the bounding rectangle of graphical scene items.

        This is a projection query only.
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
        Remove all graphical items.

        Core/application state is not modified.
        """

        self.clear()

    # --------------------------------------------------------

    def reset_scene(
        self,
    ) -> None:
        """
        Clear graphical content and restore the default scene
        rectangle.
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
        Return a stable snapshot of scene items.
        """

        return tuple(
            self.items()
        )

    # --------------------------------------------------------

    def get_item_count(
        self,
    ) -> int:
        """
        Return the number of graphical scene items.
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
        Return the first graphical item whose ``object_id``
        matches the requested application object ID.

        This is projection lookup only.
        """

        if object_id is None:
            return None

        for item in tuple(
            self.items()
        ):
            if getattr(
                item,
                "object_id",
                None,
            ) == object_id:
                return item

        return None

    # --------------------------------------------------------

    def find_items_by_object_id(
        self,
        object_id: Any,
    ) -> tuple[Any, ...]:
        """
        Return all graphical items whose ``object_id`` matches.
        """

        if object_id is None:
            return ()

        result: list[Any] = []

        for item in tuple(
            self.items()
        ):
            if getattr(
                item,
                "object_id",
                None,
            ) == object_id:
                result.append(
                    item
                )

        return tuple(
            result
        )

    # ========================================================
    # GRAPHICAL SELECTION PROJECTION
    # ========================================================

    def clear_graphical_selection(
        self,
    ) -> None:
        """
        Clear the Qt graphical selection state of scene items.

        This does not modify authoritative application selection.
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
        Return whether a point lies within the configured
        scene rectangle.
        """

        self._validate_point(
            point,
            "point",
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
        content = self.itemsBoundingRect()
        items = self.items()

        return {
            "item_count": len(items),
            "scene_rect": QRectF(rect),
            "content_rect": QRectF(content),
            "has_content": bool(items),
        }

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_rect(
        rect: Any,
        name: str,
    ) -> None:
        """
        Validate a QRectF-compatible canvas rectangle.

        Public canvas configuration deliberately requires QRectF
        so the Qt boundary remains explicit and deterministic.
        """

        if rect is None:
            raise ValueError(
                f"{name} must not be None."
            )

        if not isinstance(
            rect,
            QRectF,
        ):
            raise TypeError(
                f"{name} must be a QRectF."
            )

    # --------------------------------------------------------

    @staticmethod
    def _validate_point(
        point: Any,
        name: str,
    ) -> None:
        """
        Validate a QPoint/QPointF-compatible point.
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
