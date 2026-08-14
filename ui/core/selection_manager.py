# ============================================================
# File: ui/core/selection_manager.py
# GridForge V2 — Selection Manager
# ============================================================
"""
Central selection adapter for the GridForge UI.

Selection ownership
-------------------
Persistent application selection is owned by Controller.

    Controller.selected_ids
            │
            ▼
    SelectionManager
            │
            ▼
    Graphics projection

SelectionManager does NOT maintain a second authoritative
selection collection.

Responsibilities
----------------
SelectionManager:

    - exposes the UI selection API;
    - delegates selection mutations to Controller;
    - reads Controller.selected_ids;
    - synchronizes QGraphicsItem selection state;
    - resolves graphics items by object_id;
    - provides selection diagnostics.

SelectionManager does NOT:

    - own persistent selection state;
    - modify Core model objects directly;
    - create graphics items;
    - render graphics;
    - implement tool behavior;
    - perform snapping;
    - perform navigation;
    - perform electrical calculations;
    - decide application-level tool selection.

Graphics selection is a projection only.

Qt Architecture
---------------
All Qt dependencies pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.qt import QGraphicsScene


class SelectionManager:
    """
    Central UI selection adapter.

    Controller remains the sole owner of persistent selection
    state.
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
            GridForge application Controller.

        scene:
            Optional graphics scene used for projection
            synchronization.

        SelectionManager does not take ownership of the scene.
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
    # AUTHORITATIVE SELECTION
    # ========================================================

    def get_selected_ids(
        self,
    ) -> tuple[Any, ...]:
        """
        Return a snapshot of Controller.selected_ids.

        Controller remains authoritative.
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
        Read-only convenience access to selected IDs.
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
        Return whether object_id is selected.
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
        Request selection of an object through Controller.

        Parameters
        ----------
        object_id:
            Authoritative application object identifier.

        multi:
            Controller-defined additive/multi-selection mode.
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
        Request additive selection of one object.
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

        Controller owns the mutation.
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
        Synchronize graphics selection from Controller.

        Authority direction:

            Controller.selected_ids
                    ↓
            QGraphicsItem.setSelected()

        Scene selection is never treated as authoritative.
        """

        target_scene = (
            scene
            if scene is not None
            else self.scene
        )

        if target_scene is None:
            return

        selected_ids = set(
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
            set_selected = getattr(
                item,
                "setSelected",
                None,
            )

            if not callable(
                set_selected
            ):
                continue

            object_id = getattr(
                item,
                "object_id",
                None,
            )

            if object_id is None:
                set_selected(False)
                continue

            set_selected(
                object_id in selected_ids
            )

    # --------------------------------------------------------

    def reconcile(
        self,
        scene: Optional[QGraphicsScene] = None,
    ) -> None:
        """
        Reconcile graphics with authoritative selection.
        """

        self.sync_graphics(
            scene=scene
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
            if getattr(
                item,
                "object_id",
                None,
            ) == object_id:
                return item

        return None

    # --------------------------------------------------------

    def get_items_for_ids(
        self,
        object_ids: Iterable[Any],
        scene: Optional[QGraphicsScene] = None,
    ) -> tuple[Any, ...]:
        """
        Return graphics items representing supplied IDs.
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

        return tuple(
            result
        )

    # --------------------------------------------------------

    def get_selected_items(
        self,
        scene: Optional[QGraphicsScene] = None,
    ) -> tuple[Any, ...]:
        """
        Return graphics items corresponding to authoritative
        selected IDs.
        """

        return self.get_items_for_ids(
            self.get_selected_ids(),
            scene=scene,
        )

    # ========================================================
    # SCENE MANAGEMENT
    # ========================================================

    def set_scene(
        self,
        scene: Optional[QGraphicsScene],
    ) -> None:
        """
        Attach a scene for graphical projection.
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
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot.
        """

        selected_ids = (
            self.get_selected_ids()
        )

        return {
            "selected_count": len(
                selected_ids
            ),
            "selected_ids": selected_ids,
            "has_selection": bool(
                selected_ids
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
