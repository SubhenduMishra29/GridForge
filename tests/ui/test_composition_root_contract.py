# ============================================================
# GridForge V2 — Composition Root Contract Tests
# ============================================================

from __future__ import annotations

from core.application.bootstrap import create_application
from core.network.network import Network
from ui.canvas.canvas_composition import CanvasComposer
from ui.core.controller import Controller
from ui.core.tool_manager import ToolManager


def _application():
    return create_application(Network())


def test_controller_retains_canonical_application_instance():
    application = _application()

    controller = Controller(application=application)

    assert controller.application is application
    assert not hasattr(controller, "gridforge_application")


def test_tool_manager_retains_canonical_dependency_instances():
    application = _application()
    controller = Controller(application=application)
    selection_manager = object()
    snap_system = object()

    tool_manager = ToolManager(
        controller=controller,
        application=application,
        selection_manager=selection_manager,
        snap_system=snap_system,
    )

    assert tool_manager.controller is controller
    assert tool_manager.application is application
    assert tool_manager.selection_manager is selection_manager
    assert tool_manager.snap_system is snap_system


def test_canvas_preparation_creates_single_shared_selection_and_snap_instances():
    application = _application()
    controller = Controller(application=application)
    composer = CanvasComposer()

    preparation = composer.prepare(controller=controller)

    assert preparation.selection_manager is not None
    assert preparation.snap_system is not None
    assert preparation.scene is not None
    assert preparation.grid_system is not None


def test_canvas_composition_uses_prepared_selection_and_snap_instances(monkeypatch):
    application = _application()
    controller = Controller(application=application)
    composer = CanvasComposer()
    preparation = composer.prepare(controller=controller)

    tool_manager = ToolManager(
        controller=controller,
        application=application,
        selection_manager=preparation.selection_manager,
        snap_system=preparation.snap_system,
    )

    composition = composer.compose(
        controller=controller,
        tool_manager=tool_manager,
        preparation=preparation,
        parent=None,
    )

    assert composition.selection_manager is preparation.selection_manager
    assert composition.snap_system is preparation.snap_system
    assert tool_manager.selection_manager is composition.selection_manager
    assert tool_manager.snap_system is composition.snap_system
