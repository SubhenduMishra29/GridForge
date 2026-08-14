"""
GridForge V2 — Canvas Preview Layer
===================================

File:
    ui/canvas/preview_layer.py

Purpose
-------
Owns transient graphics used exclusively during canvas
interaction.

Preview graphics are presentation-only and are never part of
the authoritative GridForge model.

Typical uses:

    - rubber-band line previews
    - placement previews
    - hover indicators
    - temporary snap indicators
    - future transient interaction graphics


Architecture
------------

    InteractionManager
           │
           ▼
      PreviewLayer
           │
           ▼
      QGraphicsScene
           │
           ▼
    transient graphics


Ownership
---------
InteractionManager owns the PreviewLayer.

PreviewLayer owns the transient QGraphicsItems that it creates.

Tools do not directly own preview graphics. They request preview
changes through the interaction layer.


Architectural boundaries
------------------------
PreviewLayer does NOT:

    - modify the Core model;
    - create domain objects;
    - persist state;
    - participate in undo/redo;
    - render authoritative model graphics;
    - perform snapping;
    - perform coordinate conversion;
    - implement tool logic;
    - perform electrical calculations;
    - handle mouse interaction.


RenderSystem
------------
Preview graphics are deliberately outside RenderSystem ownership.

RenderSystem is responsible for authoritative/persistent model
visualization.

PreviewLayer is responsible only for transient interaction
feedback.


Qt Rule
-------
All Qt dependencies must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import (
    QColor,
    QGraphicsLineItem,
    QPen,
    Qt,
)


class PreviewLayer:
    """
    Manager for transient canvas preview graphics.

    PreviewLayer contains no domain-model state and no
    interaction policy.

    It manages only temporary graphics attached to the
    canvas scene.
    """

    # ========================================================
    # VISUAL CONSTANTS
    # ========================================================

    # Preview graphics remain visually above normal
    # authoritative graphics.
    PREVIEW_Z_VALUE = 1000.0

    PREVIEW_PEN_WIDTH = 2.0

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        scene: Any,
    ) -> None:
        """
        Initialize the PreviewLayer.

        Parameters
        ----------
        scene:
            QGraphicsScene receiving transient preview items.
        """

        if scene is None:
            raise ValueError(
                "scene must not be None."
            )

        if not callable(
            getattr(
                scene,
                "addItem",
                None,
            )
        ):
            raise TypeError(
                "scene must provide addItem()."
            )

        if not callable(
            getattr(
                scene,
                "removeItem",
                None,
            )
        ):
            raise TypeError(
                "scene must provide removeItem()."
            )

        self.scene = scene

        # ----------------------------------------------------
        # Active line preview.
        # ----------------------------------------------------

        self._line_item: Optional[
            QGraphicsLineItem
        ] = None

        # ----------------------------------------------------
        # Default transient preview style.
        # ----------------------------------------------------

        self._pen = QPen(
            QColor("gray"),
            self.PREVIEW_PEN_WIDTH,
            Qt.PenStyle.DashLine,
        )

    # ========================================================
    # LINE PREVIEW
    # ========================================================

    def show_line(
        self,
        start_pos: Any,
        end_pos: Any,
    ) -> QGraphicsLineItem:
        """
        Create or update the active line preview.

        Parameters
        ----------
        start_pos:
            Scene-space start point.

        end_pos:
            Scene-space end point.

        Returns
        -------
        QGraphicsLineItem
            The active transient preview item.

        Notes
        -----
        The supplied points must already be in scene
        coordinates.

        Coordinate conversion and snapping are deliberately
        outside PreviewLayer.
        """

        self._validate_point(
            start_pos,
            "start_pos",
        )

        self._validate_point(
            end_pos,
            "end_pos",
        )

        # ----------------------------------------------------
        # Create lazily.
        # ----------------------------------------------------

        if self._line_item is None:

            item = QGraphicsLineItem()

            # ------------------------------------------------
            # Preview graphics are never interaction targets.
            # ------------------------------------------------

            item.setAcceptedMouseButtons(
                Qt.MouseButton.NoButton
            )

            item.setFlag(
                QGraphicsLineItem.GraphicsItemFlag.ItemIsSelectable,
                False,
            )

            item.setFlag(
                QGraphicsLineItem.GraphicsItemFlag.ItemIsFocusable,
                False,
            )

            item.setZValue(
                self.PREVIEW_Z_VALUE
            )

            item.setPen(
                self._pen
            )

            self._line_item = item

            self.scene.addItem(
                item
            )

        # ----------------------------------------------------
        # Update geometry.
        # ----------------------------------------------------

        self._line_item.setLine(
            float(start_pos.x()),
            float(start_pos.y()),
            float(end_pos.x()),
            float(end_pos.y()),
        )

        return self._line_item

    # ========================================================
    # LINE PREVIEW ACCESS
    # ========================================================

    def has_line(
        self,
    ) -> bool:
        """
        Return whether an active line preview exists.
        """

        return self._line_item is not None

    # --------------------------------------------------------

    def get_line(
        self,
    ) -> Optional[QGraphicsLineItem]:
        """
        Return the active line preview item, if present.
        """

        return self._line_item

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Remove all active transient preview graphics.

        The operation is idempotent.
        """

        item = self._line_item

        if item is None:
            return

        self.scene.removeItem(
            item
        )

        self._line_item = None

    # ========================================================
    # RESET
    # ========================================================

    def reset(
        self,
    ) -> None:
        """
        Reset all transient preview state.

        Resetting the PreviewLayer is equivalent to clearing
        all active transient graphics.
        """

        self.clear()

    # ========================================================
    # STYLE
    # ========================================================

    def set_pen(
        self,
        pen: QPen,
    ) -> None:
        """
        Set the pen used by line previews.

        The active preview, if present, is updated immediately.
        """

        if pen is None:
            raise ValueError(
                "pen must not be None."
            )

        self._pen = pen

        if self._line_item is not None:

            self._line_item.setPen(
                self._pen
            )

    # --------------------------------------------------------

    def get_pen(
        self,
    ) -> QPen:
        """
        Return the current preview pen.
        """

        return self._pen

    # ========================================================
    # SCENE ACCESS
    # ========================================================

    def get_scene(
        self,
    ) -> Any:
        """
        Return the scene receiving transient preview graphics.
        """

        return self.scene

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_point(
        point: Any,
        name: str,
    ) -> None:
        """
        Validate a QPointF-compatible object.

        Only the x()/y() interface is required.
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
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic preview state.

        The diagnostic state deliberately does not expose
        QGraphicsItem instances.
        """

        return {
            "has_line": self.has_line(),
        }

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "PreviewLayer("
            f"has_line={self.has_line()}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "PreviewLayer",
]
