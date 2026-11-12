# ============================================================
# GridForge V2 — Mouse Event Adapter Contract Tests
# ============================================================

from __future__ import annotations

from types import SimpleNamespace

from ui.canvas.mouse_event_adapter import MouseEventAdapter
from ui.core.qt import QPointF, QTransform, Qt


class _ViewProbe:
    def mapToScene(self, position):
        return QPointF(position.x(), position.y())

    def viewportTransform(self):
        return QTransform()


class _SceneProbe:
    def itemAt(self, x, y, transform=None):
        return None


def _adapter() -> MouseEventAdapter:
    return MouseEventAdapter(view=_ViewProbe(), scene=_SceneProbe())


def test_qt_keyboard_modifier_is_normalized_at_input_boundary():
    event = SimpleNamespace(
        position=lambda: QPointF(10.0, 20.0),
        button=lambda: Qt.MouseButton.LeftButton,
        buttons=lambda: Qt.MouseButton.LeftButton,
        modifiers=lambda: Qt.KeyboardModifier.ShiftModifier,
    )

    semantic = _adapter().adapt(event)

    assert semantic.modifiers == Qt.KeyboardModifier.ShiftModifier.value
    assert isinstance(semantic.modifiers, int)


def test_qt_mouse_button_is_normalized_at_input_boundary():
    event = SimpleNamespace(
        position=lambda: QPointF(10.0, 20.0),
        button=lambda: Qt.MouseButton.LeftButton,
        buttons=lambda: Qt.MouseButton.LeftButton | Qt.MouseButton.RightButton,
        modifiers=lambda: Qt.KeyboardModifier.NoModifier,
    )

    semantic = _adapter().adapt(event)

    assert semantic.button == Qt.MouseButton.LeftButton.value
    assert semantic.buttons == (
        Qt.MouseButton.LeftButton.value | Qt.MouseButton.RightButton.value
    )
    assert isinstance(semantic.button, int)
    assert isinstance(semantic.buttons, int)


def test_integer_semantic_flags_are_preserved():
    event = {
        "position": QPointF(10.0, 20.0),
        "button": 1,
        "buttons": 3,
        "modifiers": 0x02000000,
    }

    semantic = _adapter().adapt(event)

    assert semantic.button == 1
    assert semantic.buttons == 3
    assert semantic.modifiers == 0x02000000


def test_scene_mapping_and_snap_tolerance_follow_viewport_scale():
    class ZoomedView(_ViewProbe):
        def viewportTransform(self):
            transform = QTransform()
            transform.scale(0.25, 0.25)
            return transform

    adapter = MouseEventAdapter(view=ZoomedView(), scene=_SceneProbe())
    event = SimpleNamespace(
        position=lambda: QPointF(10.5, 20.5),
        button=lambda: Qt.MouseButton.LeftButton,
        buttons=lambda: Qt.MouseButton.LeftButton,
        modifiers=lambda: Qt.KeyboardModifier.NoModifier,
    )

    semantic = adapter.adapt(event)

    assert semantic.scene_position == QPointF(42.0, 82.0)
    assert semantic.snap_tolerance_scene == 56.0
