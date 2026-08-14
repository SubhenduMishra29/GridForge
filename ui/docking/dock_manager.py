# ============================================================
# File: ui/docking/dock_manager.py
# GridForge V2 — Dock Manager
# ============================================================
"""
Centralized dock creation and layout management for GridForge.

Responsibilities
----------------
DockManager owns the UI-level lifecycle of QDockWidget instances.

It is responsible for:

    - creating dock widgets;
    - assigning stable dock identifiers;
    - inserting docks into the main window;
    - tracking managed docks;
    - resolving docks by identifier;
    - removing managed docks;
    - providing basic dock diagnostics;
    - releasing managed dock resources.

DockManager does NOT:

    - own the widgets placed inside docks;
    - modify the Core model;
    - perform electrical calculations;
    - implement application business logic;
    - manage canvas interaction;
    - manage tools;
    - manage commands;
    - subscribe to Core domain events.

Ownership
---------

    MainWindow
        │
        ▼
    DockManager
        │
        ├── QDockWidget
        │       │
        │       └── content widget
        │
        └── dock registry

Qt Architecture
---------------

All Qt classes must be imported through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted.

Dock Identity
-------------

Each managed dock has a stable application-level identifier.

Example:

    dock_manager.add_dock(
        "project",
        "Project",
        project_widget,
        Qt.LeftDockWidgetArea,
    )

The identifier is used for programmatic lookup and lifecycle
operations.

The visible dock title is independent from the identifier.

Lifecycle
---------

    add_dock()
        │
        ▼
    create QDockWidget
        │
        ▼
    assign content widget
        │
        ▼
    add to MainWindow
        │
        ▼
    register dock

Removal removes the dock from the main window and releases the
manager's ownership reference.

Widget Ownership
----------------

DockManager owns the QDockWidget it creates.

The content widget is assigned to the dock but is not treated as
an independently managed application resource. Qt's parent-child
ownership model governs the content widget after it is assigned
to the dock.

Duplicate IDs are prohibited.

Registering an existing dock ID raises ValueError rather than
silently replacing the existing dock.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from ui.core.qt import (
    QDockWidget,
    QMainWindow,
)


class DockManager:
    """
    Central manager for GridForge application docks.

    DockManager is intentionally UI infrastructure only.

    It does not know what a dock contains or what application
    functionality the contained widget provides.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        main_window: QMainWindow,
    ) -> None:
        """
        Initialize the DockManager.

        Parameters
        ----------
        main_window:
            Main application window that owns the docks.

        Raises
        ------
        ValueError
            If main_window is None.

        TypeError
            If main_window is not a QMainWindow-compatible
            object.
        """

        if main_window is None:
            raise ValueError(
                "main_window must not be None."
            )

        if not isinstance(
            main_window,
            QMainWindow,
        ):
            raise TypeError(
                "main_window must be a QMainWindow."
            )

        self.main_window = main_window

        # ----------------------------------------------------
        # Managed dock registry.
        #
        # Application-level dock ID → QDockWidget
        # ----------------------------------------------------

        self._docks: Dict[
            str,
            QDockWidget,
        ] = {}

        self._disposed = False

    # ========================================================
    # VALIDATION
    # ========================================================

    @staticmethod
    def _validate_dock_id(
        dock_id: str,
    ) -> str:
        """
        Validate and normalize a dock identifier.
        """

        if not isinstance(
            dock_id,
            str,
        ):
            raise TypeError(
                "dock_id must be a string."
            )

        dock_id = dock_id.strip()

        if not dock_id:
            raise ValueError(
                "dock_id must be a non-empty string."
            )

        return dock_id

    # ========================================================

    @staticmethod
    def _validate_title(
        title: str,
    ) -> str:
        """
        Validate and normalize a dock title.
        """

        if not isinstance(
            title,
            str,
        ):
            raise TypeError(
                "title must be a string."
            )

        title = title.strip()

        if not title:
            raise ValueError(
                "title must be a non-empty string."
            )

        return title

    # ========================================================
    # ADD DOCK
    # ========================================================

    def add_dock(
        self,
        dock_id: str,
        title: str,
        widget: Any,
        area: Any,
    ) -> QDockWidget:
        """
        Create, register, and add a dock to the main window.

        Parameters
        ----------
        dock_id:
            Stable application-level identifier.

        title:
            Visible dock window title.

        widget:
            QWidget-compatible content widget.

        area:
            QMainWindow dock area, normally one of:

                Qt.LeftDockWidgetArea
                Qt.RightDockWidgetArea
                Qt.TopDockWidgetArea
                Qt.BottomDockWidgetArea

        Returns
        -------
        QDockWidget
            The newly created dock.

        Raises
        ------
        RuntimeError
            If the manager has already been disposed.

        ValueError
            If dock_id is already registered.

        TypeError
            If arguments have invalid types.

        Notes
        -----
        DockManager does not replace existing docks. Duplicate
        identifiers are configuration errors.
        """

        if self._disposed:
            raise RuntimeError(
                "DockManager has been disposed."
            )

        dock_id = self._validate_dock_id(
            dock_id
        )

        title = self._validate_title(
            title
        )

        if dock_id in self._docks:
            raise ValueError(
                "Dock already registered with ID "
                f"'{dock_id}'."
            )

        if widget is None:
            raise ValueError(
                "widget must not be None."
            )

        # ----------------------------------------------------
        # QDockWidget creation.
        #
        # The manager creates the dock container only.
        # The content widget remains application-owned.
        # ----------------------------------------------------

        dock = QDockWidget(
            title,
            self.main_window,
        )

        # ----------------------------------------------------
        # Stable application-level identity.
        # ----------------------------------------------------

        dock.setObjectName(
            dock_id
        )

        # ----------------------------------------------------
        # Assign content widget.
        # ----------------------------------------------------

        dock.setWidget(
            widget
        )

        # ----------------------------------------------------
        # Add dock to main window.
        # ----------------------------------------------------

        self.main_window.addDockWidget(
            area,
            dock,
        )

        # ----------------------------------------------------
        # Register only after successful creation and insertion.
        # ----------------------------------------------------

        self._docks[
            dock_id
        ] = dock

        return dock

    # ========================================================
    # GET DOCK
    # ========================================================

    def get_dock(
        self,
        dock_id: str,
    ) -> Optional[QDockWidget]:
        """
        Return a managed dock by identifier.

        Returns None when no such dock is registered.
        """

        dock_id = self._validate_dock_id(
            dock_id
        )

        return self._docks.get(
            dock_id
        )

    # ========================================================
    # REQUIRE DOCK
    # ========================================================

    def require_dock(
        self,
        dock_id: str,
    ) -> QDockWidget:
        """
        Return a managed dock or raise KeyError.
        """

        dock_id = self._validate_dock_id(
            dock_id
        )

        dock = self._docks.get(
            dock_id
        )

        if dock is None:
            raise KeyError(
                "No dock registered with ID "
                f"'{dock_id}'."
            )

        return dock

    # ========================================================
    # CHECK DOCK
    # ========================================================

    def has_dock(
        self,
        dock_id: str,
    ) -> bool:
        """
        Return True when a dock is registered.
        """

        dock_id = self._validate_dock_id(
            dock_id
        )

        return dock_id in self._docks

    # ========================================================
    # DOCK IDS
    # ========================================================

    def get_dock_ids(
        self,
    ) -> list[str]:
        """
        Return all managed dock identifiers.

        Registration order is preserved.
        """

        return list(
            self._docks.keys()
        )

    # ========================================================
    # DOCKS
    # ========================================================

    def get_docks(
        self,
    ) -> Dict[
        str,
        QDockWidget,
    ]:
        """
        Return a detached snapshot of managed docks.

        Mutating the returned dictionary does not modify the
        manager's internal registry.
        """

        return dict(
            self._docks
        )

    # ========================================================
    # REMOVE DOCK
    # ========================================================

    def remove_dock(
        self,
        dock_id: str,
    ) -> bool:
        """
        Remove a managed dock from the main window.

        Parameters
        ----------
        dock_id:
            Stable application-level dock identifier.

        Returns
        -------
        bool
            True when a dock was removed.

            False when the dock was not registered.

        Notes
        -----
        The dock is removed from the manager registry and from
        the main window. Qt then owns destruction according to
        the normal QObject/widget lifecycle.
        """

        dock_id = self._validate_dock_id(
            dock_id
        )

        dock = self._docks.pop(
            dock_id,
            None,
        )

        if dock is None:
            return False

        # ----------------------------------------------------
        # Remove from the main-window docking system.
        # ----------------------------------------------------

        self.main_window.removeDockWidget(
            dock
        )

        # ----------------------------------------------------
        # Schedule Qt-side deletion.
        #
        # deleteLater() is preferred over immediate destruction
        # while the Qt event system is active.
        # ----------------------------------------------------

        delete_later = getattr(
            dock,
            "deleteLater",
            None,
        )

        if callable(
            delete_later
        ):
            delete_later()

        return True

    # ========================================================
    # REMOVE ALL DOCKS
    # ========================================================

    def remove_all_docks(
        self,
    ) -> None:
        """
        Remove all managed docks.

        Dock identifiers are snapshotted before removal so that
        registry mutation does not affect iteration.
        """

        for dock_id in list(
            self._docks.keys()
        ):
            self.remove_dock(
                dock_id
            )

    # ========================================================
    # LAYOUT
    # ========================================================

    def add_dock_to_area(
        self,
        dock_id: str,
        area: Any,
    ) -> None:
        """
        Move an existing managed dock to another main-window
        dock area.

        This method changes only Qt UI layout state.
        """

        dock = self.require_dock(
            dock_id
        )

        self.main_window.addDockWidget(
            area,
            dock,
        )

    # ========================================================
    # VISIBILITY
    # ========================================================

    def show_dock(
        self,
        dock_id: str,
    ) -> None:
        """
        Show a managed dock.
        """

        self.require_dock(
            dock_id
        ).show()

    # --------------------------------------------------------

    def hide_dock(
        self,
        dock_id: str,
    ) -> None:
        """
        Hide a managed dock.
        """

        self.require_dock(
            dock_id
        ).hide()

    # --------------------------------------------------------

    def is_dock_visible(
        self,
        dock_id: str,
    ) -> bool:
        """
        Return the current visibility state of a managed dock.
        """

        return self.require_dock(
            dock_id
        ).isVisible()

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return a diagnostic snapshot of dock-manager state.
        """

        return {
            "disposed": self._disposed,
            "dock_count": len(
                self._docks
            ),
            "dock_ids": list(
                self._docks.keys()
            ),
        }

    # ========================================================
    # DISPOSE
    # ========================================================

    def dispose(
        self,
    ) -> None:
        """
        Release all managed dock resources.

        The operation is idempotent.

        DockManager does not destroy the main window.
        """

        if self._disposed:
            return

        self.remove_all_docks()

        self._disposed = True

    # ========================================================
    # LENGTH
    # ========================================================

    def __len__(
        self,
    ) -> int:
        """
        Return the number of managed docks.
        """

        return len(
            self._docks
        )

    # ========================================================
    # DEBUG REPRESENTATION
    # ========================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "DockManager("
            f"docks={list(self._docks.keys())!r}, "
            f"disposed={self._disposed}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "DockManager",
]
