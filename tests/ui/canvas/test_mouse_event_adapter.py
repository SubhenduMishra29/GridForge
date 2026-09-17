# ============================================================
# GridForge V2 — Mouse Event Adapter Contract Tests
# ============================================================

from __future__ import annotations

from types import SimpleNamespace

from ui.canvas.mouse_event_adapter import MouseEventAdapter
from ui.core.qt import QPointF, Qt


class _ViewProbe:
    def mapToScene(self, position):
        return QPointF(position.x(), position.y())


class _SceneProbe:
    def items(self, position):
        return []


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
