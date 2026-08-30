from __future__ import annotations

import pytest

from ui.core.qt import QApplication, QDockWidget, QMainWindow
from ui.plugins.panels_plugin import PanelsPlugin, PluginContext


def _application() -> QApplication:
    application = QApplication.instance()
    if application is None:
        application = QApplication([])
    return application


def test_initialize_registers_canonical_default_panels() -> None:
    _application()
    window = QMainWindow()
    plugin = PanelsPlugin()
    context = PluginContext(main_window=window)

    plugin.initialize(context)

    assert plugin.panel_ids == (
        "project",
        "equipment",
        "properties",
    )

    for panel_id in plugin.panel_ids:
        dock = plugin.get_dock(panel_id)
        assert isinstance(dock, QDockWidget)
        assert dock.objectName() == panel_id

    first_docks = tuple(plugin.get_dock(panel_id) for panel_id in plugin.panel_ids)

    plugin.initialize(context)

    assert tuple(plugin.get_dock(panel_id) for panel_id in plugin.panel_ids) == first_docks

    plugin.shutdown()
    window.close()


def test_initialize_requires_main_window() -> None:
    _application()
    plugin = PanelsPlugin()

    with pytest.raises(ValueError):
        plugin.initialize(PluginContext())
