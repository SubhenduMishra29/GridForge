# ============================================================
# File: ui/renderers/bus_renderer.py
# GridForge V2 — Bus Renderer
# ============================================================
"""
Concrete renderer for authoritative GridForge Bus objects.

Architecture
------------

    Authoritative Core/Application Bus
                    │
                    ▼
              BusRenderer
                    │
                    ▼
                 BusItem
                    │
                    ▼
              QGraphicsScene

Purpose
-------
BusRenderer converts authoritative Bus state into its graphical
presentation.

The Bus object remains the single source of engineering truth.

BusRenderer is a presentation-layer adapter only.

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
        BusRenderer
            ↓
          BusItem
            ↓
       Graphics Scene

The reverse direction is prohibited:

    BusItem
       ↓
    BusRenderer
       ↓
    Core engineering state

Qt Architecture
----------------
All Qt dependencies pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.qt import (
    QGraphicsScene,
    QPointF,
)

from ui.items.bus_item import BusItem
from ui.renderers.renderer_base import RendererBase
from ui.renderers.renderer_utils import (
    find_item_by_object_id,
    get_object_id,
    to_pointf,
)


class BusRenderer(RendererBase):
    """
    Render authoritative Bus objects as BusItem projections.

    The renderer does not maintain a persistent application-model
    cache. The graphics scene is the container for graphical
    projections.

    Parameters
    ----------
    scene:
        Target QGraphicsScene-compatible object.
    """

    # ========================================================
    # DEFAULT PRESENTATION
    # ========================================================

    DEFAULT_RADIUS = BusItem.DEFAULT_RADIUS

    # ========================================================
    # RENDER
    # ========================================================

    def render(
        self,
        model: Any,
    ) -> BusItem:
        """
        Create or update the graphical projection of a Bus.

        If a BusItem representing the same authoritative
        object_id already exists, that projection is updated.

        Otherwise a new BusItem is created, attached to the
        renderer scene, and returned.

        The authoritative Bus is never modified.
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
    ) -> BusItem:
        """
        Create a BusItem projection without adding it to the
        scene.

        This method performs projection construction only.

        Raises
        ------
        ValueError
            If a projection with the same object_id already
            exists in the attached scene.
        """

        object_id = self._get_object_id(
            model
        )

        if self.get_item(
            object_id
        ) is not None:
            raise ValueError(
                "A BusItem for "
                f"object_id={object_id!r} "
                "already exists."
            )

        position = self.get_model_position(
            model
        )

        return BusItem(
            object_id=object_id,
            position=position,
            radius=self.DEFAULT_RADIUS,
            model=model,
        )

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        item: BusItem,
        model: Any,
    ) -> BusItem:
        """
        Synchronize an existing BusItem from authoritative Bus
        state.

        Only the graphical projection is modified.

        The supplied Core/application object is never mutated.
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
            model
        )

        if item.object_id != object_id:
            raise ValueError(
                "BusItem object_id does not match "
                "the supplied Bus."
            )

        position = self.get_model_position(
            model
        )

        item.set_model(
            model
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
        Remove the graphical projection identified by object_id.

        Only the BusItem is removed.

        The corresponding authoritative Core Bus is never
        deleted or modified.

        Returns
        -------
        bool
            True when a graphical projection was removed,
            otherwise False.
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
        Return the BusItem projection for object_id.

        Returns None when no matching projection exists.
        """

        if object_id is None:
            return None

        item = find_item_by_object_id(
            self.scene,
            object_id,
            BusItem,
        )

        if item is None:
            return None

        return item

    # ========================================================
    # BULK SYNCHRONIZATION
    # ========================================================

    def render_all(
        self,
        models: Any,
    ) -> tuple[BusItem, ...]:
        """
        Render a collection of authoritative Bus objects.

        Existing projections are updated.

        Missing projections are created.

        Existing scene projections not represented by the supplied
        collection are deliberately retained.

        Removal is explicit through remove().
        """

        if models is None:
            raise ValueError(
                "models must not be None."
            )

        result: list[BusItem] = []

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
    # MODEL POSITION
    # ========================================================

    @staticmethod
    def get_model_position(
        model: Any,
    ) -> QPointF:
        """
        Extract the authoritative presentation position from a
        Bus model.

        The supported public model representation is:

            bus.position

        A callable position property is also supported.

        No coordinate-system transformation is performed.

        Coordinate conversion belongs to CoordinateSystem.
        Grid resolution/snapping belongs to the appropriate UI
        coordinate/snap infrastructure.
        """

        if model is None:
            raise ValueError(
                "model must not be None."
            )

        position = getattr(
            model,
            "position",
            None,
        )

        if callable(position):
            position = position()

        if position is None:
            raise AttributeError(
                "Bus must provide a position."
            )

        return to_pointf(
            position,
            name="bus.position",
        )

    # ========================================================
    # MODEL IDENTITY
    # ========================================================

    @staticmethod
    def _get_object_id(
        model: Any,
    ) -> Any:
        """
        Extract the authoritative object identifier.

        The common renderer identity contract is centralized in
        renderer_utils.get_object_id().
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

        RendererBase owns the scene-contract validation.
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

        bus_item_count = sum(
            1
            for item in tuple(
                self.scene.items()
            )
            if isinstance(
                item,
                BusItem,
            )
        )

        state.update(
            {
                "bus_item_count": bus_item_count,
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
