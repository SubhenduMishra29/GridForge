"""
Main application window (ROOT UI CONTAINER)

Architecture Role:
------------------
This class is intentionally THIN.

It does NOT:
- create toolbars
- create docks
- create status bars
- import UI components

Instead, it delegates ALL UI construction to the plugin system.

Why?
----
To enforce a PLUGIN-BASED ARCHITECTURE where:
- UI components are decoupled
- Features are plug-and-play
- No file needs modification when adding new UI

Golden Rule:
------------
If you feel the urge to modify this file to add UI...
➡️ STOP — create a plugin instead.

Flow:
-----
MainWindow
    → build_ui()
        → loads registered plugins
            → each plugin attaches itself to the window

Result:
-------
self.components = {
    "toolbar": QToolBar,
    "properties": QDockWidget,
    ...
}
"""

from PySide6.QtWidgets import QMainWindow

# Central UI builder (plugin-driven)
from ui.ui_registry import build_ui


class MainWindow(QMainWindow):
    """
    Root application window.

    Responsibilities:
    - Own the Qt window
    - Initialize base window settings
    - Delegate UI construction
    - Store references to UI components

    It MUST remain simple and stable.
    """

    def __init__(self, controller):
        super().__init__()

        # Core app controller (business logic layer)
        self.controller = controller

        # Stores all UI components created by plugins
        # Example:
        # {
        #     "toolbar": MainToolbar,
        #     "layers": LayersDock,
        # }
        self.components = {}

        # Initialize window
        self._setup_window()

        # Build UI via plugin system
        self._build_ui()

    # ------------------------------------------------------------------
    # Window Setup
    # ------------------------------------------------------------------
    def _setup_window(self):
        """
        Configure base window properties.

        Keep this minimal — no UI logic here.
        """
        self.setWindowTitle("GridForge")
        self.resize(1200, 800)

    # ------------------------------------------------------------------
    # UI Construction (PLUGIN ENTRY POINT)
    # ------------------------------------------------------------------
    def _build_ui(self):
        """
        Build UI using plugin registry.

        This is the ONLY place where UI is assembled.

        What happens here:
        ------------------
        1. Registry discovers all plugins
        2. Each plugin builds its UI component
        3. Each plugin attaches itself to this window
        4. Components are collected into a dictionary

        Important:
        ----------
        - This method must NOT contain UI creation logic
        - Do NOT add widgets here
        - Do NOT import UI components here

        To add new UI:
        --------------
        1. Create a new plugin class
        2. Register it using @register
        3. Done — it will load automatically
        """

        self.components = build_ui(self, self.controller)

    # ------------------------------------------------------------------
    # Optional Helper Accessors
    # ------------------------------------------------------------------
    def get_component(self, name):
        """
        Safely retrieve a UI component by name.

        Example:
            toolbar = self.get_component("toolbar")
        """
        return self.components.get(name)
