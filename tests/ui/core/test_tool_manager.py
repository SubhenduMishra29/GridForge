# ============================================================
# File: tests/ui/core/test_tool_manager.py
# GridForge V2 — ToolManager Tests
# ============================================================

from __future__ import annotations

import pytest

from ui.core.tool_manager import ToolManager


# ============================================================
# TEST DOUBLES
# ============================================================


class FakeController:
    """Minimal Controller double implementing the canonical API."""

    def __init__(self) -> None:
        self.subscriptions: dict[str, list] = {}
        self.unsubscribe_calls: list[tuple[str, object]] = []

    def subscribe(self, event_name, callback) -> None:
        self.subscriptions.setdefault(
            event_name,
            [],
        ).append(callback)

    def unsubscribe(self, event_name, callback) -> None:
        callbacks = self.subscriptions.get(
            event_name,
            [],
        )

        if callback in callbacks:
            callbacks.remove(callback)

        self.unsubscribe_calls.append(
            (event_name, callback)
        )

    def emit(
        self,
        event_name,
        *args,
        **kwargs,
    ) -> None:
        for callback in tuple(
            self.subscriptions.get(
                event_name,
                [],
            )
        ):
            callback(
                *args,
                **kwargs,
            )


class FakePreview:
    """Minimal PreviewLayer double."""

    def __init__(self) -> None:
        self.clear_count = 0

    def clear(self) -> None:
        self.clear_count += 1


class FakeTool:
    """Lifecycle-aware concrete tool double."""

    def __init__(
        self,
        interaction_manager=None,
        preview=None,
    ) -> None:
        self.interaction_manager = interaction_manager
        self.preview = preview

        self.activate_count = 0
        self.deactivate_count = 0
        self.cancel_count = 0
        self.reset_count = 0
        self.dispose_count = 0

        self.fail_activate = False
        self.fail_deactivate = False
        self.fail_dispose = False

        self.cancel_result = None

    def activate(self) -> None:
        self.activate_count += 1

        if self.fail_activate:
            raise RuntimeError(
                "activation failure"
            )

    def deactivate(self) -> None:
        self.deactivate_count += 1

        if self.fail_deactivate:
            raise RuntimeError(
                "deactivation failure"
            )

    def cancel(self):
        self.cancel_count += 1
        return self.cancel_result

    def reset(self) -> None:
        self.reset_count += 1

    def dispose(self) -> None:
        self.dispose_count += 1

        if self.fail_dispose:
            raise RuntimeError(
                "disposal failure"
            )


class FailingConstructorTool:
    """Tool whose constructor fails with TypeError."""

    def __init__(
        self,
        interaction_manager=None,
        preview=None,
    ) -> None:
        raise TypeError(
            "constructor-internal failure"
        )


class NoneFactory:
    """Callable returning None."""

    def __call__(
        self,
        interaction_manager=None,
        preview=None,
    ):
        return None


class FactoryRecorder:
    """Factory recording canonical constructor arguments."""

    def __init__(self) -> None:
        self.calls = []

    def __call__(
        self,
        *,
        interaction_manager,
        preview,
    ):
        tool = FakeTool(
            interaction_manager=interaction_manager,
            preview=preview,
        )

        self.calls.append(
            (
                interaction_manager,
                preview,
                tool,
            )
        )

        return tool


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture
def controller():
    return FakeController()


@pytest.fixture
def preview():
    return FakePreview()


@pytest.fixture
def interaction_manager():
    return object()


@pytest.fixture
def manager(
    controller,
    interaction_manager,
    preview,
):
    return ToolManager(
        controller=controller,
        interaction_manager=interaction_manager,
        preview=preview,
    )


# ============================================================
# INITIALIZATION
# ============================================================


def test_requires_controller():
    with pytest.raises(
        ValueError,
        match="controller must not be None",
    ):
        ToolManager(
            controller=None
        )


def test_requires_controller_subscribe():
    class InvalidController:
        pass

    with pytest.raises(
        TypeError,
        match="controller must provide subscribe",
    ):
        ToolManager(
            controller=InvalidController()
        )


def test_initial_state(
    manager,
):
    assert manager.active_tool is None
    assert manager.active_tool_id is None

    state = manager.get_state()

    assert state["connected"] is True
    assert state["disposed"] is False
    assert state["registered_tools"] == ()
    assert state["instantiated_tools"] == ()
    assert state["active_tool_id"] is None
    assert state["has_active_tool"] is False


def test_subscribes_to_controller(
    manager,
    controller,
):
    callbacks = controller.subscriptions[
        "tool_changed"
    ]

    assert len(callbacks) == 1
    assert callbacks[0] == manager._on_tool_changed


# ============================================================
# REGISTRATION
# ============================================================


def test_register_tool(
    manager,
):
    factory = FakeTool

    manager.register_tool(
        "select",
        factory,
    )

    assert manager.has_tool("select")
    assert manager.get_tool_ids() == (
        "select",
    )


def test_register_tool_is_lazy(
    manager,
):
    recorder = FactoryRecorder()

    manager.register_tool(
        "select",
        recorder,
    )

    assert recorder.calls == []
    assert manager.get_state()[
        "instantiated_tools"
    ] == ()


def test_register_tool_rejects_duplicate(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    with pytest.raises(
        ValueError,
        match="Tool already registered",
    ):
        manager.register_tool(
            "select",
            FakeTool,
        )


def test_register_tool_requires_callable(
    manager,
):
    with pytest.raises(
        TypeError,
        match="factory must be callable",
    ):
        manager.register_tool(
            "select",
            object(),
        )


@pytest.mark.parametrize(
    "tool_id, expected_exception",
    [
        (None, TypeError),
        (123, TypeError),
        ("", ValueError),
        ("   ", ValueError),
    ],
)
def test_register_tool_validates_tool_id(
    manager,
    tool_id,
    expected_exception,
):
    with pytest.raises(
        expected_exception
    ):
        manager.register_tool(
            tool_id,
            FakeTool,
        )


def test_register_tools_is_atomic(
    manager,
):
    manager.register_tool(
        "existing",
        FakeTool,
    )

    with pytest.raises(
        ValueError,
        match="Tool already registered",
    ):
        manager.register_tools(
            {
                "new": FakeTool,
                "existing": FakeTool,
            }
        )

    assert manager.get_tool_ids() == (
        "existing",
    )


def test_register_tools_rejects_invalid_factory_atomically(
    manager,
):
    with pytest.raises(
        TypeError,
        match="factory must be callable",
    ):
        manager.register_tools(
            {
                "valid": FakeTool,
                "invalid": object(),
            }
        )

    assert manager.get_tool_ids() == ()


def test_register_tools(
    manager,
):
    manager.register_tools(
        {
            "select": FakeTool,
            "bus": FakeTool,
            "line": FakeTool,
        }
    )

    assert manager.get_tool_ids() == (
        "select",
        "bus",
        "line",
    )


def test_load_registry_from_dict(
    controller,
):
    manager = ToolManager(
        controller=controller,
        tool_registry={
            "select": FakeTool,
            "bus": FakeTool,
        },
    )

    assert manager.get_tool_ids() == (
        "select",
        "bus",
    )


def test_load_registry_from_get_tools(
    controller,
):
    class Registry:
        def get_tools(self):
            return {
                "select": FakeTool,
                "bus": FakeTool,
            }

    manager = ToolManager(
        controller=controller,
        tool_registry=Registry(),
    )

    assert manager.get_tool_ids() == (
        "select",
        "bus",
    )


def test_load_registry_from_items(
    controller,
):
    class Registry:
        def items(self):
            return [
                ("select", FakeTool),
                ("bus", FakeTool),
            ]

    manager = ToolManager(
        controller=controller,
        tool_registry=Registry(),
    )

    assert manager.get_tool_ids() == (
        "select",
        "bus",
    )


def test_invalid_registry(
    controller,
):
    class InvalidRegistry:
        pass

    with pytest.raises(
        TypeError,
        match="tool_registry must provide",
    ):
        ToolManager(
            controller=controller,
            tool_registry=InvalidRegistry(),
        )


# ============================================================
# TOOL CREATION
# ============================================================


def test_tool_is_created_lazily(
    manager,
    interaction_manager,
    preview,
):
    recorder = FactoryRecorder()

    manager.register_tool(
        "select",
        recorder,
    )

    assert recorder.calls == []

    tool = manager.activate(
        "select"
    )

    assert len(recorder.calls) == 1

    recorded_interaction_manager = (
        recorder.calls[0][0]
    )

    recorded_preview = (
        recorder.calls[0][1]
    )

    assert recorded_interaction_manager is (
        interaction_manager
    )

    assert recorded_preview is preview
    assert tool is recorder.calls[0][2]


def test_tool_instance_is_cached(
    manager,
):
    recorder = FactoryRecorder()

    manager.register_tool(
        "select",
        recorder,
    )

    first = manager.activate(
        "select"
    )

    manager.deactivate()

    second = manager.activate(
        "select"
    )

    assert first is second
    assert len(recorder.calls) == 1


def test_constructor_type_error_propagates_unchanged(
    manager,
):
    manager.register_tool(
        "broken",
        FailingConstructorTool,
    )

    with pytest.raises(
        TypeError,
        match="constructor-internal failure",
    ):
        manager.activate(
            "broken"
        )

    assert manager.active_tool is None
    assert manager.active_tool_id is None


def test_factory_returning_none_is_rejected(
    manager,
):
    manager.register_tool(
        "broken",
        NoneFactory(),
    )

    with pytest.raises(
        RuntimeError,
        match="Tool factory returned None",
    ):
        manager.activate(
            "broken"
        )


# ============================================================
# ACTIVATION
# ============================================================


def test_activate_tool(
    manager,
):
    tool = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    result = manager.activate(
        "select"
    )

    assert result is tool
    assert manager.active_tool is tool
    assert manager.active_tool_id == "select"
    assert tool.activate_count == 1


def test_activate_unknown_tool_does_not_touch_active_tool(
    manager,
):
    current = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: current,
    )

    manager.activate(
        "select"
    )

    current_deactivate_count = (
        current.deactivate_count
    )

    with pytest.raises(
        KeyError,
        match="Unknown tool ID",
    ):
        manager.activate(
            "missing"
        )

    assert manager.active_tool is current
    assert manager.active_tool_id == "select"

    assert (
        current.deactivate_count
        == current_deactivate_count
    )


def test_activate_same_tool_is_noop(
    manager,
):
    tool = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    manager.activate(
        "select"
    )

    assert tool.activate_count == 1
    assert tool.deactivate_count == 0


def test_transition_deactivates_previous_before_activating_new(
    manager,
):
    events = []

    class ToolA(FakeTool):
        def deactivate(self):
            events.append("a.deactivate")
            super().deactivate()

    class ToolB(FakeTool):
        def activate(self):
            events.append("b.activate")
            super().activate()

    tool_a = ToolA()
    tool_b = ToolB()

    manager.register_tools(
        {
            "a": lambda **kwargs: tool_a,
            "b": lambda **kwargs: tool_b,
        }
    )

    manager.activate("a")
    manager.activate("b")

    assert events == [
        "a.deactivate",
        "b.activate",
    ]

    assert manager.active_tool is tool_b
    assert manager.active_tool_id == "b"


def test_transition_clears_preview(
    manager,
    preview,
):
    tool_a = FakeTool()
    tool_b = FakeTool()

    manager.register_tools(
        {
            "a": lambda **kwargs: tool_a,
            "b": lambda **kwargs: tool_b,
        }
    )

    manager.activate("a")

    clear_before = preview.clear_count

    manager.activate("b")

    assert preview.clear_count == (
        clear_before + 1
    )


def test_constructor_failure_preserves_previous_active_tool(
    manager,
):
    previous = FakeTool()

    manager.register_tool(
        "previous",
        lambda **kwargs: previous,
    )

    manager.register_tool(
        "broken",
        FailingConstructorTool,
    )

    manager.activate(
        "previous"
    )

    with pytest.raises(
        TypeError,
        match="constructor-internal failure",
    ):
        manager.activate(
            "broken"
        )

    assert manager.active_tool is previous
    assert manager.active_tool_id == "previous"

    assert previous.activate_count == 1
    assert previous.deactivate_count == 0


def test_deactivation_failure_preserves_previous_active_state(
    manager,
):
    previous = FakeTool()
    previous.fail_deactivate = True

    new_tool = FakeTool()

    manager.register_tools(
        {
            "previous": lambda **kwargs: previous,
            "new": lambda **kwargs: new_tool,
        }
    )

    manager.activate(
        "previous"
    )

    with pytest.raises(
        RuntimeError,
        match="deactivation failure",
    ):
        manager.activate(
            "new"
        )

    assert manager.active_tool is previous
    assert manager.active_tool_id == "previous"

    assert new_tool.activate_count == 0


def test_activation_failure_restores_previous_tool(
    manager,
):
    previous = FakeTool()
    failing = FakeTool()
    failing.fail_activate = True

    manager.register_tools(
        {
            "previous": lambda **kwargs: previous,
            "failing": lambda **kwargs: failing,
        }
    )

    manager.activate(
        "previous"
    )

    with pytest.raises(
        RuntimeError,
        match="activation failure",
    ):
        manager.activate(
            "failing"
        )

    assert manager.active_tool is previous
    assert manager.active_tool_id == "previous"

    assert previous.deactivate_count == 1
    assert previous.activate_count == 2
    assert failing.activate_count == 1


def test_activation_failure_without_previous_leaves_no_active_tool(
    manager,
):
    failing = FakeTool()
    failing.fail_activate = True

    manager.register_tool(
        "failing",
        lambda **kwargs: failing,
    )

    with pytest.raises(
        RuntimeError,
        match="activation failure",
    ):
        manager.activate(
            "failing"
        )

    assert manager.active_tool is None
    assert manager.active_tool_id is None


def test_activation_failure_and_restoration_failure_leave_no_active_tool(
    manager,
):
    class RestorationFailureTool(FakeTool):
        def __init__(self):
            super().__init__()
            self.activation_attempts = 0

        def activate(self):
            self.activation_attempts += 1

            if self.activation_attempts >= 2:
                raise RuntimeError(
                    "restoration failure"
                )

            super().activate()

    previous = RestorationFailureTool()

    failing = FakeTool()
    failing.fail_activate = True

    manager.register_tools(
        {
            "previous": lambda **kwargs: previous,
            "failing": lambda **kwargs: failing,
        }
    )

    manager.activate(
        "previous"
    )

    with pytest.raises(
        RuntimeError,
        match="activation failure",
    ) as exc_info:
        manager.activate(
            "failing"
        )

    assert isinstance(
        exc_info.value.__cause__,
        RuntimeError,
    )

    assert (
        str(exc_info.value.__cause__)
        == "restoration failure"
    )

    assert manager.active_tool is None
    assert manager.active_tool_id is None


# ============================================================
# EXPLICIT DEACTIVATION
# ============================================================


def test_deactivate(
    manager,
    preview,
):
    tool = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    clear_before = preview.clear_count

    manager.deactivate()

    assert tool.deactivate_count == 1
    assert manager.active_tool is None
    assert manager.active_tool_id is None

    assert preview.clear_count == (
        clear_before + 1
    )


def test_deactivation_failure_preserves_manager_state(
    manager,
):
    tool = FakeTool()
    tool.fail_deactivate = True

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    with pytest.raises(
        RuntimeError,
        match="deactivation failure",
    ):
        manager.deactivate()

    assert manager.active_tool is tool
    assert manager.active_tool_id == "select"


def test_deactivate_when_no_tool_is_active(
    manager,
    preview,
):
    manager.deactivate()

    assert manager.active_tool is None
    assert manager.active_tool_id is None
    assert preview.clear_count == 1


def test_activate_none_deactivates_current_tool(
    manager,
):
    tool = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    result = manager.activate(
        None
    )

    assert result is None
    assert manager.active_tool is None
    assert manager.active_tool_id is None
    assert tool.deactivate_count == 1


# ============================================================
# CONTROLLER INTEGRATION
# ============================================================


def test_controller_tool_changed_activates_tool(
    manager,
    controller,
):
    tool = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    controller.emit(
        "tool_changed",
        "select",
        None,
    )

    assert manager.active_tool is tool
    assert manager.active_tool_id == "select"


def test_controller_callback_does_not_modify_controller_selection(
    manager,
    controller,
):
    tool = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    controller.emit(
        "tool_changed",
        "select",
        None,
    )

    assert manager.active_tool_id == "select"


# ============================================================
# CANCELLATION
# ============================================================


def test_cancel_without_active_tool_returns_false(
    manager,
    preview,
):
    clear_before = preview.clear_count

    result = manager.cancel()

    assert result is False
    assert preview.clear_count == (
        clear_before + 1
    )


def test_cancel_active_tool(
    manager,
):
    tool = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    result = manager.cancel()

    assert result is True
    assert tool.cancel_count == 1

    assert manager.active_tool is tool
    assert manager.active_tool_id == "select"


def test_cancel_uses_tool_result(
    manager,
):
    tool = FakeTool()
    tool.cancel_result = False

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    assert manager.cancel() is False


def test_cancel_none_result_means_success(
    manager,
):
    tool = FakeTool()
    tool.cancel_result = None

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    assert manager.cancel() is True


def test_cancel_without_cancel_handler_is_success(
    manager,
):
    class ToolWithoutCancel:
        pass

    tool = ToolWithoutCancel()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    assert manager.cancel() is True


# ============================================================
# RESET
# ============================================================


def test_reset_active_tool(
    manager,
    preview,
):
    tool = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    clear_before = preview.clear_count

    manager.reset()

    assert tool.reset_count == 1
    assert manager.active_tool is tool
    assert manager.active_tool_id == "select"

    assert preview.clear_count == (
        clear_before + 1
    )


def test_reset_without_active_tool(
    manager,
    preview,
):
    clear_before = preview.clear_count

    manager.reset()

    assert preview.clear_count == (
        clear_before + 1
    )


# ============================================================
# UNREGISTER
# ============================================================


def test_unregister_uninstantiated_tool(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.unregister_tool(
        "select"
    )

    assert not manager.has_tool(
        "select"
    )


def test_unregister_disposes_existing_instance(
    manager,
):
    tool = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    manager.deactivate()

    manager.unregister_tool(
        "select"
    )

    assert tool.dispose_count == 1
    assert not manager.has_tool(
        "select"
    )

    assert "select" not in (
        manager.get_state()[
            "instantiated_tools"
        ]
    )


def test_cannot_unregister_active_tool(
    manager,
):
    tool = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    with pytest.raises(
        RuntimeError,
        match="Cannot unregister the active tool",
    ):
        manager.unregister_tool(
            "select"
        )

    assert manager.has_tool(
        "select"
    )

    assert manager.active_tool is tool


def test_unregister_disposal_failure_preserves_ownership(
    manager,
):
    tool = FakeTool()
    tool.fail_dispose = True

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    manager.deactivate()

    with pytest.raises(
        RuntimeError,
        match="disposal failure",
    ):
        manager.unregister_tool(
            "select"
        )

    assert manager.has_tool(
        "select"
    )

    assert (
        manager.get_state()[
            "instantiated_tools"
        ]
        == ("select",)
    )


# ============================================================
# DISPOSAL
# ============================================================


def test_dispose_manager(
    manager,
    controller,
    preview,
):
    tool_a = FakeTool()
    tool_b = FakeTool()

    manager.register_tools(
        {
            "a": lambda **kwargs: tool_a,
            "b": lambda **kwargs: tool_b,
        }
    )

    manager.activate(
        "a"
    )

    manager.deactivate()

    manager.activate(
        "b"
    )

    clear_before = preview.clear_count

    manager.dispose()

    assert tool_b.deactivate_count == 1
    assert tool_a.dispose_count == 1
    assert tool_b.dispose_count == 1

    assert preview.clear_count == (
        clear_before + 1
    )

    assert controller.unsubscribe_calls

    state = manager.get_state()

    assert state["connected"] is False
    assert state["disposed"] is True
    assert state["registered_tools"] == (
        "a",
        "b",
    )
    assert state["instantiated_tools"] == ()
    assert state["active_tool_id"] is None
    assert state["has_active_tool"] is False


def test_dispose_is_idempotent(
    manager,
):
    tool = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    manager.dispose()

    deactivate_count = tool.deactivate_count
    dispose_count = tool.dispose_count

    manager.dispose()

    assert tool.deactivate_count == (
        deactivate_count
    )

    assert tool.dispose_count == (
        dispose_count
    )


def test_dispose_deactivation_failure_does_not_mark_disposed(
    manager,
):
    tool = FakeTool()
    tool.fail_deactivate = True

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    with pytest.raises(
        RuntimeError,
        match="deactivation failure",
    ):
        manager.dispose()

    state = manager.get_state()

    assert state["disposed"] is False
    assert state["connected"] is True
    assert state["active_tool_id"] == "select"
    assert manager.active_tool is tool


def test_dispose_tool_failure_does_not_mark_disposed(
    manager,
):
    tool = FakeTool()
    tool.fail_dispose = True

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    manager.deactivate()

    with pytest.raises(
        RuntimeError,
        match="disposal failure",
    ):
        manager.dispose()

    state = manager.get_state()

    assert state["disposed"] is False


def test_disposed_manager_cannot_register(
    manager,
):
    manager.dispose()

    with pytest.raises(
        RuntimeError,
        match="ToolManager has been disposed",
    ):
        manager.register_tool(
            "select",
            FakeTool,
        )


def test_disposed_manager_cannot_activate(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.dispose()

    with pytest.raises(
        RuntimeError,
        match="ToolManager has been disposed",
    ):
        manager.activate(
            "select"
        )


def test_disposed_manager_cannot_deactivate(
    manager,
):
    manager.dispose()

    with pytest.raises(
        RuntimeError,
        match="ToolManager has been disposed",
    ):
        manager.deactivate()


def test_disposed_manager_cannot_cancel(
    manager,
):
    manager.dispose()

    with pytest.raises(
        RuntimeError,
        match="ToolManager has been disposed",
    ):
        manager.cancel()


def test_disposed_manager_cannot_reset(
    manager,
):
    manager.dispose()

    with pytest.raises(
        RuntimeError,
        match="ToolManager has been disposed",
    ):
        manager.reset()


def test_disposed_manager_cannot_unregister(
    manager,
):
    manager.dispose()

    with pytest.raises(
        RuntimeError,
        match="ToolManager has been disposed",
    ):
        manager.unregister_tool(
            "select"
        )


def test_disposed_manager_cannot_get_tool_ids(
    manager,
):
    manager.dispose()

    with pytest.raises(
        RuntimeError,
        match="ToolManager has been disposed",
    ):
        manager.get_tool_ids()


def test_disposed_manager_cannot_get_current_tool(
    manager,
):
    manager.dispose()

    with pytest.raises(
        RuntimeError,
        match="ToolManager has been disposed",
    ):
        manager.get_current_tool()


def test_disposed_manager_cannot_get_current_tool_id(
    manager,
):
    manager.dispose()

    with pytest.raises(
        RuntimeError,
        match="ToolManager has been disposed",
    ):
        manager.get_current_tool_id()


def test_disposed_manager_active_tool_property_raises(
    manager,
):
    manager.dispose()

    with pytest.raises(
        RuntimeError,
        match="ToolManager has been disposed",
    ):
        _ = manager.active_tool


def test_disposed_manager_active_tool_id_property_raises(
    manager,
):
    manager.dispose()

    with pytest.raises(
        RuntimeError,
        match="ToolManager has been disposed",
    ):
        _ = manager.active_tool_id


# ============================================================
# DISPOSED CONTROLLER CALLBACK
# ============================================================


def test_controller_callback_is_ignored_after_disposal(
    manager,
    controller,
):
    tool = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.dispose()

    # Simulate a stale callback directly.
    manager._on_tool_changed(
        "select",
        None,
    )

    assert manager.get_state()["disposed"] is True
    assert tool.activate_count == 0


# ============================================================
# DIAGNOSTICS
# ============================================================


def test_get_state_tracks_instantiated_tools(
    manager,
):
    manager.register_tools(
        {
            "a": FakeTool,
            "b": FakeTool,
        }
    )

    assert manager.get_state()[
        "instantiated_tools"
    ] == ()

    manager.activate("a")

    assert manager.get_state()[
        "instantiated_tools"
    ] == ("a",)

    manager.deactivate()

    manager.activate("b")

    assert manager.get_state()[
        "instantiated_tools"
    ] == (
        "a",
        "b",
    )


def test_repr(
    manager,
):
    representation = repr(
        manager
    )

    assert "ToolManager(" in representation
    assert "active=None" in representation
    assert "registered=0" in representation
    assert "disposed=False" in representation


def test_repr_after_disposal(
    manager,
):
    manager.dispose()

    representation = repr(
        manager
    )

    assert "disposed=True" in representation


# ============================================================
# PREVIEW CLEANUP FAILURE PROPAGATION
# ============================================================


def test_preview_clear_failure_propagates(
    manager,
):
    class FailingPreview:
        def clear(self):
            raise RuntimeError(
                "preview clear failure"
            )

    manager.preview = FailingPreview()

    tool = FakeTool()

    manager.register_tool(
        "select",
        lambda **kwargs: tool,
    )

    manager.activate(
        "select"
    )

    with pytest.raises(
        RuntimeError,
        match="preview clear failure",
    ):
        manager.deactivate()

    # The tool lifecycle completed, but preview cleanup failed.
    # Manager state has already been committed to deactivated.
    assert manager.active_tool is None
    assert manager.active_tool_id is None
