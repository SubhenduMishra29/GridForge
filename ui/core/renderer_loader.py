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
RendererLoader is the explicit composition boundary for the
concrete GridForge renderer set.

Current renderer set:

    - BusRenderer
    - LineRenderer

The loader explicitly imports:

    - concrete renderer implementations;
    - authoritative Core model types.

It then registers the renderer implementation against its
corresponding model type.

No dynamic discovery is performed.

No filesystem scanning is performed.

No package introspection is performed.

No renderer instances are created here.

RendererLoader only performs deterministic registration.

Responsibilities
----------------
RendererLoader:

    - explicitly imports concrete renderers;
    - explicitly imports authoritative model types;
    - registers renderer/model-type associations;
    - validates the canonical renderer set;
    - provides deterministic bootstrap state.

RendererLoader does NOT:

    - instantiate renderers;
    - render graphics;
    - create QGraphicsItems;
    - own RenderSystem;
    - own QGraphicsScene;
    - manage renderer lifecycle;
    - modify Core state;
    - perform electrical calculations;
    - perform selection;
    - perform snapping;
    - perform navigation;
    - discover plugins dynamically.

Registration ownership
----------------------
RendererLoader
    = explicit composition / registration

RendererRegistry
    = registration storage / renderer resolution

RenderSystem
    = rendering lifecycle / graphical projection

Qt architecture
---------------
This module contains no Qt imports.
"""

from __future__ import annotations

from typing import Any

from ui.core.renderer_registry import RendererRegistry


class RendererLoader:
    """
    Explicit loader for the GridForge V2 renderer set.

    RendererLoader owns knowledge of the concrete renderer set,
    but does not own renderer instances.
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
        Initialize the renderer loader.

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
        Explicitly import and register the canonical renderers.

        Each renderer is registered against its authoritative
        Core model type.

        Registration therefore supports the canonical lookup:

            registry.get_renderer(type(element))

        Parameters
        ----------
        replace:
            Replace existing registrations when True.

        Raises
        ------
        ValueError
            If a renderer is already registered and replace=False.

        TypeError
            If the supplied registry or registration contract
            is invalid.
        """

        # ----------------------------------------------------
        # Concrete renderer imports.
        #
        # These imports are intentionally local. The registry
        # remains independent of concrete renderer modules.
        # ----------------------------------------------------

        from ui.renderers.bus_renderer import (
            BusRenderer,
        )

        from ui.renderers.line_renderer import (
            LineRenderer,
        )

        # ----------------------------------------------------
        # Authoritative Core model imports.
        #
        # These establish the renderer → model-type mapping
        # required by RenderSystem.
        # ----------------------------------------------------

        from core.model.bus import (
            Bus,
        )

        from core.model.line import (
            Line,
        )

        # ----------------------------------------------------
        # Explicit registration.
        # ----------------------------------------------------

        self.registry.register(
            self.BUS_RENDERER_ID,
            BusRenderer,
            model_type=Bus,
            replace=replace,
        )

        self.registry.register(
            self.LINE_RENDERER_ID,
            LineRenderer,
            model_type=Line,
            replace=replace,
        )

        # ----------------------------------------------------
        # Mark loaded only after every registration succeeds.
        # ----------------------------------------------------

        self._loaded = True

    # ========================================================
    # VALIDATION
    # ========================================================

    def validate(
        self,
    ) -> None:
        """
        Validate the complete canonical renderer set.

        Validation checks both:

            1. required renderer IDs exist;
            2. every canonical renderer has a model type.

        Raises
        ------
        KeyError
            If a required renderer is missing.

        TypeError
            If a required renderer has no model type.
        """

        registrations = self.registry.require_renderers(
            self.REQUIRED_RENDERER_IDS
        )

        for registration in registrations:
            if registration.model_type is None:
                raise TypeError(
                    "Renderer registration "
                    f"{registration.renderer_id!r} must "
                    "declare a model_type."
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
        Load and validate the complete renderer set.

        The loader is marked loaded by load() only after all
        registrations have succeeded.
        """

        self.load(
            replace=replace
        )

        self.validate()

    # ========================================================
    # STATUS
    # ========================================================

    @property
    def loaded(
        self,
    ) -> bool:
        """
        Return True after successful loading.
        """

        return self._loaded

    # --------------------------------------------------------

    def is_loaded(
        self,
    ) -> bool:
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
        Return the target RendererRegistry.
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
    # DIAGNOSTICS
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
                self.registry.renderer_ids
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
            f"renderers={self.registry.renderer_ids!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RendererLoader",
]
