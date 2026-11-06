# ============================================================
# File: ui/controllers/selection_controller.py
# GridForge V2 — UI Selection Controller
# ============================================================
"""
UI Selection Controller for GridForge V2.

Architecture
------------

    UI / Canvas
         │
         ▼
    SelectionController
         │
         ▼
    SelectionManager
         │
         ├──────────────► authoritative Controller
         │
         └──────────────► graphical projection
                            │
                            ▼
                       QGraphicsItems

Purpose
-------
SelectionController is the UI orchestration boundary for
selection operations.

The authoritative selection state remains owned by the
application Controller / SelectionManager contract.

This class provides a stable controller-level API while
delegating selection behavior to SelectionManager.

Responsibilities
----------------
SelectionController:

    - expose selection operations;
    - request selection and deselection;
    - request clearing;
    - synchronize graphical selection;
    - expose current selection;
    - provide selection diagnostics.

SelectionController does NOT:

    - implement selection ownership;
    - maintain a second selection set;
    - perform hit testing;
    - decide electrical topology;
    - mutate Core model objects;
    - render graphics;
    - implement tools;
    - implement snapping;
    - perform navigation.

Qt Architecture
---------------
This module contains no direct Qt dependencies.

SelectionManager owns the concrete graphical-selection
integration.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

from ui.core.selection_manager import SelectionManager


class SelectionController:
    """
    Thin UI orchestration adapter around SelectionManager.

    SelectionManager remains the authoritative UI selection
    service.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        selection_manager: SelectionManager,
    ) -> None:
        """
        Initialize the SelectionController.

        Parameters
        ----------
        selection_manager:
            Existing GridForge SelectionManager.

        The manager is not copied or duplicated.
        """

        if selection_manager is None:
            raise ValueError(
                "selection_manager must not be None."
            )

        if not isinstance(
            selection_manager,
            SelectionManager,
        ):
            raise TypeError(
                "selection_manager must be a "
                "SelectionManager."
            )

        self.selection_manager = (
            selection_manager
        )

        self._disposed = False

    # ========================================================
    # MANAGER ACCESS
    # ========================================================

    def get_selection_manager(
        self,
    ) -> SelectionManager:
        """
        Return the underlying SelectionManager.
        """

        self._ensure_active()

        return self.selection_manager

    # ========================================================
    # SELECT
    # ========================================================

    def select(
        self,
        object_id: Any,
        *,
        additive: bool = False,
    ) -> Any:
        """
        Select an object through SelectionManager.

        Parameters
        ----------
        object_id:
            Authoritative object identifier.

        additive:
            Preserve existing selection when True.

        Returns
        -------
        Any
            Result returned by SelectionManager.
        """

        self._ensure_active()

        if object_id is None:
            raise ValueError(
                "object_id must not be None."
            )

        manager = self.selection_manager

        method = getattr(
            manager,
            "select",
            None,
        )

        if not callable(method):
            raise TypeError(
                "SelectionManager must provide select()."
            )

        return method(
            object_id,
            additive=additive,
        )

    # ========================================================
    # DESELECT
    # ========================================================

    def deselect(
        self,
        object_id: Any,
    ) -> Any:
        """
        Deselect an object through SelectionManager.
        """

        self._ensure_active()

        if object_id is None:
            raise ValueError(
                "object_id must not be None."
            )

        method = getattr(
            self.selection_manager,
            "deselect",
            None,
        )

        if not callable(method):
            raise TypeError(
                "SelectionManager must provide deselect()."
            )

        return method(
            object_id
        )

    # ========================================================
    # TOGGLE
    # ========================================================

    def toggle(
        self,
        object_id: Any,
    ) -> Any:
        """
        Toggle selection of an object.
        """

        self._ensure_active()

        if object_id is None:
            raise ValueError(
                "object_id must not be None."
            )

        method = getattr(
            self.selection_manager,
            "toggle",
            None,
        )

        if not callable(method):
            raise TypeError(
                "SelectionManager must provide toggle()."
            )

        return method(
            object_id
        )

    # ========================================================
    # CLEAR
    # ========================================================

    def clear(
        self,
    ) -> Any:
        """
        Clear authoritative selection through SelectionManager.
        """

        self._ensure_active()

        method = getattr(
            self.selection_manager,
            "clear",
            None,
        )

        if not callable(method):
            raise TypeError(
                "SelectionManager must provide clear()."
            )

        return method()

    # ========================================================
    # SELECT MULTIPLE
    # ========================================================

    def select_many(
        self,
        object_ids: Iterable[Any],
        *,
        additive: bool = False,
    ) -> Any:
        """
        Select multiple objects through SelectionManager.
        """

        self._ensure_active()

        if object_ids is None:
            raise ValueError(
                "object_ids must not be None."
            )

        ids = tuple(
            object_ids
        )

        if any(
            object_id is None
            for object_id in ids
        ):
            raise ValueError(
                "object_ids must not contain None."
            )

        manager = self.selection_manager

        method = getattr(
            manager,
            "select_many",
            None,
        )

        if callable(method):
            return method(
                ids,
                additive=additive,
            )

        # ----------------------------------------------------
        # Do not implement a parallel selection algorithm.
        #
        # Fall back only to the manager's canonical select()
        # operation when bulk selection is not exposed.
        # ----------------------------------------------------

        if not additive:
            self.clear()

        result = []

        for object_id in ids:
            result.append(
                self.select(
                    object_id,
                    additive=True,
                )
            )

        return tuple(
            result
        )

    # ========================================================
    # QUERY
    # ========================================================

    @property
    def selected_ids(
        self,
    ) -> frozenset[Any]:
        """
        Return the current authoritative selection.

        A defensive immutable view is returned.
        """

        self._ensure_active()

        value = getattr(
            self.selection_manager,
            "selected_ids",
            None,
        )

        if value is None:
            getter = getattr(
                self.selection_manager,
                "get_selected_ids",
                None,
            )

            if callable(getter):
                value = getter()

        if value is None:
            return frozenset()

        return frozenset(
            value
        )

    # --------------------------------------------------------

    def get_selected_ids(
        self,
    ) -> frozenset[Any]:
        """
        Return the current selected object identifiers.
        """

        return self.selected_ids

    # --------------------------------------------------------

    def is_selected(
        self,
        object_id: Any,
    ) -> bool:
        """
        Return whether object_id is currently selected.
        """

        self._ensure_active()

        if object_id is None:
            return False

        method = getattr(
            self.selection_manager,
            "is_selected",
            None,
        )

        if callable(method):
            return bool(
                method(
                    object_id
                )
            )

        return object_id in self.selected_ids

    # --------------------------------------------------------

    def selection_count(
        self,
    ) -> int:
        """
        Return the number of currently selected objects.
        """

        return len(
            self.selected_ids
        )

    # ========================================================
    # GRAPHICAL SYNCHRONIZATION
    # ========================================================

    def sync_graphics(
        self,
        scene: Optional[Any] = None,
    ) -> Any:
        """
        Synchronize graphical selection from authoritative
        selection state.

        Parameters
        ----------
        scene:
            Optional graphics scene.

        The operation is delegated to SelectionManager.
        """

        self._ensure_active()

        method = getattr(
            self.selection_manager,
            "sync_graphics",
            None,
        )

        if not callable(method):
            raise TypeError(
                "SelectionManager must provide "
                "sync_graphics()."
            )

        if scene is None:
            return method()

        return method(
            scene
        )

    # --------------------------------------------------------

    def clear_graphical_selection(
        self,
        scene: Optional[Any] = None,
    ) -> Any:
        """
        Clear graphical selection only.

        Authoritative selection is preserved.
        """

        self._ensure_active()

        method = getattr(
            self.selection_manager,
            "reset_graphics",
            None,
        )

        if not callable(method):
            method = getattr(
                self.selection_manager,
                "clear_graphics",
                None,
            )

        if not callable(method):
            raise TypeError(
                "SelectionManager must provide "
                "reset_graphics() or clear_graphics()."
            )

        if scene is None:
            return method()

        return method(
            scene
        )

    # ========================================================
    # SCENE
    # ========================================================

    def set_scene(
        self,
        scene: Any,
    ) -> None:
        """
        Set the graphical scene used by SelectionManager.

        Scene ownership remains with the canvas.
        """

        self._ensure_active()

        if scene is None:
            raise ValueError(
                "scene must not be None."
            )

        method = getattr(
            self.selection_manager,
            "set_scene",
            None,
        )

        if not callable(method):
            raise TypeError(
                "SelectionManager must provide set_scene()."
            )

        method(
            scene
        )

    # ========================================================
    # RESET GRAPHICS
    # ========================================================

    def reset_graphics(
        self,
        scene: Optional[Any] = None,
    ) -> Any:
        """
        Reset only graphical selection state.
        """

        return self.clear_graphical_selection(
            scene
        )

    # ========================================================
    # STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic selection snapshot.

        The SelectionManager remains authoritative.
        """

        if self._disposed:
            return {
                "disposed": True,
            }

        manager_state: Any = None

        getter = getattr(
            self.selection_manager,
            "get_state",
            None,
        )

        if callable(getter):
            manager_state = getter()

        return {
            "disposed": False,
            "selected_ids": tuple(
                self.selected_ids
            ),
            "selection_count": (
                self.selection_count()
            ),
            "manager_state": manager_state,
        }

    # ========================================================
    # LIFECYCLE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Dispose this controller adapter.

        SelectionManager is not disposed because ownership remains
        with the UI/core composition layer.
        """

        if self._disposed:
            return

        self._disposed = True

    # ========================================================
    # ACTIVE STATE
    # ========================================================

    def _ensure_active(
        self,
    ) -> None:
        """
        Ensure this controller has not been disposed.
        """

        if self._disposed:
            raise RuntimeError(
                "SelectionController has been disposed."
            )

    # ========================================================
    # REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        if self._disposed:
            return (
                "SelectionController("
                "disposed=True"
                ")"
            )

        return (
            "SelectionController("
            f"count={self.selection_count()}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "SelectionController",
]
