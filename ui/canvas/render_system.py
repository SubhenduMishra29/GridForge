# ============================================================
# File: ui/canvas/render_system.py
# GridForge Canvas Render System
# ============================================================

"""
Central rendering orchestration layer for the GridForge canvas.

Architecture
------------

    Authoritative Core Model
              │
              ▼
        RenderSystem
              │
        ┌─────┴─────┐
        ▼           ▼
RendererRegistry  QGraphicsScene
        │           │
        ▼           ▼
Renderer Class   Graphics Item
        │
        ▼
   create_item()

Responsibilities
----------------
RenderSystem:

    - owns the RendererRegistry
    - loads renderer plugins
    - resolves renderers for Core model types
    - creates permanent graphics
    - tracks model-to-graphics projections
    - removes stale graphics
    - refreshes existing graphics
    - reconciles graphics against authoritative model state
    - synchronizes graphical selection
    - provides renderer lookup
    - provides rendering diagnostics

RenderSystem does NOT:

    - modify the Core model
    - perform electrical calculations
    - perform topology operations
    - handle mouse or keyboard events
    - implement tools
    - perform snapping
    - own transient previews
    - implement grid rendering
    - implement individual renderers
    - own renderer instances

Authority
---------
The Core model is authoritative.

QGraphicsItems are projections of Core model state.

The RenderSystem must therefore never use a graphics item as the
authoritative representation of an electrical object.

Renderer contract
-----------------
Every renderer must provide:

    model_type = <Core model class>

    create_item(element, controller)

Optional renderer/item synchronization is performed through the
graphics item's:

    refresh_from_model()

method when available.

Renderer discovery and registration are delegated to
RendererLoader and RendererRegistry respectively.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional, Type

from ui.core.renderer_loader import load_renderers
from ui.core.renderer_registry import RendererRegistry


# ============================================================
# RENDER SYSTEM
# ============================================================


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

    Notes
    -----
    RenderSystem owns the renderer registry for the canvas
    rendering domain.

    It does not own renderer instances. Renderer classes are
    invoked through their static/class-level rendering contract.
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
        """
        Initialize the RenderSystem.
        """

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
        # Rendered model projections
        #
        # Runtime object identity is intentionally used for the
        # projection cache.
        #
        # _elements retains the actual model references so that
        # the mapping remains identity-safe while an element is
        # rendered.
        # ----------------------------------------------------

        self._items: Dict[int, Any] = {}
        self._elements: Dict[int, Any] = {}

        # ----------------------------------------------------
        # Discover and register renderers.
        #
        # RendererLoader owns discovery.
        # RendererRegistry owns registration.
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
        Create and attach the permanent graphics projection
        for one authoritative Core model element.

        Existing graphics for the same model object are reused.

        Parameters
        ----------
        element:
            Authoritative Core model object.

        Returns
        -------
        Any
            Graphics item representing the model element.

        Raises
        ------
        ValueError
            If element is None.

        KeyError
            If no renderer is registered.

        TypeError
            If the renderer violates its contract.

        RuntimeError
            If renderer item creation returns None.
        """

        if element is None:
            raise ValueError(
                "Cannot render a None model element."
            )

        element_key = id(element)

        # ----------------------------------------------------
        # Existing projection
        # ----------------------------------------------------

        existing = self._items.get(
            element_key
        )

        if existing is not None:
            return existing

        # ----------------------------------------------------
        # Resolve renderer from authoritative model type.
        # ----------------------------------------------------

        renderer_cls = self.registry.require_renderer(
            type(element)
        )

        # ----------------------------------------------------
        # Validate renderer contract.
        # ----------------------------------------------------

        create_item = getattr(
            renderer_cls,
            "create_item",
            None,
        )

        if not callable(create_item):
            raise TypeError(
                f"{renderer_cls.__name__} must implement "
                "create_item(element, controller)."
            )

        # ----------------------------------------------------
        # Create graphics projection.
        # ----------------------------------------------------

        item = create_item(
            element,
            self.controller,
        )

        if item is None:
            raise RuntimeError(
                f"{renderer_cls.__name__}.create_item() "
                "returned None."
            )

        # ----------------------------------------------------
        # Attach to scene.
        # ----------------------------------------------------

        self.scene.addItem(
            item
        )

        # ----------------------------------------------------
        # Register projection only after successful scene
        # attachment.
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

        Existing projections are reused.

        Returns
        -------
        dict
            Mapping of runtime model identity to graphics item.
        """

        if elements is None:
            raise ValueError(
                "elements must not be None."
            )

        rendered: Dict[int, Any] = {}

        for element in elements:

            if element is None:
                raise ValueError(
                    "Cannot render a None model element."
                )

            item = self.render(
                element
            )

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
        Remove the graphics projection belonging to a model
        element.

        Only the visual projection is modified.

        The Core model is never modified.

        Returns
        -------
        bool
            True when a projection was removed.
            False when no projection existed.
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

        self.scene.removeItem(
            item
        )

        return True

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self) -> None:
        """
        Remove all permanent graphics projections.

        The Core model is not modified.
        """

        for item in tuple(
            self._items.values()
        ):
            self.scene.removeItem(
                item
            )

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
        Return the graphics projection associated with a model
        element.

        Returns None when the element is not currently rendered.
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
        Return True when the model element currently has a
        graphics projection.
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
        Synchronize the graphics projection with the current
        authoritative model state.

        Preferred synchronization path:

            item.refresh_from_model()

        If the graphics item does not implement that contract,
        the projection is recreated through the canonical
        renderer contract.

        The Core model is never modified.
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
            return self.render(
                element
            )

        # ----------------------------------------------------
        # Preferred in-place synchronization.
        # ----------------------------------------------------

        refresh_from_model = getattr(
            item,
            "refresh_from_model",
            None,
        )

        if callable(
            refresh_from_model
        ):
            refresh_from_model()
            return item

        # ----------------------------------------------------
        # Fallback: recreate the visual projection.
        #
        # This path is intentionally secondary. Graphics items
        # should preferably implement refresh_from_model().
        # ----------------------------------------------------

        self.remove(
            element
        )

        return self.render(
            element
        )

    # ========================================================
    # REFRESH ALL
    # ========================================================

    def refresh_all(
        self,
        elements: Optional[Iterable[Any]] = None,
    ) -> None:
        """
        Refresh selected or all currently rendered elements.

        Parameters
        ----------
        elements:
            Optional iterable of authoritative model elements.

            If omitted, all currently rendered elements are
            refreshed.
        """

        if elements is None:
            elements = tuple(
                self._elements.values()
            )

        for element in tuple(
            elements
        ):
            self.refresh(
                element
            )

    # ========================================================
    # RECONCILIATION
    # ========================================================

    def reconcile(
        self,
        elements: Iterable[Any],
    ) -> None:
        """
        Reconcile permanent graphics against an authoritative
        collection of Core model elements.

        Reconciliation guarantees:

            authoritative element without graphics
                → render

            authoritative element with graphics
                → retain and refresh

            graphics without authoritative element
                → remove

        The Core model remains authoritative.

        Notes
        -----
        Reconciliation is a full synchronization operation.

        It intentionally refreshes existing graphics because the
        caller is explicitly requesting synchronization against
        the supplied authoritative collection.
        """

        if elements is None:
            raise ValueError(
                "elements must not be None."
            )

        authoritative = tuple(
            elements
        )

        # ----------------------------------------------------
        # Validate collection.
        # ----------------------------------------------------

        for element in authoritative:
            if element is None:
                raise ValueError(
                    "Authoritative element collection "
                    "must not contain None."
                )

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
                self.remove(
                    element
                )

        # ----------------------------------------------------
        # Render missing projections and refresh existing ones.
        # ----------------------------------------------------

        for element in authoritative:

            element_key = id(element)

            if element_key in self._items:
                self.refresh(
                    element
                )
            else:
                self.render(
                    element
                )

    # ========================================================
    # SELECTION SYNCHRONIZATION
    # ========================================================

    def refresh_selection(
        self,
        selected_ids: Optional[Iterable[str]] = None,
    ) -> None:
        """
        Synchronize graphical selection from authoritative
        application selection.

        Parameters
        ----------
        selected_ids:
            Iterable of authoritative Core object IDs.

            If omitted, ``controller.selected_ids`` is used when
            available.

        Notes
        -----
        Selection is application state.

        QGraphicsItem selection is only a visual projection of
        that state.
        """

        if selected_ids is None:
            selected_ids = getattr(
                self.controller,
                "selected_ids",
                (),
            )

        selected = set(
            selected_ids
        )

        for item in tuple(
            self._items.values()
        ):

            object_id = getattr(
                item,
                "object_id",
                None,
            )

            if object_id is None:
                item.setSelected(
                    False
                )
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
    ) -> Optional[Type[Any]]:
        """
        Return the renderer resolved for a Core model type.

        RendererRegistry performs exact and inheritance lookup.
        """

        return self.registry.get_renderer(
            model_type
        )

    # --------------------------------------------------------

    def require_renderer(
        self,
        model_type: Type[Any],
    ) -> Type[Any]:
        """
        Require a renderer for a Core model type.

        Raises KeyError when no renderer can be resolved.
        """

        return self.registry.require_renderer(
            model_type
        )

    # ========================================================
    # REGISTRY ACCESS
    # ========================================================

    def get_registry(
        self,
    ) -> RendererRegistry:
        """
        Return the renderer registry owned by this RenderSystem.

        The caller should treat the registry as an orchestration
        dependency rather than as the rendering authority.
        """

        return self.registry

    # ========================================================
    # RENDERED ELEMENTS
    # ========================================================

    def get_rendered_elements(
        self,
    ) -> tuple[Any, ...]:
        """
        Return the currently rendered model elements.

        The returned tuple is a snapshot and cannot modify the
        RenderSystem's internal mapping.
        """

        return tuple(
            self._elements.values()
        )

    # --------------------------------------------------------

    def get_rendered_items(
        self,
    ) -> tuple[Any, ...]:
        """
        Return the currently attached graphics projections.

        The returned tuple is a snapshot.
        """

        return tuple(
            self._items.values()
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic rendering state.
        """

        return {
            "rendered_count": len(
                self._items
            ),
            "renderer_count": len(
                self.registry
            ),
            "renderers": self.registry.list_renderers(),
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
