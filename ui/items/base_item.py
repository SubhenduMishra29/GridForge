# ============================================================
# File: ui/items/base_item.py
# GridForge V2 — Base Graphics Item
# Author: Subhendu Mishra
# ============================================================

"""
GridForge V2 Base Graphics Item.

BaseItem is the common presentation-layer foundation for
GridForge QGraphicsObject implementations.

Architecture
------------

    SLD read-side / presentation identity
                  │
                  ▼
               BaseItem
                  │
                  ├── graphical state
                  ├── selection projection
                  ├── interaction state
                  └── presentation lifecycle
                           │
                           ▼
                      QGraphicsScene

BaseItem is a presentation object only.

It does not own engineering truth, application state, or
network topology. Its ``object_id`` identifies the projected
presentation object; it is not a Core object reference.

Authoritative engineering mutation remains outside the item layer
and follows the command boundary:

    user intent → Command → Application → Core
"""

from __future__ import annotations

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
    Common presentation-layer base class for GridForge
    graphics items.

    BaseItem provides shared graphics infrastructure while
    keeping engineering ownership outside the UI layer.

    Concrete subclasses are responsible for implementing:

        - boundingRect()
        - paint()

    BaseItem does not define item-specific visual geometry.
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
        Initialize the graphics item.

        Parameters
        ----------
        object_id:
            Stable identity of the projected presentation object.
            It is an identity reference only and does not transfer
            ownership of authoritative engineering state to the item.

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
        Return the stable identity of the projected object.

        The identifier is an identity reference only.

        It is not:

            - a QGraphicsItem identity;
            - an authoritative network index;
            - an electrical topology index;
            - a Core object reference owned by the item.
        """

        return self._object_id

    # --------------------------------------------------------

    def get_object_id(self) -> Any:
        """
        Return the stable identity of the projected object.
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

        This changes presentation state only.

        Application-level selection must be coordinated through
        the appropriate presentation/controller selection
        infrastructure.
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

    # --------------------------------------------------------

    def clear_graphical_selection(self) -> None:
        """
        Clear the graphical selection state.

        This affects only the QGraphicsItem presentation.
        """

        self.setSelected(False)

    # ========================================================
    # POSITION
    # ========================================================

    def get_scene_position(self) -> tuple[float, float]:
        """
        Return the item's scene position.

        The returned coordinates represent UI presentation
        geometry only.

        They are not electrical coordinates or topology state.
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

        Validation of whether the position is appropriate for
        an engineering object belongs outside BaseItem.
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

        Concrete graphics items must provide their own
        presentation geometry.
        """

        raise NotImplementedError

    # --------------------------------------------------------

    def scene_bounding_rect(self) -> QRectF:
        """
        Return the item's scene-space bounding rectangle.

        This is a convenience accessor for UI infrastructure.
        """

        return self.mapRectToScene(
            self.boundingRect()
        )

    # ========================================================
    # PAINTING
    # ========================================================

    @abstractmethod
    def paint(
        self,
        painter: Any,
        option: Any,
        widget: Optional[Any] = None,
    ) -> None:
        """
        Paint the item.

        Concrete graphics items must implement their own
        presentation painting.

        Rendering policy may remain outside the item when the
        renderer architecture requires it.
        """

        raise NotImplementedError

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


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "BaseItem",
]
