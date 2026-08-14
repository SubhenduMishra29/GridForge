# ============================================================
# File: ui/core/renderer_loader.py
# GridForge V2 — Renderer Loader
# ============================================================
"""
Explicit renderer registration loader for GridForge V2.

Architecture
------------

    UI Composition / Bootstrap
              │
              ▼
       RendererLoader
              │
              ▼
       RendererRegistry
              │
              ▼
       RenderSystem
              │
              ▼
      Concrete Renderers

Purpose
-------
RendererLoader provides the explicit registration boundary for
concrete GridForge renderers.

It intentionally separates:

    registry
        stores renderer factories;

    loader
        explicitly imports and registers concrete renderers;

    RenderSystem
        owns renderer instances and rendering lifecycle.

This module prevents RendererRegistry from becoming an implicit
plugin loader.

Concrete Renderers
------------------
The loader is the explicit composition point for the concrete
renderer set.

Current renderer set:

    - BusRenderer
    - LineRenderer

No renderer is discovered dynamically.

No filesystem scanning is performed.

No package introspection is performed.

No automatic imports are performed.

Responsibilities
----------------
RendererLoader:

    - explicitly import concrete renderer classes;
    - register them with RendererRegistry;
    - validate the expected renderer set;
    - provide one deterministic loading operation.

RendererLoader does NOT:

    - own renderer instances;
    - render anything;
    - create QGraphicsItems directly;
    - manage renderer lifecycle;
    - select renderers dynamically;
    - subscribe to Controller events;
    - modify Core state;
    - perform electrical calculations;
    - perform selection;
    - perform snapping.

Registration Ownership
----------------------
The explicit loader owns registration knowledge.

RendererRegistry owns the resulting registrations.

RenderSystem owns the resulting renderer instances.

Therefore:

    RendererLoader
        = explicit composition

    RendererRegistry
        = registration/factory lookup

    RenderSystem
        = renderer lifecycle + rendering

Qt Architecture
---------------
Concrete renderer modules must obey the GridForge Qt rule:

    all Qt imports through ui.core.qt

This loader itself does not import Qt.
"""

from __future__ import annotations

from typing import Any, Optional

from ui.core.renderer_registry import RendererRegistry


class RendererLoader:
    """
    Explicit loader for the GridForge V2 renderer set.

    The loader does not retain renderer instances.

    It only performs deterministic registration into the supplied
    RendererRegistry.
    """

    # ========================================================
    # CANONICAL RENDERER IDS
    # ========================================================

    BUS_RENDERER_ID = "bus"
    LINE_RENDERER_ID = "line"

    REQUIRED_RENDERER_IDS = (
        BUS_RENDERER_ID,
        LINE_RENDERER_ID,
    )

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        registry: RendererRegistry,
    ) -> None:
        """
        Initialize the loader.

        Parameters
        ----------
        registry:
            RendererRegistry receiving the explicit renderer
            registrations.
        """

        if registry is None:
            raise ValueError(
                "registry must not be None."
            )

        if not isinstance(
            registry,
            RendererRegistry,
        ):
            raise TypeError(
                "registry must be a RendererRegistry."
            )

        self.registry = registry
        self._loaded = False

    # ========================================================
    # EXPLICIT LOADING
    # ========================================================

    def load(
        self,
        *,
        replace: bool = False,
    ) -> None:
        """
        Explicitly import and register all concrete renderers.

        Parameters
        ----------
        replace:
            Replace existing registrations when True.

        Notes
        -----
        Imports are intentionally local to this method.

        This keeps the registry independent of concrete renderer
        implementations and makes the composition boundary
        explicit.
        """

        from ui.renderers.bus_renderer import (
            BusRenderer,
        )

        from ui.renderers.line_renderer import (
            LineRenderer,
        )

        self.registry.register(
            self.BUS_RENDERER_ID,
            BusRenderer,
            replace=replace,
        )

        self.registry.register(
            self.LINE_RENDERER_ID,
            LineRenderer,
            replace=replace,
        )

        self._loaded = True

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(
        self,
    ) -> None:
        """
        Validate that all canonical renderer registrations exist.

        Raises
        ------
        KeyError
            If a required renderer is missing.
        """

        self.registry.require_renderers(
            self.REQUIRED_RENDERER_IDS
        )

    # ========================================================
    # LOAD + VALIDATE
    # ========================================================

    def load_and_validate(
        self,
        *,
        replace: bool = False,
    ) -> None:
        """
        Load the concrete renderer set and validate it.
        """

        self.load(
            replace=replace
        )

        self.validate()

    # ========================================================
    # STATUS
    # ========================================================

    @property
    def loaded(self) -> bool:
        """
        Return True after load() has completed successfully.
        """

        return self._loaded

    # --------------------------------------------------------

    def is_loaded(self) -> bool:
        """
        Semantic alias for loaded.
        """

        return self._loaded

    # ========================================================
    # REGISTRY ACCESS
    # ========================================================

    def get_registry(
        self,
    ) -> RendererRegistry:
        """
        Return the registry receiving the registrations.
        """

        return self.registry

    # ========================================================
    # REQUIRED IDS
    # ========================================================

    @classmethod
    def required_renderer_ids(
        cls,
    ) -> tuple[str, ...]:
        """
        Return the canonical renderer IDs expected by V2.
        """

        return cls.REQUIRED_RENDERER_IDS

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of loader state.
        """

        return {
            "loaded": self._loaded,
            "required_renderer_ids": (
                self.REQUIRED_RENDERER_IDS
            ),
            "registered_renderer_ids": (
                self.registry.renderer_ids()
            ),
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
            "RendererLoader("
            f"loaded={self._loaded}, "
            f"renderers="
            f"{self.registry.renderer_ids()!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RendererLoader",
]
