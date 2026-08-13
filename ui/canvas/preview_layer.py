"""
GridForge V2 — Canvas Preview Layer
===================================

File:
    ui/canvas/preview_layer.py

Purpose
-------
Provides transient, non-model graphics used during canvas
interaction.

Typical uses include:

    - rubber-band line previews;
    - placement previews;
    - hover indicators;
    - temporary snap indicators;
    - future transient interaction graphics.

Architectural Rules
-------------------
Preview graphics:

    - are NOT part of the Core model;
    - are NOT persisted;
    - are NOT authoritative;
    - are NOT rendered by RenderSystem;
    - exist only for the duration of an interaction;
    - are owned by the canvas interaction layer.

Ownership
---------
InteractionManager owns PreviewLayer.

PreviewLayer owns the temporary QGraphicsItems that it creates.

Tools may request preview changes through the interaction layer,
but tools do not own the preview graphics themselves.

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

    PreviewLayer deliberately contains no domain-model logic.

    It operates exclusively on temporary graphics associated
    with the canvas scene.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        scene: Any,
    ) -> None:
        """
        Initialize the preview layer.

        Parameters
        ----------
        scene:
            QGraphicsScene on which transient preview graphics
            will be displayed.
        """

        if scene is None:
            raise ValueError(
                "scene must not be None"
            )

        self.scene = scene

        # ----------------------------------------------------
        # Active line preview
        # ----------------------------------------------------
        #
        # None means no line preview currently exists.
        # ----------------------------------------------------

        self._line_item: Optional[
            QGraphicsLineItem
        ] = None

        # ----------------------------------------------------
        # Default preview style
        # ----------------------------------------------------

        self._pen = QPen(
            QColor("gray"),
            2,
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
        Create or update a transient line preview.

        Parameters
        ----------
        start_pos:
            Scene-space point providing the line origin.

        end_pos:
            Scene-space point providing the line endpoint.

        Returns
        -------
        QGraphicsLineItem
            The active preview line item.

        Notes
        -----
        The returned item is transient and must not be inserted
        into the Core model or treated as an authoritative
        graphical representation.
        """

        if start_pos is None:
            raise ValueError(
                "start_pos must not be None"
            )

        if end_pos is None:
            raise ValueError(
                "end_pos must not be None"
            )

        # ----------------------------------------------------
        # Create the preview item lazily.
        # ----------------------------------------------------

        if self._line_item is None:

            self._line_item = (
                QGraphicsLineItem()
            )

            self._line_item.setPen(
                self._pen
            )

            self.scene.addItem(
                self._line_item
            )

        # ----------------------------------------------------
        # Update geometry.
        # ----------------------------------------------------

        self._line_item.setLine(
            start_pos.x(),
            start_pos.y(),
            end_pos.x(),
            end_pos.y(),
        )

        return self._line_item

    # ========================================================
    # LINE PREVIEW ACCESS
    # ========================================================

    def has_line(
        self,
    ) -> bool:
        """
        Return True when a line preview is currently active.
        """

        return self._line_item is not None

    # --------------------------------------------------------

    def get_line(
        self,
    ) -> Optional[QGraphicsLineItem]:
        """
        Return the active line preview item.

        Returns
        -------
        QGraphicsLineItem | None
        """

        return self._line_item

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Remove all currently active preview graphics.

        This operation is idempotent.
        """

        if self._line_item is not None:

            self.scene.removeItem(
                self._line_item
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

        Currently equivalent to clear(), but kept as an
        explicit lifecycle operation so additional preview
        types can be added without changing callers.
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
        Set the pen used for subsequently created or updated
        line previews.

        Parameters
        ----------
        pen:
            QPen defining the preview line appearance.
        """

        if not isinstance(pen, QPen):
            raise TypeError(
                "pen must be a QPen"
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
        Return the QGraphicsScene owned by this preview layer.
        """

        return self.scene

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of preview state.
        """

        return {
            "has_line": self.has_line(),
            "line_item": self._line_item,
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
