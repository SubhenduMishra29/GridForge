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
# Architectural boundary
# ----------------------
#
# MainWindow owns:
#     - Qt window construction;
#     - central application surface;
#     - dock-host mechanics;
#     - plugin registry reference;
#     - UI Controller reference.
#
# MainWindow does NOT own:
#     - WorkspaceDefinition;
#     - WorkspaceLayout;
#     - WorkspaceState;
#     - WorkspaceManager;
#     - WorkspaceController;
#     - WorkspaceRealizer;
#     - Workspace activation;
#     - Workspace construction.
#
# Workspace orchestration belongs to the application
# composition root.
#
# ============================================================

"""
GridForge V2 — Main Window.

MainWindow is deliberately a mechanical Qt host.

The application composition root owns Workspace orchestration.
WorkspaceRealizer translates logical WorkspaceLayout objects
into the host operations exposed by this class.
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
from ui.core.plugin_registry import PluginRegistry


class MainWindow(QMainWindow):
    """
    Main GridForge application window.

    This class provides the host surface required by the UI
    subsystem and WorkspaceRealizer.

    It never constructs or activates a Workspace.
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

    # ========================================================
    # PUBLIC PROPERTIES
    # ========================================================

    @property
    def controller(self) -> Controller | None:
        """
        Return the application UI controller.

        MainWindow does not create or own the controller.
        """

        return self._controller

    @property
    def plugin_registry(self) -> PluginRegistry | None:
        """
        Return the application plugin registry.

        MainWindow does not construct or manage Workspace
        services through the registry.
        """

        return self._plugin_registry

    @property
    def central_surface(self) -> QWidget | None:
        """
        Return the central application surface.

        For the current SLD-first workflow this is the central
        canvas/presentation surface.
        """

        return self._central_widget

    # ========================================================
    # WINDOW INITIALIZATION
    # ========================================================

    def _initialize_window(self) -> None:
        """Initialize basic Qt window properties."""

        self.setWindowTitle(
            self.WINDOW_TITLE
        )

        self.setMinimumSize(
            self.WINDOW_MINIMUM_WIDTH,
            self.WINDOW_MINIMUM_HEIGHT,
        )

    def _initialize_central_surface(self) -> None:
        """
        Initialize the central application surface.

        The concrete SLD/canvas widget may be supplied later by
        the application composition/plugin layer.

        No Workspace definition is constructed here.
        """

        central = QWidget(self)

        central.setObjectName(
            "GridForgeCentralSurface"
        )

        self._central_widget = central

        self.setCentralWidget(
            central
        )

    # ========================================================
    # CENTRAL SURFACE
    # ========================================================

    def set_central_surface(
        self,
        widget: QWidget,
    ) -> None:
        """
        Replace the central application surface.

        This is a host operation only.
        """

        if not isinstance(
            widget,
            QWidget,
        ):
            raise TypeError(
                "widget must be QWidget."
            )

        if widget is self._central_widget:
            return

        old_widget = self._central_widget

        self._central_widget = widget

        self.setCentralWidget(
            widget
        )

        if old_widget is not None:
            old_widget.deleteLater()

    # ========================================================
    # DOCK HOST API
    # ========================================================
    #
    # These methods are intentionally mechanical.
    #
    # WorkspaceRealizer is responsible for deciding WHEN and
    # WHY these operations happen.
    #
    # ========================================================

    def add_dock_widget(
        self,
        area: Qt.DockWidgetArea,
        dock_widget: QDockWidget,
    ) -> None:
        """
        Add a dock widget to the requested Qt dock area.

        WorkspaceRealizer supplies the area.
        """

        self._validate_dock(
            dock_widget
        )

        if not isinstance(
            area,
            Qt.DockWidgetArea,
        ):
            raise TypeError(
                "area must be Qt.DockWidgetArea."
            )

        self.addDockWidget(
            area,
            dock_widget,
        )

    def remove_dock_widget(
        self,
        dock_widget: QDockWidget,
    ) -> None:
        """
        Remove a dock widget from the main window.

        This does not delete the dock object.
        """

        self._validate_dock(
            dock_widget
        )

        self.removeDockWidget(
            dock_widget
        )

    def tabify_dock_widgets(
        self,
        first: QDockWidget,
        second: QDockWidget,
    ) -> None:
        """
        Tabify two existing dock widgets.

        WorkspaceRealizer determines the logical tab group.
        """

        self._validate_dock(
            first
        )

        self._validate_dock(
            second
        )

        if first is second:
            raise ValueError(
                "Cannot tabify a dock widget with itself."
            )

        self.tabifyDockWidget(
            first,
            second,
        )

    def set_dock_visible(
        self,
        dock_widget: QDockWidget,
        visible: bool,
    ) -> None:
        """
        Set dock visibility.

        Visibility policy originates from WorkspaceRealizer.
        """

        self._validate_dock(
            dock_widget
        )

        if not isinstance(
            visible,
            bool,
        ):
            raise TypeError(
                "visible must be bool."
            )

        dock_widget.setVisible(
            visible
        )

    def set_dock_floating(
        self,
        dock_widget: QDockWidget,
        floating: bool,
    ) -> None:
        """
        Set dock floating state.

        Floating policy originates from WorkspaceRealizer.
        """

        self._validate_dock(
            dock_widget
        )

        if not isinstance(
            floating,
            bool,
        ):
            raise TypeError(
                "floating must be bool."
            )

        dock_widget.setFloating(
            floating
        )

    # ========================================================
    # OPTIONAL LOW-LEVEL HOST HELPERS
    # ========================================================

    def dock_area(
        self,
        dock_widget: QDockWidget,
    ) -> Qt.DockWidgetArea:
        """
        Return the current Qt dock area.

        This is observational host state only.
        """

        self._validate_dock(
            dock_widget
        )

        return self.dockWidgetArea(
            dock_widget
        )

    def is_dock_floating(
        self,
        dock_widget: QDockWidget,
    ) -> bool:
        """
        Return whether a dock is currently floating.
        """

        self._validate_dock(
            dock_widget
        )

        return dock_widget.isFloating()

    def is_dock_visible(
        self,
        dock_widget: QDockWidget,
    ) -> bool:
        """
        Return whether a dock is currently visible.
        """

        self._validate_dock(
            dock_widget
        )

        return dock_widget.isVisible()

    # ========================================================
    # GENERIC HOST ACCESS
    # ========================================================

    def find_dock(
        self,
        object_name: str,
    ) -> QDockWidget | None:
        """
        Find a dock by Qt object name.

        This is a host lookup only and has no Workspace meaning.
        """

        if not isinstance(
            object_name,
            str,
        ):
            raise TypeError(
                "object_name must be a string."
            )

        if not object_name.strip():
            raise ValueError(
                "object_name must not be empty."
            )

        widget = self.findChild(
            QDockWidget,
            object_name,
        )

        return widget

    # ========================================================
    # STATE / DEBUG
    # ========================================================

    def get_state(self) -> dict[str, Any]:
        """
        Return a lightweight host/UI state snapshot.

        Workspace logical state is deliberately excluded.
        """

        return {
            "window_title": self.windowTitle(),
            "visible": self.isVisible(),
            "enabled": self.isEnabled(),
            "central_surface": (
                self._central_widget.objectName()
                if self._central_widget is not None
                else None
            ),
            "has_controller": (
                self._controller is not None
            ),
            "has_plugin_registry": (
                self._plugin_registry is not None
            ),
        }

    # ========================================================
    # INTERNAL VALIDATION
    # ========================================================

    @staticmethod
    def _validate_dock(
        dock_widget: QDockWidget,
    ) -> None:
        """Validate a QDockWidget argument."""

        if not isinstance(
            dock_widget,
            QDockWidget,
        ):
            raise TypeError(
                "dock_widget must be QDockWidget."
            )


__all__ = [
    "MainWindow",
]
