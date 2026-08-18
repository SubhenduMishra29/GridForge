# ============================================================
# File: tests/ui/plugins/test_plugin_state.py
# GridForge V2 — Plugin State Tests
# ============================================================

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from ui.plugins.plugin_state import (
    PluginState,
    PluginStateStore,
    is_active,
    is_enabled,
    is_initialized,
    is_registered,
)


# ============================================================
# PLUGIN STATE
# ============================================================


class TestPluginState:

    def test_constructs_with_defaults(self):
        state = PluginState(
            plugin_id="test.plugin",
        )

        assert state.plugin_id == "test.plugin"
        assert state.registered is False
        assert state.enabled is False
        assert state.initialized is False
        assert state.generation == 0
        assert state.last_error is None
        assert state.metadata == {}

    def test_valid_state(self):
        state = PluginState(
            plugin_id="test.plugin",
            registered=True,
            enabled=True,
            initialized=True,
            generation=3,
            last_error="failure",
            metadata={
                "category": "test",
            },
        )

        assert state.plugin_id == "test.plugin"
        assert state.registered is True
        assert state.enabled is True
        assert state.initialized is True
        assert state.generation == 3
        assert state.last_error == "failure"
        assert state.metadata["category"] == "test"

    def test_state_is_immutable(self):
        state = PluginState(
            plugin_id="test.plugin",
        )

        with pytest.raises(
            FrozenInstanceError
        ):
            state.plugin_id = "changed"

    def test_metadata_is_immutable(self):
        state = PluginState(
            plugin_id="test.plugin",
            metadata={
                "key": "value",
            },
        )

        with pytest.raises(TypeError):
            state.metadata["key"] = "changed"

        assert state.metadata["key"] == "value"

    def test_state_metadata_is_not_shared(self):
        source = {
            "key": "value",
        }

        state = PluginState(
            plugin_id="test.plugin",
            metadata=source,
        )

        source["key"] = "changed"

        assert state.metadata["key"] == "value"

    def test_rejects_non_string_plugin_id(self):
        with pytest.raises(TypeError):
            PluginState(
                plugin_id=123,
            )

    def test_rejects_empty_plugin_id(self):
        with pytest.raises(ValueError):
            PluginState(
                plugin_id="",
            )

    def test_rejects_whitespace_plugin_id(self):
        with pytest.raises(ValueError):
            PluginState(
                plugin_id="   ",
            )

    @pytest.mark.parametrize(
        "field_name",
        [
            "registered",
            "enabled",
            "initialized",
        ],
    )
    def test_rejects_non_bool_flags(
        self,
        field_name,
    ):
        kwargs = {
            "plugin_id": "test.plugin",
            field_name: 1,
        }

        with pytest.raises(TypeError):
            PluginState(**kwargs)

    def test_rejects_non_integer_generation(self):
        with pytest.raises(TypeError):
            PluginState(
                plugin_id="test.plugin",
                generation="1",
            )

    def test_rejects_bool_generation(self):
        with pytest.raises(TypeError):
            PluginState(
                plugin_id="test.plugin",
                generation=True,
            )

    def test_rejects_negative_generation(self):
        with pytest.raises(ValueError):
            PluginState(
                plugin_id="test.plugin",
                generation=-1,
            )

    def test_rejects_non_string_last_error(self):
        with pytest.raises(TypeError):
            PluginState(
                plugin_id="test.plugin",
                last_error=123,
            )

    def test_rejects_non_mapping_metadata(self):
        with pytest.raises(TypeError):
            PluginState(
                plugin_id="test.plugin",
                metadata=[],
            )

    def test_enabled_requires_registered(self):
        with pytest.raises(ValueError):
            PluginState(
                plugin_id="test.plugin",
                enabled=True,
            )

    def test_initialized_requires_registered(self):
        with pytest.raises(ValueError):
            PluginState(
                plugin_id="test.plugin",
                initialized=True,
            )

    def test_initialized_requires_enabled(self):
        with pytest.raises(ValueError):
            PluginState(
                plugin_id="test.plugin",
                registered=True,
                initialized=True,
            )


# ============================================================
# STORE CONSTRUCTION
# ============================================================


class TestPluginStateStoreConstruction:

    def test_constructs_empty_store(self):
        store = PluginStateStore()

        assert store.plugin_ids == ()
        assert store.snapshots == ()

    def test_contains_returns_false_for_empty_store(self):
        store = PluginStateStore()

        assert store.contains("test.plugin") is False

    def test_get_returns_none_for_unknown_plugin(self):
        store = PluginStateStore()

        assert store.get("test.plugin") is None

    def test_require_raises_for_unknown_plugin(self):
        store = PluginStateStore()

        with pytest.raises(
            KeyError,
            match="No state exists",
        ):
            store.require("test.plugin")


# ============================================================
# VALIDATION
# ============================================================


class TestValidation:

    @pytest.mark.parametrize(
        "value",
        [
            None,
            123,
            [],
            {},
        ],
    )
    def test_plugin_id_must_be_string(
        self,
        value,
    ):
        store = PluginStateStore()

        with pytest.raises(TypeError):
            store.contains(value)

    def test_empty_plugin_id_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(ValueError):
            store.contains("")

    def test_whitespace_plugin_id_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(ValueError):
            store.contains("   ")


# ============================================================
# REGISTRATION
# ============================================================


class TestRegistration:

    def test_register_creates_state(self):
        store = PluginStateStore()

        state = store.register(
            "test.plugin",
        )

        assert state.plugin_id == "test.plugin"
        assert state.registered is True
        assert state.enabled is False
        assert state.initialized is False
        assert state.generation == 0
        assert state.last_error is None
        assert state.metadata == {}

    def test_register_enabled(self):
        store = PluginStateStore()

        state = store.register(
            "test.plugin",
            enabled=True,
        )

        assert state.registered is True
        assert state.enabled is True
        assert state.initialized is False

    def test_register_metadata(self):
        store = PluginStateStore()

        state = store.register(
            "test.plugin",
            metadata={
                "category": "test",
                "owner": "GridForge",
            },
        )

        assert state.metadata == {
            "category": "test",
            "owner": "GridForge",
        }

    def test_register_copies_metadata(self):
        store = PluginStateStore()

        metadata = {
            "key": "value",
        }

        state = store.register(
            "test.plugin",
            metadata=metadata,
        )

        metadata["key"] = "changed"

        assert state.metadata["key"] == "value"

    def test_duplicate_registration_is_rejected(self):
        store = PluginStateStore()

        store.register("test.plugin")

        with pytest.raises(
            KeyError,
            match="already exists",
        ):
            store.register("test.plugin")

    def test_register_enabled_must_be_bool(self):
        store = PluginStateStore()

        with pytest.raises(TypeError):
            store.register(
                "test.plugin",
                enabled=1,
            )

    def test_register_metadata_must_be_mapping(self):
        store = PluginStateStore()

        with pytest.raises(TypeError):
            store.register(
                "test.plugin",
                metadata=[],
            )

    def test_plugin_ids_preserve_registration_order(self):
        store = PluginStateStore()

        store.register("plugin.a")
        store.register("plugin.b")
        store.register("plugin.c")

        assert store.plugin_ids == (
            "plugin.a",
            "plugin.b",
            "plugin.c",
        )

    def test_snapshots_preserve_registration_order(self):
        store = PluginStateStore()

        store.register("plugin.a")
        store.register("plugin.b")

        snapshots = store.snapshots

        assert tuple(
            state.plugin_id
            for state in snapshots
        ) == (
            "plugin.a",
            "plugin.b",
        )


# ============================================================
# QUERIES
# ============================================================


class TestQueries:

    def test_contains_registered_plugin(self):
        store = PluginStateStore()

        store.register("test.plugin")

        assert store.contains("test.plugin") is True

    def test_get_returns_registered_state(self):
        store = PluginStateStore()

        registered = store.register(
            "test.plugin"
        )

        state = store.get(
            "test.plugin"
        )

        assert state == registered

    def test_require_returns_registered_state(self):
        store = PluginStateStore()

        registered = store.register(
            "test.plugin"
        )

        assert store.require(
            "test.plugin"
        ) == registered

    def test_is_registered(self):
        store = PluginStateStore()

        store.register("test.plugin")

        assert store.is_registered(
            "test.plugin"
        ) is True

    def test_is_enabled(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        assert store.is_enabled(
            "test.plugin"
        ) is True

    def test_is_initialized(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        assert store.is_initialized(
            "test.plugin"
        ) is False

    def test_generation(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        assert store.generation(
            "test.plugin"
        ) == 0

    def test_last_error(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        assert store.last_error(
            "test.plugin"
        ) is None


# ============================================================
# ENABLEMENT
# ============================================================


class TestEnablement:

    def test_enable_registered_plugin(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
        )

        state = store.set_enabled(
            "test.plugin",
            True,
        )

        assert state.enabled is True
        assert state.registered is True

    def test_disable_registered_plugin(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        state = store.set_enabled(
            "test.plugin",
            False,
        )

        assert state.enabled is False

    def test_enable_unregistered_plugin_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(
            KeyError,
        ):
            store.set_enabled(
                "test.plugin",
                True,
            )

    def test_cannot_disable_initialized_plugin(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        store.mark_initialized(
            "test.plugin"
        )

        with pytest.raises(
            RuntimeError,
            match="Cannot disable initialized",
        ):
            store.set_enabled(
                "test.plugin",
                False,
            )

    def test_enabled_must_be_bool(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        with pytest.raises(TypeError):
            store.set_enabled(
                "test.plugin",
                1,
            )

    def test_enablement_preserves_other_state(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            metadata={
                "key": "value",
            },
        )

        state = store.set_enabled(
            "test.plugin",
            True,
        )

        assert state.registered is True
        assert state.enabled is True
        assert state.initialized is False
        assert state.generation == 0
        assert state.metadata["key"] == "value"


# ============================================================
# INITIALIZATION
# ============================================================


class TestInitialization:

    def test_mark_initialized(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        state = store.mark_initialized(
            "test.plugin"
        )

        assert state.initialized is True
        assert state.generation == 1
        assert state.last_error is None

    def test_mark_initialized_increments_generation(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        assert store.get(
            "test.plugin"
        ).generation == 0

        store.mark_initialized(
            "test.plugin"
        )

        assert store.get(
            "test.plugin"
        ).generation == 1

        store.mark_uninitialized(
            "test.plugin"
        )

        store.mark_initialized(
            "test.plugin"
        )

        assert store.get(
            "test.plugin"
        ).generation == 2

    def test_mark_initialized_again_is_idempotent(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        first = store.mark_initialized(
            "test.plugin"
        )

        second = store.mark_initialized(
            "test.plugin"
        )

        assert first == second
        assert first is second

        assert second.generation == 1

    def test_mark_initialized_requires_registered_plugin(self):
        store = PluginStateStore()

        with pytest.raises(
            KeyError,
        ):
            store.mark_initialized(
                "test.plugin"
            )

    def test_mark_initialized_requires_enabled_plugin(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=False,
        )

        with pytest.raises(
            RuntimeError,
            match="Cannot initialize disabled",
        ):
            store.mark_initialized(
                "test.plugin"
            )

    def test_mark_uninitialized(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        store.mark_initialized(
            "test.plugin"
        )

        state = store.mark_uninitialized(
            "test.plugin"
        )

        assert state.initialized is False
        assert state.generation == 1

    def test_mark_uninitialized_is_idempotent(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        first = store.mark_uninitialized(
            "test.plugin"
        )

        second = store.mark_uninitialized(
            "test.plugin"
        )

        assert first == second
        assert first is second

    def test_mark_uninitialized_preserves_generation(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        store.mark_initialized(
            "test.plugin"
        )

        store.mark_uninitialized(
            "test.plugin"
        )

        assert store.generation(
            "test.plugin"
        ) == 1

    def test_successful_initialization_clears_error(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        store.set_last_error(
            "test.plugin",
            RuntimeError("failure"),
        )

        state = store.mark_initialized(
            "test.plugin"
        )

        assert state.initialized is True
        assert state.last_error is None


# ============================================================
# ERRORS
# ============================================================


class TestErrors:

    def test_set_last_error_from_exception(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        error = RuntimeError(
            "plugin failure"
        )

        state = store.set_last_error(
            "test.plugin",
            error,
        )

        assert state.last_error == (
            "plugin failure"
        )

        assert store.get(
            "test.plugin"
        ).last_error == "plugin failure"

    def test_set_last_error_from_string(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        state = store.set_last_error(
            "test.plugin",
            "plugin failure",
        )

        assert state.last_error == (
            "plugin failure"
        )

    def test_set_last_error_strips_whitespace(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        state = store.set_last_error(
            "test.plugin",
            "  failure  ",
        )

        assert state.last_error == "failure"

    def test_empty_error_gets_default_message(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        state = store.set_last_error(
            "test.plugin",
            "   ",
        )

        assert state.last_error == (
            "Unknown plugin failure."
        )

    def test_set_last_error_rejects_invalid_type(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        with pytest.raises(TypeError):
            store.set_last_error(
                "test.plugin",
                123,
            )

    def test_clear_last_error(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        store.set_last_error(
            "test.plugin",
            "failure",
        )

        state = store.clear_last_error(
            "test.plugin"
        )

        assert state.last_error is None

    def test_clear_last_error_is_idempotent(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        store.set_last_error(
            "test.plugin",
            "failure",
        )

        first = store.clear_last_error(
            "test.plugin"
        )

        second = store.clear_last_error(
            "test.plugin"
        )

        assert first.last_error is None
        assert second.last_error is None
        assert first == second
        assert first is not second

    def test_error_recording_does_not_change_lifecycle_state(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        store.set_last_error(
            "test.plugin",
            "failure",
        )

        state = store.get(
            "test.plugin"
        )

        assert state.registered is True
        assert state.enabled is True
        assert state.initialized is False
        assert state.generation == 0


# ============================================================
# METADATA
# ============================================================


class TestMetadata:

    def test_set_metadata(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        state = store.set_metadata(
            "test.plugin",
            "category",
            "test",
        )

        assert state.metadata == {
            "category": "test",
        }

    def test_set_metadata_updates_existing_value(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            metadata={
                "category": "old",
            },
        )

        state = store.set_metadata(
            "test.plugin",
            "category",
            "new",
        )

        assert state.metadata["category"] == "new"

    def test_set_metadata_preserves_existing_values(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            metadata={
                "category": "test",
            },
        )

        state = store.set_metadata(
            "test.plugin",
            "owner",
            "GridForge",
        )

        assert state.metadata == {
            "category": "test",
            "owner": "GridForge",
        }

    def test_metadata_returns_mutable_copy(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            metadata={
                "key": "value",
            },
        )

        metadata = store.metadata(
            "test.plugin"
        )

        metadata["key"] = "changed"

        assert metadata["key"] == "changed"
        assert store.metadata(
            "test.plugin"
        )["key"] == "value"

    def test_metadata_key_must_be_string(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        with pytest.raises(TypeError):
            store.set_metadata(
                "test.plugin",
                123,
                "value",
            )

    def test_metadata_key_cannot_be_empty(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        with pytest.raises(ValueError):
            store.set_metadata(
                "test.plugin",
                "",
                "value",
            )


# ============================================================
# UNREGISTRATION
# ============================================================


class TestUnregistration:

    def test_unregister_disabled_uninitialized_plugin(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=False,
        )

        state = store.unregister(
            "test.plugin"
        )

        assert state.plugin_id == (
            "test.plugin"
        )

        assert store.get(
            "test.plugin"
        ) is None

        assert store.contains(
            "test.plugin"
        ) is False

    def test_unregister_initialized_plugin_is_rejected(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        store.mark_initialized(
            "test.plugin"
        )

        with pytest.raises(
            RuntimeError,
            match="Cannot unregister initialized",
        ):
            store.unregister(
                "test.plugin"
            )

    def test_unregister_enabled_plugin_is_rejected(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        with pytest.raises(
            RuntimeError,
            match="Cannot unregister enabled",
        ):
            store.unregister(
                "test.plugin"
            )

    def test_unregister_unknown_plugin_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(
            KeyError,
        ):
            store.unregister(
                "test.plugin"
            )

    def test_unregister_removes_plugin(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=False,
        )

        store.unregister(
            "test.plugin"
        )

        assert store.get(
            "test.plugin"
        ) is None

        assert store.contains(
            "test.plugin"
        ) is False

        assert store.plugin_ids == ()

    def test_unregister_preserves_other_plugins(self):
        store = PluginStateStore()

        store.register(
            "plugin.a",
            enabled=False,
        )

        store.register(
            "plugin.b",
            enabled=False,
        )

        store.unregister(
            "plugin.a"
        )

        assert store.plugin_ids == (
            "plugin.b",
        )

        assert store.contains(
            "plugin.b"
        ) is True


# ============================================================
# LIFECYCLE STATE
# ============================================================


class TestLifecycleState:

    def test_normal_lifecycle(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        state = store.get(
            "test.plugin"
        )

        assert state.registered is True
        assert state.enabled is True
        assert state.initialized is False
        assert state.generation == 0

        store.mark_initialized(
            "test.plugin"
        )

        state = store.get(
            "test.plugin"
        )

        assert state.registered is True
        assert state.enabled is True
        assert state.initialized is True
        assert state.generation == 1

        store.mark_uninitialized(
            "test.plugin"
        )

        state = store.get(
            "test.plugin"
        )

        assert state.registered is True
        assert state.enabled is True
        assert state.initialized is False
        assert state.generation == 1

    def test_reinitialize_increments_generation(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        store.mark_initialized(
            "test.plugin"
        )

        store.mark_uninitialized(
            "test.plugin"
        )

        store.mark_initialized(
            "test.plugin"
        )

        assert store.generation(
            "test.plugin"
        ) == 2

    def test_error_can_be_cleared_after_successful_transition(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        store.set_last_error(
            "test.plugin",
            RuntimeError("failure"),
        )

        assert store.last_error(
            "test.plugin"
        ) == "failure"

        store.mark_initialized(
            "test.plugin"
        )

        assert store.last_error(
            "test.plugin"
        ) is None


# ============================================================
# STATE AUTHORITY
# ============================================================


class TestStateAuthority:

    def test_state_object_reflects_store_transitions(self):
        store = PluginStateStore()

        initial = store.register(
            "test.plugin",
            enabled=True,
        )

        initialized = store.mark_initialized(
            "test.plugin"
        )

        uninitialized = store.mark_uninitialized(
            "test.plugin"
        )

        assert initial.registered is True
        assert initial.enabled is True
        assert initial.initialized is False
        assert initial.generation == 0

        assert initialized.registered is True
        assert initialized.enabled is True
        assert initialized.initialized is True
        assert initialized.generation == 1

        assert uninitialized.registered is True
        assert uninitialized.enabled is True
        assert uninitialized.initialized is False
        assert uninitialized.generation == 1

        assert store.get(
            "test.plugin"
        ) == uninitialized

        assert initial != initialized
        assert initialized != uninitialized

    def test_snapshots_are_immutable(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        snapshot = store.get(
            "test.plugin"
        )

        store.mark_initialized(
            "test.plugin"
        )

        assert snapshot.initialized is False
        assert snapshot.generation == 0

        current = store.get(
            "test.plugin"
        )

        assert current.initialized is True
        assert current.generation == 1


# ============================================================
# STATE HELPERS
# ============================================================


class TestStateHelpers:

    def test_is_registered(self):
        state = PluginState(
            plugin_id="test.plugin",
            registered=True,
        )

        assert is_registered(state) is True

    def test_is_enabled(self):
        state = PluginState(
            plugin_id="test.plugin",
            registered=True,
            enabled=True,
        )

        assert is_enabled(state) is True

    def test_is_initialized(self):
        state = PluginState(
            plugin_id="test.plugin",
            registered=True,
            enabled=True,
            initialized=True,
        )

        assert is_initialized(state) is True

    def test_is_active(self):
        state = PluginState(
            plugin_id="test.plugin",
            registered=True,
            enabled=True,
            initialized=True,
        )

        assert is_active(state) is True

    def test_inactive_when_unregistered(self):
        state = PluginState(
            plugin_id="test.plugin",
        )

        assert is_active(state) is False

    def test_inactive_when_disabled(self):
        state = PluginState(
            plugin_id="test.plugin",
            registered=True,
            enabled=False,
            initialized=False,
        )

        assert is_active(state) is False

    def test_inactive_when_uninitialized(self):
        state = PluginState(
            plugin_id="test.plugin",
            registered=True,
            enabled=True,
            initialized=False,
        )

        assert is_active(state) is False

    @pytest.mark.parametrize(
        "helper",
        [
            is_registered,
            is_enabled,
            is_initialized,
            is_active,
        ],
    )
    def test_helpers_reject_invalid_state(
        self,
        helper,
    ):
        with pytest.raises(TypeError):
            helper(None)


# ============================================================
# END
# ============================================================
