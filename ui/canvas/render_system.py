# ============================================================

# File: ui/canvas/render_system.py

# GridForge V2 — Canvas Render System

# ============================================================

"""
Central rendering coordinator for the GridForge canvas.

## Responsibilities

RenderSystem is the canvas-side rendering coordinator.

It is responsible for:

```
- projecting authoritative model elements into the scene;
- resolving renderers through RendererRegistry;
- creating graphics items through the canonical renderer
  contract;
- coordinating grid rendering;
- removing stale graphical projections;
- synchronizing graphical selection;
- providing rendering diagnostics.
```

## Architecture

```
Controller
    │
    ▼
  Model
    │
    ▼
  Graph
    │
    ├───────────────┐
    ▼               ▼
  Bus              Line
    │               │
    └───────┬───────┘
            ▼
      RenderSystem
            │
            ▼
    RendererRegistry
            │
    ┌───────┴────────┐
    ▼                ▼
BusRenderer      LineRenderer
    │                │
    ▼                ▼
  BusItem         LineItem
    │                │
    └───────┬────────┘
            ▼
      QGraphicsScene
```

## Renderer contract

RendererRegistry is authoritative for renderer resolution.

The canonical model-type resolution contract is:

```
renderer = registry.get_for_type(type(element))
```

The canonical renderer interface is:

```
item = renderer.create_item(
    element,
    controller,
)
```

RenderSystem does not probe alternative registry APIs and does
not invoke arbitrary callable renderers.

RendererRegistry stores renderer implementations, normally
renderer classes, and never instantiates them.

Renderer instantiation and graphics-item creation therefore
remain the responsibility of the registered renderer
implementation and its owning canvas/rendering context.

## Responsibilities explicitly excluded

RenderSystem does NOT:

```
- modify Core model state;
- perform electrical calculations;
- implement tool behavior;
- perform snapping;
- own navigation;
- create concrete tools;
- decide application-level tool selection;
- derive authoritative application selection from
  QGraphicsScene.selectedItems();
- replace RendererRegistry;
- contain renderer-specific drawing logic.
```

## Selection

Controller/application selection remains authoritative.

RenderSystem may ask SelectionManager to synchronize the
graphical projection of that authoritative selection.

## Grid

GridSystem owns grid geometry and configuration.

RenderSystem owns the transient graphical projection of that
geometry.

GridSystem does not create QGraphicsItems.

## Qt architecture

All Qt dependencies pass through:

```
ui.core.qt
```

No direct PySide6/PyQt imports are permitted.
"""

from **future** import annotations

from typing import Any, Iterable, Optional

from ui.core.qt import (
QGraphicsLineItem,
QGraphicsScene,
QPen,
)

from ui.canvas.grid_system import GridSystem

class RenderSystem:
"""
Central canvas rendering coordinator.

```
RenderSystem is deliberately thin.

The authoritative model remains outside the canvas.
RendererRegistry remains responsible for renderer lookup.
Concrete renderers remain responsible for constructing
concrete graphics items.
"""

# ========================================================
# INITIALIZATION
# ========================================================

def __init__(
    self,
    scene: QGraphicsScene,
    controller: Any = None,
    renderer_registry: Any = None,
    grid_system: Optional[GridSystem] = None,
    selection_manager: Any = None,
) -> None:
    """
    Initialize RenderSystem.

    Parameters
    ----------
    scene:
        QGraphicsScene used by the canvas.

    controller:
        Application Controller.

    renderer_registry:
        RendererRegistry responsible for renderer lookup.

    grid_system:
        GridSystem providing grid geometry/configuration.

    selection_manager:
        Optional SelectionManager responsible for graphical
        selection synchronization.
    """

    if scene is None:
        raise ValueError(
            "scene must not be None."
        )

    if renderer_registry is None:
        raise ValueError(
            "renderer_registry must not be None."
        )

    self.scene = scene
    self.controller = controller
    self.renderer_registry = renderer_registry
    self.grid_system = grid_system
    self.selection_manager = selection_manager

    # ----------------------------------------------------
    # Permanent model projection.
    #
    # Python object identity is used only internally.
    # It is NOT an application/Core object identifier.
    # ----------------------------------------------------

    self._rendered_elements: dict[
        int,
        Any,
    ] = {}

    self._renderer_items: dict[
        int,
        tuple[Any, ...],
    ] = {}

    # ----------------------------------------------------
    # Transient grid projection.
    # ----------------------------------------------------

    self._grid_items: list[Any] = []

    # ----------------------------------------------------
    # Diagnostics.
    # ----------------------------------------------------

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
    Replace the active RendererRegistry.

    RendererRegistry is required for model rendering.
    """

    if renderer_registry is None:
        raise ValueError(
            "renderer_registry must not be None."
        )

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
    grid_system: Optional[GridSystem],
) -> None:
    """
    Attach or replace the GridSystem.
    """

    self.grid_system = grid_system

# --------------------------------------------------------

def get_grid_system(
    self,
) -> Optional[GridSystem]:
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
    Attach or replace the SelectionManager.
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
    Rebuild the complete graphical projection.

    When ``objects`` is omitted, authoritative renderable
    elements are obtained from Controller.model.graph.

    Existing graphical projections are removed before the
    new projection is created.

    The Core model is never modified.
    """

    self.clear()

    if objects is None:
        objects = self._get_controller_objects()

    object_list = tuple(
        objects
    )

    rendered_count = 0

    for element in object_list:
        items = self.render_object(
            element
        )

        if items:
            rendered_count += 1

    self.render_grid()

    self._render_count += 1
    self._last_rendered_count = rendered_count

    self.sync_selection()

# ========================================================
# OBJECT RENDERING
# ========================================================

def render_object(
    self,
    element: Any,
) -> tuple[Any, ...]:
    """
    Render one authoritative model element.

    Renderer resolution follows the canonical contract:

        registry.get_for_type(type(element))

    Renderer creation follows the canonical contract:

        renderer.create_item(
            element,
            controller,
        )

    The original Core element is passed to the renderer.

    Returns
    -------
    tuple
        Graphics items created by the renderer.

    Raises
    ------
    ValueError
        If element is None.

    LookupError
        If no renderer is registered for the element type.

    TypeError
        If the resolved renderer violates the renderer
        contract.

    RuntimeError
        If a returned graphics item already belongs to a
        different scene.
    """

    if element is None:
        raise ValueError(
            "element must not be None."
        )

    renderer = self.resolve_renderer(
        element
    )

    if renderer is None:
        raise LookupError(
            "No renderer registered for model type "
            f"{type(element).__name__}."
        )

    create_item = getattr(
        renderer,
        "create_item",
        None,
    )

    if not callable(
        create_item
    ):
        raise TypeError(
            "Resolved renderer must provide "
            "create_item(element, controller)."
        )

    rendered = create_item(
        element,
        self.controller,
    )

    items = self._normalize_items(
        rendered
    )

    for item in items:
        if item is None:
            continue

        item_scene = item.scene()

        if item_scene is None:
            self.scene.addItem(
                item
            )
        elif item_scene is not self.scene:
            raise RuntimeError(
                "Renderer returned a graphics item "
                "already attached to a different scene."
            )

    key = id(
        element
    )

    self._rendered_elements[
        key
    ] = element

    self._renderer_items[
        key
    ] = items

    return items

# ========================================================
# RENDERER RESOLUTION
# ========================================================

def resolve_renderer(
    self,
    element: Any,
) -> Any:
    """
    Resolve the renderer implementation for an authoritative
    model element.

    RendererRegistry owns all renderer resolution policy.

    Canonical contract:

        registry.get_for_type(type(element))

    The registry returns the registered renderer
    implementation. RenderSystem does not instantiate the
    implementation itself.
    """

    if element is None:
        raise ValueError(
            "element must not be None."
        )

    renderer = self.renderer_registry.get_for_type(
        type(element)
    )

    return renderer

# ========================================================
# GRID
# ========================================================

def render_grid(
    self,
    rect: Any = None,
) -> None:
    """
    Render the current grid geometry.

    GridSystem provides geometry.

    RenderSystem owns the transient graphical projection.

    The grid is rendered as ordinary QGraphicsLineItems;
    GridSystem itself remains completely independent of Qt
    rendering.
    """

    self.clear_grid()

    grid = self.grid_system

    if grid is None:
        return

    if not grid.is_visible():
        return

    target_rect = (
        self.scene.sceneRect()
        if rect is None
        else rect
    )

    # ----------------------------------------------------
    # Minor grid.
    # ----------------------------------------------------

    if grid.is_minor_visible():
        minor_lines = grid.get_minor_lines(
            target_rect
        )

        minor_pen = QPen()

        for (
            x1,
            y1,
            x2,
            y2,
        ) in minor_lines:

            item = QGraphicsLineItem(
                x1,
                y1,
                x2,
                y2,
            )

            item.setPen(
                minor_pen
            )

            self.scene.addItem(
                item
            )

            self._grid_items.append(
                item
            )

    # ----------------------------------------------------
    # Major grid.
    # ----------------------------------------------------

    if grid.is_major_visible():
        major_lines = grid.get_major_lines(
            target_rect
        )

        major_pen = QPen()

        for (
            x1,
            y1,
            x2,
            y2,
        ) in major_lines:

            item = QGraphicsLineItem(
                x1,
                y1,
                x2,
                y2,
            )

            item.setPen(
                major_pen
            )

            self.scene.addItem(
                item
            )

            self._grid_items.append(
                item
            )

# --------------------------------------------------------

def refresh_grid(
    self,
    rect: Any = None,
) -> None:
    """
    Refresh only the grid projection.
    """

    self.render_grid(
        rect
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
    """

    self.render(
        objects
    )

# ========================================================
# OBJECT REMOVAL
# ========================================================

def remove_object(
    self,
    element: Any,
) -> bool:
    """
    Remove the graphical projection of one model element.

    The model element itself is never modified.

    Parameters
    ----------
    element:
        The original authoritative model element.

    Returns
    -------
    bool
        True when one or more graphics items were removed.
    """

    if element is None:
        return False

    key = id(
        element
    )

    items = self._renderer_items.pop(
        key,
        (),
    )

    self._rendered_elements.pop(
        key,
        None,
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

    return removed

# ========================================================
# CLEAR
# ========================================================

def clear(
    self,
) -> None:
    """
    Clear all canvas projections managed by RenderSystem.

    Core/application state remains untouched.
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
    self._rendered_elements.clear()

    self.clear_grid()

# --------------------------------------------------------

def clear_grid(
    self,
) -> None:
    """
    Remove all transient grid graphics.
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
    application selection.

    RenderSystem never derives application selection from
    QGraphicsScene.selectedItems().
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

def get_rendered_elements(
    self,
) -> tuple[Any, ...]:
    """
    Return the model elements currently projected.
    """

    return tuple(
        self._rendered_elements.values()
    )

# --------------------------------------------------------

def get_rendered_ids(
    self,
) -> tuple[int, ...]:
    """
    Return internal projection keys.

    These are Python object identities used only for
    RenderSystem bookkeeping.

    They are not application or Core object IDs.
    """

    return tuple(
        self._rendered_elements.keys()
    )

# --------------------------------------------------------

def get_items_for_element(
    self,
    element: Any,
) -> tuple[Any, ...]:
    """
    Return graphics items associated with a model element.
    """

    if element is None:
        return ()

    return self._renderer_items.get(
        id(element),
        (),
    )

# --------------------------------------------------------

def get_items_for_id(
    self,
    object_id: Any,
) -> tuple[Any, ...]:
    """
    Return graphics items using the internal projection key.

    RenderSystem does not interpret this value as an
    application/Core object ID.
    """

    return self._renderer_items.get(
        object_id,
        (),
    )

# --------------------------------------------------------

def is_rendered(
    self,
    element: Any,
) -> bool:
    """
    Return True when the supplied model element is currently
    projected.
    """

    if element is None:
        return False

    return id(
        element
    ) in self._rendered_elements

# ========================================================
# CONTROLLER / MODEL ACCESS
# ========================================================

def _get_controller_objects(
    self,
) -> tuple[Any, ...]:
    """
    Obtain authoritative renderable elements from Controller.

    Finalized GridForge model boundary:

        controller.model
            ↓
        model.graph
            ↓
        graph.buses
        graph.lines

    RenderSystem does not search arbitrary Controller
    attributes or invent alternate model-access contracts.
    """

    if self.controller is None:
        return ()

    model = getattr(
        self.controller,
        "model",
        None,
    )

    if model is None:
        return ()

    graph = getattr(
        model,
        "graph",
        None,
    )

    if graph is None:
        return ()

    objects: list[Any] = []

    buses = getattr(
        graph,
        "buses",
        None,
    )

    if buses is not None:
        objects.extend(
            self._collection_values(
                buses
            )
        )

    lines = getattr(
        graph,
        "lines",
        None,
    )

    if lines is not None:
        objects.extend(
            self._collection_values(
                lines
            )
        )

    return tuple(
        objects
    )

# --------------------------------------------------------

@staticmethod
def _collection_values(
    collection: Any,
) -> tuple[Any, ...]:
    """
    Normalize a model collection to its element values.

    Graph collections are normally dictionaries or
    dictionary-like containers.
    """

    values = getattr(
        collection,
        "values",
        None,
    )

    if callable(
        values
    ):
        return tuple(
            values()
        )

    return tuple(
        collection
    )

# ========================================================
# ITEM NORMALIZATION
# ========================================================

@staticmethod
def _normalize_items(
    rendered: Any,
) -> tuple[Any, ...]:
    """
    Normalize canonical renderer output.

    Renderer contract permits:

        QGraphicsItem
        iterable of QGraphicsItems
        None

    No arbitrary callable or duck-typed renderer contract is
    accepted here.
    """

    if rendered is None:
        return ()

    # ----------------------------------------------------
    # Single QGraphicsItem.
    #
    # QGraphicsItem provides scene() and setSelected().
    # ----------------------------------------------------

    if (
        callable(
            getattr(
                rendered,
                "scene",
                None,
            )
        )
        and callable(
            getattr(
                rendered,
                "setSelected",
                None,
            )
        )
    ):
        return (
            rendered,
        )

    try:
        items = tuple(
            rendered
        )
    except TypeError as exc:
        raise TypeError(
            "Renderer.create_item() must return "
            "a graphics item, an iterable of graphics "
            "items, or None."
        ) from exc

    for item in items:
        if item is None:
            continue

        if not (
            callable(
                getattr(
                    item,
                    "scene",
                    None,
                )
            )
            and callable(
                getattr(
                    item,
                    "setSelected",
                    None,
                )
            )
        ):
            raise TypeError(
                "Renderer.create_item() returned an "
                "invalid graphics item."
            )

    return items

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
            self._rendered_elements
        ),
        "rendered_ids": tuple(
            self._rendered_elements.keys()
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

    Controller and Core state remain untouched.
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
        f"{len(self._rendered_elements)}, "
        f"grid_items="
        f"{len(self._grid_items)}, "
        f"renders="
        f"{self._render_count}"
        ")"
    )
```

# ============================================================

# PUBLIC API

# ============================================================

**all** = [
"RenderSystem",
]
