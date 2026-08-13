"""
GridForge V2 — Main Application Window
======================================

File:
    ui/main_window.py

Purpose
-------
Root Qt window for the GridForge application.

Architectural Role
------------------
MainWindow is the root UI container.

It owns:

    - the Qt top-level window;
    - the UI Controller reference;
    - references to UI components assembled by the
      plugin-driven UI registry.

It does NOT own:

    - domain state;
    - application/business logic;
    - electrical calculations;
    - tool instances;
    - tool lifecycle;
    - canvas interaction;
    - rendering logic;
    - individual UI component construction.

UI Construction
---------------
All UI assembly is delegated to the central UI registry.

    MainWindow
        |
        v
    build_ui()
        |
        v
    registered UI plugins
        |
        v
    UI components

Plugin Architecture
--------------------
UI features are added through plugins rather than by modifying
this class.

Adding a new UI feature should therefore follow:

    1. Create the UI component/plugin.
    2. Register the plugin.
    3. Allow the UI registry to discover it.

MainWindow itself should remain stable.

Controller Boundary
--------------------
The supplied Controller is the UI coordination controller.

It may provide:

    - requested tool identifier;
    - logical selection state;
    - UI coordination notifications;
    - reference to the authoritative application/domain context.

MainWindow does not perform domain mutations through the
Controller.

Qt Rule
-------
This module is a Qt UI boundary and may use Qt through the
established GridForge Qt abstraction policy.

The window remains a presentation/container layer.
"""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtWidgets import QMainWindow

from ui.ui_registry import build_ui


class MainWindow(QMainWindow):
    """
    Root application window.

    MainWindow is intentionally thin and stable.

    Its primary responsibilities are:

        1. Own the top-level Qt window.
        2. Retain the UI Controller reference.
        3. Configure minimal window properties.
        4. Delegate UI construction to the plugin registry.
        5. Retain references to constructed UI components.
    """

    # ============================================================
    # INITIALIZATION
    # ============================================================

    def __init__(
        self,
        controller: Any,
    ) -> None:
        """
        Initialize the GridForge root window.

        Parameters
        ----------
        controller:
            GridForge UI Controller.

            The Controller provides UI coordination state and
            access to the application-facing model context.

            MainWindow does not become the owner of that state.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        super().__init__()

        # --------------------------------------------------------
        # UI coordination controller
        # --------------------------------------------------------

        self.controller = controller

        # --------------------------------------------------------
        # Plugin-created UI components
        # --------------------------------------------------------
        #
        # The registry is responsible for constructing the
        # registered UI components.
        #
        # MainWindow only retains the resulting references.
        # --------------------------------------------------------

        self.components: dict[str, Any] = {}

        # --------------------------------------------------------
        # Base window configuration
        # --------------------------------------------------------

        self._setup_window()

        # --------------------------------------------------------
        # Plugin-driven UI construction
        # --------------------------------------------------------

        self._build_ui()

    # ============================================================
    # WINDOW SETUP
    # ============================================================

    def _setup_window(
        self,
    ) -> None:
        """
        Configure minimal root-window properties.

        This method must remain free of feature-specific UI
        construction.
        """

        self.setWindowTitle(
            "GridForge"
        )

        self.resize(
            1200,
            800,
        )

    # ============================================================
    # UI CONSTRUCTION
    # ============================================================

    def _build_ui(
        self,
    ) -> None:
        """
        Assemble the UI through the central plugin registry.

        MainWindow deliberately contains no component-specific
        construction logic.

        The UI registry is responsible for:

            - discovering registered UI plugins;
            - constructing their components;
            - attaching components to this window;
            - returning component references.

        The resulting references are retained in
        ``self.components``.
        """

        components = build_ui(
            self,
            self.controller,
        )

        if components is None:
            self.components = {}
            return

        if not isinstance(
            components,
            dict,
        ):
            raise TypeError(
                "build_ui() must return a dictionary "
                "of UI components."
            )

        self.components = components

    # ============================================================
    # COMPONENT ACCESS
    # ============================================================

    def get_component(
        self,
        name: str,
    ) -> Optional[Any]:
        """
        Return a UI component registered under ``name``.

        Parameters
        ----------
        name:
            Registry component identifier.

        Returns
        -------
        object | None
            Registered component, or None when no component with
            that identifier exists.
        """

        if not isinstance(
            name,
            str,
        ):
            raise TypeError(
                "component name must be a string."
            )

        name = name.strip()

        if not name:
            raise ValueError(
                "component name must not be empty."
            )

        return self.components.get(
            name
        )

    # ============================================================
    # DIAGNOSTICS
    # ============================================================

    def get_components(
        self,
    ) -> dict[str, Any]:
        """
        Return a detached mapping of registered UI components.

        The mapping itself is copied so callers cannot directly
        modify ``self.components``.
        """

        return self.components.copy()

    # ============================================================
    # REPRESENTATION
    # ============================================================

    def __repr__(
        self,
    ) -> str:
        """
        Return a concise diagnostic representation.
        """

        return (
            "MainWindow("
            f"components={len(self.components)}"
            ")"
        )


# ================================================================
# PUBLIC API
# ================================================================

__all__ = [
    "MainWindow",
]
