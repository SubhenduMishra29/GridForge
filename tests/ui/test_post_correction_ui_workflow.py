# ============================================================
# GridForge V2 — Post-Correction UI Workflow Regression Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from types import SimpleNamespace

from ui.core.tool_manager import ToolManager
from ui.plugins.plugin_context import PluginContext


class _Tool:
    def __init__(self, events):
        self.events = events
        self.is_active = False

    def activate(self):
        self.is_active = True

    def deactivate(self):
        self.is_active = False

    def mouse_move(self, event):
        self.events.append(("mouse_move", event))
        return True

    def mouse_press(self, event):
        self.events.append(("mouse_press", event))
        return True

    def mouse_release(self, event):
        self.events.append(("mouse_release", event))
        return True

    def mouse_double_click(self, event):
        self.events.append(("mouse_double_click", event))
        return True

    def key_press(self, event):
        self.events.append(("key_press", event))
        return True

    def key_release(self, event):
        self.events.append(("key_release", event))
        return True

    def cancel(self):
        self.events.append(("cancel", None))
        return True

    def reset(self):
        self.events.append(("reset", None))

    def dispose(self):
        self.is_active = False


def _manager(events):
    manager = ToolManager(
        controller=object(),
        application=object(),
        selection_manager=object(),
        snap_system=object(),
    )
    manager.register_tool("probe", lambda **_: _Tool(events))
    manager.activate("probe")
    return manager


def test_canonical_tool_manager_routes_double_click():
    events = []
    manager = _manager(events)
    semantic_event = SimpleNamespace(event_type=4, button=1, buttons=1, modifiers=0)

    assert manager.mouse_double_click(semantic_event) is True
    assert events == [("mouse_double_click", semantic_event)]


def test_canonical_tool_manager_routes_all_canvas_input_events():
    events = []
    manager = _manager(events)
    semantic_event = SimpleNamespace(event_type=0, button=1, buttons=1, modifiers=0)

    assert manager.mouse_move(semantic_event)
    assert manager.mouse_press(semantic_event)
    assert manager.mouse_release(semantic_event)
    assert manager.key_press(semantic_event)
    assert manager.key_release(semantic_event)

    assert [name for name, _ in events] == [
        "mouse_move",
        "mouse_press",
        "mouse_release",
        "key_press",
        "key_release",
    ]


def test_plugin_context_has_one_canonical_application_dependency():
    application = object()
    context = PluginContext(application=application)

    assert context.application is application
    assert not hasattr(context, "gridforge_application")
