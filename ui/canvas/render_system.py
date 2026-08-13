# ============================================================
# File: ui/canvas/render_system.py
# GridForge Canvas Render System
# ============================================================

"""
Central rendering orchestration layer for the GridForge canvas.

Responsibilities
----------------
RenderSystem is responsible for synchronizing the authoritative
Core model with permanent graphics in the QGraphicsScene.

It:

    - owns the RendererRegistry
    - loads renderer plugins
    - creates graphics for model elements
    - tracks rendered model elements
    - removes graphics when model elements disappear
    - refreshes graphics when requested
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

from typing import Any, Dict, Optional, Type

from ui.core.renderer_registry import RendererRegistry
from ui.core.renderer_loader import load_renderers


class RenderSystem:
    """
    Central permanent-rendering orchestration service.

    Parameters
    ----------
    scene:
        QGraphicsScene owned by the canvas.

    controller:
        GridForge application controller.

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
        # Rendered element mapping
        #
        # Model object identity is used deliberately.
        #
        # The scene is NOT used as the source of truth.
        # ----------------------------------------------------

        self._items: Dict[int, Any] = {}

        # Keep the corresponding model references for diagnostics
        # and identity-safe reconciliation.
        self._elements: Dict[int, Any] = {}

        # ----------------------------------------------------
        # Load renderer plugins.
        #
        # Renderer loading is explicit and belongs to the
        # rendering layer.
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
        for one model element.

        Parameters
        ----------
        element:
            Authoritative Core model element.

        Returns
        -------
        object
            Renderer-created graphics item.

        Raises
        ------
        ValueError
            If element is None.

        KeyError
            If no renderer is registered.
        """

        if element is None:
            raise ValueError(
                "Cannot render a None model element."
            )

        # ----------------------------------------------------
        # Avoid duplicate graphics for the same model object.
        # ----------------------------------------------------

        element_key = id(element)

        existing = self._items.get(element_key)

        if existing is not None:
            return existing

        # ----------------------------------------------------
        # Determine renderer from the model class.
        # ----------------------------------------------------

        renderer_cls = self.registry.require_renderer(
            type(element)
        )

        # ----------------------------------------------------
        # Renderer contract.
        #
        # Renderer classes expose:
        #
        #     create_item(element, controller)
        #
        # The renderer creates the visual representation.
        # ----------------------------------------------------

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
        # Track visual projection.
        # ----------------------------------------------------

        self._items[element_key] = item
        self._elements[element_key] = element

        return item

    # ========================================================
    # RENDER MANY
    # ========================================================

    def render_all(
        self,
        elements,
    ) -> Dict[int, Any]:
        """
        Render a collection of model elements.

        Existing rendered elements are reused.

        Returns
        -------
        dict
            Mapping of model identity to graphics item.
        """

        rendered = {}

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

        This method removes only the visual projection.

        It does NOT modify the Core model.
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

        for item in list(
            self._items.values()
        ):
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

        return self._items.get(
            id(element)
        )

    # --------------------------------------------------------

    def contains(
        self,
        element: Any,
    ) -> bool:
        """
        Return True when an element currently has a rendered
        graphics representation.
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

        Renderer implementations may optionally provide:

            update_item(item, element, controller)

        If unavailable, the existing item is removed and the
        element is rendered again.
        """

        if element is None:
            raise ValueError(
                "Cannot refresh a None model element."
            )

        element_key = id(element)

        item = self._items.get(
            element_key
        )

        # ----------------------------------------------------
        # Element is not currently rendered.
        # ----------------------------------------------------

        if item is None:
            return self.render(element)

        # ----------------------------------------------------
        # Obtain renderer.
        # ----------------------------------------------------

        renderer_cls = self.registry.require_renderer(
            type(element)
        )

        update_item = getattr(
            renderer_cls,
            "update_item",
            None,
        )

        # ----------------------------------------------------
        # Renderer supports in-place update.
        # ----------------------------------------------------

        if callable(update_item):

            result = update_item(
                item,
                element,
                self.controller,
            )

            # Renderer may return a replacement item.
            if result is not None and result is not item:

                self.scene.removeItem(item)

                self._items[element_key] = result

                self.scene.addItem(result)

                return result

            return item

        # ----------------------------------------------------
        # No update contract.
        #
        # Recreate the visual projection.
        # ----------------------------------------------------

        self.remove(element)

        return self.render(element)

    # ========================================================
    # REFRESH ALL
    # ========================================================

    def refresh_all(
        self,
        elements=None,
    ) -> None:
        """
        Refresh all currently rendered elements.

        If elements are supplied, only those elements are
        refreshed.
        """

        if elements is None:
            elements = list(
                self._elements.values()
            )

        for element in list(elements):
            self.refresh(element)

    # ========================================================
    # RECONCILE
    # ========================================================

    def reconcile(
        self,
        elements,
    ) -> None:
        """
        Reconcile the permanent graphics with an authoritative
        collection of model elements.

        This is the preferred synchronization operation after
        loading/rebuilding a model.

        The algorithm:

            authoritative model
                    │
                    ├── missing graphics → render
                    │
                    ├── existing graphics → retain
                    │
                    └── stale graphics → remove

        The Core model remains authoritative.
        """

        authoritative = list(elements)

        authoritative_ids = {
            id(element)
            for element in authoritative
        }

        # ----------------------------------------------------
        # Remove stale graphics.
        # ----------------------------------------------------

        for element_key, element in list(
            self._elements.items()
        ):

            if element_key not in authoritative_ids:
                self.remove(element)

        # ----------------------------------------------------
        # Render missing elements.
        # ----------------------------------------------------

        for element in authoritative:

            if id(element) not in self._items:
                self.render(element)

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
