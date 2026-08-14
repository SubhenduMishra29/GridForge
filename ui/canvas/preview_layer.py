# ============================================================
# File: ui/canvas/preview_layer.py
# GridForge V2 — Canvas Preview Layer
# ============================================================
"""
Transient preview layer for the GridForge canvas.

PreviewLayer owns temporary graphics used while an interaction
is in progress.

Typical uses include:

    - LineTool connection preview;
    - cursor-to-bus preview;
    - placement preview;
    - temporary connection path;
    - tool-specific transient geometry.

Architecture
------------

    Active Tool
         │
         ▼
    InteractionManager
         │
         ▼
    PreviewLayer
         │
         ▼
    QGraphicsScene
         │
         ▼
    Temporary QGraphicsItems

Ownership
---------
PreviewLayer owns the lifecycle of preview graphics.

Preview graphics:

    - are transient;
    - are never Core model objects;
    - are never persisted;
    - are never authoritative;
    - must be removed when the interaction is cancelled,
      completed, reset, or disposed.

PreviewLayer does NOT:

    - modify Core state;
    - create permanent model graphics;
    - manage tools;
    - manage selection;
    - perform snapping;
    - perform navigation;
    - perform electrical calculations;
    - decide tool behavior.

Renderer relationship
---------------------
Permanent model rendering belongs to RenderSystem and the
RendererRegistry.

PreviewLayer is intentionally separate because preview graphics
do not represent committed application state.

Qt Architecture
---------------
All Qt dependencies must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.qt import (
    QGraphicsItem,
    QGraphicsScene,
)


class PreviewLayer:
    """
    Owner of transient canvas preview graphics.

    The class provides a small, deterministic API for tools and
    InteractionManager without exposing scene-management policy
    to individual tools.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        scene: QGraphicsScene,
    ) -> None:
        """
        Initialize the preview layer.

        Parameters
        ----------
        scene:
            QGraphicsScene in which transient preview items are
            displayed.
        """

        if scene is None:
            raise ValueError(
                "scene must not be None."
            )

        self.scene = scene

        self._items: list[QGraphicsItem] = []

    # ========================================================
    # SCENE ACCESS
    # ========================================================

    def get_scene(
        self,
    ) -> QGraphicsScene:
        """
        Return the scene managed by the preview layer.
        """

        return self.scene

    # ========================================================
    # ADD PREVIEW
    # ========================================================

    def add(
        self,
        item: QGraphicsItem,
    ) -> QGraphicsItem:
        """
        Add one transient graphics item to the preview layer.

        The item is added to the scene if it is not already
        associated with a scene.

        Returns
        -------
        QGraphicsItem
            The supplied item.
        """

        if item is None:
            raise ValueError(
                "item must not be None."
            )

        if not isinstance(
            item,
            QGraphicsItem,
        ):
            raise TypeError(
                "item must be a QGraphicsItem."
            )

        # Prevent accidental duplicate ownership.
        if item not in self._items:
            self._items.append(
                item
            )

        if item.scene() is None:
            self.scene.addItem(
                item
            )

        return item

    # --------------------------------------------------------

    def add_items(
        self,
        items: Iterable[QGraphicsItem],
    ) -> tuple[QGraphicsItem, ...]:
        """
        Add multiple transient graphics items.
        """

        if items is None:
            raise ValueError(
                "items must not be None."
            )

        added = []

        for item in items:
            added.append(
                self.add(
                    item
                )
            )

        return tuple(
            added
        )

    # ========================================================
    # REMOVE PREVIEW
    # ========================================================

    def remove(
        self,
        item: QGraphicsItem,
    ) -> bool:
        """
        Remove one preview item.

        Returns
        -------
        bool
            True when the item was owned by this preview layer.
        """

        if item is None:
            return False

        if item not in self._items:
            return False

        self._items.remove(
            item
        )

        if item.scene() is self.scene:
            self.scene.removeItem(
                item
            )

        return True

    # --------------------------------------------------------

    def remove_items(
        self,
        items: Iterable[QGraphicsItem],
    ) -> int:
        """
        Remove multiple preview items.

        Returns the number of removed items.
        """

        if items is None:
            raise ValueError(
                "items must not be None."
            )

        removed = 0

        for item in tuple(
            items
        ):
            if self.remove(
                item
            ):
                removed += 1

        return removed

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Remove every transient preview item.
        """

        for item in tuple(
            self._items
        ):
            if item.scene() is self.scene:
                self.scene.removeItem(
                    item
                )

        self._items.clear()

    # ========================================================
    # QUERY
    # ========================================================

    def items(
        self,
    ) -> tuple[QGraphicsItem, ...]:
        """
        Return a snapshot of currently owned preview items.
        """

        return tuple(
            self._items
        )

    # --------------------------------------------------------

    def count(
        self,
    ) -> int:
        """
        Return the number of active preview items.
        """

        return len(
            self._items
        )

    # --------------------------------------------------------

    def is_empty(
        self,
    ) -> bool:
        """
        Return True when no preview graphics are active.
        """

        return not self._items

    # --------------------------------------------------------

    def contains(
        self,
        item: QGraphicsItem,
    ) -> bool:
        """
        Return True when the item belongs to this preview layer.
        """

        return item in self._items

    # ========================================================
    # REPLACE
    # ========================================================

    def replace(
        self,
        items: Iterable[QGraphicsItem],
    ) -> tuple[QGraphicsItem, ...]:
        """
        Replace the complete transient preview set.

        Existing preview graphics are removed before the new
        items are added.
        """

        self.clear()

        return self.add_items(
            items
        )

    # ========================================================
    # VISIBILITY
    # ========================================================

    def set_visible(
        self,
        visible: bool,
    ) -> None:
        """
        Set visibility of all preview graphics.
        """

        if not isinstance(
            visible,
            bool,
        ):
            raise TypeError(
                "visible must be a bool."
            )

        for item in tuple(
            self._items
        ):
            item.setVisible(
                visible
            )

    # --------------------------------------------------------

    def is_visible(
        self,
    ) -> bool:
        """
        Return True when the preview layer is visible.

        If the layer contains no items, this returns False.
        """

        if not self._items:
            return False

        return any(
            item.isVisible()
            for item in self._items
        )

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
    ) -> None:
        """
        Request a visual update for all preview items.
        """

        for item in tuple(
            self._items
        ):
            item.update()

    # ========================================================
    # RESET / DISPOSE
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset transient preview state.
        """

        self.clear()

    # --------------------------------------------------------

    def dispose(
        self,
    ) -> None:
        """
        Release all transient preview graphics.

        The scene itself is not owned by PreviewLayer and is not
        destroyed.
        """

        self.clear()

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic preview state.
        """

        return {
            "scene": self.scene is not None,
            "item_count": len(
                self._items
            ),
            "visible": self.is_visible(),
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

        return (
            "PreviewLayer("
            f"items={len(self._items)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "PreviewLayer",
]
