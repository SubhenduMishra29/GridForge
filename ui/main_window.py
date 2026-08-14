```python
# ============================================================
# File: ui/main_window.py
# GridForge V2 — Main Application Window
# ============================================================
"""
GridForge V2 — Main Application Window
======================================

Root Qt window for the GridForge application.

Responsibilities
----------------
MainWindow is the top-level UI container.

It is responsible for:

    - owning the top-level Qt window;
    - retaining the UI Controller reference;
    - configuring minimal window properties;
    - delegating UI composition to ui_registry;
    - retaining references to constructed UI components.

MainWindow does NOT:

    - own Core/domain state;
    - perform business logic;
    - perform electrical calculations;
    - create tools;
    - manage tool lifecycle;
    - perform canvas interaction;
    - perform rendering;
    - construct individual panels;
    - construct toolbars;
    - construct the status bar;
    - perform filesystem operations;
    - create Commands;
    - directly mutate the Core model.

UI Composition
--------------
UI construction is delegated to:

    ui.ui_registry.build_ui()

The registry obtains registered UI plugins and asks them to
construct their components.

The resulting component instances are stored in:

    self.components

Controller Boundary
-------------------
The Controller is injected into MainWindow.

MainWindow retains the reference but does not become the owner
of application/domain state.

Qt Architecture
---------------
All Qt imports pass through:

    ui.core.qt

No direct PySide6/PyQt imports are permitted in this module.

Dependency Direction
--------------------

    Application
        |
        v
    Controller
        |
        v
    MainWindow
        |
        v
    UI Registry
        |
        v
    UI Plugins
        |
        +---- Panels
        +---- Toolbars
        +---- Status
        +---- Canvas
        +---- Other UI components
"""

from __future__ import annotations

from typing import Any

from ui.core.qt import (
    QMainWindow,
)

from ui.ui_registry import build_ui


class MainWindow(QMainWindow):
    """
    Root application window for GridForge.

    MainWindow deliberately contains no feature-specific UI
    construction logic.

    Its stable responsibilities are:

        1. Own the top-level Qt window.
        2. Retain the Controller reference.
        3. Configure basic window properties.
        4. Delegate UI composition to the UI Registry.
        5. Retain constructed component references.
    """

    # ========================================================
    # INITIALIZATION
    # ========================================================

    def __init__(
        self,
        controller: Any,
    ) -> None:
        """
        Initialize the GridForge main window.

        Parameters
        ----------
        controller:
            Existing GridForge UI/application controller.

        Raises
        ------
        ValueError
            If controller is None.
        """

        if controller is None:
            raise ValueError(
                "controller must not be None."
            )

        super().__init__()

        # ----------------------------------------------------
        # Controller reference
        # ----------------------------------------------------
        #
        # MainWindow does not own controller state.
        # It merely retains the injected reference.
        # ----------------------------------------------------

        self.controller = controller

        # ----------------------------------------------------
        # Constructed UI components
        # ----------------------------------------------------
        #
        # The UI Registry owns composition.
        # MainWindow owns only these references for access.
        # ----------------------------------------------------

        self.components: dict[str, Any] = {}

        # ----------------------------------------------------
        # Basic window configuration
        # ----------------------------------------------------

        self._setup_window()

        # ----------------------------------------------------
        # Plugin-driven UI construction
        # ----------------------------------------------------

        self._build_ui()

    # ========================================================
    # WINDOW SETUP
    # ========================================================

    def _setup_window(
        self,
    ) -> None:
        """
        Configure minimal root-window properties.

        Feature-specific widgets must not be created here.
        """

        self.setWindowTitle(
            "GridForge"
        )

        self.resize(
            1200,
            800,
        )

    # ========================================================
    # UI COMPOSITION
    # ========================================================

    def _build_ui(
        self,
    ) -> None:
        """
        Build the UI through the central UI Registry.

        The registry is responsible for:

            - obtaining registered UI plugins;
            - ordering plugins;
            - constructing their components;
            - returning component references.

        MainWindow only stores the resulting mapping.
        """

        components = build_ui(
            self,
            self.controller,
        )

        if not isinstance(
            components,
            dict,
        ):
            raise TypeError(
                "build_ui() must return a dictionary "
                "of UI components."
            )

        self.components = components

    # ========================================================
    # COMPONENT ACCESS
    # ========================================================

    def get_component(
        self,
        name: str,
    ) -> Any | None:
        """
        Return a registered UI component.

        Parameters
        ----------
        name:
            Component identifier assigned by the UI plugin.

        Returns
        -------
        object | None
            The registered component, or None when absent.
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

    # ========================================================
    # COMPONENT SNAPSHOT
    # ========================================================

    def get_components(
        self,
    ) -> dict[str, Any]:
        """
        Return a detached mapping of UI components.

        The returned dictionary can be modified by the caller
        without modifying MainWindow's component registry.
        """

        return dict(
            self.components
        )

    # ========================================================
    # COMPONENT PRESENCE
    # ========================================================

    def has_component(
        self,
        name: str,
    ) -> bool:
        """
        Return whether a component is registered.
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

        return name in self.components

    # ========================================================
    # DIAGNOSTICS
    # ========================================================

    def get_state(
        self,
    ) -> dict[str, Any]:
        """
        Return diagnostic state for the main window.

        This method does not expose or mutate domain state.
        """

        return {
            "window_title": self.windowTitle(),
            "component_count": len(
                self.components
            ),
            "component_names": list(
                self.components.keys()
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
            "MainWindow("
            f"components={len(self.components)}"
            ")"
        )


# ============================================================
# PUBLIC API
# ============================================================

__all__ = [
    "MainWindow",
]
```
