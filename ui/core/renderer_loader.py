```python
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
concrete GridForge canvas renderer set.

It intentionally separates:

    RendererLoader
        explicit knowledge of concrete renderers and their
        authoritative Core model types;

    RendererRegistry
        stores renderer registrations and resolves them;

    RenderSystem
        consumes the registry and owns rendering coordination.

The loader performs no rendering and never creates renderer
instances.

Current Renderer Set
--------------------
GridForge V2 currently defines exactly:

    - BusRenderer
    - LineRenderer

Their authoritative model bindings are:

    BusRenderer  -> core.model.bus.Bus
    LineRenderer -> core.model.line.Line

No renderer discovery is performed.

No filesystem scanning is performed.

No package introspection is performed.

No decorator-based self-registration is performed.

Registration Contract
---------------------
The loader explicitly performs:

    registry.register(
        "bus",
        BusRenderer,
        model_type=Bus,
    )

    registry.register(
        "line",
        LineRenderer,
        model_type=Line,
    )

This allows RenderSystem to resolve renderers through the
authoritative model type:

    registry.get_for_type(type(element))

or equivalently:

    registry.get_for_object(element)

Responsibilities
----------------
RendererLoader:

    - explicitly imports concrete renderer classes;
    - explicitly imports their authoritative Core model types;
    - registers renderer implementations;
    - binds renderers to Core model types;
    - validates the canonical renderer set;
    - provides deterministic loading.

RendererLoader does NOT:

    - instantiate renderers;
    - create QGraphicsItems;
    - render anything;
    - own QGraphicsScene;
    - manage renderer lifecycle;
    - perform renderer selection;
    - subscribe to Controller events;
    - modify Core state;
    - perform electrical calculations;
    - perform selection;
    - perform snapping;
    - perform navigation.

Registration Ownership
----------------------
The ownership chain is:

    RendererLoader
        = explicit composition knowledge

    RendererRegistry
        = registration and renderer resolution

    RenderSystem
        = rendering coordination and graphical projection

The loader does not retain renderer instances.

Qt Architecture
---------------
This module does not import Qt.

Concrete renderers must obey the GridForge Qt rule:

    all Qt imports through ui.core.qt
"""

from __future__ import annotations

from typing import Any

from ui.core.renderer_registry import RendererRegistry


class RendererLoader:
    """
    Explicit loader for the GridForge V2 renderer set.

    RendererLoader contains the application's concrete renderer
    composition knowledge.

    It performs registration only. It never instantiates a
    renderer and never creates graphics items.
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
            RendererRegistry receiving the explicit
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
        Explicitly import and register all canonical renderers.

        Parameters
        ----------
        replace:
            Replace existing registrations when True.

        Notes
        -----
        Concrete renderer and model imports are intentionally
        local to this composition operation.

        This prevents RendererRegistry from importing concrete
        renderers and keeps renderer composition explicit.
        """

        from core.model.bus import Bus
        from core.model.line import Line

        from ui.renderers.bus_renderer import (
            BusRenderer,
        )
        from ui.renderers.line_renderer import (
            LineRenderer,
        )

        # ----------------------------------------------------
        # Bus renderer.
        # ----------------------------------------------------

        self.registry.register(
            self.BUS_RENDERER_ID,
            BusRenderer,
            model_type=Bus,
            replace=replace,
        )

        # ----------------------------------------------------
        # Line renderer.
        # ----------------------------------------------------

        self.registry.register(
            self.LINE_RENDERER_ID,
            LineRenderer,
            model_type=Line,
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
        Validate the canonical renderer registrations.

        Validation checks:

            - required renderer ID exists;
            - renderer implementation is registered;
            - renderer is bound to the correct Core model type.

        Raises
        ------
        KeyError
            If a required renderer is missing.

        TypeError
            If a renderer is bound to the wrong model type.
        """

        from core.model.bus import Bus
        from core.model.line import Line

        expected = {
            self.BUS_RENDERER_ID: Bus,
            self.LINE_RENDERER_ID: Line,
        }

        for (
            renderer_id,
            expected_model_type,
        ) in expected.items():

            registration = self.registry.get(
                renderer_id
            )

            if registration is None:
                raise KeyError(
                    "Required renderer is not registered: "
                    f"{renderer_id!r}"
                )

            if (
                registration.model_type
                is not expected_model_type
            ):
                raise TypeError(
                    "Renderer "
                    f"{renderer_id!r} is bound to "
                    f"{registration.model_type!r}, "
                    "expected "
                    f"{expected_model_type!r}."
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
        Load the canonical renderer set and validate it.
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
        Return True after a successful load operation.
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
            f"renderers="
            f"{self.registry.renderer_ids!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RendererLoader",
]
```
