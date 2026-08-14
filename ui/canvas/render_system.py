# ============================================================
# File: ui/canvas/render_system.py
# GridForge Canvas Render System
# ============================================================

"""
Central rendering orchestration layer for the GridForge canvas.

Responsibilities
----------------
RenderSystem synchronizes the authoritative Core model with
permanent graphics in the QGraphicsScene.

It:

    - owns the RendererRegistry
    - loads renderer plugins
    - creates graphics for model elements
    - tracks rendered model elements
    - removes graphics when model elements disappear
    - refreshes graphics when requested
    - reconciles graphics against authoritative model elements
    - synchronizes graphical selection
    - provides renderer lookup
    - provides rendering diagnostics

It does NOT:

    - modify the Core model
    - implement electrical calculations
    - implement topology logic
    - handle mouse/keyboard events
    - implement tools
    - own transient previews
    - implement grid rendering
    - contain individual renderer implementations


Architecture
------------

    Core Model
        │
        ▼
    RenderSystem
        │
        ├── RendererRegistry
        │
        ├── RendererLoader
        │
        └── QGraphicsScene
                │
                ▼
          Permanent Graphics


Important
---------
The Core model remains authoritative.

QGraphicsItems are visual projections of model state.

The RenderSystem must therefore never use a graphics item as
the authoritative representation of an electrical element.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Type

from ui.core.renderer_loader import load_renderers
from ui.core.renderer_registry import RendererRegistry


class RenderSystem:
    """
    Central permanent-rendering orchestration service.

    Parameters
    ----------
    scene:
        QGraphicsScene owned by the canvas.

    controller:
        GridForge application Controller.

    renderer_registry:
        Optional preconfigured RendererRegistry.

        If omitted, a new registry is created.

    renderer_package:
        Python package containing renderer plugins.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        scene: Any,
        controller: Any,
        renderer_registry: Optional[RendererRegistry] = None,
        renderer_package: str = "ui.renderers",
    ) -> None:

        if scene is None:
            raise ValueError(
                "RenderSystem requires a valid graphics scene."
            )

        if controller is None:
            raise ValueError(
                "RenderSystem requires a valid controller."
            )

        self.scene = scene
        self.controller = controller

        # ----------------------------------------------------
        # Renderer registry
        # ----------------------------------------------------

        self.registry = (
            renderer_registry
            if renderer_registry is not None
            else RendererRegistry()
        )

        # ----------------------------------------------------
        # Rendered element mapping.
        #
        # Python object identity is used deliberately.
        #
        # _elements retains the corresponding model references,
        # preventing identity ambiguity while rendered.
        # ----------------------------------------------------

        self._items: Dict[int, Any] = {}
        self._elements: Dict[int, Any] = {}

        # ----------------------------------------------------
        # Load renderer plugins.
        # ----------------------------------------------------

        load_renderers(
            self.registry,
            package=renderer_package,
        )

    # ========================================================
    # RENDER SINGLE ELEMENT
    # ========================================================

    def render(
        self,
        element: Any,
    ) -> Any:
        """
        Create and attach the permanent graphics representation
        for one authoritative model element.

        Existing graphics for the same model object are reused.
        """

        if element is None:
            raise ValueError(
                "Cannot render a None model element."
            )

        element_key = id(element)

        existing = self._items.get(element_key)

        if existing is not None:
            return existing

        # ----------------------------------------------------
        # Resolve renderer from the model type.
        # ----------------------------------------------------

        renderer_cls = self.registry.require_renderer(
            type(element)
        )

        create_item = getattr(
            renderer_cls,
            "create_item",
            None,
        )

        if not callable(create_item):
            raise TypeError(
                f"{renderer_cls.__name__} must implement "
                "create_item(element, controller)"
            )

        # ----------------------------------------------------
        # Renderer creates the graphics item.
        # ----------------------------------------------------

        item = create_item(
            element,
            self.controller,
        )

        if item is None:
            raise RuntimeError(
                f"{renderer_cls.__name__}.create_item() "
                "returned None"
            )

        # ----------------------------------------------------
        # Attach permanent graphics to the scene.
        # ----------------------------------------------------

        self.scene.addItem(item)

        # ----------------------------------------------------
        # Track model → graphics projection.
        # ----------------------------------------------------

        self._items[element_key] = item
        self._elements[element_key] = element

        return item

    # ========================================================
    # RENDER MANY
    # ========================================================

    def render_all(
        self,
        elements: Iterable[Any],
    ) -> Dict[int, Any]:
        """
        Render a collection of authoritative model elements.

        Existing rendered elements are reused.

        Returns
        -------
        dict
            Mapping of model identity to graphics item.
        """

        rendered: Dict[int, Any] = {}

        for element in elements:
            item = self.render(element)
            rendered[id(element)] = item

        return rendered

    # ========================================================
    # REMOVE SINGLE ELEMENT
    # ========================================================

    def remove(
        self,
        element: Any,
    ) -> bool:
        """
        Remove the permanent graphics belonging to a model
        element.

        This method modifies only the visual projection.
        The Core model is never modified.
        """

        if element is None:
            return False

        element_key = id(element)

        item = self._items.pop(
            element_key,
            None,
        )

        self._elements.pop(
            element_key,
            None,
        )

        if item is None:
            return False

        self.scene.removeItem(item)

        return True

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self) -> None:
        """
        Remove all permanent rendered graphics.

        The Core model is not modified.
        """

        for item in tuple(self._items.values()):
            self.scene.removeItem(item)

        self._items.clear()
        self._elements.clear()

    # ========================================================
    # LOOKUP
    # ========================================================

    def get_item(
        self,
        element: Any,
    ) -> Optional[Any]:
        """
        Return the graphics item associated with a model element.
        """

        if element is None:
            return None

        return self._items.get(id(element))

    # --------------------------------------------------------

    def contains(
        self,
        element: Any,
    ) -> bool:
        """
        Return True when a model element currently has a
        rendered graphics representation.
        """

        if element is None:
            return False

        return id(element) in self._items

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh(
        self,
        element: Any,
    ) -> Any:
        """
        Refresh one rendered model element.

        The preferred path is an item-level:

            refresh_from_model()

        method.

        If the item does not provide that method, the visual
        projection is recreated through the canonical renderer
        contract.

        The Core model is never modified.
        """

        if element is None:
            raise ValueError(
                "Cannot refresh a None model element."
            )

        element_key = id(element)

        item = self._items.get(element_key)

        # ----------------------------------------------------
        # Not currently rendered.
        # ----------------------------------------------------

        if item is None:
            return self.render(element)

        # ----------------------------------------------------
        # Prefer item-level model synchronization.
        # ----------------------------------------------------

        refresh_from_model = getattr(
            item,
            "refresh_from_model",
            None,
        )

        if callable(refresh_from_model):
            refresh_from_model()
            return item

        # ----------------------------------------------------
        # No in-place item refresh contract.
        #
        # Recreate using the canonical renderer contract.
        # ----------------------------------------------------

        self.remove(element)

        return self.render(element)

    # ========================================================
    # REFRESH ALL
    # ========================================================

    def refresh_all(
        self,
        elements: Optional[Iterable[Any]] = None,
    ) -> None:
        """
        Refresh all currently rendered elements.

        If elements are supplied, only those elements are
        refreshed.
        """

        if elements is None:
            elements = tuple(
                self._elements.values()
            )

        for element in tuple(elements):
            self.refresh(element)

    # ========================================================
    # RECONCILE
    # ========================================================

    def reconcile(
        self,
        elements: Iterable[Any],
    ) -> None:
        """
        Reconcile permanent graphics against an authoritative
        collection of model elements.

        The algorithm is:

            authoritative model
                    │
                    ├── missing graphics → render
                    │
                    ├── existing graphics → refresh
                    │
                    └── stale graphics → remove

        The Core model remains authoritative.
        """

        authoritative = tuple(elements)

        authoritative_ids = {
            id(element)
            for element in authoritative
        }

        # ----------------------------------------------------
        # Remove stale graphics.
        # ----------------------------------------------------

        for element_key, element in tuple(
            self._elements.items()
        ):
            if element_key not in authoritative_ids:
                self.remove(element)

        # ----------------------------------------------------
        # Render or refresh authoritative elements.
        # ----------------------------------------------------

        for element in authoritative:

            if id(element) in self._items:
                self.refresh(element)
            else:
                self.render(element)

    # ========================================================
    # SELECTION SYNCHRONIZATION
    # ========================================================

    def refresh_selection(
        self,
        selected_ids: Optional[Iterable[str]] = None,
    ) -> None:
        """
        Synchronize QGraphicsItem selection with authoritative
        Controller selection.

        Parameters
        ----------
        selected_ids:
            Iterable of authoritative model IDs.

            If omitted, the method attempts to read
            ``controller.selected_ids``.

        Notes
        -----
        Selection in the graphics scene is a projection of
        application selection.

        The graphics scene does not become the selection
        authority.
        """

        if selected_ids is None:
            selected_ids = getattr(
                self.controller,
                "selected_ids",
                (),
            )

        selected = set(selected_ids)

        for item in tuple(self._items.values()):

            object_id = getattr(
                item,
                "object_id",
                None,
            )

            if object_id is None:
                item.setSelected(False)
                continue

            item.setSelected(
                object_id in selected
            )

    # ========================================================
    # RENDERER LOOKUP
    # ========================================================

    def get_renderer(
        self,
        model_type: Type[Any],
    ):
        """
        Return the renderer registered for a model type.

        Inheritance fallback is handled by RendererRegistry.
        """

        return self.registry.get_renderer(
            model_type
        )

    # --------------------------------------------------------

    def require_renderer(
        self,
        model_type: Type[Any],
    ):
        """
        Require a renderer for a model type.
        """

        return self.registry.require_renderer(
            model_type
        )

    # ========================================================
    # REGISTRY ACCESS
    # ========================================================

    def get_registry(self) -> RendererRegistry:
        """
        Return the renderer registry.

        The registry remains owned by RenderSystem.
        """

        return self.registry

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(self) -> dict:
        """
        Return diagnostic rendering state.
        """

        return {
            "rendered_count": len(self._items),
            "renderer_count": len(self.registry),
            "renderers": self.registry.list_renderers(),
        }

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "RenderSystem("
            f"rendered={len(self._items)}, "
            f"renderers={len(self.registry)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RenderSystem",
]
