# ============================================================
# File: ui/canvas/render_system.py
# GridForge Canvas Render System
# ============================================================
#
# PURPOSE
# -------
# Central rendering orchestration layer for the GridForge
# canvas.
#
# Architecture:
#
#     Core Model
#         │
#         ▼
#     RendererRegistry
#         │
#         ▼
#     Renderer
#         │
#         ▼
#     QGraphicsItem
#         │
#         ▼
#     QGraphicsScene
#
#
# RESPONSIBILITIES
# ----------------
#
# RenderSystem:
#
#     - resolve the renderer for a model element
#     - create permanent graphics representations
#     - attach graphics items to the scene
#     - update existing graphics representations
#     - remove graphics representations
#     - synchronize a collection of model elements
#     - maintain model-element → graphics-item ownership
#     - provide diagnostics
#
#
# RenderSystem does NOT:
#
#     - modify the Core model
#     - create Core model objects
#     - perform electrical calculations
#     - implement interaction logic
#     - manage tools
#     - perform snapping
#     - manage previews
#     - perform coordinate conversion
#     - import individual renderers
#     - discover renderer modules
#     - contain renderer-specific drawing logic
#
#
# OWNERSHIP
# ---------
#
# RendererRegistry:
#     Determines which renderer handles a model type.
#
# Renderer:
#     Creates and updates the graphical representation.
#
# RenderSystem:
#     Owns the scene attachment and model-element-to-item
#     mapping.
#
# GraphicsView:
#     Owns the QGraphicsView/QGraphicsScene infrastructure.
#
# InteractionManager:
#     Owns transient interaction routing.
#
# PreviewLayer:
#     Owns temporary interaction graphics.
#
#
# CORE AUTHORITY
# --------------
#
# The Core model is authoritative.
#
# QGraphicsItems are projections of Core state and must never
# become a second source of model truth.
#
#
# RENDERER CONTRACT
# -----------------
#
# Every renderer registered with RendererRegistry MUST provide:
#
#     model_type = <ModelClass>
#
#     create_item(element, controller)
#
# Optional lifecycle hooks:
#
#     update_item(item, element, controller)
#
#     remove_item(item, element, controller)
#
#
# `create_item()` is mandatory.
#
# `update_item()` is optional. If absent, RenderSystem replaces
# the graphical representation when an explicit update is
# requested.
#
#
# IMPORTANT
# ---------
#
# RenderSystem never discovers renderer modules.
#
# Renderer discovery belongs to:
#
#     ui/core/renderer_loader.py
#
# Registry construction belongs to the application/bootstrap
# layer.
#
# ============================================================

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Tuple, Type


class RenderSystem:
    """
    Central permanent-rendering system for the GridForge canvas.

    The Core model remains authoritative.

    RenderSystem maintains only the visual projection:

        model element
            ↓
        renderer
            ↓
        graphics item
            ↓
        scene
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        scene: Any,
        controller: Any,
        renderer_registry: Any,
    ) -> None:
        """
        Initialize the RenderSystem.

        Parameters
        ----------
        scene:
            QGraphicsScene receiving permanent model graphics.

        controller:
            GridForge application controller.

        renderer_registry:
            Runtime RendererRegistry.

        Notes
        -----
        The RenderSystem does not create the registry and does
        not discover renderer plugins.
        """

        if scene is None:
            raise ValueError(
                "RenderSystem requires a scene."
            )

        if renderer_registry is None:
            raise ValueError(
                "RenderSystem requires a renderer registry."
            )

        self.scene = scene
        self.controller = controller
        self.renderer_registry = renderer_registry

        # ----------------------------------------------------
        # Permanent graphics projection.
        #
        # Object identity is deliberately used as the mapping
        # key. Model equality must not determine graphics
        # ownership.
        # ----------------------------------------------------

        self._items: Dict[int, Any] = {}

        self._elements: Dict[int, Any] = {}

    # ========================================================
    # INTERNAL IDENTITY
    # ========================================================

    @staticmethod
    def _key(
        element: Any,
    ) -> int:
        """
        Return the identity key for a model element.
        """

        return id(element)

    # ========================================================
    # RENDERER LOOKUP
    # ========================================================

    def get_renderer(
        self,
        element: Any,
    ) -> Optional[Type[Any]]:
        """
        Return the renderer registered for an element.

        RendererRegistry is responsible for:

            exact-type lookup
            inheritance fallback
        """

        if element is None:
            return None

        return self.renderer_registry.get_renderer(
            type(element)
        )

    # --------------------------------------------------------

    def require_renderer(
        self,
        element: Any,
    ) -> Type[Any]:
        """
        Return the required renderer for an element.

        Raises
        ------
        ValueError
            If element is None.

        KeyError
            If no renderer is registered.
        """

        if element is None:
            raise ValueError(
                "Cannot resolve a renderer for None."
            )

        return self.renderer_registry.require_renderer(
            type(element)
        )

    # ========================================================
    # RENDERER CREATE CONTRACT
    # ========================================================

    def _create_item(
        self,
        element: Any,
    ) -> Any:
        """
        Create a graphics item through the registered renderer.

        RenderSystem does not know how the graphics item itself
        is constructed.
        """

        renderer = self.require_renderer(
            element
        )

        create_item = getattr(
            renderer,
            "create_item",
            None,
        )

        if not callable(create_item):
            raise TypeError(
                f"Renderer '{renderer.__name__}' for "
                f"'{type(element).__name__}' must provide "
                "create_item(element, controller)."
            )

        item = create_item(
            element,
            self.controller,
        )

        if item is None:
            raise RuntimeError(
                f"Renderer '{renderer.__name__}' returned None "
                f"for model element "
                f"'{type(element).__name__}'."
            )

        return item

    # ========================================================
    # SCENE OWNERSHIP
    # ========================================================

    def _add_to_scene(
        self,
        item: Any,
    ) -> None:
        """
        Attach a permanent graphics item to the scene.
        """

        self.scene.addItem(
            item
        )

    # --------------------------------------------------------

    def _remove_from_scene(
        self,
        item: Any,
    ) -> None:
        """
        Detach a permanent graphics item from the scene.
        """

        if item is None:
            return

        self.scene.removeItem(
            item
        )

    # ========================================================
    # RENDER
    # ========================================================

    def render(
        self,
        element: Any,
        *,
        replace: bool = False,
    ) -> Any:
        """
        Render one model element.

        Parameters
        ----------
        element:
            Core model element.

        replace:
            Recreate an existing graphics representation when
            True.

        Returns
        -------
        object
            Graphics item representing the element.

        Notes
        -----
        Calling render() repeatedly for an already-rendered
        element is idempotent unless replace=True.
        """

        if element is None:
            raise ValueError(
                "Cannot render None."
            )

        key = self._key(
            element
        )

        existing = self._items.get(
            key
        )

        # ----------------------------------------------------
        # Existing projection.
        # ----------------------------------------------------

        if existing is not None:

            if not replace:
                return existing

            self.remove(
                element
            )

        # ----------------------------------------------------
        # Create graphics representation.
        # ----------------------------------------------------

        item = self._create_item(
            element
        )

        # ----------------------------------------------------
        # Attach graphics representation.
        # ----------------------------------------------------

        self._add_to_scene(
            item
        )

        # ----------------------------------------------------
        # Record ownership.
        # ----------------------------------------------------

        self._items[key] = item
        self._elements[key] = element

        return item

    # ========================================================
    # RENDER COLLECTION
    # ========================================================

    def render_all(
        self,
        elements: Iterable[Any],
    ) -> Dict[Any, Any]:
        """
        Render all supplied model elements.

        Existing graphics representations are reused.
        """

        result = {}

        for element in elements:

            if element is None:
                continue

            result[element] = self.render(
                element
            )

        return result

    # ========================================================
    # UPDATE
    # ========================================================

    def update(
        self,
        element: Any,
    ) -> Any:
        """
        Update the graphics representation of a model element.

        If the element is not currently rendered, it is rendered.

        If its renderer provides update_item(), that method is
        used.

        Otherwise the existing representation is replaced.

        This fallback is deliberate: the renderer remains the
        owner of graphical construction while RenderSystem
        guarantees that the projection can always be rebuilt.
        """

        if element is None:
            raise ValueError(
                "Cannot update None."
            )

        key = self._key(
            element
        )

        item = self._items.get(
            key
        )

        # ----------------------------------------------------
        # No existing projection.
        # ----------------------------------------------------

        if item is None:
            return self.render(
                element
            )

        renderer = self.require_renderer(
            element
        )

        update_item = getattr(
            renderer,
            "update_item",
            None,
        )

        # ----------------------------------------------------
        # Incremental renderer update.
        # ----------------------------------------------------

        if callable(update_item):

            result = update_item(
                item,
                element,
                self.controller,
            )

            # Standard in-place update.
            if result is None:
                return item

            # Renderer explicitly supplied a replacement item.
            if result is not item:

                self._remove_from_scene(
                    item
                )

                self._add_to_scene(
                    result
                )

                self._items[key] = result

                return result

            return item

        # ----------------------------------------------------
        # Renderer has no incremental update contract.
        #
        # Rebuild the projection.
        # ----------------------------------------------------

        return self.render(
            element,
            replace=True,
        )

    # ========================================================
    # UPDATE COLLECTION
    # ========================================================

    def update_all(
        self,
        elements: Iterable[Any],
    ) -> Dict[Any, Any]:
        """
        Update all supplied model elements.
        """

        result = {}

        for element in elements:

            if element is None:
                continue

            result[element] = self.update(
                element
            )

        return result

    # ========================================================
    # REMOVE
    # ========================================================

    def remove(
        self,
        element: Any,
    ) -> bool:
        """
        Remove the graphical projection of a model element.

        IMPORTANT
        ---------
        This method NEVER removes or modifies the Core model
        element itself.
        """

        if element is None:
            return False

        key = self._key(
            element
        )

        item = self._items.get(
            key
        )

        if item is None:
            return False

        renderer = self.renderer_registry.get_renderer(
            type(element)
        )

        # ----------------------------------------------------
        # Optional renderer cleanup.
        # ----------------------------------------------------

        if renderer is not None:

            remove_item = getattr(
                renderer,
                "remove_item",
                None,
            )

            if callable(remove_item):

                remove_item(
                    item,
                    element,
                    self.controller,
                )

        # ----------------------------------------------------
        # Detach graphics.
        # ----------------------------------------------------

        self._remove_from_scene(
            item
        )

        # ----------------------------------------------------
        # Remove ownership records only after successful scene
        # detachment.
        # ----------------------------------------------------

        del self._items[key]

        self._elements.pop(
            key,
            None,
        )

        return True

    # ========================================================
    # REMOVE COLLECTION
    # ========================================================

    def remove_all(
        self,
        elements: Iterable[Any],
    ) -> int:
        """
        Remove graphical projections for supplied elements.

        Returns
        -------
        int
            Number of removed representations.
        """

        count = 0

        for element in elements:

            if self.remove(
                element
            ):
                count += 1

        return count

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self) -> None:
        """
        Remove every permanent graphics representation managed
        by this RenderSystem.

        This does NOT:

            - modify the Core model
            - clear the QGraphicsScene indiscriminately
            - remove PreviewLayer graphics owned elsewhere
        """

        elements = tuple(
            self._elements.values()
        )

        for element in elements:
            self.remove(
                element
            )

    # ========================================================
    # SYNCHRONIZATION
    # ========================================================

    def synchronize(
        self,
        elements: Iterable[Any],
    ) -> Dict[Any, Any]:
        """
        Synchronize the permanent graphics projection with an
        authoritative collection of Core model elements.

        Processing:

            1. Remove stale graphics.
            2. Render new elements.
            3. Update existing elements.

        The supplied collection is authoritative for what should
        currently be visible.
        """

        desired = tuple(
            element
            for element in elements
            if element is not None
        )

        desired_keys = {
            self._key(element)
            for element in desired
        }

        # ----------------------------------------------------
        # Remove stale projections.
        # ----------------------------------------------------

        stale = tuple(
            element
            for element in self._elements.values()
            if self._key(element) not in desired_keys
        )

        for element in stale:
            self.remove(
                element
            )

        # ----------------------------------------------------
        # Render/update desired projections.
        # ----------------------------------------------------

        result = {}

        for element in desired:
            result[element] = self.update(
                element
            )

        return result

    # ========================================================
    # LOOKUP
    # ========================================================

    def get_item(
        self,
        element: Any,
    ) -> Optional[Any]:
        """
        Return the graphics item associated with an element.
        """

        if element is None:
            return None

        return self._items.get(
            self._key(element)
        )

    # --------------------------------------------------------

    def contains(
        self,
        element: Any,
    ) -> bool:
        """
        Return whether an element currently has a graphics
        projection.
        """

        if element is None:
            return False

        return (
            self._key(element)
            in self._items
        )

    # ========================================================
    # COLLECTION ACCESS
    # ========================================================

    def rendered_elements(
        self,
    ) -> Tuple[Any, ...]:
        """
        Return all currently rendered model elements.
        """

        return tuple(
            self._elements.values()
        )

    # --------------------------------------------------------

    def rendered_items(
        self,
    ) -> Tuple[Any, ...]:
        """
        Return all currently managed graphics items.
        """

        return tuple(
            self._items.values()
        )

    # ========================================================
    # COUNT
    # ========================================================

    def __len__(
        self,
    ) -> int:
        """
        Return the number of active graphics projections.
        """

        return len(
            self._items
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict:
        """
        Return diagnostic state.

        The returned state does not expose internal mutable
        dictionaries.
        """

        return {
            "rendered_count": len(
                self._items
            ),
            "registry_size": len(
                self.renderer_registry
            ),
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
            "RenderSystem("
            f"rendered={len(self)}, "
            f"registry={len(self.renderer_registry)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RenderSystem",
]
