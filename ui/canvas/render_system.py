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
# RenderSystem bridges:
#
#     Core Model
#         │
#         ▼
#     RendererRegistry
#         │
#         ▼
#     Renderer implementation
#         │
#         ▼
#     QGraphicsItem
#
#
# RESPONSIBILITIES
# ----------------
#
# RenderSystem:
#
#     - owns the runtime collection of rendered model elements
#     - obtains renderer classes from RendererRegistry
#     - creates graphics representations through renderers
#     - adds/removes graphics items from the scene
#     - synchronizes existing graphics with model state
#     - renders individual model elements
#     - renders collections of model elements
#     - clears permanent model graphics
#     - provides diagnostics
#
#
# RenderSystem does NOT:
#
#     - modify the Core model
#     - perform electrical calculations
#     - create model objects
#     - implement interaction logic
#     - manage tools
#     - perform snapping
#     - manage previews
#     - perform coordinate conversion
#     - discover/import renderer modules
#     - contain renderer-specific drawing logic
#
#
# ARCHITECTURAL OWNERSHIP
# -----------------------
#
# RendererRegistry:
#     Knows WHICH renderer handles a model type.
#
# Renderer:
#     Knows HOW a model element is represented graphically.
#
# RenderSystem:
#     Knows WHEN and WHERE renderer output is attached to the
#     canvas scene.
#
# GraphicsView:
#     Owns the Qt view and scene.
#
# InteractionManager:
#     Owns transient interaction and tool routing.
#
# PreviewLayer:
#     Owns temporary interaction graphics.
#
#
# IMPORTANT
# ---------
#
# RenderSystem stores graphics items, not model state.
#
# The Core model remains authoritative.
#
# The graphics layer is therefore a projection of Core state:
#
#             Core Model
#                 │
#                 ▼
#           RenderSystem
#                 │
#                 ▼
#          Graphics Projection
#
#
# RENDERER CONTRACT
# -----------------
#
# A renderer registered for a model class is expected to provide:
#
#     model_type = <ModelClass>
#
#     create_item(element, controller)
#
# and may optionally provide:
#
#     update_item(item, element, controller)
#
#     remove_item(item, element, controller)
#
#
# `create_item()` is the minimum required rendering contract.
#
#
# QT RULE
# -------
#
# This module must not import PySide6/PyQt directly.
#
# Qt types are obtained through:
#
#     ui.core.qt
#
# ============================================================

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Tuple, Type


class RenderSystem:
    """
    Central orchestration layer for permanent model graphics.

    RenderSystem does not know individual renderer classes.

    It obtains renderers through the supplied RendererRegistry
    and maintains the relationship:

        model element -> graphics item

    The Core model remains authoritative. Graphics items are
    merely its visual projection.
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
            RendererRegistry containing model-type-to-renderer
            mappings.

        Notes
        -----
        RenderSystem does not create or own the registry.
        The registry is supplied by the application composition
        layer.
        """

        if scene is None:
            raise ValueError(
                "RenderSystem requires a valid scene."
            )

        if renderer_registry is None:
            raise ValueError(
                "RenderSystem requires a renderer registry."
            )

        self.scene = scene
        self.controller = controller
        self.renderer_registry = renderer_registry

        # ----------------------------------------------------
        # Model → Graphics mapping
        #
        # Identity rather than equality is important here.
        #
        # Two model elements may theoretically compare equal
        # while still representing different domain objects.
        #
        # Therefore the internal mapping is keyed by object
        # identity.
        # ----------------------------------------------------

        self._items: Dict[int, Any] = {}

        # Keep the actual model object alongside the graphics
        # item so diagnostics and synchronization remain safe.
        self._elements: Dict[int, Any] = {}

    # ========================================================
    # IDENTITY
    # ========================================================

    @staticmethod
    def _key(
        element: Any,
    ) -> int:
        """
        Return the identity key for a model element.

        Python object identity is deliberately used instead of
        model equality.
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
        Return the renderer class applicable to a model element.

        RendererRegistry performs exact-type lookup followed by
        its defined inheritance fallback.

        Parameters
        ----------
        element:
            Core model element.

        Returns
        -------
        Type | None
            Renderer class or None when no renderer is registered.
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
        Return the renderer class for a model element.

        Raises
        ------
        KeyError
            When no renderer is registered.
        """

        if element is None:
            raise ValueError(
                "Cannot resolve renderer for None."
            )

        return self.renderer_registry.require_renderer(
            type(element)
        )

    # ========================================================
    # CREATE GRAPHICS ITEM
    # ========================================================

    def _create_item(
        self,
        element: Any,
    ) -> Any:
        """
        Create a graphics item for a model element.

        Renderer-specific creation logic remains entirely inside
        the renderer implementation.
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
                f"'{type(element).__name__}' does not provide "
                "a callable create_item(element, controller)"
            )

        item = create_item(
            element,
            self.controller,
        )

        if item is None:
            raise RuntimeError(
                f"Renderer '{renderer.__name__}' returned None "
                f"while rendering '{type(element).__name__}'"
            )

        return item

    # ========================================================
    # ADD TO SCENE
    # ========================================================

    def _add_item_to_scene(
        self,
        item: Any,
    ) -> None:
        """
        Add a graphics item to the scene.

        Renderers create graphics representations but do not
        own scene insertion.
        """

        self.scene.addItem(
            item
        )

    # ========================================================
    # REMOVE FROM SCENE
    # ========================================================

    def _remove_item_from_scene(
        self,
        item: Any,
    ) -> None:
        """
        Remove a graphics item from the scene.

        The graphics item is detached from the scene but is not
        responsible for modifying the model.
        """

        if item is None:
            return

        self.scene.removeItem(
            item
        )

    # ========================================================
    # RENDER SINGLE ELEMENT
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
            Core model element to render.

        replace:
            If True, an existing graphics representation for the
            same model object is removed and recreated.

            If False, an already-rendered element is returned
            unchanged.

        Returns
        -------
        QGraphicsItem
            Graphics representation associated with the element.

        Raises
        ------
        ValueError
            If element is None.

        KeyError
            If no renderer exists.

        RuntimeError
            If renderer creation fails.
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
        # Existing representation.
        # ----------------------------------------------------

        if existing is not None:

            # Preserve the existing projection unless the
            # caller explicitly requests replacement.
            if not replace:
                return existing

            self.remove(
                element
            )

        # ----------------------------------------------------
        # Create renderer output.
        # ----------------------------------------------------

        item = self._create_item(
            element
        )

        # ----------------------------------------------------
        # Attach to scene.
        # ----------------------------------------------------

        self._add_item_to_scene(
            item
        )

        # ----------------------------------------------------
        # Store projection mapping.
        # ----------------------------------------------------

        self._items[key] = item
        self._elements[key] = element

        return item

    # ========================================================
    # RENDER MANY
    # ========================================================

    def render_all(
        self,
        elements: Iterable[Any],
    ) -> Dict[Any, Any]:
        """
        Render a collection of model elements.

        Existing representations are reused.

        Parameters
        ----------
        elements:
            Iterable of Core model elements.

        Returns
        -------
        dict
            Mapping:

                model element -> graphics item

        Notes
        -----
        The returned dictionary is a convenience result.
        Internal ownership remains with RenderSystem.
        """

        rendered = {}

        for element in elements:

            if element is None:
                continue

            item = self.render(
                element
            )

            rendered[element] = item

        return rendered

    # ========================================================
    # UPDATE SINGLE ELEMENT
    # ========================================================

    def update(
        self,
        element: Any,
    ) -> Any:
        """
        Synchronize the graphics representation of a model
        element with its current Core state.

        If the renderer implements:

            update_item(item, element, controller)

        that method is used.

        If no update method exists, the graphics representation
        is recreated.

        Returns
        -------
        QGraphicsItem
            Current graphics representation.
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
        # No existing representation.
        #
        # RenderSystem treats update() as an idempotent
        # synchronization operation.
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
        # Renderer provides incremental synchronization.
        # ----------------------------------------------------

        if callable(update_item):

            result = update_item(
                item,
                element,
                self.controller,
            )

            # Renderer may mutate the item in place and return
            # None. In that case the existing item remains the
            # authoritative graphics representation.
            if result is None:
                return item

            # A renderer may deliberately return a replacement
            # graphics item.
            if result is not item:

                self._remove_item_from_scene(
                    item
                )

                self._add_item_to_scene(
                    result
                )

                self._items[key] = result

                return result

            return item

        # ----------------------------------------------------
        # No incremental update contract.
        #
        # Recreate the representation through the renderer.
        # ----------------------------------------------------

        return self.render(
            element,
            replace=True,
        )

    # ========================================================
    # UPDATE MANY
    # ========================================================

    def update_all(
        self,
        elements: Iterable[Any],
    ) -> Dict[Any, Any]:
        """
        Synchronize a collection of model elements.

        Returns
        -------
        dict
            Mapping of model elements to their current graphics
            representations.
        """

        updated = {}

        for element in elements:

            if element is None:
                continue

            item = self.update(
                element
            )

            updated[element] = item

        return updated

    # ========================================================
    # REMOVE SINGLE ELEMENT
    # ========================================================

    def remove(
        self,
        element: Any,
    ) -> bool:
        """
        Remove the permanent graphics representation of a model
        element.

        IMPORTANT
        ---------
        This method does NOT remove the model element from Core.

        It only removes the graphics projection.
        """

        if element is None:
            return False

        key = self._key(
            element
        )

        item = self._items.pop(
            key,
            None,
        )

        self._elements.pop(
            key,
            None,
        )

        if item is None:
            return False

        # ----------------------------------------------------
        # Give the renderer an opportunity to perform renderer-
        # specific cleanup.
        # ----------------------------------------------------

        renderer = self.renderer_registry.get_renderer(
            type(element)
        )

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
        # RenderSystem remains responsible for scene ownership.
        # ----------------------------------------------------

        self._remove_item_from_scene(
            item
        )

        return True

    # ========================================================
    # REMOVE MANY
    # ========================================================

    def remove_all(
        self,
        elements: Iterable[Any],
    ) -> int:
        """
        Remove graphics representations for a collection of
        model elements.

        Returns
        -------
        int
            Number of representations removed.
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
        Remove all permanent model graphics managed by this
        RenderSystem.

        IMPORTANT
        ---------
        This clears the graphics projection only.

        It does NOT clear or mutate the Core model.

        PreviewLayer graphics are not owned by RenderSystem and
        therefore are not touched here.
        """

        # Work on a snapshot because remove() mutates the
        # internal mappings.
        elements = list(
            self._elements.values()
        )

        for element in elements:
            self.remove(
                element
            )

        # Defensive cleanup in case a renderer behaved
        # unexpectedly during removal.
        self._items.clear()
        self._elements.clear()

    # ========================================================
    # LOOKUP GRAPHICS ITEM
    # ========================================================

    def get_item(
        self,
        element: Any,
    ) -> Optional[Any]:
        """
        Return the graphics item associated with a model element.

        Returns None when the element is not currently rendered.
        """

        if element is None:
            return None

        return self._items.get(
            self._key(element)
        )

    # ========================================================
    # EXISTENCE CHECK
    # ========================================================

    def contains(
        self,
        element: Any,
    ) -> bool:
        """
        Return True if a model element currently has a graphics
        representation managed by this RenderSystem.
        """

        if element is None:
            return False

        return self._key(
            element
        ) in self._items

    # ========================================================
    # MODEL ELEMENTS
    # ========================================================

    def rendered_elements(self) -> Tuple[Any, ...]:
        """
        Return all currently rendered model elements.

        A tuple is returned so callers cannot directly mutate
        the internal collection.
        """

        return tuple(
            self._elements.values()
        )

    # ========================================================
    # GRAPHICS ITEMS
    # ========================================================

    def rendered_items(self) -> Tuple[Any, ...]:
        """
        Return all currently managed graphics items.
        """

        return tuple(
            self._items.values()
        )

    # ========================================================
    # COUNT
    # ========================================================

    def __len__(self) -> int:
        """
        Return the number of currently rendered model elements.
        """

        return len(
            self._items
        )

    # ========================================================
    # SYNCHRONIZATION
    # ========================================================

    def synchronize(
        self,
        elements: Iterable[Any],
    ) -> Dict[Any, Any]:
        """
        Synchronize the canvas with a supplied model-element
        collection.

        The supplied collection is treated as the authoritative
        set of elements that should currently be rendered.

        Processing:

            1. Existing elements absent from the collection are
               removed from the graphics layer.

            2. Existing elements are updated.

            3. New elements are rendered.

        IMPORTANT
        ---------
        This method does not mutate the Core model.

        Parameters
        ----------
        elements:
            Current authoritative set of model elements to
            display.

        Returns
        -------
        dict
            Current model-element-to-graphics-item mapping.
        """

        # Materialize once because callers may supply a generator.
        elements = tuple(
            element
            for element in elements
            if element is not None
        )

        desired_keys = {
            self._key(element)
            for element in elements
        }

        # ----------------------------------------------------
        # Remove stale graphics.
        # ----------------------------------------------------

        stale_elements = [
            element
            for element in self._elements.values()
            if self._key(element) not in desired_keys
        ]

        for element in stale_elements:
            self.remove(
                element
            )

        # ----------------------------------------------------
        # Render or update desired elements.
        # ----------------------------------------------------

        result = {}

        for element in elements:

            item = self.update(
                element
            )

            result[element] = item

        return result

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(self) -> dict:
        """
        Return diagnostic information about the RenderSystem.
        """

        return {
            "rendered_count": len(
                self._items
            ),
            "registry_size": len(
                self.renderer_registry
            ),
            "scene": self.scene,
            "controller": self.controller,
        }

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
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
