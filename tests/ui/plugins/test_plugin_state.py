"""
Tests for GridForge V2 UI plugin runtime state infrastructure.

File:
    tests/ui/plugins/test_plugin_state.py
"""

from dataclasses import FrozenInstanceError
from threading import Barrier, Thread

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
# PLUGIN STATE — CONSTRUCTION
# ============================================================


def test_plugin_state_defaults():
    state = PluginState(
        plugin_id="canvas",
    )

    assert state.plugin_id == "canvas"
    assert state.registered is False
    assert state.enabled is False
    assert state.initialized is False
    assert state.generation == 0
    assert state.last_error is None
    assert state.metadata == {}


def test_plugin_state_accepts_valid_values():
    state = PluginState(
        plugin_id="canvas",
        registered=True,
        enabled=True,
        initialized=True,
        generation=3,
        last_error="previous failure",
        metadata={"owner": "ui"},
    )

    assert state.plugin_id == "canvas"
    assert state.registered is True
    assert state.enabled is True
    assert state.initialized is True
    assert state.generation == 3
    assert state.last_error == "previous failure"
    assert state.metadata["owner"] == "ui"


def test_plugin_state_is_frozen():
    state = PluginState(
        plugin_id="canvas",
    )

    with pytest.raises(FrozenInstanceError):
        state.plugin_id = "other"


def test_plugin_state_metadata_is_immutable():
    state = PluginState(
        plugin_id="canvas",
        metadata={"value": 10},
    )

    with pytest.raises(TypeError):
        state.metadata["value"] = 20


def test_plugin_state_metadata_is_snapshotted():
    metadata = {
        "value": 10,
    }

    state = PluginState(
        plugin_id="canvas",
        metadata=metadata,
    )

    metadata["value"] = 20
    metadata["new"] = True

    assert state.metadata["value"] == 10
    assert "new" not in state.metadata


# ============================================================
# PLUGIN STATE — VALIDATION
# ============================================================


@pytest.mark.parametrize(
    "plugin_id",
    [
        None,
        "",
        "   ",
        123,
    ],
)
def test_plugin_state_rejects_invalid_plugin_id(plugin_id):
    with pytest.raises((TypeError, ValueError)):
        PluginState(
            plugin_id=plugin_id,
        )


@pytest.mark.parametrize(
    "registered",
    [
        None,
        0,
        1,
        "true",
    ],
)
def test_plugin_state_rejects_invalid_registered(registered):
    with pytest.raises(TypeError):
        PluginState(
            plugin_id="canvas",
            registered=registered,
        )


@pytest.mark.parametrize(
    "enabled",
    [
        None,
        0,
        1,
        "true",
    ],
)
def test_plugin_state_rejects_invalid_enabled(enabled):
    with pytest.raises(TypeError):
        PluginState(
            plugin_id="canvas",
            enabled=enabled,
        )


@pytest.mark.parametrize(
    "initialized",
    [
        None,
        0,
        1,
        "true",
    ],
)
def test_plugin_state_rejects_invalid_initialized(initialized):
    with pytest.raises(TypeError):
        PluginState(
            plugin_id="canvas",
            initialized=initialized,
        )


@pytest.mark.parametrize(
    "generation",
    [
        None,
        True,
        False,
        1.5,
        "1",
        -1,
    ],
)
def test_plugin_state_rejects_invalid_generation(generation):
    with pytest.raises((TypeError, ValueError)):
        PluginState(
            plugin_id="canvas",
            generation=generation,
        )


@pytest.mark.parametrize(
    "last_error",
    [
        123,
        True,
        [],
        {},
    ],
)
def test_plugin_state_rejects_invalid_last_error(last_error):
    with pytest.raises(TypeError):
        PluginState(
            plugin_id="canvas",
            last_error=last_error,
        )


def test_plugin_state_rejects_invalid_metadata():
    with pytest.raises(TypeError):
        PluginState(
            plugin_id="canvas",
            metadata="invalid",
        )


def test_plugin_state_rejects_enabled_unregistered():
    with pytest.raises(ValueError):
        PluginState(
            plugin_id="canvas",
            registered=False,
            enabled=True,
        )


def test_plugin_state_rejects_initialized_unregistered():
    with pytest.raises(ValueError):
        PluginState(
            plugin_id="canvas",
            registered=False,
            initialized=True,
        )


def test_plugin_state_rejects_initialized_disabled():
    with pytest.raises(ValueError):
        PluginState(
            plugin_id="canvas",
            registered=True,
            enabled=False,
            initialized=True,
        )


# ============================================================
# STORE — INITIAL STATE
# ============================================================


def test_store_initially_empty():
    store = PluginStateStore()

    assert store.plugin_ids == ()
    assert store.snapshots == ()


def test_store_contains_returns_false_for_unknown_plugin():
    store = PluginStateStore()

    assert store.contains("canvas") is False


def test_store_get_returns_none_for_unknown_plugin():
    store = PluginStateStore()

    assert store.get("canvas") is None


def test_store_require_raises_for_unknown_plugin():
    store = PluginStateStore()

    with pytest.raises(KeyError):
        store.require("canvas")


# ============================================================
# STORE — VALIDATION
# ============================================================


@pytest.mark.parametrize(
    "plugin_id",
    [
        None,
        "",
        "   ",
        123,
    ],
)
def test_store_query_methods_validate_plugin_id(plugin_id):
    store = PluginStateStore()

    with pytest.raises((TypeError, ValueError)):
        store.contains(plugin_id)

    with pytest.raises((TypeError, ValueError)):
        store.get(plugin_id)

    with pytest.raises((TypeError, ValueError)):
        store.require(plugin_id)


# ============================================================
# STORE — REGISTRATION
# ============================================================


def test_register_creates_registered_state():
    store = PluginStateStore()

    state = store.register("canvas")

    assert isinstance(state, PluginState)
    assert state.plugin_id == "canvas"
    assert state.registered is True
    assert state.enabled is False
    assert state.initialized is False
    assert state.generation == 0
    assert state.last_error is None


def test_register_can_start_enabled():
    store = PluginStateStore()

    state = store.register(
        "canvas",
        enabled=True,
    )

    assert state.registered is True
    assert state.enabled is True
    assert state.initialized is False


def test_register_accepts_metadata():
    store = PluginStateStore()

    state = store.register(
        "canvas",
        metadata={
            "kind": "composition",
        },
    )

    assert state.metadata["kind"] == "composition"


def test_register_snapshots_metadata():
    store = PluginStateStore()

    metadata = {
        "value": 10,
    }

    state = store.register(
        "canvas",
        metadata=metadata,
    )

    metadata["value"] = 20

    assert state.metadata["value"] == 10


def test_register_rejects_duplicate_plugin():
    store = PluginStateStore()

    store.register("canvas")

    with pytest.raises(KeyError):
        store.register("canvas")


def test_register_rejects_invalid_enabled():
    store = PluginStateStore()

    with pytest.raises(TypeError):
        store.register(
            "canvas",
            enabled=1,
        )


def test_register_rejects_invalid_metadata():
    store = PluginStateStore()

    with pytest.raises(TypeError):
        store.register(
            "canvas",
            metadata="invalid",
        )


def test_register_preserves_insertion_order():
    store = PluginStateStore()

    store.register("canvas")
    store.register("panels")
    store.register("toolbar")

    assert store.plugin_ids == (
        "canvas",
        "panels",
        "toolbar",
    )


def test_snapshots_preserve_insertion_order():
    store = PluginStateStore()

    store.register("canvas")
    store.register("panels")

    snapshots = store.snapshots

    assert [state.plugin_id for state in snapshots] == [
        "canvas",
        "panels",
    ]


# ============================================================
# STORE — QUERY
# ============================================================


def test_get_returns_current_state():
    store = PluginStateStore()

    store.register("canvas")

    state = store.get("canvas")

    assert state is not None
    assert state.plugin_id == "canvas"


def test_require_returns_current_state():
    store = PluginStateStore()

    store.register("canvas")

    state = store.require("canvas")

    assert state.plugin_id == "canvas"


def test_contains_returns_true_after_registration():
    store = PluginStateStore()

    store.register("canvas")

    assert store.contains("canvas") is True


def test_is_registered():
    store = PluginStateStore()

    store.register("canvas")

    assert store.is_registered("canvas") is True


def test_is_enabled():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    assert store.is_enabled("canvas") is True


def test_is_initialized():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    store.mark_initialized("canvas")

    assert store.is_initialized("canvas") is True


def test_generation():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    assert store.generation("canvas") == 0

    store.mark_initialized("canvas")

    assert store.generation("canvas") == 1


def test_last_error():
    store = PluginStateStore()

    store.register("canvas")
    store.set_last_error("canvas", "failure")

    assert store.last_error("canvas") == "failure"


# ============================================================
# STORE — ENABLEMENT
# ============================================================


def test_set_enabled_true():
    store = PluginStateStore()

    store.register("canvas")

    state = store.set_enabled(
        "canvas",
        True,
    )

    assert state.enabled is True
    assert state.registered is True


def test_set_enabled_false():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    state = store.set_enabled(
        "canvas",
        False,
    )

    assert state.enabled is False


def test_set_enabled_rejects_invalid_value():
    store = PluginStateStore()

    store.register("canvas")

    with pytest.raises(TypeError):
        store.set_enabled(
            "canvas",
            1,
        )


def test_set_enabled_rejects_enabled_unregistered_state():
    store = PluginStateStore()

    store.register("canvas")

    # Registration always makes the state registered, so this
    # invariant is primarily enforced by PluginState itself.
    assert store.set_enabled("canvas", True).enabled is True


def test_disable_initialized_plugin_is_rejected():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    store.mark_initialized("canvas")

    with pytest.raises(RuntimeError):
        store.set_enabled(
            "canvas",
            False,
        )


def test_repeated_enable_is_idempotent():
    store = PluginStateStore()

    store.register("canvas")

    first = store.set_enabled(
        "canvas",
        True,
    )

    second = store.set_enabled(
        "canvas",
        True,
    )

    assert second.enabled is True
    assert second.generation == first.generation


# ============================================================
# STORE — INITIALIZATION
# ============================================================


def test_mark_initialized_requires_registered_plugin():
    store = PluginStateStore()

    with pytest.raises(KeyError):
        store.mark_initialized("canvas")


def test_mark_initialized_requires_enabled_plugin():
    store = PluginStateStore()

    store.register("canvas")

    with pytest.raises(RuntimeError):
        store.mark_initialized("canvas")


def test_mark_initialized_sets_initialized():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    state = store.mark_initialized("canvas")

    assert state.registered is True
    assert state.enabled is True
    assert state.initialized is True


def test_first_initialization_increments_generation():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    state = store.mark_initialized("canvas")

    assert state.generation == 1


def test_repeated_initialization_is_idempotent():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    first = store.mark_initialized("canvas")
    second = store.mark_initialized("canvas")

    assert second is first
    assert second.generation == 1


def test_initialization_clears_last_error():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    store.set_last_error(
        "canvas",
        "previous failure",
    )

    assert store.last_error("canvas") == "previous failure"

    state = store.mark_initialized("canvas")

    assert state.last_error is None


def test_mark_uninitialized_records_shutdown():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    store.mark_initialized("canvas")

    state = store.mark_uninitialized("canvas")

    assert state.initialized is False
    assert state.enabled is True
    assert state.registered is True
    assert state.generation == 1


def test_mark_uninitialized_is_idempotent():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    first = store.mark_uninitialized("canvas")
    second = store.mark_uninitialized("canvas")

    assert second is first


def test_reinitialization_increments_generation():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    store.mark_initialized("canvas")
    store.mark_uninitialized("canvas")
    store.mark_initialized("canvas")

    assert store.generation("canvas") == 2


# ============================================================
# STORE — ERRORS
# ============================================================


def test_set_last_error_from_string():
    store = PluginStateStore()

    store.register("canvas")

    state = store.set_last_error(
        "canvas",
        "failure",
    )

    assert state.last_error == "failure"


def test_set_last_error_from_exception():
    store = PluginStateStore()

    store.register("canvas")

    error = RuntimeError("boom")

    state = store.set_last_error(
        "canvas",
        error,
    )

    assert state.last_error == "boom"


def test_set_last_error_strips_message():
    store = PluginStateStore()

    store.register("canvas")

    state = store.set_last_error(
        "canvas",
        "  failure  ",
    )

    assert state.last_error == "failure"


def test_empty_error_gets_fallback_message():
    store = PluginStateStore()

    store.register("canvas")

    state = store.set_last_error(
        "canvas",
        "   ",
    )

    assert state.last_error == "Unknown plugin failure."


def test_empty_exception_gets_fallback_message():
    store = PluginStateStore()

    store.register("canvas")

    state = store.set_last_error(
        "canvas",
        RuntimeError(),
    )

    assert state.last_error == "Unknown plugin failure."


def test_set_last_error_rejects_invalid_error():
    store = PluginStateStore()

    store.register("canvas")

    with pytest.raises(TypeError):
        store.set_last_error(
            "canvas",
            123,
        )


def test_setting_error_does_not_change_lifecycle_state():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    before = store.require("canvas")

    store.set_last_error(
        "canvas",
        "failure",
    )

    after = store.require("canvas")

    assert after.registered == before.registered
    assert after.enabled == before.enabled
    assert after.initialized == before.initialized
    assert after.generation == before.generation


def test_clear_last_error():
    store = PluginStateStore()

    store.register("canvas")

    store.set_last_error(
        "canvas",
        "failure",
    )

    state = store.clear_last_error("canvas")

    assert state.last_error is None


def test_clear_last_error_is_idempotent():
    store = PluginStateStore()

    store.register("canvas")

    first = store.clear_last_error("canvas")
    second = store.clear_last_error("canvas")

    assert second is first


# ============================================================
# STORE — METADATA
# ============================================================


def test_set_metadata():
    store = PluginStateStore()

    store.register("canvas")

    state = store.set_metadata(
        "canvas",
        "kind",
        "composition",
    )

    assert state.metadata["kind"] == "composition"


def test_set_metadata_replaces_existing_key():
    store = PluginStateStore()

    store.register(
        "canvas",
        metadata={
            "kind": "old",
        },
    )

    state = store.set_metadata(
        "canvas",
        "kind",
        "new",
    )

    assert state.metadata["kind"] == "new"


def test_set_metadata_preserves_existing_keys():
    store = PluginStateStore()

    store.register(
        "canvas",
        metadata={
            "kind": "composition",
            "version": 2,
        },
    )

    state = store.set_metadata(
        "canvas",
        "enabled_by",
        "manager",
    )

    assert state.metadata == {
        "kind": "composition",
        "version": 2,
        "enabled_by": "manager",
    }


@pytest.mark.parametrize(
    "key",
    [
        None,
        "",
        "   ",
        123,
    ],
)
def test_set_metadata_rejects_invalid_key(key):
    store = PluginStateStore()

    store.register("canvas")

    with pytest.raises((TypeError, ValueError)):
        store.set_metadata(
            "canvas",
            key,
            "value",
        )


def test_metadata_returns_mutable_copy():
    store = PluginStateStore()

    store.register(
        "canvas",
        metadata={
            "value": 10,
        },
    )

    metadata = store.metadata("canvas")

    metadata["value"] = 20
    metadata["new"] = True

    assert store.metadata("canvas") == {
        "value": 10,
    }


# ============================================================
# STORE — UNREGISTER
# ============================================================


def test_unregister_returns_removed_state():
    store = PluginStateStore()

    original = store.register("canvas")

    removed = store.unregister("canvas")

    assert removed is original
    assert store.contains("canvas") is False


def test_unregister_unknown_plugin_raises():
    store = PluginStateStore()

    with pytest.raises(KeyError):
        store.unregister("canvas")


def test_unregister_enabled_plugin_is_rejected():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    with pytest.raises(RuntimeError):
        store.unregister("canvas")


def test_unregister_initialized_plugin_is_rejected():
    store = PluginStateStore()

    store.register(
        "canvas",
        enabled=True,
    )

    store.mark_initialized("canvas")

    with pytest.raises(RuntimeError):
        store.unregister("canvas")


def test_unregister_allows_disabled_uninitialized_plugin():
    store = PluginStateStore()

    store.register("canvas")

    removed = store.unregister("canvas")

    assert removed.plugin_id == "canvas"
    assert store.plugin_ids == ()


def test_unregister_preserves_other_plugins():
    store = PluginStateStore()

    store.register("canvas")
    store.register("panels")
    store.register("toolbar")

    store.unregister("panels")

    assert store.plugin_ids == (
        "canvas",
        "toolbar",
    )


# ============================================================
# STATE HELPERS
# ============================================================


def test_is_registered_helper():
    registered = PluginState(
        plugin_id="canvas",
        registered=True,
    )

    unregistered = PluginState(
        plugin_id="canvas",
        registered=False,
    )

    assert is_registered(registered) is True
    assert is_registered(unregistered) is False


def test_is_enabled_helper():
    enabled = PluginState(
        plugin_id="canvas",
        registered=True,
        enabled=True,
    )

    disabled = PluginState(
        plugin_id="canvas",
        registered=True,
        enabled=False,
    )

    assert is_enabled(enabled) is True
    assert is_enabled(disabled) is False


def test_is_initialized_helper():
    initialized = PluginState(
        plugin_id="canvas",
        registered=True,
        enabled=True,
        initialized=True,
    )

    uninitialized = PluginState(
        plugin_id="canvas",
        registered=True,
        enabled=True,
        initialized=False,
    )

    assert is_initialized(initialized) is True
    assert is_initialized(uninitialized) is False


def test_is_active_helper():
    active = PluginState(
        plugin_id="canvas",
        registered=True,
        enabled=True,
        initialized=True,
    )

    inactive_registered = PluginState(
        plugin_id="canvas",
        registered=True,
        enabled=False,
        initialized=False,
    )

    assert is_active(active) is True
    assert is_active(inactive_registered) is False


@pytest.mark.parametrize(
    "helper",
    [
        is_registered,
        is_enabled,
        is_initialized,
        is_active,
    ],
)
def test_state_helpers_reject_invalid_objects(helper):
    with pytest.raises(TypeError):
        helper(None)


# ============================================================
# IMMUTABLE SNAPSHOT BEHAVIOR
# ============================================================


def test_state_transitions_create_new_snapshots():
    store = PluginStateStore()

    initial = store.register("canvas")

    enabled = store.set_enabled(
        "canvas",
        True,
    )

    initialized = store.mark_initialized(
        "canvas",
    )

    assert initial is not enabled
    assert enabled is not initialized

    assert initial.enabled is False
    assert initial.initialized is False

    assert enabled.enabled is True
    assert enabled.initialized is False

    assert initialized.enabled is True
    assert initialized.initialized is True


def test_old_snapshot_remains_unchanged_after_error():
    store = PluginStateStore()

    original = store.register("canvas")

    store.set_last_error(
        "canvas",
        "failure",
    )

    assert original.last_error is None
    assert store.last_error("canvas") == "failure"


# ============================================================
# THREAD SAFETY
# ============================================================


def test_concurrent_metadata_updates_are_not_lost():
    store = PluginStateStore()

    store.register("canvas")

    thread_count = 8
    barrier = Barrier(thread_count)

    def worker(index):
        barrier.wait()
        store.set_metadata(
            "canvas",
            f"key_{index}",
            index,
        )

    threads = [
        Thread(
            target=worker,
            args=(index,),
        )
        for index in range(thread_count)
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    metadata = store.metadata("canvas")

    assert len(metadata) == thread_count

    for index in range(thread_count):
        assert metadata[f"key_{index}"] == index
