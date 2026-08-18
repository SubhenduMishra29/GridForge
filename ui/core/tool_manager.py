# ============================================================
# File: tests/ui/core/test_tool_manager.py
# GridForge V2 — Tool Manager Tests
# ============================================================

import pytest

from ui.core.tool_manager import ToolManager


# ============================================================
# TEST DOUBLES
# ============================================================


class FakeController:
    """
    Controller test double.

    The canonical ToolManager contract does not subscribe to
    Controller signals and does not modify Controller selection.
    """

    def __init__(self):
        self.selected_tool_id = None
        self.set_tool_calls = []

    def set_tool(self, tool_id):
        self.set_tool_calls.append(tool_id)
        self.selected_tool_id = tool_id


class FakeInteractionManager:
    pass


class FakePreview:
    def __init__(self):
        self.clear_count = 0

    def clear(self):
        self.clear_count += 1


class FakeTool:
    constructed = 0
    constructor_arguments = []

    def __init__(
        self,
        interaction_manager=None,
        preview=None,
    ):
        type(self).constructed += 1
        type(self).constructor_arguments.append(
            {
                "interaction_manager": interaction_manager,
                "preview": preview,
            }
        )

        self.interaction_manager = interaction_manager
        self.preview = preview

        self.activate_count = 0
        self.deactivate_count = 0
        self.dispose_count = 0
        self.cancel_count = 0
        self.reset_count = 0

        self.fail_activate = False
        self.fail_deactivate = False
        self.fail_dispose = False
        self.fail_cancel = False
        self.fail_reset = False

    def activate(self):
        self.activate_count += 1

        if self.fail_activate:
            raise RuntimeError("activation failure")

    def deactivate(self):
        self.deactivate_count += 1

        if self.fail_deactivate:
            raise RuntimeError("deactivation failure")

    def dispose(self):
        self.dispose_count += 1

        if self.fail_dispose:
            raise RuntimeError("disposal failure")

    def cancel(self):
        self.cancel_count += 1

        if self.fail_cancel:
            raise RuntimeError("cancel failure")

        return True

    def reset(self):
        self.reset_count += 1

        if self.fail_reset:
            raise RuntimeError("reset failure")


class MinimalTool:
    """
    Tool implementing only the constructor contract.
    """

    def __init__(
        self,
        interaction_manager=None,
        preview=None,
    ):
        self.interaction_manager = interaction_manager
        self.preview = preview


class ConstructorTypeErrorTool:
    def __init__(
        self,
        interaction_manager=None,
        preview=None,
    ):
        raise TypeError(
            "real constructor failure"
        )


# ============================================================
# FIXTURES
# ============================================================


@pytest.fixture(autouse=True)
def reset_fake_tool_class():
    FakeTool.constructed = 0
    FakeTool.constructor_arguments = []
    yield
    FakeTool.constructed = 0
    FakeTool.constructor_arguments = []


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


def test_controller_is_retained(
    controller,
):
    manager = ToolManager(
        controller=controller
    )

    assert manager.controller is controller


def test_controller_does_not_need_subscription_api():
    class MinimalController:
        pass

    manager = ToolManager(
        controller=MinimalController()
    )

    assert manager.controller is not None


def test_initial_state(
    manager,
):
    assert manager.active_tool is None
    assert manager.active_tool_id is None
    assert manager.get_tool_ids() == ()


# ============================================================
# REGISTRATION
# ============================================================


def test_register_tool(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    assert manager.has_tool("select")
    assert manager.get_tool_ids() == ("select",)


def test_register_tool_does_not_instantiate(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    assert FakeTool.constructed == 0


@pytest.mark.parametrize(
    "tool_id",
    [
        None,
        123,
        [],
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


def test_register_rejects_empty_id(
    manager,
):
    with pytest.raises(ValueError):
        manager.register_tool(
            "",
            FakeTool,
        )


def test_register_rejects_whitespace_id(
    manager,
):
    with pytest.raises(ValueError):
        manager.register_tool(
            "   ",
            FakeTool,
        )


def test_register_rejects_non_callable_factory(
    manager,
):
    with pytest.raises(TypeError):
        manager.register_tool(
            "select",
            object(),
        )


def test_duplicate_registration_fails(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    with pytest.raises(ValueError):
        manager.register_tool(
            "select",
            FakeTool,
        )


def test_register_tools(
    manager,
):
    manager.register_tools(
        {
            "select": FakeTool,
            "line": FakeTool,
        }
    )

    assert manager.get_tool_ids() == (
        "select",
        "line",
    )


def test_register_tools_is_atomic(
    manager,
):
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


def test_register_tools_rejects_none(
    manager,
):
    with pytest.raises(ValueError):
        manager.register_tools(None)


def test_register_tools_rejects_non_dict(
    manager,
):
    with pytest.raises(TypeError):
        manager.register_tools([])


def test_registry_can_be_passed_as_dict(
    controller,
):
    manager = ToolManager(
        controller=controller,
        tool_registry={
            "select": FakeTool,
            "line": FakeTool,
        },
    )

    assert manager.get_tool_ids() == (
        "select",
        "line",
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
        controller=controller,
        tool_registry=Registry(),
    )

    assert manager.get_tool_ids() == (
        "select",
    )


def test_registry_can_expose_items(
    controller,
):
    class Registry:
        def items(self):
            return [
                ("select", FakeTool),
            ]

    manager = ToolManager(
        controller=controller,
        tool_registry=Registry(),
    )

    assert manager.get_tool_ids() == (
        "select",
    )


def test_invalid_registry_fails(
    controller,
):
    class InvalidRegistry:
        pass

    with pytest.raises(TypeError):
        ToolManager(
            controller=controller,
            tool_registry=InvalidRegistry(),
        )


# ============================================================
# LAZY INSTANTIATION
# ============================================================


def test_tool_is_constructed_on_first_activation(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    assert FakeTool.constructed == 0

    tool = manager.activate("select")

    assert FakeTool.constructed == 1
    assert manager.active_tool is tool


def test_tool_constructor_receives_canonical_arguments(
    manager,
    interaction_manager,
    preview,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.activate("select")

    args = FakeTool.constructor_arguments[0]

    assert args["interaction_manager"] is interaction_manager
    assert args["preview"] is preview


def test_existing_tool_instance_is_reused(
    manager,
):
    manager.register_tools(
        {
            "select": FakeTool,
            "line": FakeTool,
        }
    )

    first = manager.activate("select")
    manager.activate("line")
    second = manager.activate("select")

    assert first is second
    assert FakeTool.constructed == 2


def test_constructor_failure_preserves_current_tool(
    manager,
):
    manager.register_tools(
        {
            "select": FakeTool,
            "broken": ConstructorTypeErrorTool,
        }
    )

    current = manager.activate("select")

    with pytest.raises(TypeError, match="real constructor failure"):
        manager.activate("broken")

    assert manager.active_tool is current
    assert manager.active_tool_id == "select"


def test_factory_returning_none_fails(
    manager,
):
    manager.register_tool(
        "broken",
        lambda **kwargs: None,
    )

    with pytest.raises(RuntimeError):
        manager.activate("broken")

    assert manager.active_tool is None
    assert manager.active_tool_id is None


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

    with pytest.raises(KeyError):
        manager.activate("missing")

    assert manager.active_tool is None
    assert manager.active_tool_id is None


def test_activate_same_tool_is_noop(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")

    activation_count = tool.activate_count

    result = manager.activate("select")

    assert result is tool
    assert tool.activate_count == activation_count


def test_activation_deactivates_previous_tool(
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

    second.fail_activate = True

    with pytest.raises(RuntimeError):
        manager.activate("second")

    assert manager.active_tool is first
    assert manager.active_tool_id == "first"
    assert first.activate_count >= 2


def test_failed_activation_without_previous_tool_leaves_none(
    manager,
):
    class BrokenTool(FakeTool):
        def activate(self):
            self.activate_count += 1
            raise RuntimeError("activation failure")

    manager.register_tool(
        "broken",
        BrokenTool,
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

    manager.register_tools(
        {
            "first": RestorationTool,
            "second": FakeTool,
        }
    )

    first = manager.activate("first")
    second = manager.activate("second")

    # The second activation of first will fail during restoration.
    with pytest.raises(RuntimeError):
        manager.activate("first")

    assert manager.active_tool is None
    assert manager.active_tool_id is None

    assert first is not manager.active_tool
    assert second is not manager.active_tool


def test_activation_clears_preview(
    manager,
    preview,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.activate("select")

    assert preview.clear_count >= 1


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

    tool = manager.activate("select")

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

    tool = manager.activate("select")
    tool.fail_deactivate = True

    with pytest.raises(RuntimeError):
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

    tool = manager.activate("select")

    result = manager.activate(None)

    assert result is None
    assert tool.deactivate_count == 1
    assert manager.active_tool is None
    assert manager.active_tool_id is None


# ============================================================
# CANCELLATION
# ============================================================


def test_cancel_active_tool(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")

    result = manager.cancel()

    assert result is True
    assert tool.cancel_count == 1
    assert manager.active_tool is tool


def test_cancel_without_active_tool_returns_false(
    manager,
):
    assert manager.cancel() is False


def test_cancel_preserves_exception_and_clears_preview(
    manager,
    preview,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")
    tool.fail_cancel = True

    before = preview.clear_count

    with pytest.raises(RuntimeError):
        manager.cancel()

    assert preview.clear_count > before
    assert manager.active_tool is tool


# ============================================================
# RESET
# ============================================================


def test_reset_active_tool(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")

    manager.reset()

    assert tool.reset_count == 1
    assert manager.active_tool is tool


def test_reset_without_active_tool(
    manager,
):
    manager.reset()

    assert manager.active_tool is None


def test_reset_clears_preview_when_tool_reset_fails(
    manager,
    preview,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")
    tool.fail_reset = True

    before = preview.clear_count

    with pytest.raises(RuntimeError):
        manager.reset()

    assert preview.clear_count > before
    assert manager.active_tool is tool


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

    manager.unregister_tool("select")

    assert not manager.has_tool("select")
    assert manager.get_tool_ids() == ()
    assert FakeTool.constructed == 0


def test_unregister_disposes_existing_instance(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")
    manager.deactivate()

    manager.unregister_tool("select")

    assert tool.dispose_count == 1
    assert not manager.has_tool("select")


def test_unregister_active_tool_fails(
    manager,
):
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

    tool.fail_dispose = False

    manager.unregister_tool("select")

    assert not manager.has_tool("select")


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


def test_dispose_is_idempotent(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    tool = manager.activate("select")

    manager.dispose()
    manager.dispose()

    assert tool.dispose_count == 1
    assert manager.get_state()["disposed"] is True


def test_dispose_failure_is_retryable(
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

    first.fail_dispose = True

    with pytest.raises(RuntimeError):
        manager.dispose()

    assert manager.get_state()["disposed"] is False

    assert "first" in manager.get_state()[
        "instantiated_tools"
    ]

    first.fail_dispose = False

    manager.dispose()

    assert manager.get_state()["disposed"] is True
    assert manager.get_state()["instantiated_tools"] == ()

    assert first.dispose_count == 2
    assert second.dispose_count == 1


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

    assert manager.get_state()["disposed"] is False
    assert manager.active_tool is tool
    assert manager.active_tool_id == "select"

    tool.fail_deactivate = False

    manager.dispose()

    assert manager.get_state()["disposed"] is True


# ============================================================
# DISPOSED STATE
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
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.activate("select")


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
    manager.register_tool(
        "select",
        FakeTool,
    )

    manager.dispose()

    with pytest.raises(RuntimeError):
        manager.unregister_tool("select")


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


def test_has_tool_after_dispose_returns_false(
    manager,
):
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
    manager,
    controller,
):
    assert not hasattr(
        controller,
        "subscribe_calls",
    )


def test_tool_manager_never_changes_controller_selection(
    manager,
    controller,
):
    manager.register_tools(
        {
            "select": FakeTool,
            "line": FakeTool,
        }
    )

    controller.selected_tool_id = "controller_selection"

    manager.activate("select")
    manager.activate("line")
    manager.deactivate()

    assert controller.selected_tool_id == (
        "controller_selection"
    )

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

    assert controller.selected_tool_id == "select"
    assert manager.active_tool is None

    manager.activate("select")

    assert manager.active_tool_id == "select"
    assert controller.selected_tool_id == "select"


# ============================================================
# DIAGNOSTICS
# ============================================================


def test_get_state_initial(
    manager,
):
    assert manager.get_state() == {
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
            "line": FakeTool,
        }
    )

    state = manager.get_state()

    assert state["registered_tools"] == (
        "select",
        "line",
    )

    assert state["instantiated_tools"] == ()


def test_get_state_tracks_instantiation(
    manager,
):
    manager.register_tools(
        {
            "select": FakeTool,
            "line": FakeTool,
        }
    )

    manager.activate("select")

    state = manager.get_state()

    assert state["registered_tools"] == (
        "select",
        "line",
    )

    assert state["instantiated_tools"] == (
        "select",
    )

    assert state["active_tool_id"] == "select"
    assert state["has_active_tool"] is True


def test_get_state_returns_snapshot(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    state = manager.get_state()

    state["registered_tools"] = ("corrupted",)
    state["instantiated_tools"] = ("corrupted",)

    fresh = manager.get_state()

    assert fresh["registered_tools"] == (
        "select",
    )

    assert fresh["instantiated_tools"] == ()


def test_repr_contains_diagnostic_state(
    manager,
):
    manager.register_tool(
        "select",
        FakeTool,
    )

    text = repr(manager)

    assert "ToolManager" in text
    assert "registered=1" in text
    assert "disposed=False" in text
    assert "active=None" in text


# ============================================================
# CONSTRUCTOR ERROR CONTRACT
# ============================================================


def test_constructor_typeerror_propagates_unchanged(
    manager,
):
    manager.register_tool(
        "broken",
        ConstructorTypeErrorTool,
    )

    with pytest.raises(
        TypeError,
        match="real constructor failure",
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

    manager.cancel()
    manager.reset()
    manager.deactivate()
    manager.dispose()

    assert manager.get_state()["disposed"] is True
