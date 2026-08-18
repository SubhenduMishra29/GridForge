# ============================================================
# File: tests/ui/plugins/test_plugin_state.py
# GridForge V2 — Plugin State Store Tests
# ============================================================

from __future__ import annotations

import pytest

from ui.plugins.plugin_state import (
    PluginState,
    PluginStateStore,
)


# ============================================================
# HELPERS
# ============================================================


def register_plugin(
    store: PluginStateStore,
    plugin_id: str = "test.plugin",
    *,
    enabled: bool = True,
    metadata=None,
):
    """
    Register one test plugin and return its state.
    """

    return store.register(
        plugin_id,
        enabled=enabled,
        metadata=metadata,
    )


# ============================================================
# PLUGIN STATE
# ============================================================


class TestPluginState:
    def test_default_state(self):
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

    def test_registered_state(self):
        state = PluginState(
            plugin_id="test.plugin",
            registered=True,
            enabled=True,
            initialized=False,
            generation=0,
            metadata={
                "category": "test",
            },
        )

        assert state.plugin_id == "test.plugin"
        assert state.registered is True
        assert state.enabled is True
        assert state.initialized is False
        assert state.generation == 0
        assert state.last_error is None
        assert state.metadata["category"] == "test"

    def test_state_metadata_is_copied(self):
        metadata = {
            "category": "test",
        }

        state = PluginState(
            plugin_id="test.plugin",
            metadata=metadata,
        )

        metadata["category"] = "changed"

        assert state.metadata["category"] == "test"

    def test_state_metadata_is_not_shared(self):
        state = PluginState(
            plugin_id="test.plugin",
            metadata={
                "key": "value",
            },
        )

        state.metadata["key"] = "changed"

        assert state.metadata["key"] == "changed"


# ============================================================
# STORE CONSTRUCTION
# ============================================================


class TestPluginStateStoreConstruction:
    def test_constructs_empty_store(self):
        store = PluginStateStore()

        assert store.plugin_ids == ()
        assert store.count == 0

    def test_new_store_contains_no_plugins(self):
        store = PluginStateStore()

        assert store.contains("test.plugin") is False
        assert store.get("test.plugin") is None


# ============================================================
# REGISTRATION
# ============================================================


class TestRegistration:
    def test_register_plugin(self):
        store = PluginStateStore()

        state = register_plugin(store)

        assert state.plugin_id == "test.plugin"
        assert state.registered is True
        assert state.enabled is True
        assert state.initialized is False
        assert state.generation == 0
        assert state.last_error is None

    def test_register_disabled_plugin(self):
        store = PluginStateStore()

        state = register_plugin(
            store,
            enabled=False,
        )

        assert state.registered is True
        assert state.enabled is False
        assert state.initialized is False

    def test_register_preserves_metadata(self):
        store = PluginStateStore()

        metadata = {
            "category": "test",
            "owner": "GridForge",
        }

        state = register_plugin(
            store,
            metadata=metadata,
        )

        assert state.metadata == metadata

    def test_register_copies_metadata(self):
        store = PluginStateStore()

        metadata = {
            "category": "test",
        }

        store.register(
            "test.plugin",
            metadata=metadata,
        )

        metadata["category"] = "changed"

        state = store.get("test.plugin")

        assert state.metadata["category"] == "test"

    def test_duplicate_registration_is_rejected(self):
        store = PluginStateStore()

        store.register("test.plugin")

        with pytest.raises(KeyError):
            store.register("test.plugin")

    def test_invalid_plugin_id_type_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(TypeError):
            store.register(123)

    def test_empty_plugin_id_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(ValueError):
            store.register("")

    def test_whitespace_plugin_id_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(ValueError):
            store.register("   ")

    def test_invalid_enabled_type_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(TypeError):
            store.register(
                "test.plugin",
                enabled=1,
            )

    def test_registration_order_is_preserved(self):
        store = PluginStateStore()

        store.register("plugin.a")
        store.register("plugin.b")
        store.register("plugin.c")

        assert store.plugin_ids == (
            "plugin.a",
            "plugin.b",
            "plugin.c",
        )


# ============================================================
# QUERIES
# ============================================================


class TestQueries:
    def test_contains_registered_plugin(self):
        store = PluginStateStore()

        store.register("test.plugin")

        assert store.contains("test.plugin") is True

    def test_contains_unknown_plugin(self):
        store = PluginStateStore()

        assert store.contains("unknown") is False

    def test_get_registered_plugin(self):
        store = PluginStateStore()

        registered = store.register(
            "test.plugin"
        )

        state = store.get(
            "test.plugin"
        )

        assert state is registered

    def test_get_unknown_plugin_returns_none(self):
        store = PluginStateStore()

        assert store.get("unknown") is None

    def test_require_registered_plugin(self):
        store = PluginStateStore()

        registered = store.register(
            "test.plugin"
        )

        state = store.require(
            "test.plugin"
        )

        assert state is registered

    def test_require_unknown_plugin_raises(self):
        store = PluginStateStore()

        with pytest.raises(KeyError):
            store.require("unknown")

    def test_plugin_ids_are_registration_order(self):
        store = PluginStateStore()

        store.register("a")
        store.register("b")
        store.register("c")

        assert store.plugin_ids == (
            "a",
            "b",
            "c",
        )

    def test_count_tracks_registered_plugins(self):
        store = PluginStateStore()

        assert store.count == 0

        store.register("a")
        assert store.count == 1

        store.register("b")
        assert store.count == 2


# ============================================================
# ENABLEMENT
# ============================================================


class TestEnablement:
    def test_is_enabled_after_registration(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        assert store.is_enabled(
            "test.plugin"
        ) is True

    def test_disabled_registration(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=False,
        )

        assert store.is_enabled(
            "test.plugin"
        ) is False

    def test_enable_plugin(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=False,
        )

        store.set_enabled(
            "test.plugin",
            True,
        )

        assert store.is_enabled(
            "test.plugin"
        ) is True

    def test_disable_plugin(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        store.set_enabled(
            "test.plugin",
            False,
        )

        assert store.is_enabled(
            "test.plugin"
        ) is False

    def test_enable_is_idempotent(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        store.set_enabled(
            "test.plugin",
            True,
        )

        assert store.is_enabled(
            "test.plugin"
        ) is True

    def test_disable_is_idempotent(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        store.set_enabled(
            "test.plugin",
            False,
        )

        store.set_enabled(
            "test.plugin",
            False,
        )

        assert store.is_enabled(
            "test.plugin"
        ) is False

    def test_cannot_disable_initialized_plugin(self):
        store = PluginStateStore()

        store.register("test.plugin")

        store.mark_initialized(
            "test.plugin"
        )

        with pytest.raises(RuntimeError):
            store.set_enabled(
                "test.plugin",
                False,
            )

    def test_unknown_plugin_enable_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(KeyError):
            store.set_enabled(
                "unknown",
                True,
            )

    def test_invalid_enabled_value_is_rejected(self):
        store = PluginStateStore()

        store.register("test.plugin")

        with pytest.raises(TypeError):
            store.set_enabled(
                "test.plugin",
                1,
            )


# ============================================================
# INITIALIZATION
# ============================================================


class TestInitialization:
    def test_plugin_starts_uninitialized(self):
        store = PluginStateStore()

        store.register("test.plugin")

        assert store.is_initialized(
            "test.plugin"
        ) is False

    def test_mark_initialized(self):
        store = PluginStateStore()

        store.register("test.plugin")

        store.mark_initialized(
            "test.plugin"
        )

        assert store.is_initialized(
            "test.plugin"
        ) is True

    def test_mark_initialized_increments_generation(self):
        store = PluginStateStore()

        store.register("test.plugin")

        assert store.get(
            "test.plugin"
        ).generation == 0

        store.mark_initialized(
            "test.plugin"
        )

        assert store.get(
            "test.plugin"
        ).generation == 1

    def test_mark_initialized_again_is_idempotent(self):
        store = PluginStateStore()

        store.register("test.plugin")

        store.mark_initialized(
            "test.plugin"
        )

        first_generation = store.get(
            "test.plugin"
        ).generation

        store.mark_initialized(
            "test.plugin"
        )

        assert store.is_initialized(
            "test.plugin"
        ) is True

        assert store.get(
            "test.plugin"
        ).generation == first_generation

    def test_mark_uninitialized(self):
        store = PluginStateStore()

        store.register("test.plugin")

        store.mark_initialized(
            "test.plugin"
        )

        store.mark_uninitialized(
            "test.plugin"
        )

        assert store.is_initialized(
            "test.plugin"
        ) is False

    def test_mark_uninitialized_is_idempotent(self):
        store = PluginStateStore()

        store.register("test.plugin")

        store.mark_uninitialized(
            "test.plugin"
        )

        assert store.is_initialized(
            "test.plugin"
        ) is False

    def test_cannot_initialize_disabled_plugin(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=False,
        )

        with pytest.raises(RuntimeError):
            store.mark_initialized(
                "test.plugin"
            )

    def test_unknown_plugin_initialize_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(KeyError):
            store.mark_initialized(
                "unknown"
            )

    def test_unknown_plugin_uninitialize_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(KeyError):
            store.mark_uninitialized(
                "unknown"
            )


# ============================================================
# ERROR STATE
# ============================================================


class TestErrors:
    def test_last_error_defaults_to_none(self):
        store = PluginStateStore()

        store.register("test.plugin")

        assert store.get(
            "test.plugin"
        ).last_error is None

    def test_set_last_error(self):
        store = PluginStateStore()

        store.register("test.plugin")

        error = RuntimeError(
            "plugin failure"
        )

        store.set_last_error(
            "test.plugin",
            error,
        )

        assert store.get(
            "test.plugin"
        ).last_error is error

    def test_clear_last_error(self):
        store = PluginStateStore()

        store.register("test.plugin")

        error = RuntimeError(
            "plugin failure"
        )

        store.set_last_error(
            "test.plugin",
            error,
        )

        store.clear_last_error(
            "test.plugin"
        )

        assert store.get(
            "test.plugin"
        ).last_error is None

    def test_clear_error_is_idempotent(self):
        store = PluginStateStore()

        store.register("test.plugin")

        store.clear_last_error(
            "test.plugin"
        )

        assert store.get(
            "test.plugin"
        ).last_error is None

    def test_unknown_plugin_set_error_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(KeyError):
            store.set_last_error(
                "unknown",
                RuntimeError(),
            )

    def test_unknown_plugin_clear_error_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(KeyError):
            store.clear_last_error(
                "unknown"
            )


# ============================================================
# UNREGISTRATION
# ============================================================


class TestUnregistration:
    def test_unregister_disabled_plugin(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=False,
        )

        result = store.unregister(
            "test.plugin"
        )

        assert result is not None
        assert store.contains(
            "test.plugin"
        ) is False

    def test_unregister_enabled_plugin_is_rejected(self):
        store = PluginStateStore()

        store.register(
            "test.plugin",
            enabled=True,
        )

        with pytest.raises(RuntimeError):
            store.unregister(
                "test.plugin"
            )

        assert store.contains(
            "test.plugin"
        ) is True

    def test_unregister_initialized_plugin_is_rejected(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        store.mark_initialized(
            "test.plugin"
        )

        with pytest.raises(RuntimeError):
            store.unregister(
                "test.plugin"
            )

        assert store.contains(
            "test.plugin"
        ) is True

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

        assert store.count == 0

    def test_unregister_unknown_plugin_is_rejected(self):
        store = PluginStateStore()

        with pytest.raises(KeyError):
            store.unregister(
                "unknown"
            )

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

        assert store.count == 1


# ============================================================
# LIFECYCLE STATE TRANSITIONS
# ============================================================


class TestLifecycleState:
    def test_normal_lifecycle(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        state = store.get(
            "test.plugin"
        )

        assert state.registered is True
        assert state.enabled is True
        assert state.initialized is False

        store.mark_initialized(
            "test.plugin"
        )

        assert state.registered is True
        assert state.enabled is True
        assert state.initialized is True
        assert state.generation == 1

        store.mark_uninitialized(
            "test.plugin"
        )

        assert state.registered is True
        assert state.enabled is True
        assert state.initialized is False

        store.set_enabled(
            "test.plugin",
            False,
        )

        assert state.registered is True
        assert state.enabled is False
        assert state.initialized is False

    def test_reinitialize_increments_generation(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

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

    def test_error_can_be_cleared_after_successful_transition(self):
        store = PluginStateStore()

        store.register(
            "test.plugin"
        )

        error = RuntimeError(
            "failure"
        )

        store.set_last_error(
            "test.plugin",
            error,
        )

        store.mark_initialized(
            "test.plugin"
        )

        store.clear_last_error(
            "test.plugin"
        )

        assert store.get(
            "test.plugin"
        ).last_error is None


# ============================================================
# STATE AUTHORITY
# ============================================================


class TestStateAuthority:
    def test_registry_state_is_canonical(self):
        store = PluginStateStore()

        state = store.register(
            "test.plugin"
        )

        assert store.is_enabled(
            "test.plugin"
        ) is state.enabled

        assert store.is_initialized(
            "test.plugin"
        ) is state.initialized

    def test_state_object_reflects_store_transitions(self):
        store = PluginStateStore()

        state = store.register(
            "test.plugin"
        )

        store.mark_initialized(
            "test.plugin"
        )

        assert state.initialized is True

        store.mark_uninitialized(
            "test.plugin"
        )

        assert state.initialized is False

        store.set_enabled(
            "test.plugin",
            False,
        )

        assert state.enabled is False

    def test_plugin_ids_are_not_mutable_through_result(self):
        store = PluginStateStore()

        store.register("plugin.a")
        store.register("plugin.b")

        plugin_ids = store.plugin_ids

        assert isinstance(
            plugin_ids,
            tuple,
        )

        assert plugin_ids == (
            "plugin.a",
            "plugin.b",
        )


# ============================================================
# INVALID IDENTIFIERS
# ============================================================


class TestIdentifierValidation:
    @pytest.mark.parametrize(
        "value",
        [
            None,
            123,
            [],
            {},
        ],
    )
    def test_contains_rejects_invalid_identifier(
        self,
        value,
    ):
        store = PluginStateStore()

        with pytest.raises(TypeError):
            store.contains(value)

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "   ",
        ],
    )
    def test_contains_rejects_empty_identifier(
        self,
        value,
    ):
        store = PluginStateStore()

        with pytest.raises(ValueError):
            store.contains(value)

    @pytest.mark.parametrize(
        "value",
        [
            None,
            123,
            [],
            {},
        ],
    )
    def test_get_rejects_invalid_identifier(
        self,
        value,
    ):
        store = PluginStateStore()

        with pytest.raises(TypeError):
            store.get(value)

    @pytest.mark.parametrize(
        "value",
        [
            "",
            "   ",
        ],
    )
    def test_get_rejects_empty_identifier(
        self,
        value,
    ):
        store = PluginStateStore()

        with pytest.raises(ValueError):
            store.get(value)
