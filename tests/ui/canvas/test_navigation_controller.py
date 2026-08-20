# ============================================================
# File: tests/ui/canvas/test_navigation_controller.py
# GridForge V2 — Navigation Controller Tests
# ============================================================
"""
Tests for:

    ui.canvas.navigation_controller.NavigationController

Test philosophy
---------------
These tests lock the public navigation contract without depending
on GridForge Core.

The controller is tested against lightweight Qt-compatible doubles
so that the tests remain focused on navigation mechanics:

    - zoom;
    - pan;
    - wheel navigation;
    - transform handling;
    - fit;
    - reset;
    - lifecycle;
    - diagnostics.

The tests intentionally verify that the controller does not require
domain/Core objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from ui.canvas.navigation_controller import (
    NavigationController,
)


# ============================================================
# TEST DOUBLES
# ============================================================


@dataclass
class FakePoint:
    _x: float
    _y: float

    def x(self) -> float:
        return self._x

    def y(self) -> float:
        return self._y

    def toPoint(self) -> "FakePoint":
        return self


@dataclass
class FakeRect:
    width_value: float = 100.0
    height_value: float = 100.0

    def center(self) -> FakePoint:
        return FakePoint(
            self.width_value / 2.0,
            self.height_value / 2.0,
        )

    def isNull(self) -> bool:
        return False

    def isEmpty(self) -> bool:
        return False


class FakeScrollBar:
    def __init__(
        self,
        value: int = 0,
    ) -> None:
        self._value = value

    def value(self) -> int:
        return self._value

    def setValue(
        self,
        value: int,
    ) -> None:
        self._value = int(value)


class FakeTransform:
    """
    Minimal QTransform-compatible test double.

    NavigationController requires:

        m11()
        m12()
        m21()
        m22()
    """

    def __init__(
        self,
        *,
        scale_x: float = 1.0,
        scale_y: float = 1.0,
        shear_x: float = 0.0,
        shear_y: float = 0.0,
    ) -> None:
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.shear_x = shear_x
        self.shear_y = shear_y

    def m11(self) -> float:
        return self.scale_x

    def m12(self) -> float:
        return self.shear_x

    def m21(self) -> float:
        return self.shear_y

    def m22(self) -> float:
        return self.scale_y


class FakeViewport:
    def __init__(
        self,
        width: int = 800,
        height: int = 600,
    ) -> None:
        self._width = width
        self._height = height

    def width(self) -> int:
        return self._width

    def height(self) -> int:
        return self._height

    def rect(self) -> FakeRect:
        return FakeRect(
            self._width,
            self._height,
        )


class FakeScene:
    def __init__(
        self,
        *,
        items: list[Any] | None = None,
        rect: FakeRect | None = None,
    ) -> None:
        self._items = (
            []
            if items is None
            else items
        )

        self._rect = (
            FakeRect()
            if rect is None
            else rect
        )

    def items(self) -> list[Any]:
        return list(self._items)

    def itemsBoundingRect(self) -> FakeRect:
        return self._rect


class FakeView:
    """
    Lightweight GraphicsView-compatible test double.

    The fake models the transform scale and scrollbar behavior
    relevant to NavigationController.
    """

    def __init__(
        self,
        *,
        width: int = 800,
        height: int = 600,
        scale: float = 1.0,
        scene: FakeScene | None = None,
    ) -> None:
        self._scale = float(scale)

        self._horizontal = FakeScrollBar()
        self._vertical = FakeScrollBar()

        self._viewport = FakeViewport(
            width,
            height,
        )

        self._scene = scene

        self.scale_calls: list[tuple[float, float]] = []
        self.fit_calls: list[tuple[Any, Any]] = []
        self.reset_transform_calls = 0
        self.set_transform_calls: list[Any] = []

        self._scene_offset_x = 0.0
        self._scene_offset_y = 0.0

    # --------------------------------------------------------
    # QGraphicsView-like API
    # --------------------------------------------------------

    def horizontalScrollBar(self) -> FakeScrollBar:
        return self._horizontal

    def verticalScrollBar(self) -> FakeScrollBar:
        return self._vertical

    def viewport(self) -> FakeViewport:
        return self._viewport

    def scene(self) -> FakeScene | None:
        return self._scene

    def transform(self) -> FakeTransform:
        return FakeTransform(
            scale_x=self._scale,
            scale_y=self._scale,
        )

    def scale(
        self,
        sx: float,
        sy: float,
    ) -> None:
        self.scale_calls.append(
            (
                float(sx),
                float(sy),
            )
        )

        assert sx == pytest.approx(sy)

        self._scale *= float(sx)

    def resetTransform(self) -> None:
        self.reset_transform_calls += 1
        self._scale = 1.0

    def setTransform(
        self,
        transform: FakeTransform,
    ) -> None:
        self.set_transform_calls.append(
            transform
        )

        self._scale = float(
            transform.m11()
        )

    def mapToScene(
        self,
        position: FakePoint,
    ) -> FakePoint:
        """
        Convert viewport coordinates to scene coordinates.

        Scrollbar values are represented as viewport translation.
        """

        return FakePoint(
            (
                position.x()
                + self._horizontal.value()
            )
            / self._scale,
            (
                position.y()
                + self._vertical.value()
            )
            / self._scale,
        )

    def mapFromScene(
        self,
        position: FakePoint,
    ) -> FakePoint:
        return FakePoint(
            position.x()
            * self._scale
            - self._horizontal.value(),
            position.y()
            * self._scale
            - self._vertical.value(),
        )

    def fitInView(
        self,
        rect: FakeRect,
        mode: Any,
    ) -> None:
        self.fit_calls.append(
            (
                rect,
                mode,
            )
        )

        # Simulate a deterministic fit scale.
        content_width = max(
            rect.width_value,
            1.0,
        )

        content_height = max(
            rect.height_value,
            1.0,
        )

        viewport_width = self._viewport.width()
        viewport_height = self._viewport.height()

        scale_x = (
            viewport_width
            / content_width
        )

        scale_y = (
            viewport_height
            / content_height
        )

        self._scale = min(
            scale_x,
            scale_y,
        )


class FakeAngleDelta:
    def __init__(
        self,
        value: Any,
    ) -> None:
        self._value = value

    def y(self) -> Any:
        return self._value


class FakeWheelEvent:
    def __init__(
        self,
        *,
        delta: Any = 120,
        position: FakePoint | None = None,
        provide_position: bool = True,
        accept_raises: bool = False,
    ) -> None:
        self._delta = delta
        self._position = position
        self._provide_position = provide_position
        self._accept_raises = accept_raises
        self.accepted = False

    def angleDelta(self) -> FakeAngleDelta:
        return FakeAngleDelta(
            self._delta
        )

    def position(self) -> FakePoint:
        if not self._provide_position:
            raise AttributeError(
                "position unavailable"
            )

        if self._position is None:
            return FakePoint(
                400.0,
                300.0,
            )

        return self._position

    def accept(self) -> None:
        if self._accept_raises:
            raise RuntimeError(
                "accept failed"
            )

        self.accepted = True


class FakeWheelEventWithoutPosition:
    def __init__(
        self,
        delta: Any = 120,
    ) -> None:
        self._delta = delta
        self.accepted = False

    def angleDelta(self) -> FakeAngleDelta:
        return FakeAngleDelta(
            self._delta
        )

    def accept(self) -> None:
        self.accepted = True


class FakeMalformedAngleDelta:
    def y(self) -> Any:
        return "invalid"


class FakeMalformedWheelEvent:
    def angleDelta(self) -> FakeMalformedAngleDelta:
        return FakeMalformedAngleDelta()


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def view() -> FakeView:
    return FakeView()


@pytest.fixture
def controller(
    view: FakeView,
) -> NavigationController:
    return NavigationController(
        view
    )


# ============================================================
# INITIALIZATION
# ============================================================


def test_controller_initializes(
    view: FakeView,
) -> None:
    controller = NavigationController(
        view
    )

    assert controller.get_view() is view
    assert controller.get_zoom_level() == pytest.approx(
        1.0
    )
    assert controller.is_panning is False


def test_controller_rejects_none_view() -> None:
    with pytest.raises(
        ValueError,
        match="view must not be None",
    ):
        NavigationController(
            None
        )


def test_controller_accepts_custom_zoom_configuration(
    view: FakeView,
) -> None:
    controller = NavigationController(
        view,
        zoom_factor=1.25,
        min_zoom=0.25,
        max_zoom=10.0,
    )

    assert controller.zoom_factor == pytest.approx(
        1.25
    )

    assert controller.min_zoom == pytest.approx(
        0.25
    )

    assert controller.max_zoom == pytest.approx(
        10.0
    )


@pytest.mark.parametrize(
    "kwargs, error, message",
    [
        (
            {"zoom_factor": True},
            TypeError,
            "zoom_factor must be numeric",
        ),
        (
            {"zoom_factor": 1.0},
            ValueError,
            "zoom_factor must be greater than 1.0",
        ),
        (
            {"zoom_factor": 0.5},
            ValueError,
            "zoom_factor must be greater than 1.0",
        ),
        (
            {"min_zoom": True},
            TypeError,
            "min_zoom must be numeric",
        ),
        (
            {"min_zoom": 0.0},
            ValueError,
            "min_zoom must be greater than zero",
        ),
        (
            {"max_zoom": 0.0},
            ValueError,
            "max_zoom must be greater than zero",
        ),
    ],
)
def test_controller_rejects_invalid_configuration(
    view: FakeView,
    kwargs: dict[str, Any],
    error: type[Exception],
    message: str,
) -> None:
    with pytest.raises(
        error,
        match=message,
    ):
        NavigationController(
            view,
            **kwargs,
        )


def test_controller_rejects_min_zoom_greater_than_max_zoom(
    view: FakeView,
) -> None:
    with pytest.raises(
        ValueError,
        match="min_zoom must not be greater than max_zoom",
    ):
        NavigationController(
            view,
            min_zoom=10.0,
            max_zoom=1.0,
        )


# ============================================================
# PAN
# ============================================================


def test_pan_initial_state(
    controller: NavigationController,
) -> None:
    assert controller.is_panning is False


def test_start_pan_sets_pan_state(
    controller: NavigationController,
) -> None:
    position = FakePoint(
        100.0,
        150.0,
    )

    controller.start_pan(
        position
    )

    assert controller.is_panning is True

    state = controller.get_state()

    assert state["is_panning"] is True
    assert state["has_pan_start"] is True


def test_start_pan_rejects_none(
    controller: NavigationController,
) -> None:
    with pytest.raises(
        ValueError,
        match="position must not be None",
    ):
        controller.start_pan(
            None
        )


@pytest.mark.parametrize(
    "position",
    [
        object(),
        type("NoX", (), {"y": lambda self: 1})(),
        type("NoY", (), {"x": lambda self: 1})(),
    ],
)
def test_start_pan_rejects_invalid_position(
    controller: NavigationController,
    position: Any,
) -> None:
    with pytest.raises(
        TypeError,
    ):
        controller.start_pan(
            position
        )


def test_update_pan_without_active_pan_is_ignored(
    controller: NavigationController,
    view: FakeView,
) -> None:
    controller.update_pan(
        FakePoint(
            200.0,
            250.0,
        )
    )

    assert view.horizontalScrollBar().value() == 0
    assert view.verticalScrollBar().value() == 0
    assert controller.is_panning is False


def test_update_pan_changes_scrollbars(
    controller: NavigationController,
    view: FakeView,
) -> None:
    view.horizontalScrollBar().setValue(100)
    view.verticalScrollBar().setValue(200)

    controller.start_pan(
        FakePoint(
            100.0,
            100.0,
        )
    )

    controller.update_pan(
        FakePoint(
            130.0,
            145.0,
        )
    )

    assert view.horizontalScrollBar().value() == 70
    assert view.verticalScrollBar().value() == 155
    assert controller.is_panning is True


def test_update_pan_uses_incremental_origin(
    controller: NavigationController,
    view: FakeView,
) -> None:
    controller.start_pan(
        FakePoint(
            100.0,
            100.0,
        )
    )

    controller.update_pan(
        FakePoint(
            120.0,
            110.0,
        )
    )

    controller.update_pan(
        FakePoint(
            135.0,
            125.0,
        )
    )

    assert view.horizontalScrollBar().value() == -35
    assert view.verticalScrollBar().value() == -25


def test_end_pan_clears_pan_state(
    controller: NavigationController,
) -> None:
    controller.start_pan(
        FakePoint(
            100.0,
            100.0,
        )
    )

    controller.end_pan()

    assert controller.is_panning is False

    state = controller.get_state()

    assert state["has_pan_start"] is False


def test_end_pan_is_idempotent(
    controller: NavigationController,
) -> None:
    controller.end_pan()
    controller.end_pan()

    assert controller.is_panning is False


# ============================================================
# ZOOM
# ============================================================


def test_zoom_in_one_step(
    controller: NavigationController,
    view: FakeView,
) -> None:
    controller.zoom_in()

    assert controller.get_zoom_level() == pytest.approx(
        1.15
    )

    assert view.transform().m11() == pytest.approx(
        1.15
    )


def test_zoom_out_one_step(
    controller: NavigationController,
    view: FakeView,
) -> None:
    controller.zoom_out()

    assert controller.get_zoom_level() == pytest.approx(
        1.0 / 1.15
    )

    assert view.transform().m11() == pytest.approx(
        1.0 / 1.15
    )


def test_zoom_in_multiple_steps(
    controller: NavigationController,
    view: FakeView,
) -> None:
    controller.zoom_in(
        3
    )

    expected = 1.15 ** 3

    assert controller.get_zoom_level() == pytest.approx(
        expected
    )

    assert view.transform().m11() == pytest.approx(
        expected
    )


def test_zoom_out_multiple_steps(
    controller: NavigationController,
    view: FakeView,
) -> None:
    controller.zoom_out(
        2
    )

    expected = 1.15 ** -2

    assert controller.get_zoom_level() == pytest.approx(
        expected
    )

    assert view.transform().m11() == pytest.approx(
        expected
    )


@pytest.mark.parametrize(
    "steps",
    [
        True,
        False,
        1.5,
        "1",
        None,
    ],
)
def test_zoom_in_rejects_non_integer_steps(
    controller: NavigationController,
    steps: Any,
) -> None:
    with pytest.raises(
        TypeError,
        match="steps must be an integer",
    ):
        controller.zoom_in(
            steps
        )


@pytest.mark.parametrize(
    "steps",
    [
        True,
        False,
        1.5,
        "1",
        None,
    ],
)
def test_zoom_out_rejects_non_integer_steps(
    controller: NavigationController,
    steps: Any,
) -> None:
    with pytest.raises(
        TypeError,
        match="steps must be an integer",
    ):
        controller.zoom_out(
            steps
        )


def test_zero_zoom_steps_do_nothing(
    controller: NavigationController,
    view: FakeView,
) -> None:
    controller.zoom_in(0)
    controller.zoom_out(0)

    assert controller.get_zoom_level() == pytest.approx(
        1.0
    )

    assert view.scale_calls == []


def test_zoom_is_clamped_at_maximum(
    view: FakeView,
) -> None:
    controller = NavigationController(
        view,
        max_zoom=2.0,
    )

    controller.zoom_in(
        100
    )

    assert controller.get_zoom_level() == pytest.approx(
        2.0
    )

    assert view.transform().m11() == pytest.approx(
        2.0
    )


def test_zoom_is_clamped_at_minimum(
    view: FakeView,
) -> None:
    controller = NavigationController(
        view,
        min_zoom=0.5,
    )

    controller.zoom_out(
        100
    )

    assert controller.get_zoom_level() == pytest.approx(
        0.5
    )

    assert view.transform().m11() == pytest.approx(
        0.5
    )


def test_set_zoom_level(
    controller: NavigationController,
    view: FakeView,
) -> None:
    controller.set_zoom_level(
        2.5
    )

    assert controller.get_zoom_level() == pytest.approx(
        2.5
    )

    assert view.transform().m11() == pytest.approx(
        2.5
    )


def test_set_zoom_level_clamps_high_value(
    view: FakeView,
) -> None:
    controller = NavigationController(
        view,
        max_zoom=3.0,
    )

    controller.set_zoom_level(
        100.0
    )

    assert controller.get_zoom_level() == pytest.approx(
        3.0
    )

    assert view.transform().m11() == pytest.approx(
        3.0
    )


def test_set_zoom_level_clamps_low_value(
    view: FakeView,
) -> None:
    controller = NavigationController(
        view,
        min_zoom=0.25,
    )

    controller.set_zoom_level(
        0.01
    )

    assert controller.get_zoom_level() == pytest.approx(
        0.25
    )

    assert view.transform().m11() == pytest.approx(
        0.25
    )


@pytest.mark.parametrize(
    "level",
    [
        True,
        False,
        "1.5",
        None,
    ],
)
def test_set_zoom_level_rejects_non_numeric(
    controller: NavigationController,
    level: Any,
) -> None:
    with pytest.raises(
        TypeError,
        match="level must be numeric",
    ):
        controller.set_zoom_level(
            level
        )


@pytest.mark.parametrize(
    "level",
    [
        0.0,
        -1.0,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_set_zoom_level_rejects_invalid_values(
    controller: NavigationController,
    level: float,
) -> None:
    with pytest.raises(
        ValueError,
    ):
        controller.set_zoom_level(
            level
        )


# ============================================================
# PROGRAMMATIC ZOOM ANCHOR
# ============================================================


def test_zoom_in_uses_viewport_center_anchor(
    controller: NavigationController,
    view: FakeView,
) -> None:
    controller.zoom_in()

    # The controller should perform anchored scaling rather
    # than merely calling scale() without compensating scroll.
    #
    # With the fake view's initial zero scrollbars, the center
    # remains geometrically stable.
    assert view.transform().m11() == pytest.approx(
        1.15
    )


def test_set_zoom_level_preserves_viewport_center(
    controller: NavigationController,
    view: FakeView,
) -> None:
    view.horizontalScrollBar().setValue(40)
    view.verticalScrollBar().setValue(30)

    center = view.viewport().rect().center()

    before = view.mapToScene(
        center
    )

    controller.set_zoom_level(
        2.0
    )

    after = view.mapToScene(
        center
    )

    assert after.x() == pytest.approx(
        before.x(),
        abs=1.0,
    )

    assert after.y() == pytest.approx(
        before.y(),
        abs=1.0,
    )


# ============================================================
# WHEEL
# ============================================================


def test_handle_wheel_positive_delta(
    controller: NavigationController,
    view: FakeView,
) -> None:
    event = FakeWheelEvent(
        delta=120,
        position=FakePoint(
            400.0,
            300.0,
        ),
    )

    consumed = controller.handle_wheel(
        event
    )

    assert consumed is True
    assert event.accepted is True

    assert controller.get_zoom_level() == pytest.approx(
        1.15
    )

    assert view.transform().m11() == pytest.approx(
        1.15
    )


def test_handle_wheel_negative_delta(
    controller: NavigationController,
) -> None:
    event = FakeWheelEvent(
        delta=-120,
        position=FakePoint(
            400.0,
            300.0,
        ),
    )

    consumed = controller.handle_wheel(
        event
    )

    assert consumed is True
    assert event.accepted is True

    assert controller.get_zoom_level() == pytest.approx(
        1.0 / 1.15
    )


def test_handle_wheel_multiple_steps(
    controller: NavigationController,
) -> None:
    event = FakeWheelEvent(
        delta=240,
        position=FakePoint(
            400.0,
            300.0,
        ),
    )

    assert controller.handle_wheel(
        event
    ) is True

    assert controller.get_zoom_level() == pytest.approx(
        1.15 ** 2
    )


def test_handle_wheel_zero_delta(
    controller: NavigationController,
) -> None:
    event = FakeWheelEvent(
        delta=0
    )

    assert controller.handle_wheel(
        event
    ) is False

    assert event.accepted is False
    assert controller.get_zoom_level() == pytest.approx(
        1.0
    )


def test_handle_wheel_none_event(
    controller: NavigationController,
) -> None:
    assert controller.handle_wheel(
        None
    ) is False


def test_handle_wheel_without_position_uses_center_zoom(
    controller: NavigationController,
) -> None:
    event = FakeWheelEventWithoutPosition(
        delta=120
    )

    consumed = controller.handle_wheel(
        event
    )

    assert consumed is True
    assert event.accepted is True
    assert controller.get_zoom_level() == pytest.approx(
        1.15
    )


def test_handle_wheel_rejects_malformed_delta(
    controller: NavigationController,
) -> None:
    event = FakeMalformedWheelEvent()

    assert controller.handle_wheel(
        event
    ) is False

    assert controller.get_zoom_level() == pytest.approx(
        1.0
    )


def test_handle_wheel_with_invalid_position_falls_back_to_center(
    controller: NavigationController,
) -> None:
    class InvalidPositionEvent:
        def angleDelta(self) -> FakeAngleDelta:
            return FakeAngleDelta(120)

        def position(self) -> object:
            return object()

        def accept(self) -> None:
            self.accepted = True

    event = InvalidPositionEvent()

    assert controller.handle_wheel(
        event
    ) is True

    assert controller.get_zoom_level() == pytest.approx(
        1.15
    )


# ============================================================
# RESET
# ============================================================


def test_reset_view(
    controller: NavigationController,
    view: FakeView,
) -> None:
    controller.zoom_in(
        4
    )

    controller.start_pan(
        FakePoint(
            100.0,
            100.0,
        )
    )

    controller.reset_view()

    assert controller.get_zoom_level() == pytest.approx(
        1.0
    )

    assert controller.is_panning is False

    assert view.transform().m11() == pytest.approx(
        1.0
    )

    assert view.reset_transform_calls == 1


def test_reset_view_clears_pan_start(
    controller: NavigationController,
) -> None:
    controller.start_pan(
        FakePoint(
            50.0,
            60.0,
        )
    )

    controller.reset_view()

    state = controller.get_state()

    assert state["has_pan_start"] is False


# ============================================================
# FIT CONTENT
# ============================================================


def test_fit_content_with_no_scene_does_nothing(
    controller: NavigationController,
    view: FakeView,
) -> None:
    view._scene = None

    controller.fit_content()

    assert view.fit_calls == []
    assert controller.get_zoom_level() == pytest.approx(
        1.0
    )


def test_fit_content_with_empty_scene_does_nothing(
    controller: NavigationController,
    view: FakeView,
) -> None:
    view._scene = FakeScene(
        items=[]
    )

    controller.fit_content()

    assert view.fit_calls == []
    assert controller.get_zoom_level() == pytest.approx(
        1.0
    )


def test_fit_content_with_empty_bounding_rect_does_nothing(
    controller: NavigationController,
    view: FakeView,
) -> None:
    class EmptyRect(FakeRect):
        def isEmpty(self) -> bool:
            return True

    view._scene = FakeScene(
        items=["bus"],
        rect=EmptyRect(),
    )

    controller.fit_content()

    assert view.fit_calls == []
    assert controller.get_zoom_level() == pytest.approx(
        1.0
    )


def test_fit_content_fits_scene(
    controller: NavigationController,
    view: FakeView,
) -> None:
    view._scene = FakeScene(
        items=["bus"],
        rect=FakeRect(
            width_value=400.0,
            height_value=300.0,
        ),
    )

    controller.fit_content(
        margin=0.0
    )

    assert len(
        view.fit_calls
    ) == 1

    assert controller.get_zoom_level() == pytest.approx(
        2.0
    )

    assert view.transform().m11() == pytest.approx(
        2.0
    )


def test_fit_content_applies_margin(
    controller: NavigationController,
    view: FakeView,
) -> None:
    view._scene = FakeScene(
        items=["bus"],
        rect=FakeRect(
            width_value=400.0,
            height_value=300.0,
        ),
    )

    controller.fit_content(
        margin=50.0
    )

    # View: 800 x 600
    # Content: 400 x 300
    #
    # Full fit = 2.0
    # Available viewport = 700 x 500
    # Margin factor = min(700/800, 500/600)
    #               = 5/6
    # Final scale = 2 * 5/6 = 5/3.
    assert controller.get_zoom_level() == pytest.approx(
        5.0 / 3.0
    )


def test_fit_content_rejects_negative_margin(
    controller: NavigationController,
) -> None:
    with pytest.raises(
        ValueError,
        match="margin must not be negative",
    ):
        controller.fit_content(
            margin=-1.0
        )


@pytest.mark.parametrize(
    "margin",
    [
        True,
        False,
        "50",
        None,
    ],
)
def test_fit_content_rejects_non_numeric_margin(
    controller: NavigationController,
    margin: Any,
) -> None:
    with pytest.raises(
        TypeError,
        match="margin must be numeric",
    ):
        controller.fit_content(
            margin
        )


@pytest.mark.parametrize(
    "margin",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_fit_content_rejects_non_finite_margin(
    controller: NavigationController,
    margin: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="margin must be finite",
    ):
        controller.fit_content(
            margin
        )


def test_fit_content_ends_active_pan(
    controller: NavigationController,
    view: FakeView,
) -> None:
    view._scene = FakeScene(
        items=["bus"],
        rect=FakeRect(
            width_value=400.0,
            height_value=300.0,
        ),
    )

    controller.start_pan(
        FakePoint(
            100.0,
            100.0,
        )
    )

    controller.fit_content()

    assert controller.is_panning is False

    assert controller.get_state()[
        "has_pan_start"
    ] is False


def test_fit_content_handles_viewport_too_small_for_margin(
    controller: NavigationController,
    view: FakeView,
) -> None:
    view._viewport = FakeViewport(
        width=100,
        height=100,
    )

    view._scene = FakeScene(
        items=["bus"],
        rect=FakeRect(
            width_value=50.0,
            height_value=50.0,
        ),
    )

    controller.fit_content(
        margin=60.0
    )

    # No fit should be attempted when the requested margin leaves
    # no usable viewport area.
    assert view.fit_calls == []


# ============================================================
# TRANSFORM
# ============================================================


def test_get_transform_returns_view_transform(
    controller: NavigationController,
    view: FakeView,
) -> None:
    transform = controller.get_transform()

    assert transform is view.transform() or (
        transform.m11()
        == pytest.approx(1.0)
    )


def test_set_transform_accepts_uniform_positive_scale(
    controller: NavigationController,
    view: FakeView,
) -> None:
    transform = FakeTransform(
        scale_x=2.0,
        scale_y=2.0,
    )

    controller.set_transform(
        transform
    )

    assert len(
        view.set_transform_calls
    ) == 1

    assert controller.get_zoom_level() == pytest.approx(
        2.0
    )

    assert view.transform().m11() == pytest.approx(
        2.0
    )


def test_set_transform_rejects_none(
    controller: NavigationController,
) -> None:
    with pytest.raises(
        ValueError,
        match="transform must not be None",
    ):
        controller.set_transform(
            None
        )


@pytest.mark.parametrize(
    "transform",
    [
        FakeTransform(
            scale_x=2.0,
            scale_y=1.0,
        ),
        FakeTransform(
            scale_x=1.0,
            scale_y=2.0,
        ),
    ],
)
def test_set_transform_rejects_non_uniform_scaling(
    controller: NavigationController,
    transform: FakeTransform,
) -> None:
    with pytest.raises(
        ValueError,
        match="uniform scaling",
    ):
        controller.set_transform(
            transform
        )


@pytest.mark.parametrize(
    "transform",
    [
        FakeTransform(
            scale_x=1.0,
            scale_y=1.0,
            shear_x=0.1,
        ),
        FakeTransform(
            scale_x=1.0,
            scale_y=1.0,
            shear_y=0.1,
        ),
    ],
)
def test_set_transform_rejects_rotation_or_shear(
    controller: NavigationController,
    transform: FakeTransform,
) -> None:
    with pytest.raises(
        ValueError,
        match="rotation or shear",
    ):
        controller.set_transform(
            transform
        )


@pytest.mark.parametrize(
    "scale",
    [
        0.0,
        -1.0,
    ],
)
def test_set_transform_rejects_non_positive_scale(
    controller: NavigationController,
    scale: float,
) -> None:
    transform = FakeTransform(
        scale_x=scale,
        scale_y=scale,
    )

    with pytest.raises(
        ValueError,
        match="positive scaling",
    ):
        controller.set_transform(
            transform
        )


def test_set_transform_clamps_to_maximum(
    view: FakeView,
) -> None:
    controller = NavigationController(
        view,
        max_zoom=2.0,
    )

    transform = FakeTransform(
        scale_x=5.0,
        scale_y=5.0,
    )

    controller.set_transform(
        transform
    )

    assert controller.get_zoom_level() == pytest.approx(
        2.0
    )

    assert view.transform().m11() == pytest.approx(
        2.0
    )


def test_set_transform_clamps_to_minimum(
    view: FakeView,
) -> None:
    controller = NavigationController(
        view,
        min_zoom=0.5,
    )

    transform = FakeTransform(
        scale_x=0.1,
        scale_y=0.1,
    )

    controller.set_transform(
        transform
    )

    assert controller.get_zoom_level() == pytest.approx(
        0.5
    )

    assert view.transform().m11() == pytest.approx(
        0.5
    )


# ============================================================
# ZOOM LIMITS
# ============================================================


def test_set_zoom_limits(
    controller: NavigationController,
) -> None:
    controller.set_zoom_limits(
        0.25,
        5.0,
    )

    assert controller.min_zoom == pytest.approx(
        0.25
    )

    assert controller.max_zoom == pytest.approx(
        5.0
    )


def test_set_zoom_limits_clamps_existing_zoom_down(
    controller: NavigationController,
    view: FakeView,
) -> None:
    controller.set_zoom_level(
        10.0
    )

    controller.set_zoom_limits(
        0.5,
        5.0,
    )

    assert controller.get_zoom_level() == pytest.approx(
        5.0
    )

    assert view.transform().m11() == pytest.approx(
        5.0
    )


def test_set_zoom_limits_clamps_existing_zoom_up(
    controller: NavigationController,
    view: FakeView,
) -> None:
    controller.set_zoom_level(
        0.5
    )

    controller.set_zoom_limits(
        1.0,
        10.0,
    )

    assert controller.get_zoom_level() == pytest.approx(
        1.0
    )

    assert view.transform().m11() == pytest.approx(
        1.0
    )


def test_set_zoom_limits_rejects_invalid_range(
    controller: NavigationController,
) -> None:
    with pytest.raises(
        ValueError,
        match="min_zoom must not be greater than max_zoom",
    ):
        controller.set_zoom_limits(
            10.0,
            1.0,
        )


# ============================================================
# DIAGNOSTICS
# ============================================================


def test_get_state(
    controller: NavigationController,
) -> None:
    state = controller.get_state()

    assert state == {
        "view": True,
        "zoom_level": pytest.approx(1.0),
        "zoom_factor": pytest.approx(1.15),
        "min_zoom": pytest.approx(0.10),
        "max_zoom": pytest.approx(20.0),
        "is_panning": False,
        "has_pan_start": False,
        "disposed": False,
    }


def test_repr(
    controller: NavigationController,
) -> None:
    result = repr(
        controller
    )

    assert result.startswith(
        "NavigationController("
    )

    assert "zoom=" in result
    assert "panning=False" in result


# ============================================================
# DISPOSAL
# ============================================================


def test_dispose_marks_controller_disposed(
    controller: NavigationController,
) -> None:
    controller.dispose()

    state = controller.get_state()

    assert state["disposed"] is True
    assert state["is_panning"] is False
    assert state["has_pan_start"] is False


def test_dispose_is_idempotent(
    controller: NavigationController,
) -> None:
    controller.dispose()
    controller.dispose()

    assert controller.get_state()["disposed"] is True


@pytest.mark.parametrize(
    "operation",
    [
        "start_pan",
        "update_pan",
        "zoom_in",
        "zoom_out",
        "set_zoom_level",
        "reset_view",
        "fit_content",
        "set_transform",
        "set_zoom_limits",
    ],
)
def test_operations_are_rejected_after_disposal(
    controller: NavigationController,
    operation: str,
) -> None:
    controller.dispose()

    with pytest.raises(
        RuntimeError,
        match="NavigationController has been disposed",
    ):
        if operation == "start_pan":
            controller.start_pan(
                FakePoint(
                    1.0,
                    1.0,
                )
            )

        elif operation == "update_pan":
            controller.update_pan(
                FakePoint(
                    1.0,
                    1.0,
                )
            )

        elif operation == "zoom_in":
            controller.zoom_in()

        elif operation == "zoom_out":
            controller.zoom_out()

        elif operation == "set_zoom_level":
            controller.set_zoom_level(
                2.0
            )

        elif operation == "reset_view":
            controller.reset_view()

        elif operation == "fit_content":
            controller.fit_content()

        elif operation == "set_transform":
            controller.set_transform(
                FakeTransform(
                    scale_x=2.0,
                    scale_y=2.0,
                )
            )

        elif operation == "set_zoom_limits":
            controller.set_zoom_limits(
                0.5,
                5.0,
            )


# ============================================================
# INTERNAL VALIDATION
# ============================================================


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        "1.15",
        None,
    ],
)
def test_validate_zoom_factor_rejects_non_numeric(
    value: Any,
) -> None:
    with pytest.raises(
        TypeError,
        match="zoom_factor must be numeric",
    ):
        NavigationController._validate_zoom_factor(
            value
        )


@pytest.mark.parametrize(
    "value",
    [
        1.0,
        0.0,
        -1.0,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_validate_zoom_factor_rejects_invalid_numeric(
    value: float,
) -> None:
    with pytest.raises(
        ValueError,
    ):
        NavigationController._validate_zoom_factor(
            value
        )


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        "1.0",
        None,
    ],
)
def test_validate_zoom_limit_rejects_non_numeric(
    value: Any,
) -> None:
    with pytest.raises(
        TypeError,
        match="min_zoom must be numeric",
    ):
        NavigationController._validate_zoom_limit(
            value,
            "min_zoom",
        )


@pytest.mark.parametrize(
    "value",
    [
        0.0,
        -1.0,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_validate_zoom_limit_rejects_invalid_numeric(
    value: float,
) -> None:
    with pytest.raises(
        ValueError,
    ):
        NavigationController._validate_zoom_limit(
            value,
            "min_zoom",
        )


# ============================================================
# PUBLIC API
# ============================================================


def test_public_api_exports_navigation_controller() -> None:
    namespace: dict[str, Any] = {}

    exec(
        "from ui.canvas.navigation_controller import "
        "NavigationController",
        namespace,
    )

    assert (
        namespace["NavigationController"]
        is NavigationController
    )


# ============================================================
# END OF TEST FILE
# ============================================================
