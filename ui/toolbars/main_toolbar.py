# ============================================================
# File: ui/toolbars/main_toolbar.py
# GridForge V2 — Main Toolbar
# ============================================================

"""
Main application toolbar for GridForge.

Responsibilities
----------------
MainToolbar provides a presentation-level container for actions
injected by UI plugins.

It is responsible for:

    - creating the main toolbar;
    - adding externally supplied tool/action callbacks;
    - maintaining stable action identifiers;
    - resolving actions by identifier;
    - removing actions;
    - clearing injected actions;
    - exposing basic toolbar diagnostics.

MainToolbar does NOT:

    - define tools;
    - create tool instances;
    - own ToolManager;
    - select tools;
    - modify the Core model;
    - execute commands directly;
    - perform rendering;
    - contain electrical logic;
    - perform business logic.

Architecture
------------

    UI Plugin / Controller
            │
            ▼
       MainToolbar
            │
            ▼
          QAction

Tool behavior remains outside the toolbar.

Qt Architecture
---------------

All Qt classes are imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from ui.core.qt import (
    QAction,
    QToolBar,
    QWidget,
)


class MainToolbar(QToolBar):
    """
    Extensible GridForge application toolbar.

    Actions are injected by plugins or other UI composition
    infrastructure. The toolbar does not know what a tool does.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        parent: Optional[QWidget] = None,
    ) -> None:
        """
        Initialize the main toolbar.
        """

        super().__init__(
            "Tools",
            parent,
        )

        self._actions: Dict[
            str,
            QAction,
        ] = {}

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_name(
        name: str,
    ) -> str:
        """
        Validate an action display name.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "name must be a string."
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "name must be a non-empty string."
            )

        return name

    # --------------------------------------------------------

    @staticmethod
    def _validate_tool_id(
        tool_id: str,
    ) -> str:
        """
        Validate an action identifier.
        """

        if not isinstance(
            tool_id,
            str,
        ):
            raise TypeError(
                "tool_id must be a string."
            )

        tool_id = tool_id.strip()

        if not tool_id:
            raise ValueError(
                "tool_id must be a non-empty string."
            )

        return tool_id

    # ========================================================
    # ADD TOOL
    # ========================================================

    def add_tool(
        self,
        name: str,
        callback: Callable[..., Any],
        tool_id: Optional[str] = None,
    ) -> QAction:
        """
        Add an externally defined tool/action to the toolbar.

        Parameters
        ----------
        name:
            Visible action text.

        callback:
            Callable connected to QAction.triggered.

        tool_id:
            Optional stable application-level identifier.

        Returns
        -------
        QAction
            The created action.

        Raises
        ------
        TypeError
            If arguments have invalid types.

        ValueError
            If the name or tool identifier is invalid, or if the
            identifier is already registered.
        """

        name = self._validate_name(
            name
        )

        if not callable(
            callback
        ):
            raise TypeError(
                "callback must be callable."
            )

        if tool_id is not None:
            tool_id = self._validate_tool_id(
                tool_id
            )

            if tool_id in self._actions:
                raise ValueError(
                    "Toolbar action already registered with ID "
                    f"'{tool_id}'."
                )

        action = QAction(
            name,
            self,
        )

        action.triggered.connect(
            callback
        )

        self.addAction(
            action
        )

        if tool_id is not None:
            self._actions[
                tool_id
            ] = action

        return action

    # ========================================================
    # GET ACTION
    # ========================================================

    def get_action(
        self,
        tool_id: str,
    ) -> Optional[QAction]:
        """
        Return a registered action by identifier.

        Returns None if no such action exists.
        """

        tool_id = self._validate_tool_id(
            tool_id
        )

        return self._actions.get(
            tool_id
        )

    # ========================================================
    # REQUIRE ACTION
    # ========================================================

    def require_action(
        self,
        tool_id: str,
    ) -> QAction:
        """
        Return a registered action or raise KeyError.
        """

        tool_id = self._validate_tool_id(
            tool_id
        )

        action = self._actions.get(
            tool_id
        )

        if action is None:
            raise KeyError(
                "No toolbar action registered with ID "
                f"'{tool_id}'."
            )

        return action

    # ========================================================
    # CHECK ACTION
    # ========================================================

    def has_action(
        self,
        tool_id: str,
    ) -> bool:
        """
        Return True when an action is registered.
        """

        tool_id = self._validate_tool_id(
            tool_id
        )

        return tool_id in self._actions

    # ========================================================
    # ACTION IDS
    # ========================================================

    def get_action_ids(
        self,
    ) -> list[str]:
        """
        Return all registered action identifiers.

        Registration order is preserved.
        """

        return list(
            self._actions.keys()
        )

    # ========================================================
    # REMOVE ACTION
    # ========================================================

    def remove_tool(
        self,
        tool_id: str,
    ) -> bool:
        """
        Remove a registered tool action.

        Returns
        -------
        bool
            True when an action was removed.
            False when no action was registered.
        """

        tool_id = self._validate_tool_id(
            tool_id
        )

        action = self._actions.pop(
            tool_id,
            None,
        )

        if action is None:
            return False

        self.removeAction(
            action
        )

        delete_later = getattr(
            action,
            "deleteLater",
            None,
        )

        if callable(
            delete_later
        ):
            delete_later()

        return True

    # ========================================================
    # CLEAR
    # ========================================================

    def clear_tools(
        self,
    ) -> None:
        """
        Remove all tracked tool actions.
        """

        for tool_id in list(
            self._actions.keys()
        ):
            self.remove_tool(
                tool_id
            )

    # ========================================================
    # STATE
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic toolbar state.
        """

        return {
            "action_count": len(
                self._actions
            ),
            "action_ids": list(
                self._actions.keys()
            ),
        }

    # ========================================================
    # LENGTH
    # ========================================================

    def __len__(
        self,
    ) -> int:
        """
        Return the number of tracked tool actions.
        """

        return len(
            self._actions
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

        return (
            "MainToolbar("
            f"actions={list(self._actions.keys())!r}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "MainToolbar",
]
