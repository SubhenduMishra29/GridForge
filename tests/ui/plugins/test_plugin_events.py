"""
Tests for GridForge V2 UI plugin event infrastructure.

File:
    tests/ui/plugins/test_plugin_events.py
"""

from dataclasses import FrozenInstanceError

import pytest

from ui.plugins.plugin_events import (
    PluginErrorEvent,
    PluginEvent,
    PluginEventSource,
    PluginEventType,
    event_to_dict,
    is_failure_event,
    is_lifecycle_event,
    is_terminal_event,
    plugin_defined,
    plugin_disabled,
    plugin_enabled,
    plugin_failed,
    plugin_initialize_requested,
    plugin_initialized,
    plugin_initializing,
    plugin_load_requested,
    plugin_loaded,
    plugin_reset,
    plugin_shutdown,
    plugin_shutdown_requested,
    plugin_shutting_down,
    plugin_unload_requested,
    plugin_unloaded,
)


# ============================================================
# ENUMS
# ============================================================


def test_event_types_are_canonical():
    assert PluginEventType.DEFINED.value == "defined"

    assert PluginEventType.LOAD_REQUESTED.value == "load_requested"
    assert PluginEventType.LOADED.value == "loaded"

    assert (
        PluginEventType.INITIALIZE_REQUESTED.value
        == "initialize_requested"
    )
    assert PluginEventType.INITIALIZING.value == "initializing"
    assert PluginEventType.INITIALIZED.value == "initialized"

    assert PluginEventType.ENABLED.value == "enabled"
    assert PluginEventType.DISABLED.value == "disabled"

    assert (
        PluginEventType.SHUTDOWN_REQUESTED.value
        == "shutdown_requested"
    )
    assert (
        PluginEventType.SHUTTING_DOWN.value
        == "shutting_down"
    )
    assert PluginEventType.SHUTDOWN.value == "shutdown"

    assert (
        PluginEventType.UNLOAD_REQUESTED.value
        == "unload_requested"
    )
    assert PluginEventType.UNLOADED.value == "unloaded"

    assert PluginEventType.FAILED.value == "failed"
    assert PluginEventType.RESET.value == "reset"


def test_event_sources_are_canonical():
    assert PluginEventSource.LOADER.value == "loader"
    assert PluginEventSource.REGISTRY.value == "registry"
    assert PluginEventSource.MANAGER.value == "manager"
    assert PluginEventSource.PLUGIN.value == "plugin"
    assert PluginEventSource.SYSTEM.value == "system"


# ============================================================
# BASE EVENT
# ============================================================


def test_plugin_event_defaults_are_valid():
    event = PluginEvent(
        event_type=PluginEventType.LOADED,
        plugin_id="canvas",
    )

    assert event.plugin_id == "canvas"
    assert event.event_type is PluginEventType.LOADED
    assert event.source is PluginEventSource.SYSTEM
    assert isinstance(event.event_id, str)
    assert event.event_id
    assert isinstance(event.timestamp, float)
    assert event.sequence is None
    assert event.metadata == {}


def test_plugin_event_generates_unique_event_ids():
    event1 = PluginEvent(
        event_type=PluginEventType.LOADED,
        plugin_id="canvas",
    )

    event2 = PluginEvent(
        event_type=PluginEventType.LOADED,
        plugin_id="canvas",
    )

    assert event1.event_id != event2.event_id


def test_plugin_event_accepts_sequence():
    event = PluginEvent(
        event_type=PluginEventType.LOADED,
        plugin_id="canvas",
        sequence=10,
    )

    assert event.sequence == 10


def test_plugin_event_metadata_is_snapshotted():
    metadata = {
        "source": "test",
        "value": 10,
    }

    event = PluginEvent(
        event_type=PluginEventType.LOADED,
        plugin_id="canvas",
        metadata=metadata,
    )

    metadata["value"] = 99
    metadata["new"] = True

    assert event.metadata["value"] == 10
    assert "new" not in event.metadata


def test_plugin_event_metadata_is_immutable():
    event = PluginEvent(
        event_type=PluginEventType.LOADED,
        plugin_id="canvas",
        metadata={"value": 10},
    )

    with pytest.raises(TypeError):
        event.metadata["value"] = 20


def test_plugin_event_is_frozen():
    event = PluginEvent(
        event_type=PluginEventType.LOADED,
        plugin_id="canvas",
    )

    with pytest.raises(FrozenInstanceError):
        event.plugin_id = "other"


# ============================================================
# BASE EVENT VALIDATION
# ============================================================


def test_plugin_event_rejects_invalid_event_type():
    with pytest.raises(TypeError):
        PluginEvent(
            event_type="loaded",
            plugin_id="canvas",
        )


@pytest.mark.parametrize(
    "plugin_id",
    [
        None,
        "",
        "   ",
        123,
    ],
)
def test_plugin_event_rejects_invalid_plugin_id(plugin_id):
    with pytest.raises((TypeError, ValueError)):
        PluginEvent(
            event_type=PluginEventType.LOADED,
            plugin_id=plugin_id,
        )


@pytest.mark.parametrize(
    "source",
    [
        "manager",
        None,
        123,
    ],
)
def test_plugin_event_rejects_invalid_source(source):
    with pytest.raises(TypeError):
        PluginEvent(
            event_type=PluginEventType.LOADED,
            plugin_id="canvas",
            source=source,
        )


@pytest.mark.parametrize(
    "event_id",
    [
        None,
        "",
        "   ",
        123,
    ],
)
def test_plugin_event_rejects_invalid_event_id(event_id):
    with pytest.raises((TypeError, ValueError)):
        PluginEvent(
            event_type=PluginEventType.LOADED,
            plugin_id="canvas",
            event_id=event_id,
        )


@pytest.mark.parametrize(
    "timestamp",
    [
        True,
        False,
        "123",
        None,
    ],
)
def test_plugin_event_rejects_invalid_timestamp(timestamp):
    with pytest.raises(TypeError):
        PluginEvent(
            event_type=PluginEventType.LOADED,
            plugin_id="canvas",
            timestamp=timestamp,
        )


@pytest.mark.parametrize(
    "sequence",
    [
        -1,
        True,
        False,
        "1",
    ],
)
def test_plugin_event_rejects_invalid_sequence(sequence):
    with pytest.raises((TypeError, ValueError)):
        PluginEvent(
            event_type=PluginEventType.LOADED,
            plugin_id="canvas",
            sequence=sequence,
        )


def test_plugin_event_rejects_invalid_metadata():
    with pytest.raises(TypeError):
        PluginEvent(
            event_type=PluginEventType.LOADED,
            plugin_id="canvas",
            metadata="invalid",
        )


# ============================================================
# ERROR EVENT
# ============================================================


def test_plugin_error_event_defaults():
    event = PluginErrorEvent(
        event_type=PluginEventType.FAILED,
        plugin_id="canvas",
        error_type="RuntimeError",
        error_message="failure",
    )

    assert event.error_type == "RuntimeError"
    assert event.error_message == "failure"
    assert event.recoverable is False
    assert event.operation is None
    assert event.traceback is None


def test_plugin_error_event_is_frozen():
    event = PluginErrorEvent(
        event_type=PluginEventType.FAILED,
        plugin_id="canvas",
        error_type="RuntimeError",
        error_message="failure",
    )

    with pytest.raises(FrozenInstanceError):
        event.error_message = "changed"


@pytest.mark.parametrize(
    "error_type",
    [
        None,
        "",
        "   ",
        123,
    ],
)
def test_plugin_error_event_rejects_invalid_error_type(error_type):
    with pytest.raises((TypeError, ValueError)):
        PluginErrorEvent(
            event_type=PluginEventType.FAILED,
            plugin_id="canvas",
            error_type=error_type,
            error_message="failure",
        )


@pytest.mark.parametrize(
    "error_message",
    [
        None,
        "",
        "   ",
        123,
    ],
)
def test_plugin_error_event_rejects_invalid_error_message(
    error_message,
):
    with pytest.raises((TypeError, ValueError)):
        PluginErrorEvent(
            event_type=PluginEventType.FAILED,
            plugin_id="canvas",
            error_type="RuntimeError",
            error_message=error_message,
        )


@pytest.mark.parametrize(
    "recoverable",
    [
        None,
        0,
        1,
        "true",
    ],
)
def test_plugin_error_event_rejects_invalid_recoverable(
    recoverable,
):
    with pytest.raises(TypeError):
        PluginErrorEvent(
            event_type=PluginEventType.FAILED,
            plugin_id="canvas",
            error_type="RuntimeError",
            error_message="failure",
            recoverable=recoverable,
        )


def test_plugin_error_event_rejects_empty_operation():
    with pytest.raises(ValueError):
        PluginErrorEvent(
            event_type=PluginEventType.FAILED,
            plugin_id="canvas",
            error_type="RuntimeError",
            error_message="failure",
            operation="   ",
        )


def test_plugin_error_event_rejects_invalid_operation():
    with pytest.raises(TypeError):
        PluginErrorEvent(
            event_type=PluginEventType.FAILED,
            plugin_id="canvas",
            error_type="RuntimeError",
            error_message="failure",
            operation=123,
        )


def test_plugin_error_event_rejects_invalid_traceback():
    with pytest.raises(TypeError):
        PluginErrorEvent(
            event_type=PluginEventType.FAILED,
            plugin_id="canvas",
            error_type="RuntimeError",
            error_message="failure",
            traceback=123,
        )


# ============================================================
# EVENT FACTORIES
# ============================================================


@pytest.mark.parametrize(
    ("factory", "event_type", "default_source"),
    [
        (
            plugin_defined,
            PluginEventType.DEFINED,
            PluginEventSource.MANAGER,
        ),
        (
            plugin_load_requested,
            PluginEventType.LOAD_REQUESTED,
            PluginEventSource.MANAGER,
        ),
        (
            plugin_loaded,
            PluginEventType.LOADED,
            PluginEventSource.LOADER,
        ),
        (
            plugin_initialize_requested,
            PluginEventType.INITIALIZE_REQUESTED,
            PluginEventSource.MANAGER,
        ),
        (
            plugin_initializing,
            PluginEventType.INITIALIZING,
            PluginEventSource.MANAGER,
        ),
        (
            plugin_initialized,
            PluginEventType.INITIALIZED,
            PluginEventSource.MANAGER,
        ),
        (
            plugin_enabled,
            PluginEventType.ENABLED,
            PluginEventSource.MANAGER,
        ),
        (
            plugin_disabled,
            PluginEventType.DISABLED,
            PluginEventSource.MANAGER,
        ),
        (
            plugin_shutdown_requested,
            PluginEventType.SHUTDOWN_REQUESTED,
            PluginEventSource.MANAGER,
        ),
        (
            plugin_shutting_down,
            PluginEventType.SHUTTING_DOWN,
            PluginEventSource.MANAGER,
        ),
        (
            plugin_shutdown,
            PluginEventType.SHUTDOWN,
            PluginEventSource.MANAGER,
        ),
        (
            plugin_unload_requested,
            PluginEventType.UNLOAD_REQUESTED,
            PluginEventSource.MANAGER,
        ),
        (
            plugin_unloaded,
            PluginEventType.UNLOADED,
            PluginEventSource.REGISTRY,
        ),
        (
            plugin_reset,
            PluginEventType.RESET,
            PluginEventSource.MANAGER,
        ),
    ],
)
def test_standard_event_factories(
    factory,
    event_type,
    default_source,
):
    event = factory(
        "canvas",
        metadata={"test": True},
    )

    assert isinstance(event, PluginEvent)
    assert event.event_type is event_type
    assert event.plugin_id == "canvas"
    assert event.source is default_source
    assert event.metadata["test"] is True


def test_event_factory_allows_custom_source():
    event = plugin_loaded(
        "canvas",
        source=PluginEventSource.PLUGIN,
    )

    assert event.source is PluginEventSource.PLUGIN


def test_event_factory_snapshots_metadata():
    metadata = {"value": 1}

    event = plugin_loaded(
        "canvas",
        metadata=metadata,
    )

    metadata["value"] = 2

    assert event.metadata["value"] == 1


# ============================================================
# FAILURE FACTORY
# ============================================================


def test_plugin_failed_from_exception():
    error = RuntimeError("boom")

    event = plugin_failed(
        "canvas",
        error,
        operation="initialize",
        recoverable=True,
        traceback="traceback text",
    )

    assert isinstance(event, PluginErrorEvent)
    assert event.event_type is PluginEventType.FAILED
    assert event.plugin_id == "canvas"
    assert event.error_type == "RuntimeError"
    assert event.error_message == "boom"
    assert event.operation == "initialize"
    assert event.recoverable is True
    assert event.traceback == "traceback text"


def test_plugin_failed_from_string():
    event = plugin_failed(
        "canvas",
        "something failed",
    )

    assert event.error_type == "PluginError"
    assert event.error_message == "something failed"


def test_plugin_failed_empty_exception_message():
    error = RuntimeError()

    event = plugin_failed(
        "canvas",
        error,
    )

    assert (
        event.error_message
        == "Plugin lifecycle operation failed."
    )


def test_plugin_failed_empty_string():
    event = plugin_failed(
        "canvas",
        "   ",
    )

    assert (
        event.error_message
        == "Plugin lifecycle operation failed."
    )


def test_plugin_failed_rejects_invalid_error():
    with pytest.raises(TypeError):
        plugin_failed(
            "canvas",
            123,
        )


# ============================================================
# PREDICATES
# ============================================================


def test_is_lifecycle_event_accepts_plugin_event():
    event = plugin_loaded("canvas")

    assert is_lifecycle_event(event) is True


def test_is_lifecycle_event_accepts_error_event():
    event = plugin_failed(
        "canvas",
        "failure",
    )

    assert is_lifecycle_event(event) is True


def test_is_lifecycle_event_rejects_invalid_object():
    with pytest.raises(TypeError):
        is_lifecycle_event("event")


def test_is_failure_event():
    normal = plugin_loaded("canvas")
    failure = plugin_failed("canvas", "failure")

    assert is_failure_event(normal) is False
    assert is_failure_event(failure) is True


def test_is_failure_event_rejects_invalid_object():
    with pytest.raises(TypeError):
        is_failure_event(None)


@pytest.mark.parametrize(
    "event",
    [
        plugin_shutdown("canvas"),
        plugin_unloaded("canvas"),
        plugin_failed("canvas", "failure"),
    ],
)
def test_is_terminal_event(event):
    assert is_terminal_event(event) is True


@pytest.mark.parametrize(
    "event",
    [
        plugin_defined("canvas"),
        plugin_loaded("canvas"),
        plugin_initialized("canvas"),
        plugin_enabled("canvas"),
        plugin_disabled("canvas"),
        plugin_shutdown_requested("canvas"),
        plugin_shutting_down("canvas"),
        plugin_unload_requested("canvas"),
        plugin_reset("canvas"),
    ],
)
def test_non_terminal_events_are_not_terminal(event):
    assert is_terminal_event(event) is False


def test_is_terminal_event_rejects_invalid_object():
    with pytest.raises(TypeError):
        is_terminal_event(object())


# ============================================================
# SERIALIZATION
# ============================================================


def test_event_to_dict_returns_independent_dictionary():
    event = plugin_loaded(
        "canvas",
        metadata={
            "value": 10,
        },
    )

    data = event_to_dict(event)

    assert data["event_id"] == event.event_id
    assert data["event_type"] == "loaded"
    assert data["plugin_id"] == "canvas"
    assert data["source"] == "loader"
    assert data["timestamp"] == event.timestamp
    assert data["sequence"] is None
    assert data["metadata"] == {
        "value": 10,
    }

    data["metadata"]["value"] = 99

    assert event.metadata["value"] == 10


def test_error_event_serialization_contains_failure_fields():
    event = plugin_failed(
        "canvas",
        RuntimeError("boom"),
        operation="initialize",
        recoverable=True,
        traceback="trace",
        metadata={"phase": "test"},
    )

    data = event_to_dict(event)

    assert data["event_type"] == "failed"
    assert data["error_type"] == "RuntimeError"
    assert data["error_message"] == "boom"
    assert data["recoverable"] is True
    assert data["operation"] == "initialize"
    assert data["traceback"] == "trace"
    assert data["metadata"] == {
        "phase": "test",
    }


def test_event_to_dict_rejects_invalid_object():
    with pytest.raises(TypeError):
        event_to_dict(None)
