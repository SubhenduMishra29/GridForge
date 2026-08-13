"""
GridForge V2 — Render System
============================

File:
    ui/canvas/render_system.py

Purpose
-------
Maintains the graphical projection of the GridForge domain
model.

The RenderSystem coordinates:

    Core Model
        ↓
    RendererRegistry
        ↓
    Renderer
        ↓
    QGraphicsItem
        ↓
    QGraphicsScene

The Core model remains authoritative.

The QGraphicsScene is strictly a visual representation and
must never become a second source of domain state.

Responsibilities
----------------
The RenderSystem:

    - owns the QGraphicsScene used by the canvas;
    - owns the runtime RendererRegistry reference;
    - creates graphics items through registered renderers;
    - removes obsolete graphics items;
    - rebuilds the graphical projection;
    - maintains model-ID → QGraphicsItem mapping;
    - listens for controller model/selection changes;
    - mirrors authoritative Controller selection into graphics;
    - provides controlled scene access to Canvas/View layers;
    - exposes diagnostic state.

The RenderSystem does NOT:

    - modify the Core model;
    - perform electrical calculations;
    - handle mouse events;
    - implement tools;
    - determine selection semantics;
    - create renderer classes;
    - import concrete renderers;
    - import concrete tools;
    - contain application business logic;
    - make the QGraphicsScene authoritative.

Renderer Contract
-----------------
A renderer registered in RendererRegistry must provide:

    model_type = <Core model class>

and:

    create_item(element, controller)

The renderer returns the QGraphicsItem representing the
supplied model element.

Model Contract
--------------
The RenderSystem expects the application model to provide:

    iter_elements()

which returns the domain elements that must be represented
on the current canvas.

Each renderable element must provide a stable:

    id

attribute.

The RenderSystem does not assume a particular Core model
implementation beyond this explicit rendering contract.

Selection Contract
------------------
Controller.selected_ids is authoritative.

RenderSystem only mirrors that state into QGraphicsItems.

Therefore:

    Controller.selected_ids
            ↓
      RenderSystem
            ↓
    QGraphicsItem.setSelected()

A QGraphicsItem selection state must never be used to update
Controller state directly by the RenderSystem.

InteractionManager/tools are responsible for translating
user interaction into Controller selection changes.

Threading
---------
The RenderSystem operates on the Qt GUI thread.

Core calculations and simulation must remain outside the UI
rendering path.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from ui.core.qt import (
    QGraphicsItem,
    QGraphicsScene,
)


class RenderSystem:
    """
    Synchronizes the GridForge domain model with a
    QGraphicsScene.

    The system owns the visual projection but does not own
    domain state.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        renderer_registry: Any,
        scene: Optional[QGraphicsScene] = None,
    ) -> None:
        """
        Initialize the RenderSystem.

        Parameters
        ----------
        controller:
            GridForge UI Controller.

            The Controller provides:

                - authoritative model reference;
                - model_changed notifications;
                - authoritative selection state.

        renderer_registry:
            RendererRegistry instance.

        scene:
            Optional existing QGraphicsScene.

            If omitted, a new QGraphicsScene is created.

        Notes
        -----
        RenderSystem does not create the renderer registry.
        It receives it through dependency injection.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None"
            )

        if renderer_registry is None:
            raise ValueError(
                "renderer_registry must not be None"
            )

        if not callable(
            getattr(
                controller,
                "subscribe",
                None,
            )
        ):
            raise TypeError(
                "controller must provide subscribe()"
            )

        if not callable(
            getattr(
                renderer_registry,
                "get_renderer",
                None,
            )
        ):
            raise TypeError(
                "renderer_registry must provide get_renderer()"
            )

        self.controller = controller
        self.renderer_registry = renderer_registry

        # ----------------------------------------------------
        # GRAPHICS SCENE
        # ----------------------------------------------------

        self.scene = (
            scene
            if scene is not None
            else QGraphicsScene()
        )

        # ----------------------------------------------------
        # MODEL → GRAPHICS MAPPING
        # ----------------------------------------------------
        #
        # The model ID is the authoritative identity key.
        #
        # Never use QGraphicsItem identity as domain identity.
        # ----------------------------------------------------

        self._items: Dict[
            str,
            QGraphicsItem,
        ] = {}

        # ----------------------------------------------------
        # CONNECTION STATE
        # ----------------------------------------------------

        self._connected = False

        self._connect_controller()

    # ========================================================
    # CONTROLLER CONNECTION
    # ========================================================

    def _connect_controller(self) -> None:
        """
        Subscribe to Controller events.

        RenderSystem listens only to application-level state
        relevant to rendering.
        """

        if self._connected:
            return

        self.controller.subscribe(
            "model_changed",
            self._on_model_changed,
        )

        self.controller.subscribe(
            "selection_changed",
            self._on_selection_changed,
        )

        self._connected = True

    # ========================================================
    # MODEL ACCESS
    # ========================================================

    def _get_model(self) -> Any:
        """
        Return the authoritative Core model.
        """

        return getattr(
            self.controller,
            "model",
            None,
        )

    # --------------------------------------------------------

    def _iter_model_elements(self) -> Iterable[Any]:
        """
        Return renderable model elements.

        Canonical model contract:

            model.iter_elements()

        The method is deliberately kept here as the single
        boundary between RenderSystem and model traversal.
        """

        model = self._get_model()

        if model is None:
            return ()

        iterator = getattr(
            model,
            "iter_elements",
            None,
        )

        if not callable(iterator):
            raise TypeError(
                "GridForge model must provide "
                "iter_elements() for rendering"
            )

        elements = iterator()

        if elements is None:
            return ()

        return elements

    # ========================================================
    # ELEMENT ID
    # ========================================================

    @staticmethod
    def _get_element_id(
        element: Any,
    ) -> str:
        """
        Return the stable domain ID of a renderable element.
        """

        element_id = getattr(
            element,
            "id",
            None,
        )

        if not isinstance(
            element_id,
            str,
        ):
            raise TypeError(
                "Renderable model elements must provide "
                "a string 'id' attribute"
            )

        element_id = element_id.strip()

        if not element_id:
            raise ValueError(
                "Renderable model element ID "
                "must not be empty"
            )

        return element_id

    # ========================================================
    # RENDERER LOOKUP
    # ========================================================

    def _get_renderer(
        self,
        element: Any,
    ) -> type:
        """
        Resolve the renderer class for a model element.
        """

        renderer = self.renderer_registry.get_renderer(
            type(element)
        )

        if renderer is None:
            raise KeyError(
                "No renderer registered for model type "
                f"'{type(element).__name__}'"
            )

        return renderer

    # ========================================================
    # ITEM CREATION
    # ========================================================

    def _create_item(
        self,
        element: Any,
    ) -> QGraphicsItem:
        """
        Create the graphics item for a model element.

        Renderer instances are not owned by RenderSystem.

        The renderer class provides create_item().
        """

        renderer = self._get_renderer(
            element
        )

        create_item = getattr(
            renderer,
            "create_item",
            None,
        )

        if not callable(create_item):
            raise TypeError(
                f"Renderer '{renderer.__name__}' must provide "
                "callable create_item()"
            )

        item = create_item(
            element,
            self.controller,
        )

        if not isinstance(
            item,
            QGraphicsItem,
        ):
            raise TypeError(
                f"Renderer '{renderer.__name__}.create_item()' "
                "must return QGraphicsItem"
            )

        return item

    # ========================================================
    # FULL SYNCHRONIZATION
    # ========================================================

    def rebuild(self) -> None:
        """
        Rebuild the complete graphical projection.

        Process:

            1. Remove existing graphics items.
            2. Read the authoritative model.
            3. Resolve renderers.
            4. Create graphics items.
            5. Add them to the scene.
            6. Reapply Controller selection.

        The Core model is never modified.
        """

        self.clear()

        for element in self._iter_model_elements():

            element_id = self._get_element_id(
                element
            )

            if element_id in self._items:
                raise ValueError(
                    "Duplicate renderable model ID: "
                    f"'{element_id}'"
                )

            item = self._create_item(
                element
            )

            self.scene.addItem(
                item
            )

            self._items[element_id] = item

        self._apply_selection()

    # ========================================================
    # SYNCHRONIZATION ALIAS
    # ========================================================

    def sync(self) -> None:
        """
        Synchronize the complete graphical projection with the
        authoritative model.

        Currently synchronization is implemented as a complete
        rebuild.

        This is intentional for the initial V2 UI architecture:
        correctness and deterministic reconstruction take
        priority over premature incremental-scene optimization.

        Incremental synchronization may be introduced later
        without changing the Controller/model authority contract.
        """

        self.rebuild()

    # ========================================================
    # MODEL CHANGE HANDLER
    # ========================================================

    def _on_model_changed(
        self,
        model: Any,
    ) -> None:
        """
        Handle Controller model_changed notification.

        The Controller remains authoritative; the supplied
        model argument is not copied into RenderSystem state.
        """

        if model is not self._get_model():
            # A stale or foreign model notification must not
            # replace the authoritative Controller model.
            return

        self.sync()

    # ========================================================
    # SELECTION HANDLER
    # ========================================================

    def _on_selection_changed(
        self,
        selected_ids: Any,
    ) -> None:
        """
        Mirror Controller selection into graphics items.

        Controller selection remains authoritative.
        """

        self._apply_selection()

    # ========================================================
    # APPLY SELECTION
    # ========================================================

    def _apply_selection(self) -> None:
        """
        Apply authoritative Controller selection to all
        graphics items.
        """

        selected_ids = set(
            self.controller.get_selection()
        )

        for element_id, item in self._items.items():

            item.setSelected(
                element_id in selected_ids
            )

    # ========================================================
    # ITEM LOOKUP
    # ========================================================

    def get_item(
        self,
        element_id: str,
    ) -> Optional[QGraphicsItem]:
        """
        Return the graphics item associated with a model ID.

        Returns None when no item exists.
        """

        if not isinstance(
            element_id,
            str,
        ):
            raise TypeError(
                "element_id must be a string"
            )

        return self._items.get(
            element_id
        )

    # ========================================================
    # REQUIRED ITEM LOOKUP
    # ========================================================

    def require_item(
        self,
        element_id: str,
    ) -> QGraphicsItem:
        """
        Return the graphics item associated with a model ID.

        Raises KeyError if no item exists.
        """

        item = self.get_item(
            element_id
        )

        if item is None:
            raise KeyError(
                "No graphics item exists for model ID "
                f"'{element_id}'"
            )

        return item

    # ========================================================
    # ITEM EXISTENCE
    # ========================================================

    def contains(
        self,
        element_id: str,
    ) -> bool:
        """
        Return True if a graphics item exists for the model ID.
        """

        if not isinstance(
            element_id,
            str,
        ):
            raise TypeError(
                "element_id must be a string"
            )

        return element_id in self._items

    # ========================================================
    # ALL ITEMS
    # ========================================================

    def items(
        self,
    ) -> Dict[
        str,
        QGraphicsItem,
    ]:
        """
        Return a detached mapping of model IDs to graphics
        items.

        The internal mapping cannot be modified through the
        returned dictionary.
        """

        return dict(
            self._items
        )

    # ========================================================
    # SCENE ACCESS
    # ========================================================

    def get_scene(self) -> QGraphicsScene:
        """
        Return the managed QGraphicsScene.
        """

        return self.scene

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self) -> None:
        """
        Remove all graphics items from the managed scene.

        This only modifies the visual projection.

        It does NOT modify the Core model or Controller
        selection state.
        """

        for item in list(
            self._items.values()
        ):
            self.scene.removeItem(
                item
            )

        self._items.clear()

    # ========================================================
    # REFRESH SELECTION
    # ========================================================

    def refresh_selection(self) -> None:
        """
        Reapply Controller selection to current graphics items.
        """

        self._apply_selection()

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh(self) -> None:
        """
        Rebuild the graphical projection.

        Alias for sync().
        """

        self.sync()

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def item_count(self) -> int:
        """
        Return the number of currently rendered model elements.
        """

        return len(
            self._items
        )

    # --------------------------------------------------------

    def get_state(self) -> Dict[str, Any]:
        """
        Return a diagnostic snapshot of RenderSystem state.
        """

        return {
            "item_count": len(
                self._items
            ),
            "item_ids": list(
                self._items.keys()
            ),
            "scene_item_count": len(
                self.scene.items()
            ),
            "connected": self._connected,
        }

    # ========================================================
    # CLEANUP
    # ========================================================

    def dispose(self) -> None:
        """
        Release the visual projection and disconnect from the
        Controller.

        The Controller's unsubscribe mechanism is used when
        available.
        """

        if self._connected:

            unsubscribe = getattr(
                self.controller,
                "unsubscribe",
                None,
            )

            if callable(unsubscribe):

                unsubscribe(
                    "model_changed",
                    self._on_model_changed,
                )

                unsubscribe(
                    "selection_changed",
                    self._on_selection_changed,
                )

            self._connected = False

        self.clear()

    # ========================================================
    # LENGTH
    # ========================================================

    def __len__(self) -> int:
        """
        Return the number of rendered model elements.
        """

        return len(
            self._items
        )

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "RenderSystem("
            f"items={len(self._items)}, "
            f"connected={self._connected}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RenderSystem",
]
