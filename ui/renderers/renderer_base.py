# ============================================================
# File: ui/renderers/renderer_base.py
# GridForge V2 — Renderer Base
# ============================================================
"""
Base contract for GridForge UI renderers.

Architecture
------------

    Core / Application Object
              │
              ▼
        Concrete Renderer
              │
              ▼
       Graphics Projection
              │
              ▼
          GridScene

RendererBase defines the common renderer boundary.

It does NOT:

    - own Core/application state;
    - mutate Core model objects;
    - implement electrical calculations;
    - implement tools;
    - perform snapping;
    - perform navigation;
    - own application selection;
    - decide topology;
    - create the scene;
    - provide concrete graphical presentation.

Concrete renderers such as:

    BusRenderer
    LineRenderer

implement the actual projection behavior.

Qt Architecture
---------------
This base class deliberately contains no direct Qt dependency.

Concrete renderers must import Qt classes only through:

    ui.core.qt

Design Rule
-----------
The renderer layer is a projection layer.

Authoritative direction:

    Core/Application State
            ↓
        Renderer
            ↓
      Graphics Item

Never:

    Graphics Item
            ↓
        Renderer
            ↓
          Core

RendererBase therefore contains no API for modifying the
authoritative model.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable, Optional


class RendererBase(ABC):
    """
    Abstract base contract for GridForge renderers.

    Concrete renderers are responsible for projecting one
    application/Core object type into graphical items.

    The base class intentionally contains only renderer-level
    lifecycle and lookup contracts.

    It does not impose a specific QGraphicsItem implementation.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        scene: Any,
    ) -> None:
        """
        Initialize the renderer.

        Parameters
        ----------
        scene:
            Target graphics scene.

        Notes
        -----
        The renderer does not take ownership of the scene.
        """

        if scene is None:
            raise ValueError(
                "scene must not be None."
            )

        self._validate_scene(
            scene
        )

        self.scene = scene

    # ========================================================
    # PRIMARY RENDER CONTRACT
    # ========================================================

    @abstractmethod
    def render(
        self,
        model: Any,
    ) -> Any:
        """
        Create or update the graphical projection of model.

        Concrete implementations must:

            1. identify the authoritative object;
            2. locate an existing graphical projection when
               appropriate;
            3. create the projection when absent;
            4. synchronize the projection from authoritative
               state;
            5. return the resulting graphics item.

        The Core/application model must not be mutated.
        """

        raise NotImplementedError

    # ========================================================
    # UPDATE CONTRACT
    # ========================================================

    @abstractmethod
    def update(
        self,
        item: Any,
        model: Any,
    ) -> Any:
        """
        Synchronize an existing graphical projection from model.

        Parameters
        ----------
        item:
            Existing graphical projection.

        model:
            Authoritative application/Core object.

        Returns
        -------
        object
            Updated graphical projection.
        """

        raise NotImplementedError

    # ========================================================
    # REMOVE CONTRACT
    # ========================================================

    @abstractmethod
    def remove(
        self,
        object_id: Any,
    ) -> bool:
        """
        Remove the graphical projection identified by object_id.

        This removes only the graphical projection.

        It must never delete or mutate the corresponding
        Core/application object.
        """

        raise NotImplementedError

    # ========================================================
    # LOOKUP CONTRACT
    # ========================================================

    @abstractmethod
    def get_item(
        self,
        object_id: Any,
    ) -> Optional[Any]:
        """
        Return the graphical projection for object_id.

        Returns
        -------
        object | None
            Matching graphics item, if present.
        """

        raise NotImplementedError

    # ========================================================
    # BULK RENDERING
    # ========================================================

    def render_all(
        self,
        models: Iterable[Any],
    ) -> tuple[Any, ...]:
        """
        Render a collection of authoritative objects.

        Concrete renderers may override this when bulk rendering
        requires specialized behavior.

        Existing projections are updated through render().
        """

        if models is None:
            raise ValueError(
                "models must not be None."
            )

        result: list[Any] = []

        for model in models:
            result.append(
                self.render(
                    model
                )
            )

        return tuple(
            result
        )

    # ========================================================
    # SCENE MANAGEMENT
    # ========================================================

    def set_scene(
        self,
        scene: Any,
    ) -> None:
        """
        Attach a different graphics scene.

        Existing graphical items are not automatically migrated.

        The renderer does not take ownership of the scene.
        """

        if scene is None:
            raise ValueError(
                "scene must not be None."
            )

        self._validate_scene(
            scene
        )

        self.scene = scene

    # --------------------------------------------------------

    def get_scene(
        self,
    ) -> Any:
        """
        Return the currently attached graphics scene.
        """

        return self.scene

    # ========================================================
    # SYNCHRONIZATION
    # ========================================================

    def synchronize(
        self,
        models: Iterable[Any],
    ) -> tuple[Any, ...]:
        """
        Synchronize graphical projections for models.

        This is intentionally an additive/update operation.

        It does not remove graphical projections that are absent
        from models.

        Explicit removal is required so a partial model update
        cannot accidentally delete unrelated graphics.
        """

        return self.render_all(
            models
        )

    # ========================================================
    # PROJECTION EXISTENCE
    # ========================================================

    def has_item(
        self,
        object_id: Any,
    ) -> bool:
        """
        Return True when a graphical projection exists for
        object_id.
        """

        return (
            self.get_item(
                object_id
            )
            is not None
        )

    # ========================================================
    # SCENE VALIDATION
    # ========================================================

    @staticmethod
    def _validate_scene(
        scene: Any,
    ) -> None:
        """
        Validate the minimum scene contract required by a
        renderer.

        The base class deliberately checks only the operations
        required by the renderer lifecycle.

        No concrete Qt type is required here.
        """

        required_methods = (
            "addItem",
            "removeItem",
            "items",
        )

        for method_name in required_methods:
            if not callable(
                getattr(
                    scene,
                    method_name,
                    None,
                )
            ):
                raise TypeError(
                    "scene must provide "
                    f"{method_name}()."
                )

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a generic renderer diagnostic snapshot.

        Concrete renderers may extend this state.
        """

        return {
            "renderer": type(self).__name__,
            "scene_attached": (
                self.scene is not None
            ),
        }

    # ========================================================
    # CLEANUP
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Release renderer-owned transient resources.

        The base renderer does not own the scene or Core model,
        so the default implementation performs no operation.

        Concrete renderers may override this when they maintain
        renderer-specific transient resources.
        """

        return None

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
            f"{type(self).__name__}("
            f"scene_attached="
            f"{self.scene is not None}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RendererBase",
]
