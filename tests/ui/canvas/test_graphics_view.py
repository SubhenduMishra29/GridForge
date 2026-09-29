from __future__ import annotations

import pytest

from ui.canvas.graphics_view import GraphicsView
from ui.canvas.grid_scene import GridScene


class FakeController:
    pass


class FakeToolManager:
    pass


class FakeInteractionManager:
    def mouse_press(self, event): return True
    def mouse_move(self, event): return True
    def mouse_release(self, event): return True
    def mouse_double_click(self, event): return True
    def key_press(self, event): return True
    def key_release(self, event): return True


class FakeNavigationController:
    def handle_wheel(self, event): return True


@pytest.fixture
def canvas(qapp):
    return GraphicsView(FakeController(), FakeToolManager(), scene=GridScene())


def test_requires_controller(qapp):
    with pytest.raises(ValueError, match="controller must not be None"):
        GraphicsView(None, FakeToolManager(), scene=GridScene())


def test_requires_tool_manager(qapp):
    with pytest.raises(ValueError, match="tool_manager must not be None"):
        GraphicsView(FakeController(), None, scene=GridScene())


def test_requires_scene(qapp):
    with pytest.raises(ValueError, match="scene must not be None"):
        GraphicsView(FakeController(), FakeToolManager(), scene=None)


def test_initialization_uses_injected_canvas_services(canvas):
    assert canvas.controller is not None
    assert canvas.tool_manager is not None
    assert canvas.graphics_scene is canvas.scene()
    assert canvas.objectName() == "SLDCanvasView"
    assert canvas.hasMouseTracking() is True


def test_services_can_be_bound_once(canvas):
    interaction = FakeInteractionManager()
    navigation = FakeNavigationController()
    canvas.bind_services(interaction_manager=interaction, navigation_controller=navigation)
    assert canvas.interaction_manager is interaction
    assert canvas.navigation_controller is navigation


def test_service_binding_rejects_duplicate_binding(canvas):
    canvas.bind_services(interaction_manager=FakeInteractionManager(), navigation_controller=FakeNavigationController())
    with pytest.raises(RuntimeError):
        canvas.bind_services(interaction_manager=FakeInteractionManager(), navigation_controller=FakeNavigationController())


def test_service_binding_requires_both_services(canvas):
    with pytest.raises(ValueError):
        canvas.bind_services(interaction_manager=None, navigation_controller=FakeNavigationController())
    with pytest.raises(ValueError):
        canvas.bind_services(interaction_manager=FakeInteractionManager(), navigation_controller=None)


def test_dispose_releases_ui_service_references(canvas):
    canvas.bind_services(interaction_manager=FakeInteractionManager(), navigation_controller=FakeNavigationController())
    canvas.dispose()
    assert canvas.interaction_manager is None
    assert canvas.navigation_controller is None
    assert canvas.controller is None
    assert canvas.tool_manager is None
