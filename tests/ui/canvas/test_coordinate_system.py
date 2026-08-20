# ============================================================
# GridForge V2
# ============================================================
# File:
#     tests/ui/canvas/test_coordinate_system.py
#
# Purpose:
#     Contract tests for the canonical SLD CoordinateSystem.
# ============================================================

from __future__ import annotations

import math

import pytest

from ui.canvas.coordinate_system import CoordinateSystem
from ui.core.qt import QPointF


# ============================================================
# TEST DOUBLES
# ============================================================


class FakeViewportPosition:
    """
    Minimal QPointF-like mouse position exposing toPoint().
    """

    def __init__(
        self,
        x: float,
        y: float,
    ) -> None:
        self._x = float(x)
        self._y = float(y)

    def x(self) -> float:
        return self._x

    def y(self) -> float:
        return self._y

    def toPoint(self):
        return QPointF(
            self._x,
            self._y,
        )


class FakeView:
    """
    Minimal QGraphicsView-compatible transformation boundary.
    """

    def mapToScene(
        self,
        position,
    ):
        return QPointF(
            position.x() + 100.0,
            position.y() + 200.0,
        )

    def mapFromScene(
        self,
        position,
    ):
        return QPointF(
            position.x() - 100.0,
            position.y() - 200.0,
        )


class FakeGridSystem:
    """
    Minimal GridSystem-compatible geometric resolver.
    """

    def __init__(self):
        self.calls = []

    def snap_point(
        self,
        point,
    ):
        self.calls.append(
            QPointF(
                point.x(),
                point.y(),
            )
        )

        return QPointF(
            round(point.x() / 10.0) * 10.0,
            round(point.y() / 10.0) * 10.0,
        )


class FakeItem:
    """
    Minimal graphical item coordinate contract.
    """

    def mapToScene(
        self,
        point,
    ):
        return QPointF(
            point.x() + 50.0,
            point.y() + 75.0,
        )

    def mapFromScene(
        self,
        point,
    ):
        return QPointF(
            point.x() - 50.0,
            point.y() - 75.0,
        )


# ============================================================
# INITIALIZATION
# ============================================================


def test_initial_state():
    view = FakeView()

    coordinate_system = CoordinateSystem(
        view
    )

    assert coordinate_system.view is view
    assert coordinate_system.grid_system is None
    assert coordinate_system.decimals == 2
    assert coordinate_system.unit == ""

    assert coordinate_system.get_state() == {
        "decimals": 2,
        "unit": "",
        "has_grid_system": False,
    }


def test_initialization_rejects_missing_view():
    with pytest.raises(
        ValueError,
        match="view must not be None",
    ):
        CoordinateSystem(None)


def test_initialization_rejects_invalid_view():
    with pytest.raises(
        TypeError,
        match="mapToScene",
    ):
        CoordinateSystem(
            object()
        )


def test_initialization_rejects_invalid_grid_system():
    with pytest.raises(
        TypeError,
        match="snap_point",
    ):
        CoordinateSystem(
            FakeView(),
            object(),
        )


# ============================================================
# VIEWPORT / SCENE
# ============================================================


def test_viewport_to_scene():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    result = coordinate_system.viewport_to_scene(
        QPointF(
            10.0,
            20.0,
        )
    )

    assert result.x() == pytest.approx(
        110.0
    )

    assert result.y() == pytest.approx(
        220.0
    )


def test_scene_to_viewport():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    result = coordinate_system.scene_to_viewport(
        QPointF(
            110.0,
            220.0,
        )
    )

    assert result.x() == pytest.approx(
        10.0
    )

    assert result.y() == pytest.approx(
        20.0
    )


def test_viewport_scene_round_trip():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    original = QPointF(
        125.0,
        240.0,
    )

    scene = coordinate_system.viewport_to_scene(
        original
    )

    viewport = coordinate_system.scene_to_viewport(
        scene
    )

    assert viewport.x() == pytest.approx(
        original.x()
    )

    assert viewport.y() == pytest.approx(
        original.y()
    )


# ============================================================
# GRID
# ============================================================


def test_scene_to_grid_without_grid_system():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    result = coordinate_system.scene_to_grid(
        QPointF(
            123.5,
            87.25,
        )
    )

    assert result.x() == pytest.approx(
        123.5
    )

    assert result.y() == pytest.approx(
        87.25
    )


def test_scene_to_grid_uses_grid_system():
    grid = FakeGridSystem()

    coordinate_system = CoordinateSystem(
        FakeView(),
        grid,
    )

    result = coordinate_system.scene_to_grid(
        QPointF(
            123.0,
            87.0,
        )
    )

    assert result.x() == pytest.approx(
        120.0
    )

    assert result.y() == pytest.approx(
        90.0
    )

    assert len(grid.calls) == 1


def test_viewport_to_grid():
    grid = FakeGridSystem()

    coordinate_system = CoordinateSystem(
        FakeView(),
        grid,
    )

    result = coordinate_system.viewport_to_grid(
        QPointF(
            23.0,
            34.0,
        )
    )

    # viewport → scene:
    # (23, 34) → (123, 234)
    #
    # scene → grid:
    # (123, 234) → (120, 230)

    assert result.x() == pytest.approx(
        120.0
    )

    assert result.y() == pytest.approx(
        230.0
    )


def test_grid_to_scene_is_explicit_identity():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    result = coordinate_system.grid_to_scene(
        QPointF(
            120.0,
            230.0,
        )
    )

    assert result.x() == pytest.approx(
        120.0
    )

    assert result.y() == pytest.approx(
        230.0
    )


def test_grid_to_viewport():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    result = coordinate_system.grid_to_viewport(
        QPointF(
            120.0,
            230.0,
        )
    )

    assert result.x() == pytest.approx(
        20.0
    )

    assert result.y() == pytest.approx(
        30.0
    )


def test_set_and_get_grid_system():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    grid = FakeGridSystem()

    coordinate_system.set_grid_system(
        grid
    )

    assert coordinate_system.get_grid_system() is grid
    assert coordinate_system.grid_system is grid


def test_grid_system_can_be_detached():
    grid = FakeGridSystem()

    coordinate_system = CoordinateSystem(
        FakeView(),
        grid,
    )

    coordinate_system.set_grid_system(
        None
    )

    assert coordinate_system.grid_system is None


# ============================================================
# ITEM LOCAL / SCENE
# ============================================================


def test_local_to_scene():
    item = FakeItem()

    result = CoordinateSystem.local_to_scene(
        item,
        QPointF(
            10.0,
            20.0,
        )
    )

    assert result.x() == pytest.approx(
        60.0
    )

    assert result.y() == pytest.approx(
        95.0
    )


def test_scene_to_local():
    item = FakeItem()

    result = CoordinateSystem.scene_to_local(
        item,
        QPointF(
            60.0,
            95.0,
        )
    )

    assert result.x() == pytest.approx(
        10.0
    )

    assert result.y() == pytest.approx(
        20.0
    )


def test_local_scene_round_trip():
    item = FakeItem()

    local = QPointF(
        12.5,
        27.5,
    )

    scene = CoordinateSystem.local_to_scene(
        item,
        local,
    )

    result = CoordinateSystem.scene_to_local(
        item,
        scene,
    )

    assert result.x() == pytest.approx(
        local.x()
    )

    assert result.y() == pytest.approx(
        local.y()
    )


# ============================================================
# POSITION ALIASES
# ============================================================


def test_current_scene_position():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    result = coordinate_system.current_scene_position(
        QPointF(
            5.0,
            15.0,
        )
    )

    assert result.x() == pytest.approx(
        105.0
    )

    assert result.y() == pytest.approx(
        215.0
    )


def test_current_grid_position():
    coordinate_system = CoordinateSystem(
        FakeView(),
        FakeGridSystem(),
    )

    result = coordinate_system.current_grid_position(
        QPointF(
            5.0,
            15.0,
        )
    )

    assert result.x() == pytest.approx(
        110.0
    )

    assert result.y() == pytest.approx(
        220.0
    )


# ============================================================
# GEOMETRY
# ============================================================


def test_distance():
    result = CoordinateSystem.distance(
        QPointF(
            0.0,
            0.0,
        ),
        QPointF(
            3.0,
            4.0,
        ),
    )

    assert result == pytest.approx(
        5.0
    )


def test_midpoint():
    result = CoordinateSystem.midpoint(
        QPointF(
            0.0,
            10.0,
        ),
        QPointF(
            20.0,
            30.0,
        ),
    )

    assert result.x() == pytest.approx(
        10.0
    )

    assert result.y() == pytest.approx(
        20.0
    )


def test_offset():
    result = CoordinateSystem.offset(
        QPointF(
            10.0,
            20.0,
        ),
        5.0,
        -7.5,
    )

    assert result.x() == pytest.approx(
        15.0
    )

    assert result.y() == pytest.approx(
        12.5
    )


def test_offset_rejects_non_numeric_dx():
    with pytest.raises(
        TypeError,
        match="dx must be numeric",
    ):
        CoordinateSystem.offset(
            QPointF(
                0.0,
                0.0,
            ),
            "5",
            0.0,
        )


def test_offset_rejects_non_numeric_dy():
    with pytest.raises(
        TypeError,
        match="dy must be numeric",
    ):
        CoordinateSystem.offset(
            QPointF(
                0.0,
                0.0,
            ),
            0.0,
            "5",
        )


# ============================================================
# FORMATTING
# ============================================================


def test_default_format_position():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    result = coordinate_system.format_position(
        QPointF(
            125.123,
            80.456,
        )
    )

    assert result == (
        "X: 125.12    Y: 80.46"
    )


def test_default_format_point():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    result = coordinate_system.format_point(
        QPointF(
            125.123,
            80.456,
        )
    )

    assert result == (
        "(125.12, 80.46)"
    )


def test_set_decimals():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    coordinate_system.set_decimals(
        4
    )

    assert coordinate_system.decimals == 4

    assert coordinate_system.format_point(
        QPointF(
            1.23456,
            7.89123,
        )
    ) == "(1.2346, 7.8912)"


def test_set_decimals_rejects_bool():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    with pytest.raises(
        TypeError,
        match="decimals",
    ):
        coordinate_system.set_decimals(
            True
        )


def test_set_decimals_rejects_negative():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        coordinate_system.set_decimals(
            -1
        )


def test_set_unit():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    coordinate_system.set_unit(
        " mm "
    )

    assert coordinate_system.unit == "mm"

    assert coordinate_system.format_point(
        QPointF(
            10.0,
            20.0,
        )
    ) == "(10.00, 20.00) mm"


def test_set_unit_rejects_non_string():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    with pytest.raises(
        TypeError,
        match="unit must be a string",
    ):
        coordinate_system.set_unit(
            10
        )


# ============================================================
# STATUS BAR
# ============================================================


def test_status_data_without_grid():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    result = coordinate_system.get_status_data(
        QPointF(
            10.0,
            20.0,
        )
    )

    assert result["scene"].x() == pytest.approx(
        110.0
    )

    assert result["scene"].y() == pytest.approx(
        220.0
    )

    assert result["grid"].x() == pytest.approx(
        110.0
    )

    assert result["grid"].y() == pytest.approx(
        220.0
    )

    assert result["scene_text"] == (
        "X: 110.00    Y: 220.00"
    )

    assert result["grid_text"] == (
        "X: 110.00    Y: 220.00"
    )


def test_status_data_with_grid():
    coordinate_system = CoordinateSystem(
        FakeView(),
        FakeGridSystem(),
    )

    result = coordinate_system.get_status_data(
        QPointF(
            13.0,
            27.0,
        )
    )

    assert result["scene"].x() == pytest.approx(
        113.0
    )

    assert result["scene"].y() == pytest.approx(
        227.0
    )

    assert result["grid"].x() == pytest.approx(
        110.0
    )

    assert result["grid"].y() == pytest.approx(
        230.0
    )


# ============================================================
# VALIDATION
# ============================================================


@pytest.mark.parametrize(
    "method_name",
    [
        "viewport_to_scene",
        "scene_to_viewport",
        "viewport_to_grid",
        "scene_to_grid",
        "grid_to_scene",
        "grid_to_viewport",
        "current_scene_position",
        "current_grid_position",
    ],
)
def test_point_methods_reject_none(
    method_name,
):
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    method = getattr(
        coordinate_system,
        method_name,
    )

    with pytest.raises(
        ValueError,
        match="must not be None",
    ):
        method(None)


def test_local_to_scene_rejects_missing_item():
    with pytest.raises(
        ValueError,
        match="item must not be None",
    ):
        CoordinateSystem.local_to_scene(
            None,
            QPointF(
                0.0,
                0.0,
            ),
        )


def test_scene_to_local_rejects_missing_item():
    with pytest.raises(
        ValueError,
        match="item must not be None",
    ):
        CoordinateSystem.scene_to_local(
            None,
            QPointF(
                0.0,
                0.0,
            ),
        )


def test_distance_rejects_invalid_point():
    with pytest.raises(
        TypeError,
        match="first must provide x",
    ):
        CoordinateSystem.distance(
            object(),
            QPointF(
                0.0,
                0.0,
            ),
        )


def test_grid_system_replacement_validates_contract():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    with pytest.raises(
        TypeError,
        match="snap_point",
    ):
        coordinate_system.set_grid_system(
            object()
        )


# ============================================================
# DIAGNOSTICS / REPRESENTATION
# ============================================================


def test_get_state_updates():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    coordinate_system.set_decimals(
        3
    )

    coordinate_system.set_unit(
        "scene"
    )

    coordinate_system.set_grid_system(
        FakeGridSystem()
    )

    assert coordinate_system.get_state() == {
        "decimals": 3,
        "unit": "scene",
        "has_grid_system": True,
    }


def test_repr():
    coordinate_system = CoordinateSystem(
        FakeView()
    )

    representation = repr(
        coordinate_system
    )

    assert representation.startswith(
        "CoordinateSystem("
    )

    assert "decimals=2" in representation
    assert "unit=''" in representation
    assert "grid_system=False" in representation
