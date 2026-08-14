# ============================================================
# File: ui/canvas/render_system.py
# GridForge V2 — Canvas Render System
# ============================================================
"""
Central rendering coordinator for the GridForge canvas.

Responsibilities
----------------
RenderSystem is the canvas-side rendering coordinator.

It is responsible for:

    - coordinating permanent model graphics;
    - coordinating grid rendering;
    - resolving renderers through RendererRegistry;
    - maintaining the graphics projection of application state;
    - refreshing the canvas when the authoritative state changes;
    - removing stale graphics;
    - providing render diagnostics.

Architecture
------------

    Controller / Core state
             │
             ▼
       RenderSystem
             │
       ┌─────┴─────┐
       ▼           ▼
 GridSystem   RendererRegistry
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
      BusRenderer LineRenderer ...
          │        │
          ▼        ▼
      QGraphicsItems

RenderSystem does NOT:

    - modify Core model state;
    - implement electrical calculations;
    - implement tool behavior;
    - perform snapping;
    - own persistent selection;
    - own navigation;
    - create concrete tools;
    - decide application-level tool selection.

Selection
---------
Controller.selected_ids remains authoritative.

RenderSystem may synchronize the graphical selection
projection through SelectionManager, but it must never derive
application selection from QGraphicsScene.selectedItems().

Renderer ownership
------------------
RendererRegistry owns renderer registration and resolution.

RenderSystem coordinates renderers but does not replace the
registry.

Qt Architecture
---------------
All Qt dependencies must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.qt import QGraphicsScene


class RenderSystem:
    """
    Central canvas rendering coordinator.

    The implementation deliberately keeps rendering policy
    separate from individual renderers and from the Core model.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        scene: QGraphicsScene,
        controller: Any = None,
        renderer_registry: Any = None,
        grid_system: Any = None,
        selection_manager: Any = None,
    ) -> None:
        """
        Initialize RenderSystem.

        Parameters
        ----------
        scene:
            QGraphicsScene used by the canvas.

        controller:
            Optional application controller.

        renderer_registry:
            RendererRegistry responsible for renderer lookup.

        grid_system:
            GridSystem providing grid geometry/configuration.

        selection_manager:
            Optional SelectionManager used to reconcile graphical
            selection with authoritative application selection.
        """

        if scene is None:
            raise ValueError(
                "scene must not be None."
            )

        self.scene = scene
        self.controller = controller
        self.renderer_registry = renderer_registry
        self.grid_system = grid_system
        self.selection_manager = selection_manager

        self._rendered_ids: set[Any] = set()
        self._renderer_items: dict[Any, tuple[Any, ...]] = {}

        self._grid_items: list[Any] = []

        self._render_count = 0
        self._last_rendered_count = 0

    # ========================================================
    # SCENE ACCESS
    # ========================================================

    def get_scene(
        self,
    ) -> QGraphicsScene:
        """
        Return the managed graphics scene.
        """

        return self.scene

    # ========================================================
    # REGISTRY / SERVICES
    # ========================================================

    def set_renderer_registry(
        self,
        renderer_registry: Any,
    ) -> None:
        """
        Attach or replace the RendererRegistry.
        """

        self.renderer_registry = renderer_registry

    # --------------------------------------------------------

    def get_renderer_registry(
        self,
    ) -> Any:
        """
        Return the active RendererRegistry.
        """

        return self.renderer_registry

    # --------------------------------------------------------

    def set_grid_system(
        self,
        grid_system: Any,
    ) -> None:
        """
        Attach or replace the GridSystem.
        """

        self.grid_system = grid_system

    # --------------------------------------------------------

    def get_grid_system(
        self,
    ) -> Any:
        """
        Return the active GridSystem.
        """

        return self.grid_system

    # --------------------------------------------------------

    def set_selection_manager(
        self,
        selection_manager: Any,
    ) -> None:
        """
        Attach or replace SelectionManager.
        """

        self.selection_manager = selection_manager

    # --------------------------------------------------------

    def get_selection_manager(
        self,
    ) -> Any:
        """
        Return the active SelectionManager.
        """

        return self.selection_manager

    # ========================================================
    # FULL RENDER
    # ========================================================

    def render(
        self,
        objects: Optional[Iterable[Any]] = None,
    ) -> None:
        """
        Render the supplied application objects.

        If objects is omitted, RenderSystem attempts to obtain
        renderable objects from the Controller.

        Existing permanent graphics are removed before the new
        projection is created.

        Grid rendering is refreshed independently.
        """

        self.clear()

        if objects is None:
            objects = self._get_controller_objects()

        object_list = tuple(
            objects
        )

        for obj in object_list:
            self.render_object(
                obj
            )

        self.render_grid()

        self._render_count += 1
        self._last_rendered_count = len(
            object_list
        )

        self.sync_selection()

    # ========================================================
    # OBJECT RENDERING
    # ========================================================

    def render_object(
        self,
        obj: Any,
    ) -> tuple[Any, ...]:
        """
        Render one application object through RendererRegistry.

        Returns the graphics items produced by the renderer.

        Renderers may return:

            - one QGraphicsItem;
            - an iterable of QGraphicsItems;
            - None.

        RenderSystem does not construct concrete graphics items
        itself.
        """

        if obj is None:
            raise ValueError(
                "obj must not be None."
            )

        renderer = self._resolve_renderer(
            obj
        )

        if renderer is None:
            return ()

        rendered = self._invoke_renderer(
            renderer,
            obj,
        )

        items = self._normalize_items(
            rendered
        )

        for item in items:
            if item is None:
                continue

            if item.scene() is None:
                self.scene.addItem(
                    item
                )

        object_id = self._get_object_id(
            obj
        )

        if object_id is not None:
            self._rendered_ids.add(
                object_id
            )

            self._renderer_items[
                object_id
            ] = items

        return items

    # ========================================================
    # RENDERER RESOLUTION
    # ========================================================

    def _resolve_renderer(
        self,
        obj: Any,
    ) -> Any:
        """
        Resolve a renderer for an application object.

        RendererRegistry remains responsible for renderer
        registration and lookup.
        """

        registry = self.renderer_registry

        if registry is None:
            return None

        object_type = type(
            obj
        )

        # Preferred registry contract.
        for method_name in (
            "get_renderer_for",
            "get_renderer",
            "resolve",
        ):
            method = getattr(
                registry,
                method_name,
                None,
            )

            if not callable(
                method
            ):
                continue

            for argument in (
                obj,
                object_type,
            ):
                try:
                    renderer = method(
                        argument
                    )
                except (KeyError, LookupError):
                    continue

                if renderer is not None:
                    return renderer

        return None

    # --------------------------------------------------------

    @staticmethod
    def _invoke_renderer(
        renderer: Any,
        obj: Any,
    ) -> Any:
        """
        Invoke a renderer using the supported renderer contract.

        The preferred contract is:

            renderer.render(obj)

        A callable renderer is also accepted.
        """

        render_method = getattr(
            renderer,
            "render",
            None,
        )

        if callable(
            render_method
        ):
            return render_method(
                obj
            )

        if callable(
            renderer
        ):
            return renderer(
                obj
            )

        raise TypeError(
            "Resolved renderer must provide render() "
            "or be callable."
        )

    # ========================================================
    # GRID
    # ========================================================

    def render_grid(
        self,
        rect: Any = None,
    ) -> None:
        """
        Refresh grid graphics.

        GridSystem provides geometry/configuration.
        RenderSystem owns the transient grid projection.

        If the configured GridSystem does not provide a
        render-geometry API, grid rendering is skipped.
        """

        self.clear_grid()

        grid = self.grid_system

        if grid is None:
            return

        is_visible = getattr(
            grid,
            "is_visible",
            None,
        )

        if callable(
            is_visible
        ) and not is_visible():
            return

        target_rect = (
            rect
            if rect is not None
            else self.scene.sceneRect()
        )

        # Prefer a dedicated grid renderer if one is registered.
        registry = self.renderer_registry

        grid_renderer = None

        if registry is not None:
            for method_name in (
                "get_grid_renderer",
                "resolve_grid_renderer",
            ):
                method = getattr(
                    registry,
                    method_name,
                    None,
                )

                if callable(
                    method
                ):
                    grid_renderer = method()
                    if grid_renderer is not None:
                        break

        if grid_renderer is not None:
            rendered = self._invoke_grid_renderer(
                grid_renderer,
                grid,
                target_rect,
            )

            self._grid_items.extend(
                self._normalize_items(
                    rendered
                )
            )

            for item in self._grid_items:
                if item.scene() is None:
                    self.scene.addItem(
                        item
                    )

            return

        # ----------------------------------------------------
        # No dedicated renderer:
        #
        # RenderSystem intentionally does not manufacture
        # permanent grid graphics. Grid rendering belongs to the
        # rendering layer and may be implemented by a registered
        # grid renderer later.
        # ----------------------------------------------------

    # --------------------------------------------------------

    @staticmethod
    def _invoke_grid_renderer(
        renderer: Any,
        grid: Any,
        rect: Any,
    ) -> Any:
        """
        Invoke a registered grid renderer.
        """

        render_grid = getattr(
            renderer,
            "render_grid",
            None,
        )

        if callable(
            render_grid
        ):
            return render_grid(
                grid,
                rect,
            )

        render = getattr(
            renderer,
            "render",
            None,
        )

        if callable(
            render
        ):
            return render(
                grid,
                rect,
            )

        if callable(
            renderer
        ):
            return renderer(
                grid,
                rect,
            )

        raise TypeError(
            "Grid renderer must provide render_grid(), "
            "render(), or be callable."
        )

    # ========================================================
    # REFRESH
    # ========================================================

    def refresh(
        self,
        objects: Optional[Iterable[Any]] = None,
    ) -> None:
        """
        Refresh the complete canvas projection.

        This is the public semantic alias for render().
        """

        self.render(
            objects
        )

    # ========================================================
    # OBJECT REMOVAL
    # ========================================================

    def remove_object(
        self,
        object_id: Any,
    ) -> bool:
        """
        Remove the graphical projection for one object ID.

        The application/Core object itself is never modified.
        """

        if object_id is None:
            return False

        items = self._renderer_items.pop(
            object_id,
            (),
        )

        removed = False

        for item in items:
            if item is None:
                continue

            if item.scene() is self.scene:
                self.scene.removeItem(
                    item
                )
                removed = True

        self._rendered_ids.discard(
            object_id
        )

        return removed

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Clear all permanent graphical projections managed by
        RenderSystem.

        The Core/application state is untouched.
        """

        for items in tuple(
            self._renderer_items.values()
        ):
            for item in items:
                if item is None:
                    continue

                if item.scene() is self.scene:
                    self.scene.removeItem(
                        item
                    )

        self._renderer_items.clear()
        self._rendered_ids.clear()

        self.clear_grid()

    # --------------------------------------------------------

    def clear_grid(
        self,
    ) -> None:
        """
        Clear grid graphics owned by RenderSystem.
        """

        for item in tuple(
            self._grid_items
        ):
            if item is None:
                continue

            if item.scene() is self.scene:
                self.scene.removeItem(
                    item
                )

        self._grid_items.clear()

    # ========================================================
    # SELECTION SYNCHRONIZATION
    # ========================================================

    def sync_selection(
        self,
    ) -> None:
        """
        Synchronize graphical selection from the authoritative
        Controller state through SelectionManager.
        """

        manager = self.selection_manager

        if manager is None:
            return

        reconcile = getattr(
            manager,
            "reconcile",
            None,
        )

        if callable(
            reconcile
        ):
            reconcile(
                scene=self.scene
            )
            return

        sync_graphics = getattr(
            manager,
            "sync_graphics",
            None,
        )

        if callable(
            sync_graphics
        ):
            sync_graphics(
                scene=self.scene
            )

    # ========================================================
    # RENDERED OBJECT ACCESS
    # ========================================================

    def get_rendered_ids(
        self,
    ) -> tuple[Any, ...]:
        """
        Return IDs currently projected into the scene.
        """

        return tuple(
            self._rendered_ids
        )

    # --------------------------------------------------------

    def get_items_for_id(
        self,
        object_id: Any,
    ) -> tuple[Any, ...]:
        """
        Return graphics items rendered for an object ID.
        """

        return self._renderer_items.get(
            object_id,
            (),
        )

    # --------------------------------------------------------

    def is_rendered(
        self,
        object_id: Any,
    ) -> bool:
        """
        Return True when an object ID has a graphical
        projection.
        """

        return object_id in self._rendered_ids

    # ========================================================
    # CONTROLLER OBJECT ACCESS
    # ========================================================

    def _get_controller_objects(
        self,
    ) -> tuple[Any, ...]:
        """
        Obtain renderable application objects from Controller.

        RenderSystem intentionally accepts several controller
        read contracts so the canvas remains decoupled from a
        specific model-container implementation.
        """

        if self.controller is None:
            return ()

        for method_name in (
            "get_renderable_objects",
            "get_objects",
            "get_model_objects",
        ):
            method = getattr(
                self.controller,
                method_name,
                None,
            )

            if callable(
                method
            ):
                result = method()

                if result is None:
                    return ()

                return tuple(
                    result
                )

        for attribute_name in (
            "objects",
            "model_objects",
        ):
            value = getattr(
                self.controller,
                attribute_name,
                None,
            )

            if value is not None:
                return tuple(
                    value
                )

        return ()

    # ========================================================
    # OBJECT ID
    # ========================================================

    @staticmethod
    def _get_object_id(
        obj: Any,
    ) -> Any:
        """
        Obtain an authoritative object ID from a model object.
        """

        for attribute_name in (
            "object_id",
            "id",
            "uuid",
        ):
            value = getattr(
                obj,
                attribute_name,
                None,
            )

            if value is not None:
                return value

        return None

    # ========================================================
    # ITEM NORMALIZATION
    # ========================================================

    @staticmethod
    def _normalize_items(
        rendered: Any,
    ) -> tuple[Any, ...]:
        """
        Normalize renderer output to a tuple of graphics items.
        """

        if rendered is None:
            return ()

        # QGraphicsItem-like single object.
        if hasattr(
            rendered,
            "setSelected",
        ) or hasattr(
            rendered,
            "scene",
        ):
            return (
                rendered,
            )

        try:
            return tuple(
                rendered
            )
        except TypeError as exc:
            raise TypeError(
                "Renderer output must be a graphics item "
                "or an iterable of graphics items."
            ) from exc

    # ========================================================
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic rendering state.
        """

        return {
            "scene": self.scene is not None,
            "rendered_count": len(
                self._rendered_ids
            ),
            "rendered_ids": tuple(
                self._rendered_ids
            ),
            "renderer_count": len(
                self._renderer_items
            ),
            "grid_item_count": len(
                self._grid_items
            ),
            "render_count": self._render_count,
            "last_rendered_count": (
                self._last_rendered_count
            ),
            "has_renderer_registry": (
                self.renderer_registry is not None
            ),
            "has_grid_system": (
                self.grid_system is not None
            ),
            "has_selection_manager": (
                self.selection_manager is not None
            ),
        }

    # ========================================================
    # CLEANUP
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Release the current graphical projection.

        Core/application state remains untouched.
        """

        self.clear()

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
            f"rendered="
            f"{len(self._rendered_ids)}, "
            f"grid_items="
            f"{len(self._grid_items)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "RenderSystem",
]
