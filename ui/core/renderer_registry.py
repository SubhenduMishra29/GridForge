# ============================================================
# File: ui/core/renderer_registry.py
# GridForge Renderer Registry
# ============================================================

"""
Runtime registry mapping Core model element types to renderer
implementations.

Architecture
------------

    Core Model Element
            │
            ▼
    RendererRegistry
            │
            ▼
      Renderer Class
            │
            ▼
      Graphics Item


Responsibilities
----------------
RendererRegistry:

    - stores renderer classes
    - registers renderer classes
    - resolves renderers by model type
    - supports inheritance fallback
    - prevents accidental replacement
    - provides diagnostics

RendererRegistry does NOT:

    - import renderers
    - discover plugins
    - import Qt
    - create graphics items
    - modify the Core model
    - own renderer instances
    - perform rendering

Renderer loading belongs to renderer_loader.py.

Rendering orchestration belongs to RenderSystem.
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Type


class RendererRegistry:
    """
    Runtime mapping from Core model classes to renderer classes.

    The registry stores renderer IMPLEMENTATIONS, not renderer
    instances and not QGraphicsItems.

    Example
    -------

        registry.register(Bus, BusRenderer)

        renderer = registry.get_renderer(Bus)

    Renderer inheritance
    --------------------

    Exact registrations have priority over inherited registrations.

    Example:

        ElectricalElement
                ↑
               Bus

    If only ElectricalElement has a renderer, Bus resolves to the
    ElectricalElement renderer.

    If Bus has its own renderer, the Bus renderer wins.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self) -> None:
        """
        Create an empty renderer registry.
        """

        self._renderers: Dict[
            Type[Any],
            Type[Any],
        ] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        model_type: Type[Any],
        renderer: Type[Any],
    ) -> Type[Any]:
        """
        Register a renderer class for a model class.

        Parameters
        ----------
        model_type:
            Core model class handled by the renderer.

        renderer:
            Renderer implementation class.

        Returns
        -------
        Type
            The registered renderer class.

        Raises
        ------
        TypeError
            If either argument is not a class.

        ValueError
            If another renderer is already registered for the
            same model type.

        Notes
        -----
        Registering the exact same renderer class more than once
        is idempotent and therefore harmless.
        """

        # ----------------------------------------------------
        # Validate model type.
        # ----------------------------------------------------

        if not isinstance(model_type, type):
            raise TypeError(
                "model_type must be a class."
            )

        # ----------------------------------------------------
        # Validate renderer type.
        # ----------------------------------------------------

        if not isinstance(renderer, type):
            raise TypeError(
                "renderer must be a class."
            )

        # ----------------------------------------------------
        # Check existing registration.
        # ----------------------------------------------------

        existing = self._renderers.get(
            model_type
        )

        if existing is not None:

            # Same registration is harmless.
            if existing is renderer:
                return renderer

            # Different renderer for the same model type is
            # an architectural/configuration error.
            raise ValueError(
                "Renderer already registered for model type "
                f"'{model_type.__name__}': "
                f"'{existing.__name__}'."
            )

        # ----------------------------------------------------
        # Register.
        # ----------------------------------------------------

        self._renderers[model_type] = renderer

        return renderer

    # ========================================================
    # UNREGISTER
    # ========================================================

    def unregister(
        self,
        model_type: Type[Any],
    ) -> bool:
        """
        Remove the directly registered renderer for a model type.

        Returns
        -------
        bool
            True if a registration was removed.
            False if no direct registration existed.
        """

        if model_type not in self._renderers:
            return False

        del self._renderers[model_type]

        return True

    # ========================================================
    # LOOKUP
    # ========================================================

    def get_renderer(
        self,
        model_type: Type[Any],
    ) -> Optional[Type[Any]]:
        """
        Resolve a renderer for a model class.

        Lookup order
        ------------

        1. Exact model-type registration.
        2. First registered renderer found in the model class MRO.

        The exact registration always takes precedence.

        Returns
        -------
        Type | None
            Renderer class, or None if no renderer is registered.
        """

        if not isinstance(model_type, type):
            raise TypeError(
                "model_type must be a class."
            )

        # ----------------------------------------------------
        # Exact match.
        # ----------------------------------------------------

        renderer = self._renderers.get(
            model_type
        )

        if renderer is not None:
            return renderer

        # ----------------------------------------------------
        # Inheritance fallback.
        #
        # Python's MRO gives deterministic nearest-base lookup.
        # ----------------------------------------------------

        for base_type in model_type.__mro__[1:]:

            renderer = self._renderers.get(
                base_type
            )

            if renderer is not None:
                return renderer

        return None

    # ========================================================
    # REQUIRED LOOKUP
    # ========================================================

    def require_renderer(
        self,
        model_type: Type[Any],
    ) -> Type[Any]:
        """
        Resolve a renderer or raise an explicit configuration
        error.

        This is the preferred API for RenderSystem when every
        renderable model type is expected to have a renderer.
        """

        renderer = self.get_renderer(
            model_type
        )

        if renderer is None:
            raise KeyError(
                "No renderer registered for model type "
                f"'{model_type.__name__}'."
            )

        return renderer

    # ========================================================
    # EXACT REGISTRATION CHECK
    # ========================================================

    def contains(
        self,
        model_type: Type[Any],
    ) -> bool:
        """
        Return True only when model_type has a direct renderer
        registration.

        This intentionally does NOT perform inheritance lookup.
        """

        if not isinstance(model_type, type):
            raise TypeError(
                "model_type must be a class."
            )

        return model_type in self._renderers

    # ========================================================
    # RESOLUTION CHECK
    # ========================================================

    def can_render(
        self,
        model_type: Type[Any],
    ) -> bool:
        """
        Return True when a renderer can be resolved for model_type.

        Unlike contains(), this includes inheritance fallback.
        """

        return (
            self.get_renderer(model_type)
            is not None
        )

    # ========================================================
    # REGISTERED MODEL TYPES
    # ========================================================

    def list_model_types(
        self,
    ) -> List[Type[Any]]:
        """
        Return all directly registered model classes.

        Registration order is preserved.
        """

        return list(
            self._renderers.keys()
        )

    # ========================================================
    # REGISTERED RENDERERS
    # ========================================================

    def list_renderer_classes(
        self,
    ) -> List[Type[Any]]:
        """
        Return all directly registered renderer classes.

        Registration order is preserved.
        """

        return list(
            self._renderers.values()
        )

    # ========================================================
    # ITERATION
    # ========================================================

    def items(
        self,
    ) -> Iterator[
        tuple[Type[Any], Type[Any]]
    ]:
        """
        Iterate over direct:

            (model_type, renderer_class)

        registrations.
        """

        return iter(
            self._renderers.items()
        )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def list_renderers(
        self,
    ) -> Dict[str, str]:
        """
        Return a human-readable representation of the registry.

        Example
        -------

            {
                "Bus": "BusRenderer",
                "Line": "LineRenderer"
            }

        This is intended for diagnostics and development tools.
        """

        return {
            model_type.__name__: renderer.__name__
            for model_type, renderer
            in self._renderers.items()
        }

    # ========================================================
    # REGISTRY SNAPSHOT
    # ========================================================

    def snapshot(
        self,
    ) -> Dict[
        Type[Any],
        Type[Any],
    ]:
        """
        Return a shallow copy of the registry.

        Mutating the returned dictionary does not modify the
        registry itself.
        """

        return dict(
            self._renderers
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self) -> None:
        """
        Remove all renderer registrations.

        Intended primarily for:

            - tests
            - development reload
            - controlled application reset

        Normal application execution should generally not call
        this method.
        """

        self._renderers.clear()

    # ========================================================
    # LENGTH
    # ========================================================

    def __len__(
        self,
    ) -> int:
        """
        Return the number of directly registered renderers.
        """

        return len(
            self._renderers
        )

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        renderer_names = ", ".join(
            renderer.__name__
            for renderer
            in self._renderers.values()
        )

        return (
            "RendererRegistry("
            f"renderers=[{renderer_names}]"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RendererRegistry",
]
