"""
Central registry for UI components.

Purpose:
    - Decouple component creation from MainWindow
    - Allow plug-and-play UI modules
"""

from ui.toolbars.main_toolbar import MainToolbar
from ui.docks.properties_dock import PropertiesDock
from ui.docks.layers_dock import LayersDock
from ui.status.status_bar import StatusBar


def build_ui(main_window, controller):
    """
    Compose all UI components.

    MainWindow calls ONLY this.
    """

    # ----------------------------------------
    # Toolbar
    # ----------------------------------------
    toolbar = MainToolbar(controller)
    main_window.addToolBar(toolbar)

    # ----------------------------------------
    # Docks
    # ----------------------------------------
    properties = PropertiesDock(controller)
    layers = LayersDock(controller)

    main_window.addDockWidget(main_window.RightDockWidgetArea, properties)
    main_window.addDockWidget(main_window.LeftDockWidgetArea, layers)

    # ----------------------------------------
    # Status Bar
    # ----------------------------------------
    status = StatusBar(controller)
    main_window.setStatusBar(status)

    return {
        "toolbar": toolbar,
        "properties": properties,
        "layers": layers,
        "status": status,
    }
