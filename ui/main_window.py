# ============================================================
# GridForge V2
# ============================================================
#
# File:
#     ui/main_window.py
#
# Purpose:
#     Main Qt application host.
#
# Author:
#     Subhendu Mishra
#
# Architectural boundary
# ----------------------
#
# MainWindow owns:
#     - Qt window construction;
#     - central application surface;
#     - dock-host mechanics;
#     - plugin registry reference;
#     - Presentation/UI Controller reference.
#
# MainWindow does NOT own:
#     - WorkspaceDefinition;
#     - WorkspaceLayout;
#     - WorkspaceState;
#     - WorkspaceManager;
#     - WorkspaceController;
#     - WorkspaceRealizer;
#     - Workspace activation;
#     - Workspace construction;
#     - Application/Core state.
#
# Workspace orchestration is supplied by the Presentation
# composition boundary. The Application layer is a future
# integration boundary and is intentionally not owned here.
#
# ============================================================

"""GridForge V2 Main Window.

MainWindow is deliberately a mechanical Qt host.
WorkspaceRealizer translates logical WorkspaceLayout objects
into host operations exposed by this class.
"""

from __future__ import annotations

from typing import Any

from ui.core.qt import (
    QDockWidget,
    QMainWindow,
    Qt,
    QWidget,
)

from ui.core.controller import Controller
from ui.plugins.plugin_registry import PluginRegistry


class MainWindow(QMainWindow):
    """Main GridForge application window.

    This class provides the host surface required by the UI
    subsystem and WorkspaceRealizer. It never constructs or
    activates a Workspace and does not own Application/Core state.
    """

    WINDOW_TITLE = "GridForge V2"
    WINDOW_MINIMUM_WIDTH = 1200
    WINDOW_MINIMUM_HEIGHT = 800

    def __init__(
        self,
        controller: Controller | None = None,
        plugin_registry: PluginRegistry | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._controller = controller
        self._plugin_registry = plugin_registry

        self._central_widget: QWidget | None = None

        self._initialize_window()
        self._initialize_central_surface()

    @property
    def controller(self) -> Controller | None:
        """Return the Presentation/UI controller reference."""
        return self._controller

    @property
    def plugin_registry(self) -> PluginRegistry | None:
        """Return the plugin registry reference."""
        return self._plugin_registry

    @property
    def central_surface(self) -> QWidget | None:
        """Return the central presentation surface."""
        return self._central_widget

    def _initialize_window(self) -> None:
        """Initialize basic Qt window properties."""
        self.setWindowTitle(self.WINDOW_TITLE)
        self.setMinimumSize(
            self.WINDOW_MINIMUM_WIDTH,
            self.WINDOW_MINIMUM_HEIGHT,
        )

    def _initialize_central_surface(self) -> None:
        """Initialize the central presentation surface."""
        central = QWidget(self)
        central.setObjectName("GridForgeCentralSurface")
        self._central_widget = central
        self.setCentralWidget(central)

    def add_dock_widget(
        self,
        area: Qt.DockWidgetArea,
        dock: QDockWidget,
    ) -> None:
        """Host an already-created dock widget."""
        self.addDockWidget(area, dock)

    def remove_dock_widget(
        self,
        dock: QDockWidget,
    ) -> None:
        """Remove a dock widget from the host."""
        self.removeDockWidget(dock)

    def set_dock_visible(
        self,
        dock: QDockWidget,
        visible: bool,
    ) -> None:
        """Set dock visibility without owning workspace policy."""
        dock.setVisible(visible)


__all__ = ["MainWindow"]
