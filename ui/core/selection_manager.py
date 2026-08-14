# ============================================================
# File: ui/core/selection_manager.py
# GridForge V2 — Selection Manager
# ============================================================
"""
Central selection adapter for GridForge UI.

Architecture
------------

    User / Tool
         │
         ▼
    SelectionManager
         │
         ▼
    Controller
         │
         ▼
    Controller.selected_ids
         │
         ▼
    Core / Application State
         │
         ▼
    Graphics projection
         │
         ▼
    QGraphicsItems


Selection Ownership
-------------------
Persistent application selection belongs exclusively to:

    Controller.selected_ids

SelectionManager does NOT maintain a second persistent
selection collection.

QGraphicsItem selection state is only a visual projection of
the authoritative Controller selection state.

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

    - provides a central UI selection API;
    - delegates selection mutations to Controller;
    - reads authoritative Controller.selected_ids;
    - synchronizes graphical selection state;
    - resolves graphics items by object ID;
    - supports single and multi-selection requests;
    - provides selection diagnostics.

SelectionManager does NOT:

    - own persistent selection state;
    - modify Core model objects directly;
    - create model objects;
    - create graphics items;
    - render graphics;
    - implement tool behavior;
    - perform snapping;
    - perform navigation;
    - perform electrical calculations;
    - decide application-level tool selection;
    - treat QGraphicsScene.selectedItems() as authoritative.

Graphics Items
--------------
Graphics items participating in selection should expose:

    object_id

and should support:

    setSelected(bool)
    isSelected()

The graphics item remains responsible for its own visual
selection appearance.

Controller Contract
-------------------
The canonical selection mutation contract is:

    controller.select(
        object_id,
        multi=bool,
    )

The authoritative selection collection is:

    controller.selected_ids

SelectionManager deliberately does not assume that the
QGraphicsScene selection state is authoritative.

Qt Architecture
---------------
All Qt imports must pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.qt import QGraphicsScene


class SelectionManager:
    """
    Central UI selection adapter.

    Persistent selection belongs to Controller.

    SelectionManager only provides a stable boundary between
    UI interaction and the application's authoritative
    selection state.
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
            Optional QGraphicsScene containing permanent
            graphical projections.

        Notes
        -----
        SelectionManager does not take ownership of the scene.

        The scene is used only to synchronize graphical
        selection state from Controller.selected_ids.
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

        self.controller = controller
        self.scene = scene

    # ========================================================
    # AUTHORITATIVE SELECTION ACCESS
    # ========================================================

    def get_selected_ids(
        self,
    ) -> tuple[Any, ...]:
        """
        Return the authoritative application selection.

        The returned tuple is a snapshot.

        Controller.selected_ids remains the source of truth.
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
        Read-only convenience property for the current
        authoritative selection.
        """

        return self.get_selected_ids()

    # --------------------------------------------------------

    def has_selection(
        self,
    ) -> bool:
        """
        Return True when at least one object is selected.
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
        Return True when object_id is in the authoritative
        Controller selection.
        """

        if object_id is None:
            return False

        return object_id in set(
            self.get_selected_ids()
        )

    # ========================================================
    # SELECTION MUTATION
    # ========================================================

    def select(
        self,
        object_id: Any,
        multi: bool = False,
    ) -> None:
        """
        Request selection of an application object.

        Parameters
        ----------
        object_id:
            Authoritative Core/application object identifier.

        multi:
            When True, request additive/multi-selection according
            to the Controller selection contract.

        Notes
        -----
        SelectionManager does not modify selected_ids directly.

        The Controller remains responsible for applying the
        selection mutation.
        """

        if object_id is None:
            raise ValueError(
                "object_id must not be None."
            )

        if isinstance(
            multi,
            bool,
        ) is False:
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
        Replace the current selection with object_id.

        The actual replacement semantics remain owned by
        Controller.select(..., multi=False).
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
        Add object_id to the current selection.

        Controller owns the actual mutation semantics.
        """

        self.select(
            object_id,
            multi=True,
        )

    # ========================================================
    # CLEAR SELECTION
    # ========================================================

    def clear(
        self,
    ) -> None:
        """
        Clear the authoritative application selection.

        Controller owns the selection mutation.

        The canonical Controller contract must provide
        clear_selection().
        """

        clear_selection = getattr(
            self.controller,
            "clear_selection",
            None,
        )

        if not callable(
            clear_selection
        ):
            raise TypeError(
                "controller must provide "
                "clear_selection()."
            )

        clear_selection()

    # ========================================================
    # GRAPHICS SYNCHRONIZATION
    # ========================================================

    def sync_graphics(
        self,
        scene: Optional[QGraphicsScene] = None,
    ) -> None:
        """
        Synchronize QGraphicsItem selection state from the
        authoritative Controller selection.

        Parameters
        ----------
        scene:
            Optional scene override.

            If omitted, the scene supplied during construction
            is used.

        Notes
        -----
        This method never reads scene.selectedItems() to determine
        application selection.

        Direction of authority:

            Controller.selected_ids
                    ↓
            QGraphicsItem.setSelected()

        The graphics scene remains a visual projection.
        """

        target_scene = (
            scene
            if scene is not None
            else self.scene
        )

        if target_scene is None:
            return

        selected = set(
            self.get_selected_ids()
        )

        items_method = getattr(
            target_scene,
            "items",
            None,
        )

        if not callable(
            items_method
        ):
            raise TypeError(
                "scene must provide items()."
            )

        for item in tuple(
            items_method()
        ):

            object_id = getattr(
                item,
                "object_id",
                None,
            )

            set_selected = getattr(
                item,
                "setSelected",
                None,
            )

            if not callable(
                set_selected
            ):
                continue

            if object_id is None:
                set_selected(False)
                continue

            set_selected(
                object_id in selected
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
        Return the first graphics item representing object_id.

        Parameters
        ----------
        object_id:
            Authoritative application object identifier.

        scene:
            Optional scene override.

        Returns
        -------
        object | None
            Matching graphics item, if present.

        Notes
        -----
        This is a UI projection lookup only.

        It does not imply that the graphics item owns the
        underlying model object.
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

        if not callable(
            items_method
        ):
            raise TypeError(
                "scene must provide items()."
            )

        for item in tuple(
            items_method()
        ):

            item_object_id = getattr(
                item,
                "object_id",
                None,
            )

            if (
                item_object_id
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
        Return graphics items representing the supplied IDs.

        The returned tuple preserves scene iteration order.

        Items without an object_id are ignored.
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

        if not callable(
            items_method
        ):
            raise TypeError(
                "scene must provide items()."
            )

        result = []

        for item in tuple(
            items_method()
        ):

            object_id = getattr(
                item,
                "object_id",
                None,
            )

            if object_id in requested_ids:
                result.append(
                    item
                )

        return tuple(
            result
        )

    # ========================================================
    # GRAPHICS SELECTION QUERY
    # ========================================================

    def get_selected_items(
        self,
        scene: Optional[QGraphicsScene] = None,
    ) -> tuple[Any, ...]:
        """
        Return graphics items corresponding to the authoritative
        Controller selection.

        This method deliberately does NOT use
        QGraphicsScene.selectedItems() as the source of truth.
        """

        selected_ids = (
            self.get_selected_ids()
        )

        return self.get_items_for_ids(
            selected_ids,
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
        Reconcile graphical selection with authoritative
        Controller selection.

        This is an alias for sync_graphics() intended for
        lifecycle/render synchronization code.
        """

        self.sync_graphics(
            scene=scene
        )

    # ========================================================
    # SCENE ACCESS
    # ========================================================

    def set_scene(
        self,
        scene: Optional[QGraphicsScene],
    ) -> None:
        """
        Attach a QGraphicsScene used for graphical selection
        synchronization.

        The SelectionManager does not take ownership of it.
        """

        self.scene = scene

    # --------------------------------------------------------

    def get_scene(
        self,
    ) -> Optional[QGraphicsScene]:
        """
        Return the currently attached scene.
        """

        return self.scene

    # ========================================================
    # RESET
    # ========================================================

    def reset_graphics(
        self,
        scene: Optional[QGraphicsScene] = None,
    ) -> None:
        """
        Clear graphical selection state only.

        This method does NOT modify Controller.selected_ids.

        It is intended for scene replacement/removal operations
        where the graphical projection must temporarily be
        cleared before the next synchronization.
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

        if not callable(
            items_method
        ):
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
    # DEBUG STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot.

        Persistent selection is read directly from Controller.
        """

        return {
            "selected_count": len(
                self.get_selected_ids()
            ),
            "selected_ids": (
                self.get_selected_ids()
            ),
            "has_scene": (
                self.scene is not None
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
