# ============================================================
# File: tests/ui/core/test_tool_manager.py
# GridForge V2 — Tool Manager Tests
# ============================================================

from __future__ import annotations

import pytest

from ui.core.tool_manager import ToolManager


# ============================================================
# TEST DOUBLES
# ============================================================


class FakeController:
    """Minimal Controller double for ToolManager tests."""

    def __init__(self):
        self.callbacks = {}
        self.subscribe_calls = []
        self.unsubscribe_calls = []

    def subscribe(self, signal_name, callback):
        self.subscribe_calls.append(
            (signal_name, callback)
        )
        self.callbacks.setdefault(
            signal_name,
            []
        ).append(callback)

    def unsubscribe(self, signal_name, callback):
        self.unsubscribe_calls.append(
            (signal_name, callback)
        )

        callbacks = self.callbacks.get(
            signal_name,
            []
        )

        if callback in callbacks:
            callbacks.remove(callback)

    def emit_tool_changed(
        self,
        new_tool_id,
        previous_tool_id=None,
    ):
        for callback in tuple(
            self.callbacks.get(
                "tool_changed",
                []
            )
        ):
            callback(
                new_tool_id,
                previous_tool_id,
            )


class FakePreview:
    """Preview-layer double."""

    def __init__(self):
        self.clear_count = 0

    def clear(self):
        self.clear_count += 1


class FakeTool:
    """Lifecycle-aware concrete tool double."""

    created = []

    def __init__(
        self,
        interaction_manager=None,
        preview=None,
    ):
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

        FakeTool.created.append(self)

    def activate(self):
        self.activate_count += 1

        if self.fail_activate:
            raise RuntimeError(
                "activation failure"
            )

    def deactivate(self):
        self.deactivate_count += 1

        if self.fail_deactivate:
            raise RuntimeError(
                "deactivation failure"
            )

    def cancel(self):
        self.cancel_count += 1
        return True

    def reset(self):
        self.reset_count += 1

    def dispose(self):
        self.dispose_count += 1

        if self.fail_dispose:
            raise RuntimeError(
                "disposal failure"
            )


class PassiveTool:
    """Tool without optional lifecycle methods."""

    created = []

    def __init__(
        self,
        interaction_manager=None,
        preview=None,
    ):
        self.interaction_manager = interaction_manager
        self.preview = preview

        PassiveTool.created.append(self)


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture(autouse=True)
def reset_tool_tracking():
    FakeTool.created.clear()
    PassiveTool.created.clear()


@pytest.fixture
def controller():
    return FakeController()


@pytest.fixture
def preview():
    return FakePreview()


@pytest.fixture
def manager(controller, preview):
    return ToolManager(
        controller=controller,
        interaction_manager="interaction",
        preview=preview,
    )


# ============================================================
# INITIALIZATION
# ============================================================


def test_requires_controller():
    with pytest.raises(ValueError):
        ToolManager(None)


def test_controller_must_provide_subscribe():
    class InvalidController:
        pass

    with pytest.raises(TypeError):
        ToolManager(
            InvalidController()
        )


def test_initial_state(manager):
    assert manager.get_current_tool() is None
    assert manager.get_current_tool_id() is None
    assert manager.active_tool is None
    assert manager.active_tool_id is None


def test_controller_subscription_is_established(
    manager,
    controller,
):
    assert len(
        controller.subscribe_calls
    ) == 1

    signal_name, callback = (
        controller.subscribe_calls[0]
    )

    assert signal_name == "tool_changed"
    assert callback == manager._on_tool_changed


# ============================================================
# REGISTRATION
# ============================================================


def test_register_tool(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    assert manager.has_tool("select")
    assert manager.get_tool_ids() == (
        "select",
    )


def test_register_tool_does_not_instantiate(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    assert FakeTool.created == []


def test_register_rejects_invalid_id(manager):
    with pytest.raises(TypeError):
        manager.register_tool(
            123,
            FakeTool,
        )


def test_register_rejects_empty_id(manager):
    with pytest.raises(ValueError):
        manager.register_tool(
            "   ",
            FakeTool,
        )


def test_register_rejects_non_callable_factory(manager):
    with pytest.raises(TypeError):
        manager.register_tool(
            "select",
            object(),
        )


def test_duplicate_registration_fails(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    with pytest.raises(ValueError):
        manager.register_tool(
            "select",
            FakeTool,
        )


def test_register_tools(manager):
    manager.register_tools(
        {
            "select": FakeTool,
            "bus": PassiveTool,
        }
    )

    assert manager.get_tool_ids() == (
        "select",
        "bus",
    )


def test_register_tools_is_atomic(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    with pytest.raises(ValueError):
        manager.register_tools(
            {
                "bus": FakeTool,
                "select": PassiveTool,
            }
        )

    assert manager.get_tool_ids() == (
        "select",
    )


def test_register_tools_rejects_none(manager):
    with pytest.raises(ValueError):
        manager.register_tools(None)


def test_register_tools_rejects_non_dict(manager):
    with pytest.raises(TypeError):
        manager.register_tools([])


# ============================================================
# REGISTRY LOADING
# ============================================================


def test_registry_can_be_passed_as_dict(
    controller,
    preview,
):
    manager = ToolManager(
        controller,
        preview=preview,
        tool_registry={
            "select": FakeTool,
        },
    )

    assert manager.get_tool_ids() == (
        "select",
    )


def test_registry_can_expose_get_tools(
    controller,
):
    class Registry:
        def get_tools(self):
            return {
                "select": FakeTool,
            }

    manager = ToolManager(
        controller,
        tool_registry=Registry(),
    )

    assert manager.has_tool("select")


def test_registry_can_expose_items(
    controller,
):
    class Registry:
        def items(self):
            return [
                ("select", FakeTool),
            ]

    manager = ToolManager(
        controller,
        tool_registry=Registry(),
    )

    assert manager.has_tool("select")


def test_invalid_registry_fails(controller):
    with pytest.raises(TypeError):
        ToolManager(
            controller,
            tool_registry=object(),
        )


# ============================================================
# LAZY CONSTRUCTION
# ============================================================


def test_tool_is_constructed_on_first_activation(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    assert FakeTool.created == []

    tool = manager.activate(
        "select"
    )

    assert len(FakeTool.created) == 1
    assert tool is FakeTool.created[0]


def test_tool_constructor_receives_canonical_arguments(
    controller,
    preview,
):
    interaction = object()

    manager = ToolManager(
        controller,
        interaction_manager=interaction,
        preview=preview,
    )

    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate(
        "select"
    )

    assert tool.interaction_manager is interaction
    assert tool.preview is preview


def test_existing_tool_instance_is_reused(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    first = manager.activate(
        "select"
    )

    manager.deactivate()

    second = manager.activate(
        "select"
    )

    assert first is second
    assert len(FakeTool.created) == 1


def test_constructor_failure_preserves_current_tool(
    manager,
):
    manager.register_tool(
        "good",
        FakeTool,
    )

    def failing_factory(
        interaction_manager=None,
        preview=None,
    ):
        raise RuntimeError(
            "constructor failure"
        )

    manager.register_tool(
        "bad",
        failing_factory,
    )

    current = manager.activate(
        "good"
    )

    with pytest.raises(
        RuntimeError,
        match="constructor failure",
    ):
        manager.activate(
            "bad"
        )

    assert manager.active_tool is current
    assert manager.active_tool_id == "good"


def test_factory_returning_none_fails(manager):
    manager.register_tool(
        "bad",
        lambda **kwargs: None,
    )

    with pytest.raises(
        RuntimeError,
        match="Tool factory returned None",
    ):
        manager.activate(
            "bad"
        )


# ============================================================
# ACTIVATION
# ============================================================


def test_activate_unknown_tool_preserves_state(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    current = manager.activate(
        "select"
    )

    with pytest.raises(KeyError):
        manager.activate(
            "unknown"
        )

    assert manager.active_tool is current
    assert manager.active_tool_id == "select"


def test_activate_same_tool_is_noop(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate(
        "select"
    )

    activate_count = tool.activate_count

    result = manager.activate(
        "select"
    )

    assert result is tool
    assert tool.activate_count == activate_count


def test_activation_deactivates_previous_tool(
    manager,
):
    manager.register_tool(
        "first",
        FakeTool,
    )
    manager.register_tool(
        "second",
        FakeTool,
    )

    first = manager.activate(
        "first"
    )

    second = manager.activate(
        "second"
    )

    assert first.deactivate_count == 1
    assert second.activate_count == 1
    assert manager.active_tool is second
    assert manager.active_tool_id == "second"


def test_failed_deactivation_preserves_previous_state(
    manager,
):
    manager.register_tool(
        "first",
        FakeTool,
    )
    manager.register_tool(
        "second",
        FakeTool,
    )

    first = manager.activate(
        "first"
    )

    first.fail_deactivate = True

    with pytest.raises(
        RuntimeError,
        match="deactivation failure",
    ):
        manager.activate(
            "second"
        )

    assert manager.active_tool is first
    assert manager.active_tool_id == "first"


def test_failed_activation_restores_previous_tool(
    manager,
):
    manager.register_tool(
        "first",
        FakeTool,
    )
    manager.register_tool(
        "second",
        FakeTool,
    )

    first = manager.activate(
        "first"
    )

    second = manager._get_or_create_tool(
        "second"
    )

    second.fail_activate = True

    with pytest.raises(
        RuntimeError,
        match="activation failure",
    ):
        manager.activate(
            "second"
        )

    assert manager.active_tool is first
    assert manager.active_tool_id == "first"
    assert first.activate_count == 2


def test_failed_activation_without_previous_tool_leaves_none(
    manager,
):
    manager.register_tool(
        "bad",
        FakeTool,
    )

    tool = manager._get_or_create_tool(
        "bad"
    )

    tool.fail_activate = True

    with pytest.raises(
        RuntimeError,
        match="activation failure",
    ):
        manager.activate(
            "bad"
        )

    assert manager.active_tool is None
    assert manager.active_tool_id is None


def test_failed_restoration_clears_active_state(
    manager,
):
    manager.register_tool(
        "first",
        FakeTool,
    )
    manager.register_tool(
        "second",
        FakeTool,
    )

    first = manager.activate(
        "first"
    )

    second = manager._get_or_create_tool(
        "second"
    )

    second.fail_activate = True

    original_activate = first.activate

    def fail_restore():
        first.activate_count += 1
        raise RuntimeError(
            "restore failure"
        )

    first.activate = fail_restore

    with pytest.raises(
        RuntimeError,
        match="activation failure",
    ):
        manager.activate(
            "second"
        )

    assert manager.active_tool is None
    assert manager.active_tool_id is None


def test_activation_clears_preview(
    manager,
    preview,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.activate(
        "select"
    )

    assert preview.clear_count >= 1


# ============================================================
# CONTROLLER INTEGRATION
# ============================================================


def test_controller_tool_changed_activates_tool(
    manager,
    controller,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    controller.emit_tool_changed(
        "select"
    )

    assert manager.active_tool_id == "select"
    assert manager.active_tool is not None


def test_controller_unknown_tool_does_not_deactivate_current(
    manager,
    controller,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    current = manager.activate(
        "select"
    )

    with pytest.raises(KeyError):
        controller.emit_tool_changed(
            "unknown"
        )

    assert manager.active_tool is current
    assert manager.active_tool_id == "select"


# ============================================================
# DEACTIVATION
# ============================================================


def test_deactivate_clears_active_state(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate(
        "select"
    )

    manager.deactivate()

    assert tool.deactivate_count == 1
    assert manager.active_tool is None
    assert manager.active_tool_id is None


def test_deactivate_without_active_tool_is_noop(
    manager,
):
    manager.deactivate()

    assert manager.active_tool is None
    assert manager.active_tool_id is None


def test_deactivate_failure_preserves_state(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate(
        "select"
    )

    tool.fail_deactivate = True

    with pytest.raises(
        RuntimeError,
        match="deactivation failure",
    ):
        manager.deactivate()

    assert manager.active_tool is tool
    assert manager.active_tool_id == "select"


def test_activate_none_deactivates(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate(
        "select"
    )

    result = manager.activate(
        None
    )

    assert result is None
    assert tool.deactivate_count == 1
    assert manager.active_tool is None
    assert manager.active_tool_id is None


# ============================================================
# CANCEL
# ============================================================


def test_cancel_active_tool(
    manager,
    preview,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate(
        "select"
    )

    result = manager.cancel()

    assert result is True
    assert tool.cancel_count == 1
    assert manager.active_tool is tool
    assert preview.clear_count >= 1


def test_cancel_without_active_tool_returns_false(
    manager,
    preview,
):
    result = manager.cancel()

    assert result is False
    assert preview.clear_count == 1


def test_cancel_preserves_exception_and_clears_preview(
    manager,
    preview,
):
    class FailingCancelTool(FakeTool):
        def cancel(self):
            self.cancel_count += 1
            raise RuntimeError(
                "cancel failure"
            )

    manager.register_tool(
        "select",
        FailingCancelTool,
    )

    manager.activate(
        "select"
    )

    with pytest.raises(
        RuntimeError,
        match="cancel failure",
    ):
        manager.cancel()

    assert preview.clear_count >= 2


# ============================================================
# RESET
# ============================================================


def test_reset_active_tool(
    manager,
    preview,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate(
        "select"
    )

    manager.reset()

    assert tool.reset_count == 1
    assert manager.active_tool is tool
    assert manager.active_tool_id == "select"
    assert preview.clear_count >= 2


def test_reset_without_active_tool(
    manager,
    preview,
):
    manager.reset()

    assert preview.clear_count == 1


def test_reset_clears_preview_when_tool_reset_fails(
    manager,
    preview,
):
    class FailingResetTool(FakeTool):
        def reset(self):
            self.reset_count += 1
            raise RuntimeError(
                "reset failure"
            )

    manager.register_tool(
        "select",
        FailingResetTool,
    )

    manager.activate(
        "select"
    )

    with pytest.raises(
        RuntimeError,
        match="reset failure",
    ):
        manager.reset()

    assert manager.active_tool is not None
    assert manager.active_tool_id == "select"
    assert preview.clear_count >= 2


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
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate(
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


def test_unregister_active_tool_fails(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.activate(
        "select"
    )

    with pytest.raises(
        RuntimeError,
        match="active tool",
    ):
        manager.unregister_tool(
            "select"
        )


def test_unregister_disposal_failure_preserves_ownership(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate(
        "select"
    )

    manager.deactivate()

    tool.fail_dispose = True

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

    assert "select" in (
        manager.get_state()[
            "instantiated_tools"
        ]
    )


# ============================================================
# DISPOSAL
# ============================================================


def test_dispose_deactivates_and_disposes_tools(
    manager,
    controller,
    preview,
):
    manager.register_tools(
        {
            "first": FakeTool,
            "second": FakeTool,
        }
    )

    first = manager.activate(
        "first"
    )

    manager.deactivate()

    second = manager.activate(
        "second"
    )

    manager.dispose()

    assert second.deactivate_count == 1
    assert first.dispose_count == 1
    assert second.dispose_count == 1

    assert manager.get_state()[
        "disposed"
    ] is True

    assert manager.get_state()[
        "connected"
    ] is False

    assert len(
        controller.unsubscribe_calls
    ) == 1

    assert preview.clear_count >= 1


def test_dispose_is_idempotent(
    manager,
    controller,
):
    manager.dispose()
    manager.dispose()

    assert len(
        controller.unsubscribe_calls
    ) == 1


def test_dispose_failure_is_retryable(
    manager,
):
    manager.register_tool(
        "first",
        FakeTool,
    )
    manager.register_tool(
        "second",
        FakeTool,
    )

    first = manager.activate(
        "first"
    )

    manager.deactivate()

    second = manager.activate(
        "second"
    )

    second.fail_dispose = True

    with pytest.raises(
        RuntimeError,
        match="disposal failure",
    ):
        manager.dispose()

    assert manager.get_state()[
        "disposed"
    ] is False

    assert "second" in (
        manager.get_state()[
            "instantiated_tools"
        ]
    )

    second.fail_dispose = False

    manager.dispose()

    assert manager.get_state()[
        "disposed"
    ] is True


def test_active_deactivation_failure_blocks_disposal(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate(
        "select"
    )

    tool.fail_deactivate = True

    with pytest.raises(
        RuntimeError,
        match="deactivation failure",
    ):
        manager.dispose()

    assert manager.get_state()[
        "disposed"
    ] is False

    assert manager.active_tool is tool
    assert manager.active_tool_id == "select"


# ============================================================
# DISPOSED BEHAVIOR
# ============================================================


def test_register_after_dispose_fails(
    manager,
):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.register_tool(
            "select",
            FakeTool,
        )


def test_activate_after_dispose_fails(
    manager,
):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.activate(
            "select"
        )


def test_deactivate_after_dispose_fails(
    manager,
):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.deactivate()


def test_cancel_after_dispose_fails(
    manager,
):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.cancel()


def test_reset_after_dispose_fails(
    manager,
):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.reset()


def test_unregister_after_dispose_fails(
    manager,
):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.unregister_tool(
            "select"
        )


def test_get_current_tool_after_dispose_fails(
    manager,
):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.get_current_tool()


def test_get_current_tool_id_after_dispose_fails(
    manager,
):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.get_current_tool_id()


def test_get_tool_ids_after_dispose_fails(
    manager,
):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.get_tool_ids()


def test_controller_event_after_dispose_is_ignored(
    manager,
    controller,
):
    manager.dispose()

    controller.emit_tool_changed(
        "unknown"
    )

    assert manager.get_state()[
        "disposed"
    ] is True


# ============================================================
# DIAGNOSTICS
# ============================================================


def test_get_state_initial(manager):
    assert manager.get_state() == {
        "connected": True,
        "disposed": False,
        "registered_tools": (),
        "instantiated_tools": (),
        "active_tool_id": None,
        "has_active_tool": False,
    }


def test_get_state_tracks_registration(
    manager,
):
    manager.register_tools(
        {
            "select": FakeTool,
            "bus": PassiveTool,
        }
    )

    state = manager.get_state()

    assert state[
        "registered_tools"
    ] == (
        "select",
        "bus",
    )

    assert state[
        "instantiated_tools"
    ] == ()


def test_get_state_tracks_instantiation(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.activate(
        "select"
    )

    state = manager.get_state()

    assert state[
        "instantiated_tools"
    ] == (
        "select",
    )

    assert state[
        "active_tool_id"
    ] == "select"

    assert state[
        "has_active_tool"
    ] is True


def test_repr_contains_diagnostic_state(
    manager,
):
    text = repr(manager)

    assert "ToolManager" in text
    assert "active=None" in text
    assert "registered=0" in text
    assert "disposed=False" in text


# ============================================================
# CONSTRUCTOR TYPEERROR PROPAGATION
# ============================================================


def test_constructor_typeerror_propagates_unchanged(
    manager,
):
    def failing_factory(
        interaction_manager=None,
        preview=None,
    ):
        raise TypeError(
            "real constructor failure"
        )

    manager.register_tool(
        "bad",
        failing_factory,
    )

    with pytest.raises(
        TypeError,
        match="real constructor failure",
    ):
        manager.activate(
            "bad"
        )


# ============================================================
# OPTIONAL TOOL LIFECYCLE
# ============================================================


def test_tool_without_optional_lifecycle_methods_works(
    manager,
):
    manager.register_tool(
        "passive",
        PassiveTool,
    )

    tool = manager.activate(
        "passive"
    )

    assert manager.active_tool is tool

    manager.cancel()
    manager.reset()
    manager.deactivate()

    assert manager.active_tool is None


# ============================================================
# NO CONTROLLER MUTATION
# ============================================================


def test_tool_manager_never_changes_controller_selection(
    manager,
    controller,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.activate(
        "select"
    )

    assert not hasattr(
        controller,
        "set_tool_calls",
    )
