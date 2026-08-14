# ============================================================
# File: ui/core/renderer_registry.py
# GridForge V2 — Renderer Registry
# ============================================================
"""
Central registry for GridForge UI renderers.

Architecture
------------

    RendererRegistry
          │
          ├── renderer_id → renderer factory
          │
          ▼
      RenderSystem
          │
          ▼
    Renderer instance
          │
          ▼
    QGraphicsScene / Graphics Items

Responsibilities
----------------
RendererRegistry:

    - stores renderer registrations;
    - maps stable renderer IDs to renderer factories;
    - validates registrations;
    - provides renderer lookup;
    - creates renderer instances on request;
    - exposes registered renderer IDs;
    - prevents accidental duplicate registrations;
    - provides diagnostic state.

RendererRegistry does NOT:

    - own the active renderer;
    - manage renderer lifecycle;
    - perform rendering itself;
    - own the QGraphicsScene;
    - create or mutate Core model objects;
    - implement electrical calculations;
    - perform selection;
    - perform snapping;
    - manage tools;
    - decide which objects should be rendered;
    - subscribe to Controller events.

Renderer Ownership
------------------
RendererRegistry owns only renderer registration/factory
definitions.

RenderSystem owns renderer instances and rendering lifecycle.

Therefore:

    RendererRegistry
        = registration + factory lookup

    RenderSystem
        = renderer ownership + rendering orchestration

Concrete Renderers
------------------
The registry deliberately does NOT import concrete renderer
classes.

Concrete renderer registration is performed explicitly by the
UI composition/bootstrap layer.

This keeps registration explicit and prevents the registry from
becoming an implicit plugin loader.

Registration Contract
----------------------
A renderer registration consists of:

    renderer_id
    factory

The factory must be callable.

The registry does not impose a concrete constructor signature.
Constructor dependencies are supplied by RenderSystem.

Stable IDs
----------
Renderer IDs are application-level identifiers.

Examples include:

    "bus"
    "line"

Additional renderer types may be registered by future UI
composition code without modifying this registry.

Qt Architecture
---------------
This registry contains no Qt dependency.

All Qt dependencies, where required by concrete renderers, must
remain behind ui.core.qt.
"""

from __future__ import annotations

from typing import Any, Callable, Optional


RendererFactory = Callable[..., Any]


class RendererRegistry:
    """
    Registry of available GridForge UI renderers.

    The registry is independent of concrete renderer classes.

    Example:

        registry.register(
            "bus",
            BusRenderer,
        )

    RenderSystem is responsible for deciding when and how the
    registered renderer is instantiated.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(self) -> None:
        """
        Initialize an empty renderer registry.
        """

        self._factories: dict[
            str,
            RendererFactory,
        ] = {}

    # ========================================================
    # REGISTRATION
    # ========================================================

    def register(
        self,
        renderer_id: str,
        factory: RendererFactory,
        *,
        replace: bool = False,
    ) -> None:
        """
        Register a renderer factory.

        Parameters
        ----------
        renderer_id:
            Stable application-level renderer identifier.

        factory:
            Callable used to construct the renderer.

        replace:
            When False, duplicate registration raises ValueError.

            When True, an existing registration is replaced.
        """

        normalized_id = self._validate_renderer_id(
            renderer_id
        )

        if not callable(factory):
            raise TypeError(
                "factory must be callable."
            )

        if (
            normalized_id in self._factories
            and not replace
        ):
            raise ValueError(
                f"Renderer {normalized_id!r} "
                "is already registered."
            )

        self._factories[
            normalized_id
        ] = factory

    # --------------------------------------------------------

    def unregister(
        self,
        renderer_id: str,
    ) -> RendererFactory:
        """
        Remove and return a registered renderer factory.

        Raises
        ------
        KeyError
            If the renderer is not registered.
        """

        normalized_id = self._validate_renderer_id(
            renderer_id
        )

        try:
            return self._factories.pop(
                normalized_id
            )
        except KeyError:
            raise KeyError(
                f"Renderer {normalized_id!r} "
                "is not registered."
            ) from None

    # --------------------------------------------------------

    def clear(self) -> None:
        """
        Remove all renderer registrations.

        Existing renderer instances owned by RenderSystem are
        unaffected.
        """

        self._factories.clear()

    # ========================================================
    # REGISTRATION QUERIES
    # ========================================================

    def contains(
        self,
        renderer_id: str,
    ) -> bool:
        """
        Return True when renderer_id is registered.
        """

        normalized_id = self._validate_renderer_id(
            renderer_id
        )

        return (
            normalized_id
            in self._factories
        )

    # --------------------------------------------------------

    def has_renderer(
        self,
        renderer_id: str,
    ) -> bool:
        """
        Semantic alias for contains().
        """

        return self.contains(
            renderer_id
        )

    # --------------------------------------------------------

    def get_factory(
        self,
        renderer_id: str,
    ) -> RendererFactory:
        """
        Return the factory registered for renderer_id.

        The factory is not executed.
        """

        normalized_id = self._validate_renderer_id(
            renderer_id
        )

        try:
            return self._factories[
                normalized_id
            ]
        except KeyError:
            raise KeyError(
                f"Renderer {normalized_id!r} "
                "is not registered."
            ) from None

    # --------------------------------------------------------

    def get_optional_factory(
        self,
        renderer_id: str,
    ) -> Optional[RendererFactory]:
        """
        Return a registered factory or None when absent.
        """

        normalized_id = self._validate_renderer_id(
            renderer_id
        )

        return self._factories.get(
            normalized_id
        )

    # ========================================================
    # RENDERER CREATION
    # ========================================================

    def create(
        self,
        renderer_id: str,
        **kwargs: Any,
    ) -> Any:
        """
        Create a renderer instance using its registered factory.

        Parameters
        ----------
        renderer_id:
            Registered renderer identifier.

        **kwargs:
            Constructor dependencies supplied by RenderSystem.

        Returns
        -------
        object
            Newly created renderer instance.

        Notes
        -----
        RendererRegistry does not retain ownership of the created
        renderer.
        """

        factory = self.get_factory(
            renderer_id
        )

        return factory(
            **kwargs
        )

    # ========================================================
    # RENDERER IDS
    # ========================================================

    def renderer_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Return all registered renderer IDs.

        Registration order is preserved.
        """

        return tuple(
            self._factories.keys()
        )

    # --------------------------------------------------------

    def get_renderer_ids(
        self,
    ) -> tuple[str, ...]:
        """
        Semantic alias for renderer_ids().
        """

        return self.renderer_ids()

    # --------------------------------------------------------

    def count(self) -> int:
        """
        Return the number of registered renderers.
        """

        return len(
            self._factories
        )

    # ========================================================
    # REQUIRED RENDERER VALIDATION
    # ========================================================

    def require(
        self,
        renderer_id: str,
    ) -> RendererFactory:
        """
        Require a renderer registration.

        Intended for UI bootstrap validation.
        """

        return self.get_factory(
            renderer_id
        )

    # --------------------------------------------------------

    def require_renderers(
        self,
        renderer_ids: tuple[str, ...] | list[str],
    ) -> None:
        """
        Verify that all supplied renderer IDs are registered.

        Raises
        ------
        KeyError
            If any required renderer is missing.
        """

        if renderer_ids is None:
            raise ValueError(
                "renderer_ids must not be None."
            )

        for renderer_id in renderer_ids:
            self.require(
                renderer_id
            )

    # ========================================================
    # FACTORY REPLACEMENT
    # ========================================================

    def replace(
        self,
        renderer_id: str,
        factory: RendererFactory,
    ) -> None:
        """
        Replace an existing renderer registration.

        A missing registration is treated as an error.
        """

        normalized_id = self._validate_renderer_id(
            renderer_id
        )

        if not callable(factory):
            raise TypeError(
                "factory must be callable."
            )

        if normalized_id not in self._factories:
            raise KeyError(
                f"Renderer {normalized_id!r} "
                "is not registered."
            )

        self._factories[
            normalized_id
        ] = factory

    # ========================================================
    # SNAPSHOT
    # ========================================================

    def get_factories(
        self,
    ) -> dict[str, RendererFactory]:
        """
        Return a shallow copy of registered factories.

        The internal registry dictionary is never exposed.
        """

        return dict(
            self._factories
        )

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_renderer_id(
        renderer_id: str,
    ) -> str:
        """
        Validate and normalize a renderer identifier.
        """

        if not isinstance(
            renderer_id,
            str,
        ):
            raise TypeError(
                "renderer_id must be a string."
            )

        normalized_id = renderer_id.strip()

        if not normalized_id:
            raise ValueError(
                "renderer_id must not be empty."
            )

        return normalized_id

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of registry state.
        """

        return {
            "renderer_count": self.count(),
            "renderer_ids": self.renderer_ids(),
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
            "RendererRegistry("
            f"renderers={self.renderer_ids()!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RendererFactory",
    "RendererRegistry",
]
