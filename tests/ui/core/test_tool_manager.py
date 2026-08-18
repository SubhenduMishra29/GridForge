# ============================================================
# File: tests/ui/core/test_tool_manager.py
# GridForge V2 — ToolManager Tests
# ============================================================

import pytest

from ui.core.tool_manager import ToolManager


# ============================================================
# TEST DOUBLES
# ============================================================


class FakeController:
    """Minimal controller reference.

    ToolManager must retain the controller but must not subscribe
    to it or mutate its tool-selection state.
    """

    def __init__(self):
        self.selected_tool = None
        self.set_tool_calls = []

    def set_tool(self, tool_id):
        self.set_tool_calls.append(tool_id)
        self.selected_tool = tool_id


class FakeInteractionManager:
    pass


class FakePreview:
    def __init__(self):
        self.clear_count = 0

    def clear(self):
        self.clear_count += 1


class FakeTool:
    """Lifecycle-aware fake concrete tool."""

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
        self.cancel_result = None

        type(self).created.append(self)

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

        if self.cancel_result is not None:
            return self.cancel_result

        return True

    def reset(self):
        self.reset_count += 1

    def dispose(self):
        self.dispose_count += 1

        if self.fail_dispose:
            raise RuntimeError(
                "disposal failure"
            )


class MinimalTool:
    """Tool exposing no optional lifecycle methods."""

    def __init__(
        self,
        interaction_manager=None,
        preview=None,
    ):
        self.interaction_manager = interaction_manager
        self.preview = preview


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture(autouse=True)
def reset_fake_tool_instances():
    FakeTool.created.clear()
    yield
    FakeTool.created.clear()


@pytest.fixture
def controller():
    return FakeController()


@pytest.fixture
def interaction_manager():
    return FakeInteractionManager()


@pytest.fixture
def preview():
    return FakePreview()


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
# CONSTRUCTION
# ============================================================


def test_requires_controller():
    with pytest.raises(ValueError):
        ToolManager(controller=None)


def test_controller_is_retained(controller):
    manager = ToolManager(controller)

    assert manager.controller is controller


def test_controller_does_not_need_subscription_api():
    class ControllerWithoutSignals:
        pass

    controller = ControllerWithoutSignals()

    manager = ToolManager(controller)

    assert manager.controller is controller


def test_initial_state(manager):
    assert manager.active_tool is None
    assert manager.active_tool_id is None
    assert manager.get_current_tool() is None
    assert manager.get_current_tool_id() is None


# ============================================================
# REGISTRATION
# ============================================================


def test_register_tool(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    assert manager.has_tool("select")
    assert manager.get_tool_ids() == ("select",)


def test_register_tool_does_not_instantiate(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    assert FakeTool.created == []


@pytest.mark.parametrize(
    "tool_id",
    [
        None,
        123,
        object(),
    ],
)
def test_register_rejects_invalid_id(
    manager,
    tool_id,
):
    with pytest.raises(TypeError):
        manager.register_tool(
            tool_id,
            FakeTool,
        )


def test_register_rejects_empty_id(manager):
    with pytest.raises(ValueError):
        manager.register_tool(
            "",
            FakeTool,
        )


def test_register_rejects_whitespace_id(manager):
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
            "bus": FakeTool,
            "line": FakeTool,
        }
    )

    assert manager.get_tool_ids() == (
        "select",
        "bus",
        "line",
    )


def test_register_tools_is_atomic(manager):
    manager.register_tool(
        "existing",
        FakeTool,
    )

    with pytest.raises(ValueError):
        manager.register_tools(
            {
                "new": FakeTool,
                "existing": FakeTool,
            }
        )

    assert manager.get_tool_ids() == (
        "existing",
    )


def test_register_tools_rejects_none(manager):
    with pytest.raises(ValueError):
        manager.register_tools(None)


def test_register_tools_rejects_non_dict(manager):
    with pytest.raises(TypeError):
        manager.register_tools([])


def test_registry_can_be_passed_as_dict(controller):
    manager = ToolManager(
        controller,
        tool_registry={
            "select": FakeTool,
        },
    )

    assert manager.get_tool_ids() == (
        "select",
    )


def test_registry_can_expose_get_tools(controller):
    class Registry:
        def get_tools(self):
            return {
                "select": FakeTool,
            }

    manager = ToolManager(
        controller,
        tool_registry=Registry(),
    )

    assert manager.get_tool_ids() == (
        "select",
    )


def test_registry_can_expose_items(controller):
    class Registry:
        def items(self):
            return [
                ("select", FakeTool),
            ]

    manager = ToolManager(
        controller,
        tool_registry=Registry(),
    )

    assert manager.get_tool_ids() == (
        "select",
    )


def test_invalid_registry_fails(controller):
    class InvalidRegistry:
        pass

    with pytest.raises(TypeError):
        ToolManager(
            controller,
            tool_registry=InvalidRegistry(),
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

    tool = manager.activate("select")

    assert len(FakeTool.created) == 1
    assert tool is FakeTool.created[0]


def test_tool_constructor_receives_canonical_arguments(
    manager,
    interaction_manager,
    preview,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")

    assert tool.interaction_manager is interaction_manager
    assert tool.preview is preview


def test_existing_tool_instance_is_reused(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    first = manager.activate("select")

    manager.deactivate()

    second = manager.activate("select")

    assert first is second
    assert len(FakeTool.created) == 1


def test_constructor_failure_preserves_current_tool(
    manager,
):
    manager.register_tool(
        "first",
        FakeTool,
    )

    def failing_factory(
        interaction_manager=None,
        preview=None,
    ):
        raise RuntimeError(
            "construction failure"
        )

    manager.register_tool(
        "broken",
        failing_factory,
    )

    first = manager.activate("first")

    with pytest.raises(RuntimeError, match="construction failure"):
        manager.activate("broken")

    assert manager.active_tool is first
    assert manager.active_tool_id == "first"


def test_factory_returning_none_fails(manager):
    def factory(
        interaction_manager=None,
        preview=None,
    ):
        return None

    manager.register_tool(
        "broken",
        factory,
    )

    with pytest.raises(RuntimeError):
        manager.activate("broken")


# ============================================================
# ACTIVATION
# ============================================================


def test_activate_unknown_tool_preserves_state(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    current = manager.activate("select")

    with pytest.raises(KeyError):
        manager.activate("unknown")

    assert manager.active_tool is current
    assert manager.active_tool_id == "select"


def test_activate_same_tool_is_noop(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")

    activation_count = tool.activate_count

    same = manager.activate("select")

    assert same is tool
    assert tool.activate_count == activation_count


def test_activation_deactivates_previous_tool(manager):
    manager.register_tools(
        {
            "first": FakeTool,
            "second": FakeTool,
        }
    )

    first = manager.activate("first")
    second = manager.activate("second")

    assert first.deactivate_count == 1
    assert second.activate_count == 1
    assert manager.active_tool is second
    assert manager.active_tool_id == "second"


def test_failed_deactivation_preserves_previous_state(
    manager,
):
    manager.register_tools(
        {
            "first": FakeTool,
            "second": FakeTool,
        }
    )

    first = manager.activate("first")

    first.fail_deactivate = True

    with pytest.raises(RuntimeError):
        manager.activate("second")

    assert manager.active_tool is first
    assert manager.active_tool_id == "first"


def test_failed_activation_restores_previous_tool(
    manager,
):
    manager.register_tools(
        {
            "first": FakeTool,
            "second": FakeTool,
        }
    )

    first = manager.activate("first")
    second = manager.activate("second")

    # The requested tool is FIRST. Therefore FIRST must fail.
    first.fail_activate = True

    with pytest.raises(RuntimeError):
        manager.activate("first")

    # SECOND was the previous authoritative tool and must
    # have been restored.
    assert manager.active_tool is second
    assert manager.active_tool_id == "second"

    assert second.deactivate_count == 1
    assert second.activate_count == 2


def test_failed_activation_without_previous_tool_leaves_none(
    manager,
):
    class FailingTool(FakeTool):
        def activate(self):
            self.activate_count += 1
            raise RuntimeError(
                "activation failure"
            )

    manager.register_tool(
        "broken",
        FailingTool,
    )

    with pytest.raises(RuntimeError):
        manager.activate("broken")

    assert manager.active_tool is None
    assert manager.active_tool_id is None


def test_failed_restoration_clears_active_state(
    manager,
):
    class RestorationTool(FakeTool):
        def activate(self):
            self.activate_count += 1

            if self.activate_count >= 2:
                raise RuntimeError(
                    "restoration failure"
                )

    class FailingTool(FakeTool):
        def activate(self):
            self.activate_count += 1
            raise RuntimeError(
                "activation failure"
            )

    manager.register_tools(
        {
            "first": RestorationTool,
            "second": FailingTool,
        }
    )

    first = manager.activate("first")

    assert first.activate_count == 1

    with pytest.raises(RuntimeError):
        manager.activate("second")

    # SECOND failed activation.
    # FIRST restoration also failed.
    # Therefore no tool may be reported as active.
    assert manager.active_tool is None
    assert manager.active_tool_id is None


def test_activation_clears_preview(manager, preview):
    manager.register_tools(
        {
            "first": FakeTool,
            "second": FakeTool,
        }
    )

    manager.activate("first")

    initial = preview.clear_count

    manager.activate("second")

    assert preview.clear_count > initial


def test_deactivate_clears_active_state(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.activate("select")
    manager.deactivate()

    assert manager.active_tool is None
    assert manager.active_tool_id is None


def test_deactivate_without_active_tool_is_noop(
    manager,
):
    manager.deactivate()

    assert manager.active_tool is None
    assert manager.active_tool_id is None


def test_deactivate_failure_preserves_state(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")

    tool.fail_deactivate = True

    with pytest.raises(RuntimeError):
        manager.deactivate()

    assert manager.active_tool is tool
    assert manager.active_tool_id == "select"


def test_activate_none_deactivates(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.activate("select")

    result = manager.activate(None)

    assert result is None
    assert manager.active_tool is None
    assert manager.active_tool_id is None


# ============================================================
# CANCELLATION
# ============================================================


def test_cancel_active_tool(manager, preview):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")

    result = manager.cancel()

    assert result is True
    assert tool.cancel_count == 1


def test_cancel_without_active_tool_returns_false(
    manager,
):
    assert manager.cancel() is False


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

    manager.activate("select")

    before = preview.clear_count

    with pytest.raises(RuntimeError):
        manager.cancel()

    assert preview.clear_count > before
    assert manager.active_tool is not None


# ============================================================
# RESET
# ============================================================


def test_reset_active_tool(manager, preview):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")

    manager.reset()

    assert tool.reset_count == 1
    assert manager.active_tool is tool


def test_reset_without_active_tool(manager):
    manager.reset()

    assert manager.active_tool is None


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

    manager.activate("select")

    before = preview.clear_count

    with pytest.raises(RuntimeError):
        manager.reset()

    assert preview.clear_count > before


# ============================================================
# UNREGISTRATION
# ============================================================


def test_unregister_uninstantiated_tool(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.unregister_tool("select")

    assert not manager.has_tool("select")
    assert manager.get_tool_ids() == ()


def test_unregister_disposes_existing_instance(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")
    manager.deactivate()

    manager.unregister_tool("select")

    assert tool.dispose_count == 1
    assert not manager.has_tool("select")


def test_unregister_active_tool_fails(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.activate("select")

    with pytest.raises(RuntimeError):
        manager.unregister_tool("select")

    assert manager.has_tool("select")


def test_unregister_disposal_failure_preserves_ownership(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")
    manager.deactivate()

    tool.fail_dispose = True

    with pytest.raises(RuntimeError):
        manager.unregister_tool("select")

    assert manager.has_tool("select")
    assert manager.get_tool_ids() == ("select",)


# ============================================================
# DISPOSAL
# ============================================================


def test_dispose_deactivates_and_disposes_tools(
    manager,
):
    manager.register_tools(
        {
            "first": FakeTool,
            "second": FakeTool,
        }
    )

    first = manager.activate("first")
    manager.deactivate()

    second = manager.activate("second")

    manager.dispose()

    assert second.deactivate_count == 1
    assert first.dispose_count == 1
    assert second.dispose_count == 1

    state = manager.get_state()

    assert state["disposed"] is True
    assert state["registered_tools"] == ()
    assert state["instantiated_tools"] == ()
    assert state["active_tool_id"] is None
    assert state["has_active_tool"] is False


def test_dispose_is_idempotent(manager):
    manager.dispose()
    manager.dispose()

    state = manager.get_state()

    assert state["disposed"] is True


def test_dispose_failure_is_retryable(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")
    manager.deactivate()

    tool.fail_dispose = True

    with pytest.raises(RuntimeError):
        manager.dispose()

    assert manager.get_state()["disposed"] is False

    tool.fail_dispose = False

    manager.dispose()

    assert manager.get_state()["disposed"] is True


def test_active_deactivation_failure_blocks_disposal(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")

    tool.fail_deactivate = True

    with pytest.raises(RuntimeError):
        manager.dispose()

    assert manager.active_tool is tool
    assert manager.active_tool_id == "select"
    assert manager.get_state()["disposed"] is False


# ============================================================
# DISPOSED MANAGER PROTECTION
# ============================================================


def test_register_after_dispose_fails(manager):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.register_tool(
            "select",
            FakeTool,
        )


def test_activate_after_dispose_fails(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.activate("select")


def test_deactivate_after_dispose_fails(manager):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.deactivate()


def test_cancel_after_dispose_fails(manager):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.cancel()


def test_reset_after_dispose_fails(manager):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.reset()


def test_unregister_after_dispose_fails(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.unregister_tool("select")


def test_get_current_tool_after_dispose_fails(manager):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.get_current_tool()


def test_get_current_tool_id_after_dispose_fails(manager):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.get_current_tool_id()


def test_get_tool_ids_after_dispose_fails(manager):
    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.get_tool_ids()


def test_has_tool_after_dispose_returns_false(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.dispose()

    assert manager.has_tool("select") is False


# ============================================================
# CONTROLLER BOUNDARY
# ============================================================


def test_tool_manager_does_not_subscribe_to_controller(
    controller,
):
    class ControllerWithSignals:
        def __init__(self):
            self.subscribe_called = False
            self.unsubscribe_called = False

        def subscribe(self, *args, **kwargs):
            self.subscribe_called = True

        def unsubscribe(self, *args, **kwargs):
            self.unsubscribe_called = True

    controller = ControllerWithSignals()

    ToolManager(controller)

    assert controller.subscribe_called is False
    assert controller.unsubscribe_called is False


def test_tool_manager_never_changes_controller_selection(
    manager,
    controller,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.activate("select")
    manager.deactivate()

    assert controller.set_tool_calls == []


def test_controller_selection_is_external_to_manager(
    manager,
    controller,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    controller.set_tool("select")

    assert controller.selected_tool == "select"
    assert manager.active_tool_id is None

    manager.activate(
        controller.selected_tool
    )

    assert manager.active_tool_id == "select"


# ============================================================
# DIAGNOSTICS
# ============================================================


def test_get_state_initial(manager):
    assert manager.get_state() == {
        "disposed": False,
        "registered_tools": (),
        "instantiated_tools": (),
        "active_tool_id": None,
        "has_active_tool": False,
    }


def test_get_state_tracks_registration(manager):
    manager.register_tools(
        {
            "select": FakeTool,
            "bus": FakeTool,
        }
    )

    state = manager.get_state()

    assert state["registered_tools"] == (
        "select",
        "bus",
    )

    assert state["instantiated_tools"] == ()


def test_get_state_tracks_instantiation(manager):
    manager.register_tools(
        {
            "select": FakeTool,
            "bus": FakeTool,
        }
    )

    manager.activate("select")

    state = manager.get_state()

    assert state["registered_tools"] == (
        "select",
        "bus",
    )

    assert state["instantiated_tools"] == (
        "select",
    )

    assert state["active_tool_id"] == "select"
    assert state["has_active_tool"] is True


def test_get_state_returns_snapshot(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    state = manager.get_state()

    state["registered_tools"] = (
        "corrupted",
    )

    assert manager.get_tool_ids() == (
        "select",
    )


def test_repr_contains_diagnostic_state(manager):
    manager.register_tool(
        "select",
        FakeTool,
    )

    representation = repr(manager)

    assert "ToolManager" in representation
    assert "active=None" in representation
    assert "registered=1" in representation
    assert "disposed=False" in representation


# ============================================================
# CONSTRUCTOR ERROR SEMANTICS
# ============================================================


def test_constructor_typeerror_propagates_unchanged(
    manager,
):
    def failing_factory(
        interaction_manager=None,
        preview=None,
    ):
        raise TypeError(
            "real constructor error"
        )

    manager.register_tool(
        "broken",
        failing_factory,
    )

    with pytest.raises(
        TypeError,
        match="real constructor error",
    ):
        manager.activate("broken")


# ============================================================
# OPTIONAL TOOL LIFECYCLE
# ============================================================


def test_tool_without_optional_lifecycle_methods_works(
    manager,
):
    manager.register_tool(
        "minimal",
        MinimalTool,
    )

    tool = manager.activate("minimal")

    assert tool is manager.active_tool

    manager.reset()
    manager.cancel()
    manager.deactivate()
    manager.dispose()

    assert manager.get_state()["disposed"] is True
