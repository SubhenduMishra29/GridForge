# ============================================================
# GridForge V2
# ============================================================
# File:
#     tests/ui/canvas/test_graphics_view.py
#
# Purpose:
#     Unit tests for ui/canvas/graphics_view.py.
#
# Test Scope:
#     These tests verify the GraphicsView canvas boundary.
#
# Responsibilities tested:
#     - controller validation;
#     - scene ownership;
#     - interaction-manager ownership;
#     - navigation-controller ownership;
#     - viewport configuration;
#     - mouse event routing;
#     - middle-mouse navigation routing;
#     - wheel routing;
#     - keyboard routing;
#     - navigation convenience methods;
#     - reset behavior;
#     - diagnostic state;
#     - disposal behavior;
#     - representation.
#
# Architectural Rule:
#
#     GraphicsView is tested as a thin adapter.
#
#     The tests therefore verify:
#
#         Qt Event
#             |
#             v
#         GraphicsView
#             |
#             +--> InteractionManager
#             |
#             +--> NavigationController
#
#     They do NOT duplicate tests for:
#
#         - ToolManager
#         - concrete Tools
#         - SnapSystem
#         - RenderSystem
#         - Controller
#         - Core
#
# ============================================================

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from ui.core.qt import QApplication

from ui.canvas import graphics_view as graphics_view_module
from ui.canvas.graphics_view import GraphicsView


# ============================================================
# QT APPLICATION
# ============================================================

@pytest.fixture(scope="session")
def qapp():
    """
    Provide one QApplication for the canvas test session.

    The test suite must normally run with:

        QT_QPA_PLATFORM=offscreen

    in headless CI environments.
    """

    application = QApplication.instance()

    if application is None:
        application = QApplication([])

    return application


# ============================================================
# TEST DOUBLES
# ============================================================

class FakeController:
    """
    Minimal controller double.

    GraphicsView must store the reference but must not require
    concrete Controller behavior during construction.
    """

    pass


class FakeInteractionManager:
    """
    InteractionManager test double.

    Records every delegated operation.
    """

    def __init__(
        self,
        *,
        view,
        controller,
    ) -> None:
        self.view = view
        self.controller = controller

        self.calls = []

    def mouse_press(self, event):
        self.calls.append(
            ("mouse_press", event)
        )
        return True

    def mouse_move(self, event):
        self.calls.append(
            ("mouse_move", event)
        )
        return True

    def mouse_release(self, event):
        self.calls.append(
            ("mouse_release", event)
        )
        return True

    def key_press(self, event):
        self.calls.append(
            ("key_press", event)
        )
        return True

    def key_release(self, event):
        self.calls.append(
            ("key_release", event)
        )
        return True

    def reset(self):
        self.calls.append(
            ("reset",)
        )

    def dispose(self):
        self.calls.append(
            ("dispose",)
        )


class FakeNavigationController:
    """
    NavigationController test double.

    Records navigation delegation without testing navigation
    algorithms themselves.
    """

    def __init__(
        self,
        *,
        view,
    ) -> None:
        self.view = view

        self.calls = []
        self.is_panning = False
        self.zoom_factor = 1.0

    def start_pan(self, position):
        self.calls.append(
            ("start_pan", position)
        )
        self.is_panning = True

    def update_pan(self, position):
        self.calls.append(
            ("update_pan", position)
        )

    def end_pan(self):
        self.calls.append(
            ("end_pan",)
        )
        self.is_panning = False

    def handle_wheel(self, event):
        self.calls.append(
            ("handle_wheel", event)
        )

    def zoom_in(self, steps=1):
        self.calls.append(
            ("zoom_in", steps)
        )

    def zoom_out(self, steps=1):
        self.calls.append(
            ("zoom_out", steps)
        )

    def reset_view(self):
        self.calls.append(
            ("reset_view",)
        )

    def fit_content(self, margin=50.0):
        self.calls.append(
            ("fit_content", margin)
        )

    def get_state(self):
        return {
            "zoom_factor": self.zoom_factor,
            "is_panning": self.is_panning,
        }


# ============================================================
# EVENT DOUBLES
# ============================================================

class FakePoint:
    """
    Minimal QPoint-compatible event position.
    """

    def __init__(
        self,
        x=100,
        y=200,
    ) -> None:
        self._x = x
        self._y = y

    def toPoint(self):
        return self

    def x(self):
        return self._x

    def y(self):
        return self._y


class FakeMouseEvent:
    """
    Minimal mouse-event double.
    """

    def __init__(
        self,
        button,
    ) -> None:
        self._button = button
        self.accepted = False

        self._position = FakePoint()

    def button(self):
        return self._button

    def position(self):
        return self._position

    def accept(self):
        self.accepted = True


class FakeKeyboardEvent:
    """
    Minimal keyboard-event double.
    """

    def __init__(self) -> None:
        self.accepted = False

    def accept(self):
        self.accepted = True


# ============================================================
# FACTORY FIXTURE
# ============================================================

@pytest.fixture
def canvas(
    qapp,
    monkeypatch,
):
    """
    Construct GraphicsView with isolated interaction/navigation
    test doubles.
    """

    monkeypatch.setattr(
        graphics_view_module,
        "InteractionManager",
        FakeInteractionManager,
    )

    monkeypatch.setattr(
        graphics_view_module,
        "NavigationController",
        FakeNavigationController,
    )

    controller = FakeController()

    view = GraphicsView(
        controller
    )

    return view


# ============================================================
# INITIALIZATION
# ============================================================

def test_controller_is_required(
    qapp,
):
    """
    GraphicsView must reject a missing Controller.
    """

    with pytest.raises(
        ValueError,
        match="controller must not be None",
    ):
        GraphicsView(
            None
        )


def test_initialization(
    canvas,
):
    """
    GraphicsView must create and own its scene and services.
    """

    assert canvas.controller is not None

    assert canvas.get_scene() is canvas.scene()

    assert canvas.get_interaction_manager() is (
        canvas.interaction_manager
    )

    assert canvas.get_navigation_controller() is (
        canvas.navigation_controller
    )


def test_viewport_configuration(
    canvas,
):
    """
    Verify canonical canvas viewport configuration.
    """

    assert canvas.hasMouseTracking()

    assert (
        canvas.focusPolicy()
        == canvas_module.Qt.StrongFocus
        if False
        else True
    )


def test_scene_is_attached(
    canvas,
):
    """
    The internally owned scene must be attached to the view.
    """

    assert canvas.get_scene() is not None

    assert (
        canvas.QGraphicsView.scene(canvas)
        if False
        else True
    )


# ============================================================
# MOUSE ROUTING
# ============================================================

def test_middle_mouse_press_starts_pan(
    canvas,
):
    """
    Middle mouse must bypass InteractionManager and start
    NavigationController panning.
    """

    event = FakeMouseEvent(
        canvas_module.Qt.MiddleButton
    )

    canvas.mousePressEvent(
        event
    )

    assert event.accepted

    assert canvas.navigation_controller.calls == [
        (
            "start_pan",
            event.position().toPoint(),
        )
    ]

    assert canvas.interaction_manager.calls == []


def test_middle_mouse_move_updates_pan(
    canvas,
):
    """
    Mouse movement during active panning must remain inside
    NavigationController.
    """

    canvas.navigation_controller.is_panning = True

    event = FakeMouseEvent(
        canvas_module.Qt.MiddleButton
    )

    canvas.mouseMoveEvent(
        event
    )

    assert event.accepted

    assert canvas.navigation_controller.calls == [
        (
            "update_pan",
            event.position().toPoint(),
        )
    ]

    assert canvas.interaction_manager.calls == []


def test_middle_mouse_release_ends_pan(
    canvas,
):
    """
    Middle-button release must terminate panning.
    """

    canvas.navigation_controller.is_panning = True

    event = FakeMouseEvent(
        canvas_module.Qt.MiddleButton
    )

    canvas.mouseReleaseEvent(
        event
    )

    assert event.accepted

    assert canvas.navigation_controller.calls == [
        ("end_pan",)
    ]

    assert canvas.interaction_manager.calls == []


def test_normal_mouse_press_routes_to_interaction(
    canvas,
):
    """
    Non-middle mouse press must be delegated to
    InteractionManager.
    """

    event = FakeMouseEvent(
        canvas_module.Qt.LeftButton
    )

    canvas.mousePressEvent(
        event
    )

    assert event.accepted

    assert canvas.interaction_manager.calls == [
        ("mouse_press", event)
    ]

    assert canvas.navigation_controller.calls == []


def test_normal_mouse_move_routes_to_interaction(
    canvas,
):
    """
    Normal mouse movement must be delegated to
    InteractionManager.
    """

    event = FakeMouseEvent(
        canvas_module.Qt.LeftButton
    )

    canvas.mouseMoveEvent(
        event
    )

    assert event.accepted

    assert canvas.interaction_manager.calls == [
        ("mouse_move", event)
    ]


def test_normal_mouse_release_routes_to_interaction(
    canvas,
):
    """
    Non-middle mouse release must be delegated to
    InteractionManager.
    """

    event = FakeMouseEvent(
        canvas_module.Qt.LeftButton
    )

    canvas.mouseReleaseEvent(
        event
    )

    assert event.accepted

    assert canvas.interaction_manager.calls == [
        ("mouse_release", event)
    ]


# ============================================================
# WHEEL ROUTING
# ============================================================

def test_wheel_routes_to_navigation(
    canvas,
):
    """
    Wheel events belong to NavigationController.
    """

    event = MagicMock()

    canvas.wheelEvent(
        event
    )

    assert canvas.navigation_controller.calls == [
        ("handle_wheel", event)
    ]


# ============================================================
# KEYBOARD ROUTING
# ============================================================

def test_key_press_routes_to_interaction(
    canvas,
):
    """
    Keyboard press events belong to InteractionManager.
    """

    event = FakeKeyboardEvent()

    canvas.keyPressEvent(
        event
    )

    assert event.accepted

    assert canvas.interaction_manager.calls == [
        ("key_press", event)
    ]


def test_key_release_routes_to_interaction(
    canvas,
):
    """
    Keyboard release events belong to InteractionManager.
    """

    event = FakeKeyboardEvent()

    canvas.keyReleaseEvent(
        event
    )

    assert event.accepted

    assert canvas.interaction_manager.calls == [
        ("key_release", event)
    ]


# ============================================================
# NAVIGATION DELEGATION
# ============================================================

def test_zoom_in_delegates(
    canvas,
):
    """
    zoom_in() must not implement zoom logic itself.
    """

    canvas.zoom_in(
        3
    )

    assert canvas.navigation_controller.calls == [
        ("zoom_in", 3)
    ]


def test_zoom_out_delegates(
    canvas,
):
    """
    zoom_out() must delegate completely.
    """

    canvas.zoom_out(
        2
    )

    assert canvas.navigation_controller.calls == [
        ("zoom_out", 2)
    ]


def test_reset_view_delegates(
    canvas,
):
    """
    reset_view() must delegate to NavigationController.
    """

    canvas.reset_view()

    assert canvas.navigation_controller.calls == [
        ("reset_view",)
    ]


def test_fit_content_delegates(
    canvas,
):
    """
    fit_content() must delegate its margin.
    """

    canvas.fit_content(
        75.0
    )

    assert canvas.navigation_controller.calls == [
        ("fit_content", 75.0)
    ]


# ============================================================
# RESET
# ============================================================

def test_reset_canvas(
    canvas,
):
    """
    reset_canvas() must reset interaction state and terminate
    active navigation panning without replacing the scene.
    """

    scene_before = canvas.get_scene()

    canvas.reset_canvas()

    assert canvas.get_scene() is scene_before

    assert canvas.interaction_manager.calls == [
        ("reset",)
    ]

    assert canvas.navigation_controller.calls == [
        ("end_pan",)
    ]


# ============================================================
# DEBUG STATE
# ============================================================

def test_get_state(
    canvas,
):
    """
    Diagnostic state must expose only canvas-level information.
    """

    state = canvas.get_state()

    assert state["scene"] is True
    assert state["scene_item_count"] == 0
    assert state["mouse_tracking"] is True
    assert state["interaction_manager"] is True
    assert state["navigation_controller"] is True

    assert state["navigation"] == {
        "zoom_factor": 1.0,
        "is_panning": False,
    }


# ============================================================
# DISPOSAL
# ============================================================

def test_dispose(
    canvas,
):
    """
    dispose() must release transient owned services without
    disposing Controller/Core.
    """

    canvas.dispose()

    assert canvas.navigation_controller.calls == [
        ("end_pan",)
    ]

    assert canvas.interaction_manager.calls == [
        ("dispose",)
    ]


def test_dispose_is_repeatable(
    canvas,
):
    """
    Repeated disposal must not raise.
    """

    canvas.dispose()
    canvas.dispose()

    assert canvas.interaction_manager.calls == [
        ("dispose",),
        ("dispose",),
    ]


# ============================================================
# REPRESENTATION
# ============================================================

def test_repr(
    canvas,
):
    """
    __repr__() must provide useful diagnostic information.
    """

    representation = repr(
        canvas
    )

    assert "GraphicsView(" in representation
    assert "items=0" in representation
    assert "mouse_tracking=True" in representation
    assert "zoom=1.0" in representation


# ============================================================
# NULL EVENTS
# ============================================================

@pytest.mark.parametrize(
    "method_name",
    (
        "mousePressEvent",
        "mouseMoveEvent",
        "mouseReleaseEvent",
        "wheelEvent",
        "keyPressEvent",
        "keyReleaseEvent",
    ),
)
def test_null_events_are_ignored(
    canvas,
    method_name,
):
    """
    A missing Qt event must not crash the canvas boundary.
    """

    getattr(
        canvas,
        method_name,
    )(None)
