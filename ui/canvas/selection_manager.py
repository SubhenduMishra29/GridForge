# ============================================================
# File: ui/canvas/selection_manager.py
# GridForge V2 — Canvas Selection Manager
# ============================================================
"""
Central selection adapter for the GridForge Canvas.

Selection architecture
-----------------------

    SelectTool
         │
         ▼
    SelectionManager
         │
         ▼
    Controller
         │
         ▼
    authoritative application selection
         │
         ▼
    SelectionManager
         │
         ▼
    QGraphicsItems


Ownership
---------

Persistent application selection belongs to Controller.

SelectionManager does NOT maintain a second persistent
selection collection.

QGraphicsItem selection state is only a visual projection of
the authoritative Controller selection.

Therefore:

    Controller.selected_ids
            │
            ▼
    SelectionManager
            │
            ▼
    QGraphicsItem.setSelected(...)


Responsibilities
----------------
SelectionManager:

    - provides the canvas selection API;
    - delegates selection mutation to Controller;
    - reads Controller.selected_ids;
    - resolves graphics items by object ID;
    - synchronizes graphical selection state;
    - provides selection queries;
    - provides selection diagnostics.

SelectionManager does NOT:

    - own persistent selection state;
    - modify Core model objects directly;
    - create model objects;
    - create graphics items;
    - render graphics;
    - implement SelectTool behavior;
    - perform snapping;
    - perform navigation;
    - perform electrical calculations;
    - own tool lifecycle;
    - decide application-level tool selection.

Graphics items
--------------

Selectable canvas graphics items must expose:

    object_id

and normally support:

    setSelected(bool)
    isSelected()

The graphics item remains responsible for its visual
selection appearance.

Controller contract
-------------------

Canonical selection mutation:

    controller.select(
        object_id,
        multi=bool,
    )

Authoritative selection:

    controller.selected_ids

Canonical clear operation:

    controller.clear_selection()

SelectionManager never assigns directly to selected_ids.

Scene selection
---------------

QGraphicsScene.selectedItems() is NEVER authoritative.

The authoritative direction is:

    Controller.selected_ids
            ↓
    SelectionManager
            ↓
    QGraphicsItem.setSelected()

Qt architecture
---------------

All Qt dependencies must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.qt import QGraphicsScene


class SelectionManager:
    """
    Canvas-level adapter between application selection and
    graphical selection state.

    The Controller owns persistent selection.

    SelectionManager owns only the translation between that
    state and the canvas graphics projection.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
        scene: Optional[QGraphicsScene] = None,
    ) -> None:
        """
        Initialize the SelectionManager.

        Parameters
        ----------
        controller:
            GridForge application/UI Controller.

        scene:
            Optional canvas scene containing permanent
            graphics items.

        The manager does not take ownership of the scene.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        if not callable(
            getattr(
                controller,
                "select",
                None,
            )
        ):
            raise TypeError(
                "controller must provide select()."
            )

        if not hasattr(
            controller,
            "selected_ids",
        ):
            raise TypeError(
                "controller must provide selected_ids."
            )

        if not callable(
            getattr(
                controller,
                "clear_selection",
                None,
            )
        ):
            raise TypeError(
                "controller must provide "
                "clear_selection()."
            )

        self.controller = controller
        self.scene = scene

    # ========================================================
    # AUTHORITATIVE SELECTION
    # ========================================================

    def get_selected_ids(
        self,
    ) -> tuple[Any, ...]:
        """
        Return a snapshot of Controller.selected_ids.

        Controller remains the sole source of truth.
        """

        selected_ids = getattr(
            self.controller,
            "selected_ids",
            (),
        )

        if selected_ids is None:
            return ()

        return tuple(
            selected_ids
        )

    # --------------------------------------------------------

    @property
    def selected_ids(
        self,
    ) -> tuple[Any, ...]:
        """
        Read-only convenience access to the authoritative
        selection.
        """

        return self.get_selected_ids()

    # --------------------------------------------------------

    def has_selection(
        self,
    ) -> bool:
        """
        Return True when one or more objects are selected.
        """

        return bool(
            self.get_selected_ids()
        )

    # --------------------------------------------------------

    def is_selected(
        self,
        object_id: Any,
    ) -> bool:
        """
        Return whether object_id is currently selected.
        """

        if object_id is None:
            return False

        return object_id in self.get_selected_ids()

    # ========================================================
    # SELECTION MUTATION
    # ========================================================

    def select(
        self,
        object_id: Any,
        multi: bool = False,
    ) -> None:
        """
        Request selection through Controller.

        Parameters
        ----------
        object_id:
            Authoritative application object ID.

        multi:
            False:
                replace selection according to Controller
                semantics.

            True:
                add/toggle according to Controller semantics.

        SelectionManager does not modify selected_ids itself.
        """

        if object_id is None:
            raise ValueError(
                "object_id must not be None."
            )

        if not isinstance(
            multi,
            bool,
        ):
            raise TypeError(
                "multi must be a bool."
            )

        self.controller.select(
            object_id,
            multi=multi,
        )

    # --------------------------------------------------------

    def select_single(
        self,
        object_id: Any,
    ) -> None:
        """
        Replace the current selection with one object.
        """

        self.select(
            object_id,
            multi=False,
        )

    # --------------------------------------------------------

    def add_to_selection(
        self,
        object_id: Any,
    ) -> None:
        """
        Request additive selection.
        """

        self.select(
            object_id,
            multi=True,
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(self) -> None:
        """
        Clear the authoritative application selection.

        Controller performs the actual mutation.
        """

        self.controller.clear_selection()

    # ========================================================
    # GRAPHICS SYNCHRONIZATION
    # ========================================================

    def sync_graphics(
        self,
        scene: Optional[QGraphicsScene] = None,
    ) -> None:
        """
        Synchronize graphical selection from Controller.

        Authority flows only in this direction:

            Controller.selected_ids
                    ↓
            QGraphicsItem.setSelected()

        The scene's existing selection is never used as input.
        """

        target_scene = (
            scene
            if scene is not None
            else self.scene
        )

        if target_scene is None:
            return

        items_method = getattr(
            target_scene,
            "items",
            None,
        )

        if not callable(items_method):
            raise TypeError(
                "scene must provide items()."
            )

        selected_ids = set(
            self.get_selected_ids()
        )

        for item in tuple(
            items_method()
        ):
            self._synchronize_item(
                item,
                selected_ids,
            )

    # --------------------------------------------------------

    @staticmethod
    def _synchronize_item(
        item: Any,
        selected_ids: set[Any],
    ) -> None:
        """
        Synchronize one graphics item.

        Items without object_id are treated as non-selectable
        presentation items.
        """

        set_selected = getattr(
            item,
            "setSelected",
            None,
        )

        if not callable(
            set_selected
        ):
            return

        object_id = getattr(
            item,
            "object_id",
            None,
        )

        if object_id is None:
            set_selected(False)
            return

        set_selected(
            object_id in selected_ids
        )

    # ========================================================
    # ITEM LOOKUP
    # ========================================================

    def get_item_for_id(
        self,
        object_id: Any,
        scene: Optional[QGraphicsScene] = None,
    ) -> Optional[Any]:
        """
        Return the first canvas graphics item representing
        object_id.

        This is a projection lookup only.
        """

        if object_id is None:
            return None

        target_scene = (
            scene
            if scene is not None
            else self.scene
        )

        if target_scene is None:
            return None

        items_method = getattr(
            target_scene,
            "items",
            None,
        )

        if not callable(items_method):
            raise TypeError(
                "scene must provide items()."
            )

        for item in tuple(
            items_method()
        ):
            if (
                getattr(
                    item,
                    "object_id",
                    None,
                )
                == object_id
            ):
                return item

        return None

    # --------------------------------------------------------

    def get_items_for_ids(
        self,
        object_ids: Iterable[Any],
        scene: Optional[QGraphicsScene] = None,
    ) -> tuple[Any, ...]:
        """
        Return all canvas graphics items representing the
        supplied object IDs.
        """

        if object_ids is None:
            raise ValueError(
                "object_ids must not be None."
            )

        requested_ids = set(
            object_ids
        )

        if not requested_ids:
            return ()

        target_scene = (
            scene
            if scene is not None
            else self.scene
        )

        if target_scene is None:
            return ()

        items_method = getattr(
            target_scene,
            "items",
            None,
        )

        if not callable(items_method):
            raise TypeError(
                "scene must provide items()."
            )

        result: list[Any] = []

        for item in tuple(
            items_method()
        ):
            object_id = getattr(
                item,
                "object_id",
                None,
            )

            if object_id in requested_ids:
                result.append(item)

        return tuple(result)

    # ========================================================
    # SELECTED GRAPHICS
    # ========================================================

    def get_selected_items(
        self,
        scene: Optional[QGraphicsScene] = None,
    ) -> tuple[Any, ...]:
        """
        Return graphics items corresponding to the
        authoritative application selection.
        """

        return self.get_items_for_ids(
            self.get_selected_ids(),
            scene=scene,
        )

    # ========================================================
    # RECONCILIATION
    # ========================================================

    def reconcile(
        self,
        scene: Optional[QGraphicsScene] = None,
    ) -> None:
        """
        Reconcile graphical selection with Controller state.
        """

        self.sync_graphics(
            scene=scene
        )

    # ========================================================
    # SCENE
    # ========================================================

    def set_scene(
        self,
        scene: Optional[QGraphicsScene],
    ) -> None:
        """
        Attach a canvas scene.

        Ownership remains external.
        """

        self.scene = scene

    # --------------------------------------------------------

    def get_scene(
        self,
    ) -> Optional[QGraphicsScene]:
        """
        Return the attached scene.
        """

        return self.scene

    # ========================================================
    # GRAPHICS RESET
    # ========================================================

    def reset_graphics(
        self,
        scene: Optional[QGraphicsScene] = None,
    ) -> None:
        """
        Clear graphical selection state only.

        Controller.selected_ids is not modified.
        """

        target_scene = (
            scene
            if scene is not None
            else self.scene
        )

        if target_scene is None:
            return

        items_method = getattr(
            target_scene,
            "items",
            None,
        )

        if not callable(items_method):
            raise TypeError(
                "scene must provide items()."
            )

        for item in tuple(
            items_method()
        ):
            set_selected = getattr(
                item,
                "setSelected",
                None,
            )

            if callable(
                set_selected
            ):
                set_selected(False)

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic selection state.
        """

        selected_ids = (
            self.get_selected_ids()
        )

        return {
            "selected_count": len(
                selected_ids
            ),
            "selected_ids": selected_ids,
            "has_scene": (
                self.scene is not None
            ),
        }

    # --------------------------------------------------------

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "SelectionManager("
            f"selected="
            f"{len(self.get_selected_ids())}, "
            f"scene="
            f"{self.scene is not None}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "SelectionManager",
]
