"""
GridForge V2 — Renderer Registry
================================

File:
    ui/core/renderer_registry.py

Purpose
-------
Maintains the runtime mapping between GridForge model element
types and their renderer implementations.

The registry stores renderer CLASSES, not renderer instances.

Architectural Contract
----------------------
1. The registry is Qt-independent.
2. The registry does not import concrete renderers.
3. The registry does not instantiate renderers.
4. The registry does not modify the Core model.
5. RenderSystem owns renderer invocation and lifecycle.
6. A model type may have only one directly registered renderer.
7. Re-registering the same renderer class is idempotent.
8. Registering a different renderer for the same model type
   raises an error.
9. Renderer lookup first uses an exact type match.
10. Renderer lookup then follows the model type's MRO.
11. The registry is a runtime mapping, separate from the
    central plugin-discovery registry.

Architecture
------------
    Core Model
        │
        │ model type
        ▼
    RendererRegistry
        │
        │ renderer class
        ▼
    RenderSystem
        │
        ▼
    Renderer
        │
        ▼
    Graphics representation
"""

from __future__ import annotations

from typing import Any, Dict, Iterator, List, Optional, Type


class RendererRegistry:
    """
    Runtime mapping from model classes to renderer classes.
    """

    def __init__(self) -> None:
        """
        Create an empty renderer registry.
        """

        self._renderers: Dict[
            Type[Any],
            Type[Any],
        ] = {}

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_model_type(
        model_type: Type[Any],
    ) -> None:
        """
        Validate a model type argument.
        """

        if not isinstance(model_type, type):
            raise TypeError(
                "model_type must be a class"
            )

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

        Duplicate registration of the same renderer is
        idempotent.

        Registering a different renderer for an already
        registered model type raises ValueError.
        """

        self._validate_model_type(model_type)

        if not isinstance(renderer, type):
            raise TypeError(
                "renderer must be a class"
            )

        existing = self._renderers.get(model_type)

        if existing is not None:

            if existing is renderer:
                return renderer

            raise ValueError(
                "Renderer already registered for "
                f"{model_type.__name__}: "
                f"{existing.__name__}"
            )

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

        Returns True when a registration was removed.
        """

        self._validate_model_type(model_type)

        if model_type not in self._renderers:
            return False

        del self._renderers[model_type]

        return True

    # ========================================================
    # RENDERER LOOKUP
    # ========================================================

    def get_renderer(
        self,
        model_type: Type[Any],
    ) -> Optional[Type[Any]]:
        """
        Retrieve the renderer class for a model type.

        Lookup order:

        1. Exact model-type registration.
        2. Registered base classes according to the model
           type's Python MRO.

        Returns None if no renderer is registered.
        """

        self._validate_model_type(model_type)

        # ----------------------------------------------------
        # Exact match
        # ----------------------------------------------------

        renderer = self._renderers.get(model_type)

        if renderer is not None:
            return renderer

        # ----------------------------------------------------
        # Base-class fallback
        # ----------------------------------------------------

        for base_type in model_type.__mro__[1:]:
            renderer = self._renderers.get(base_type)

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
        Retrieve a renderer class.

        Raises KeyError when no applicable renderer exists.
        """

        self._validate_model_type(model_type)

        renderer = self.get_renderer(model_type)

        if renderer is None:
            raise KeyError(
                "No renderer registered for model type "
                f"'{model_type.__name__}'"
            )

        return renderer

    # ========================================================
    # EXISTENCE CHECK
    # ========================================================

    def contains(
        self,
        model_type: Type[Any],
    ) -> bool:
        """
        Return True when an exact renderer registration exists.

        This intentionally does not perform inheritance lookup.
        """

        self._validate_model_type(model_type)

        return model_type in self._renderers

    # ========================================================
    # REGISTERED MODEL TYPES
    # ========================================================

    def list_model_types(self) -> List[Type[Any]]:
        """
        Return all model classes with directly registered
        renderers.
        """

        return list(self._renderers.keys())

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def list_renderers(self) -> Dict[str, str]:
        """
        Return a human-readable renderer mapping.

        Example
        -------
        {
            "Bus": "BusRenderer",
            "Line": "LineRenderer",
        }
        """

        return {
            model_type.__name__: renderer.__name__
            for model_type, renderer
            in self._renderers.items()
        }

    # ========================================================
    # ITERATION
    # ========================================================

    def items(
        self,
    ) -> Iterator[
        tuple[Type[Any], Type[Any]]
    ]:
        """
        Iterate over directly registered
        (model_type, renderer_class) pairs.
        """

        return iter(self._renderers.items())

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self) -> None:
        """
        Remove all renderer registrations.

        Primarily intended for testing and controlled
        development reload scenarios.
        """

        self._renderers.clear()

    # ========================================================
    # LENGTH
    # ========================================================

    def __len__(self) -> int:
        """
        Return the number of directly registered renderers.
        """

        return len(self._renderers)

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(self) -> str:
        """
        Return a concise diagnostic representation.
        """

        renderer_names = ", ".join(
            renderer.__name__
            for renderer in self._renderers.values()
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
