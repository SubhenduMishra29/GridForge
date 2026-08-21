# ============================================================

# File: ui/main_window.py

# GridForge V2 — Main Window

# ============================================================

"""
GridForge V2
============

Main application window and Qt workspace host.

MainWindow is the top-level Qt host for the GridForge UI.

It owns:
- the main Qt window;
- the central SLD/editor host;
- Qt docking infrastructure;
- the explicitly supplied UI Controller;
- the plugin-context attachment point;
- mechanical Qt operations required by WorkspaceRealizer.

It does NOT own:
- electrical/model state;
- WorkspaceDefinition;
- WorkspaceLayout;
- WorkspaceState;
- workspace policy;
- panel placement policy;
- panel registration;
- panel creation;
- workspace activation;
- WorkspaceRealizer orchestration.

Workspace policy belongs to the Workspace subsystem.

WorkspaceRealizer translates logical WorkspaceLayout decisions
into the host methods provided here.

PanelsPlugin remains responsible for panel composition and dock
creation, not workspace arrangement.
"""

from **future** import annotations

from typing import Optional

from ui.core.controller import Controller
from ui.core.plugin_registry import PluginRegistry
from ui.core.qt import (
QDockWidget,
QMainWindow,
Qt,
QWidget,
)
from ui.plugins.plugin_context import PluginContext

# ============================================================

# MainWindow

# ============================================================

class MainWindow(QMainWindow):
"""
Top-level GridForge Qt application window.

```
MainWindow is a Qt realization host.

It performs Qt operations requested by higher-level
orchestration but does not own workspace policy.
"""

def __init__(
    self,
    *,
    controller: Optional[Controller] = None,
    plugin_registry: Optional[PluginRegistry] = None,
    parent: Optional[QWidget] = None,
) -> None:
    """
    Construct the main application window.

    Dependencies are explicitly supplied.
    MainWindow does not construct application services.
    """

    super().__init__(parent)

    self._controller = controller
    self._plugin_registry = plugin_registry

    self._plugin_context: Optional[PluginContext] = None

    self._central_widget: Optional[QWidget] = None

    self._configure_window()
    self._create_central_host()

# ========================================================
# Window Configuration
# ========================================================

def _configure_window(self) -> None:
    """
    Configure intrinsic MainWindow properties only.

    Workspace arrangement is intentionally absent.
    """

    self.setWindowTitle(
        "GridForge V2"
    )

    self.resize(
        1600,
        1000,
    )

    self.setDockNestingEnabled(
        True
    )

# ========================================================
# Central Workspace / SLD Host
# ========================================================

def _create_central_host(self) -> None:
    """
    Create the central editor/SLD host.

    The central widget is a host only. SLD/editor composition
    belongs to the appropriate UI subsystem.
    """

    self._central_widget = QWidget(
        self
    )

    self._central_widget.setObjectName(
        "GridForgeCentralWorkspace"
    )

    self.setCentralWidget(
        self._central_widget
    )

# ========================================================
# Properties
# ========================================================

@property
def controller(
    self,
) -> Optional[Controller]:
    """Return the explicitly supplied UI Controller."""

    return self._controller

@property
def plugin_registry(
    self,
) -> Optional[PluginRegistry]:
    """Return the explicitly supplied PluginRegistry."""

    return self._plugin_registry

@property
def plugin_context(
    self,
) -> Optional[PluginContext]:
    """Return the current PluginContext."""

    return self._plugin_context

@property
def central_workspace(
    self,
) -> Optional[QWidget]:
    """Return the central SLD/editor host widget."""

    return self._central_widget

# ========================================================
# Plugin Context
# ========================================================

def set_plugin_context(
    self,
    context: PluginContext,
) -> None:
    """
    Attach an existing PluginContext.

    MainWindow does not create the context.
    """

    if context is None:
        raise ValueError(
            "context must not be None."
        )

    if not isinstance(
        context,
        PluginContext,
    ):
        raise TypeError(
            "context must be PluginContext."
        )

    self._plugin_context = context

# ========================================================
# Qt Workspace / Dock Host API
# ========================================================

def add_dock_widget(
    self,
    area: Qt.DockWidgetArea,
    dock_widget: QDockWidget,
) -> None:
    """
    Add an existing dock widget to the MainWindow.

    Workspace/Layout decides the logical area.
    MainWindow performs the Qt operation.
    """

    if not isinstance(
        area,
        Qt.DockWidgetArea,
    ):
        raise TypeError(
            "area must be Qt.DockWidgetArea."
        )

    if not isinstance(
        dock_widget,
        QDockWidget,
    ):
        raise TypeError(
            "dock_widget must be QDockWidget."
        )

    self.addDockWidget(
        area,
        dock_widget,
    )

# --------------------------------------------------------

def remove_dock_widget(
    self,
    dock_widget: QDockWidget,
) -> None:
    """
    Remove an existing dock widget from MainWindow.

    Removing a dock does not destroy the dock widget.
    """

    if not isinstance(
        dock_widget,
        QDockWidget,
    ):
        raise TypeError(
            "dock_widget must be QDockWidget."
        )

    self.removeDockWidget(
        dock_widget
    )

# --------------------------------------------------------

def tabify_dock_widgets(
    self,
    first: QDockWidget,
    second: QDockWidget,
) -> None:
    """
    Tabify two existing dock widgets.

    Workspace/Layout decides grouping.
    MainWindow performs the Qt operation.
    """

    if not isinstance(
        first,
        QDockWidget,
    ):
        raise TypeError(
            "first must be QDockWidget."
        )

    if not isinstance(
        second,
        QDockWidget,
    ):
        raise TypeError(
            "second must be QDockWidget."
        )

    if first is second:
        raise ValueError(
            "first and second dock widgets must be different."
        )

    self.tabifyDockWidget(
        first,
        second,
    )

# --------------------------------------------------------

def set_dock_visible(
    self,
    dock_widget: QDockWidget,
    visible: bool,
) -> None:
    """
    Set dock visibility.

    Visibility policy belongs to WorkspaceLayout.
    """

    if not isinstance(
        dock_widget,
        QDockWidget,
    ):
        raise TypeError(
            "dock_widget must be QDockWidget."
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

# --------------------------------------------------------

def set_dock_floating(
    self,
    dock_widget: QDockWidget,
    floating: bool,
) -> None:
    """
    Set dock floating state.

    Floating policy belongs to WorkspaceLayout.
    """

    if not isinstance(
        dock_widget,
        QDockWidget,
    ):
        raise TypeError(
            "dock_widget must be QDockWidget."
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
# Controller Integration
# ========================================================

def dispatch_command(
    self,
    command,
):
    """
    Dispatch a command through the existing Controller.
    """

    if self._controller is None:
        raise RuntimeError(
            "No Controller is attached to MainWindow."
        )

    return self._controller.dispatch(
        command
    )

# ========================================================
# Lifecycle
# ========================================================

def closeEvent(
    self,
    event,
) -> None:
    """
    Handle MainWindow shutdown.

    Application/service lifecycle remains outside MainWindow.
    """

    event.accept()
```

# ============================================================

# Public API

# ============================================================

**all** = [
"MainWindow",
]
