# ============================================================
# File: ui/renderers/bus_renderer.py
# GridForge V2 — Bus Renderer
# ============================================================
"""
Renderer for authoritative GridForge Bus objects.

Architecture
------------

    Core / Application Bus
              │
              ▼
         BusRenderer
              │
              ▼
           BusItem
              │
              ▼
         GridScene

Purpose
-------
BusRenderer is the presentation-layer adapter responsible for
creating and updating the graphical projection of a Bus.

The Bus model remains authoritative.

BusRenderer does NOT:

    - modify the Core model;
    - create electrical objects;
    - determine topology;
    - perform electrical calculations;
    - own selection state;
    - implement tools;
    - perform snapping;
    - perform navigation;
    - own the QGraphicsScene;
    - manage application-level object lifetime.

Rendering ownership
-------------------
The renderer owns the visual representation it creates or
updates, but does not own the underlying model object.

The renderer operates on a supplied scene.

Identity
--------
Every rendered BusItem exposes:

    object_id

The renderer uses that identifier to locate an existing
projection before creating a new one.

Qt Architecture
---------------
All Qt dependencies must pass through:

    ui.core.qt
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import QPointF, QGraphicsScene

from ui.items.bus_item import BusItem


class BusRenderer:
    """
    Render and synchronize Bus objects as BusItem instances.

    A BusRenderer is intentionally stateless with respect to the
    application model. It does not maintain a persistent object
    cache.

    Parameters
    ----------
    scene:
        QGraphicsScene receiving the graphical projections.
    """

    # ========================================================
    # DEFAULT PRESENTATION
    # ========================================================

    DEFAULT_RADIUS = BusItem.DEFAULT_RADIUS

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

        if not callable(
            getattr(scene, "addItem", None)
        ):
            raise TypeError(
                "scene must provide addItem()."
            )

        if not callable(
            getattr(scene, "removeItem", None)
        ):
            raise TypeError(
                "scene must provide removeItem()."
            )

        if not callable(
            getattr(scene, "items", None)
        ):
            raise TypeError(
                "scene must provide items()."
            )

        self.scene = scene

    # ========================================================
    # RENDER
    # ========================================================

    def render(
        self,
        bus: Any,
    ) -> BusItem:
        """
        Create or update the graphical projection of a Bus.

        If a BusItem with the same object_id already exists,
        that item is updated and returned.

        Otherwise a new BusItem is created and added to the
        renderer's scene.

        Parameters
        ----------
        bus:
            Authoritative Bus/application object.

        Returns
        -------
        BusItem
            The graphical projection representing the Bus.
        """

        object_id = self._get_object_id(
            bus
        )

        existing = self.get_item(
            object_id
        )

        if existing is not None:
            self.update(
                existing,
                bus,
            )
            return existing

        position = self.get_model_position(
            bus
        )

        item = BusItem(
            object_id=object_id,
            position=position,
            radius=self.DEFAULT_RADIUS,
            model=bus,
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
        bus: Any,
    ) -> BusItem:
        """
        Create a new BusItem without automatically adding it to
        the scene.

        This method is useful for explicit scene lifecycle
        management.

        Raises
        ------
        ValueError
            If a projection for the same object_id already
            exists in the scene.
        """

        object_id = self._get_object_id(
            bus
        )

        if self.get_item(
            object_id
        ) is not None:
            raise ValueError(
                "A BusItem for "
                f"object_id={object_id!r} "
                "already exists."
            )

        return BusItem(
            object_id=object_id,
            position=self.get_model_position(
                bus
            ),
            radius=self.DEFAULT_RADIUS,
            model=bus,
        )

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        item: BusItem,
        bus: Any,
    ) -> BusItem:
        """
        Synchronize an existing BusItem from the authoritative
        Bus object.

        The model object is never modified.

        Parameters
        ----------
        item:
            Existing graphical Bus projection.

        bus:
            Authoritative Bus/application object.

        Returns
        -------
        BusItem
            The updated graphical projection.
        """

        if item is None:
            raise ValueError(
                "item must not be None."
            )

        if not isinstance(
            item,
            BusItem,
        ):
            raise TypeError(
                "item must be a BusItem."
            )

        object_id = self._get_object_id(
            bus
        )

        if item.object_id != object_id:
            raise ValueError(
                "BusItem object_id does not match "
                "the supplied Bus."
            )

        position = self.get_model_position(
            bus
        )

        item.set_model(
            bus
        )

        item.set_scene_position(
            position
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
        Remove the graphical Bus projection identified by
        object_id.

        Returns True when an item was removed.

        This does not delete the Core Bus.
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
    ) -> Optional[BusItem]:
        """
        Return the BusItem representing object_id.

        Returns None when no projection exists.
        """

        if object_id is None:
            return None

        for item in tuple(
            self.scene.items()
        ):
            if (
                isinstance(item, BusItem)
                and item.object_id == object_id
            ):
                return item

        return None

    # ========================================================
    # BULK SYNCHRONIZATION
    # ========================================================

    def render_all(
        self,
        buses: Any,
    ) -> tuple[BusItem, ...]:
        """
        Render a collection of authoritative Bus objects.

        Existing projections are updated.

        New projections are created.

        Existing scene items not represented by the supplied
        collection are not removed. Removal is deliberately
        explicit so this method cannot accidentally delete
        unrelated scene content.
        """

        if buses is None:
            raise ValueError(
                "buses must not be None."
            )

        result = []

        for bus in buses:
            result.append(
                self.render(
                    bus
                )
            )

        return tuple(
            result
        )

    # ========================================================
    # MODEL POSITION
    # ========================================================

    @staticmethod
    def get_model_position(
        bus: Any,
    ) -> QPointF:
        """
        Extract the presentation position from a Bus object.

        The renderer accepts common GridForge position
        representations:

            bus.position
            bus.pos

        and QPointF-compatible values.

        No coordinate transformation is performed here.

        Coordinate conversion belongs to CoordinateSystem.
        """

        position = getattr(
            bus,
            "position",
            None,
        )

        if callable(position):
            position = position()

        if position is None:
            position = getattr(
                bus,
                "pos",
                None,
            )

            if callable(position):
                position = position()

        if position is None:
            raise AttributeError(
                "Bus must provide a position "
                "through position or pos."
            )

        if not callable(
            getattr(position, "x", None)
        ):
            raise TypeError(
                "Bus position must provide x()."
            )

        if not callable(
            getattr(position, "y", None)
        ):
            raise TypeError(
                "Bus position must provide y()."
            )

        return QPointF(
            position.x(),
            position.y(),
        )

    # ========================================================
    # MODEL IDENTITY
    # ========================================================

    @staticmethod
    def _get_object_id(
        bus: Any,
    ) -> Any:
        """
        Extract the authoritative object ID from a Bus.

        Supported forms:

            bus.object_id
            bus.id
        """

        if bus is None:
            raise ValueError(
                "bus must not be None."
            )

        object_id = getattr(
            bus,
            "object_id",
            None,
        )

        if callable(object_id):
            object_id = object_id()

        if object_id is None:
            object_id = getattr(
                bus,
                "id",
                None,
            )

            if callable(object_id):
                object_id = object_id()

        if object_id is None:
            raise AttributeError(
                "Bus must provide object_id or id."
            )

        return object_id

    # ========================================================
    # SCENE
    # ========================================================

    def set_scene(
        self,
        scene: QGraphicsScene,
    ) -> None:
        """
        Replace the target scene.

        The renderer does not migrate existing items between
        scenes automatically.
        """

        if scene is None:
            raise ValueError(
                "scene must not be None."
            )

        if not callable(
            getattr(scene, "addItem", None)
        ):
            raise TypeError(
                "scene must provide addItem()."
            )

        if not callable(
            getattr(scene, "removeItem", None)
        ):
            raise TypeError(
                "scene must provide removeItem()."
            )

        if not callable(
            getattr(scene, "items", None)
        ):
            raise TypeError(
                "scene must provide items()."
            )

        self.scene = scene

    # --------------------------------------------------------

    def get_scene(
        self,
    ) -> QGraphicsScene:
        """
        Return the target QGraphicsScene.
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
                BusItem,
            )
        )

        return {
            "renderer": type(self).__name__,
            "scene_attached": self.scene is not None,
            "bus_item_count": item_count,
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

        state = self.get_state()

        return (
            "BusRenderer("
            f"bus_items="
            f"{state['bus_item_count']}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "BusRenderer",
]
