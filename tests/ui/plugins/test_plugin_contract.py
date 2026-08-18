# ============================================================
# File: tests/ui/plugins/test_plugin_contract.py
# GridForge V2 — Plugin Contract Tests
# ============================================================

from __future__ import annotations

import pytest

from ui.plugins.plugin_contract import (
    BasePlugin,
    PluginContractError,
    PluginContextProtocol,
    PluginLifecycleProtocol,
    PluginMetadata,
    PluginProtocol,
    PluginWidgetProvider,
    is_plugin,
    plugin_dependencies,
    plugin_id,
    plugin_metadata,
    plugin_widget,
    validate_plugin,
)
from ui.core.qt import QApplication, QWidget


# ============================================================
# QT FIXTURE
# ============================================================


@pytest.fixture(scope="session")
def qapp():
    """
    Provide one QApplication for the plugin contract test suite.
    """

    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    return app


# ============================================================
# TEST PLUGINS
# ============================================================


class ValidPlugin:
    """Minimal structural plugin satisfying PluginProtocol."""

    plugin_id = "test.plugin"
    plugin_name = "Test Plugin"
    plugin_version = "1.0"

    def __init__(self):
        self.initialized = False
        self.context_received = None
        self.shutdown_called = False

    def initialize(self, context=None):
        self.initialized = True
        self.context_received = context
        return "initialized"

    def shutdown(self):
        self.shutdown_called = True
        self.initialized = False


class InvalidPluginMissingID:
    plugin_name = "Invalid"
    plugin_version = "1.0"

    def initialize(self, context=None):
        pass

    def shutdown(self):
        pass


class InvalidPluginEmptyID:
    plugin_id = ""
    plugin_name = "Invalid"
    plugin_version = "1.0"

    def initialize(self, context=None):
        pass

    def shutdown(self):
        pass


class InvalidPluginMissingName:
    plugin_id = "invalid"
    plugin_version = "1.0"

    def initialize(self, context=None):
        pass

    def shutdown(self):
        pass


class InvalidPluginEmptyName:
    plugin_id = "invalid"
    plugin_name = ""
    plugin_version = "1.0"

    def initialize(self, context=None):
        pass

    def shutdown(self):
        pass


class InvalidPluginMissingVersion:
    plugin_id = "invalid"
    plugin_name = "Invalid"

    def initialize(self, context=None):
        pass

    def shutdown(self):
        pass


class InvalidPluginEmptyVersion:
    plugin_id = "invalid"
    plugin_name = "Invalid"
    plugin_version = ""

    def initialize(self, context=None):
        pass

    def shutdown(self):
        pass


class InvalidPluginMissingInitialize:
    plugin_id = "invalid"
    plugin_name = "Invalid"
    plugin_version = "1.0"

    def shutdown(self):
        pass


class InvalidPluginMissingShutdown:
    plugin_id = "invalid"
    plugin_name = "Invalid"
    plugin_version = "1.0"

    def initialize(self, context=None):
        pass


class MetadataPlugin(ValidPlugin):
    plugin_description = "A metadata test plugin."
    plugin_dependencies = ("canvas", "panels")
    plugin_optional = True
    plugin_metadata = {
        "category": "test",
        "author": "GridForge",
    }


class WidgetPlugin(ValidPlugin):
    def __init__(self, widget):
        super().__init__()
        self._widget = widget

    @property
    def widget(self):
        return self._widget


class CallableWidgetPlugin(ValidPlugin):
    def __init__(self, widget):
        super().__init__()
        self._widget = widget

    def widget(self):
        return self._widget


class NoWidgetPlugin(ValidPlugin):
    pass


class InvalidWidgetPlugin(ValidPlugin):
    @property
    def widget(self):
        return object()


class RaisingWidgetPlugin(ValidPlugin):
    @property
    def widget(self):
        raise RuntimeError("widget failure")


class BaseTestPlugin(BasePlugin):
    plugin_id = "base.test"
    plugin_name = "Base Test Plugin"
    plugin_version = "1.0"

    def __init__(
        self,
        events=None,
        *,
        initialize_error=None,
        shutdown_error=None,
        before_initialize_error=None,
        after_initialize_error=None,
        before_shutdown_error=None,
        after_shutdown_error=None,
    ):
        super().__init__()

        self.events = (
            events
            if events is not None
            else []
        )

        self.initialize_error = initialize_error
        self.shutdown_error = shutdown_error
        self.before_initialize_error = (
            before_initialize_error
        )
        self.after_initialize_error = (
            after_initialize_error
        )
        self.before_shutdown_error = (
            before_shutdown_error
        )
        self.after_shutdown_error = (
            after_shutdown_error
        )

        self.context_seen = None

    def before_initialize(self, context):
        self.events.append(
            "before_initialize"
        )

        if self.before_initialize_error is not None:
            raise self.before_initialize_error

    def _initialize(self, context):
        self.events.append(
            "initialize"
        )

        self.context_seen = context

        if self.initialize_error is not None:
            raise self.initialize_error

        return "initialize-result"

    def after_initialize(self):
        self.events.append(
            "after_initialize"
        )

        if self.after_initialize_error is not None:
            raise self.after_initialize_error

    def before_shutdown(self):
        self.events.append(
            "before_shutdown"
        )

        if self.before_shutdown_error is not None:
            raise self.before_shutdown_error

    def _shutdown(self):
        self.events.append(
            "shutdown"
        )

        if self.shutdown_error is not None:
            raise self.shutdown_error

    def after_shutdown(self):
        self.events.append(
            "after_shutdown"
        )

        if self.after_shutdown_error is not None:
            raise self.after_shutdown_error


class BaseWidgetPlugin(BasePlugin):
    plugin_id = "base.widget"
    plugin_name = "Base Widget Plugin"
    plugin_version = "1.0"

    def __init__(self, widget):
        super().__init__()
        self._widget = widget

    @property
    def widget(self):
        return self._widget

    def _initialize(self, context):
        return None

    def _shutdown(self):
        pass


# ============================================================
# PLUGIN METADATA
# ============================================================


class TestPluginMetadata:
    def test_valid_metadata(self):
        metadata = PluginMetadata(
            plugin_id="plugin.test",
            name="Plugin Test",
            version="2.5",
            description="Description",
            dependencies=("canvas", "panels"),
            optional=True,
            metadata={
                "category": "test",
                "owner": "GridForge",
            },
        )

        assert metadata.plugin_id == "plugin.test"
        assert metadata.name == "Plugin Test"
        assert metadata.version == "2.5"
        assert metadata.description == "Description"
        assert metadata.dependencies == (
            "canvas",
            "panels",
        )
        assert metadata.optional is True

    def test_metadata_is_immutable(self):
        metadata = PluginMetadata(
            plugin_id="plugin.test",
            name="Plugin Test",
            metadata={
                "key": "value",
            },
        )

        with pytest.raises(TypeError):
            metadata.metadata["key"] = "changed"

    def test_metadata_mapping_is_copied(self):
        source = {
            "key": "value",
        }

        metadata = PluginMetadata(
            plugin_id="plugin.test",
            name="Plugin Test",
            metadata=source,
        )

        source["key"] = "changed"

        assert metadata.metadata["key"] == "value"

    @pytest.mark.parametrize(
        "kwargs",
        [
            {
                "plugin_id": "",
                "name": "Plugin",
            },
            {
                "plugin_id": "plugin",
                "name": "",
            },
            {
                "plugin_id": "plugin",
                "name": "Plugin",
                "version": "",
            },
        ],
    )
    def test_rejects_empty_required_strings(self, kwargs):
        with pytest.raises(
            (TypeError, ValueError)
        ):
            PluginMetadata(**kwargs)

    def test_rejects_non_string_plugin_id(self):
        with pytest.raises(TypeError):
            PluginMetadata(
                plugin_id=123,
                name="Plugin",
            )

    def test_rejects_non_string_name(self):
        with pytest.raises(TypeError):
            PluginMetadata(
                plugin_id="plugin",
                name=123,
            )

    def test_rejects_non_string_version(self):
        with pytest.raises(TypeError):
            PluginMetadata(
                plugin_id="plugin",
                name="Plugin",
                version=123,
            )

    def test_rejects_non_string_description(self):
        with pytest.raises(TypeError):
            PluginMetadata(
                plugin_id="plugin",
                name="Plugin",
                description=123,
            )

    def test_rejects_non_tuple_dependencies(self):
        with pytest.raises(TypeError):
            PluginMetadata(
                plugin_id="plugin",
                name="Plugin",
                dependencies=["canvas"],
            )

    def test_rejects_duplicate_dependencies(self):
        with pytest.raises(ValueError):
            PluginMetadata(
                plugin_id="plugin",
                name="Plugin",
                dependencies=(
                    "canvas",
                    "canvas",
                ),
            )

    def test_rejects_self_dependency(self):
        with pytest.raises(ValueError):
            PluginMetadata(
                plugin_id="plugin",
                name="Plugin",
                dependencies=("plugin",),
            )

    def test_rejects_invalid_optional(self):
        with pytest.raises(TypeError):
            PluginMetadata(
                plugin_id="plugin",
                name="Plugin",
                optional=1,
            )

    def test_rejects_non_mapping_metadata(self):
        with pytest.raises(TypeError):
            PluginMetadata(
                plugin_id="plugin",
                name="Plugin",
                metadata=[],
            )

    def test_rejects_non_string_metadata_key(self):
        with pytest.raises(TypeError):
            PluginMetadata(
                plugin_id="plugin",
                name="Plugin",
                metadata={
                    1: "value",
                },
            )

    def test_rejects_empty_metadata_key(self):
        with pytest.raises(ValueError):
            PluginMetadata(
                plugin_id="plugin",
                name="Plugin",
                metadata={
                    "": "value",
                },
            )


# ============================================================
# STRUCTURAL PROTOCOLS
# ============================================================


class TestProtocols:
    def test_valid_plugin_is_runtime_protocol_instance(self):
        plugin = ValidPlugin()

        assert isinstance(
            plugin,
            PluginProtocol,
        )

    def test_invalid_plugin_is_not_runtime_protocol_instance(self):
        plugin = InvalidPluginMissingShutdown()

        assert not isinstance(
            plugin,
            PluginProtocol,
        )

    def test_widget_provider_is_structural(self, qapp):
        widget = QWidget()
        plugin = WidgetPlugin(widget)

        assert isinstance(
            plugin,
            PluginWidgetProvider,
        )

    def test_lifecycle_protocol_is_structural(self):
        class LifecycleObject:
            def before_initialize(self, context):
                pass

            def after_initialize(self):
                pass

            def before_shutdown(self):
                pass

            def after_shutdown(self):
                pass

        assert isinstance(
            LifecycleObject(),
            PluginLifecycleProtocol,
        )


# ============================================================
# BASE PLUGIN
# ============================================================


class TestBasePlugin:
    def test_constructs_uninitialized(self, qapp):
        plugin = BaseTestPlugin()

        assert plugin.initialized is False
        assert plugin.context is None

    def test_initialize_success(self, qapp):
        events = []
        context = object()

        plugin = BaseTestPlugin(events)

        result = plugin.initialize(context)

        assert result == "initialize-result"
        assert plugin.initialized is True
        assert plugin.context is context

        assert events == [
            "before_initialize",
            "initialize",
            "after_initialize",
        ]

    def test_initialize_is_idempotent(self, qapp):
        events = []
        context = object()

        plugin = BaseTestPlugin(events)

        first = plugin.initialize(context)
        second = plugin.initialize(object())

        assert first == "initialize-result"

        # BasePlugin returns self.widget when initialization is
        # repeated. BaseTestPlugin uses the default widget property,
        # which returns None.
        assert second is None

        assert plugin.initialized is True
        assert plugin.context is context

        assert events == [
            "before_initialize",
            "initialize",
            "after_initialize",
        ]

    def test_failed_initialize_clears_state(self, qapp):
        events = []

        error = RuntimeError(
            "initialize failure"
        )

        plugin = BaseTestPlugin(
            events,
            initialize_error=error,
        )

        with pytest.raises(
            RuntimeError,
            match="initialize failure",
        ):
            plugin.initialize(object())

        assert plugin.initialized is False
        assert plugin.context is None

        assert events == [
            "before_initialize",
            "initialize",
        ]

    def test_before_initialize_failure_clears_state(
        self,
        qapp,
    ):
        events = []

        plugin = BaseTestPlugin(
            events,
            before_initialize_error=RuntimeError(
                "before initialize failure"
            ),
        )

        with pytest.raises(
            RuntimeError,
            match="before initialize failure",
        ):
            plugin.initialize(object())

        assert plugin.initialized is False
        assert plugin.context is None

        assert events == [
            "before_initialize",
        ]

    def test_after_initialize_failure_clears_state(
        self,
        qapp,
    ):
        events = []

        plugin = BaseTestPlugin(
            events,
            after_initialize_error=RuntimeError(
                "after initialize failure"
            ),
        )

        with pytest.raises(
            RuntimeError,
            match="after initialize failure",
        ):
            plugin.initialize(object())

        assert plugin.initialized is False
        assert plugin.context is None

        assert events == [
            "before_initialize",
            "initialize",
            "after_initialize",
        ]

    def test_shutdown_success(self, qapp):
        events = []
        context = object()

        plugin = BaseTestPlugin(events)

        plugin.initialize(context)
        plugin.shutdown()

        assert plugin.initialized is False
        assert plugin.context is None

        assert events == [
            "before_initialize",
            "initialize",
            "after_initialize",
            "before_shutdown",
            "shutdown",
            "after_shutdown",
        ]

    def test_shutdown_is_idempotent(self, qapp):
        events = []

        plugin = BaseTestPlugin(events)

        plugin.initialize(object())
        plugin.shutdown()
        plugin.shutdown()

        assert events == [
            "before_initialize",
            "initialize",
            "after_initialize",
            "before_shutdown",
            "shutdown",
            "after_shutdown",
        ]

    def test_shutdown_clears_state_when_shutdown_fails(
        self,
        qapp,
    ):
        events = []

        plugin = BaseTestPlugin(
            events,
            shutdown_error=RuntimeError(
                "shutdown failure"
            ),
        )

        plugin.initialize(object())

        with pytest.raises(
            RuntimeError,
            match="shutdown failure",
        ):
            plugin.shutdown()

        assert plugin.initialized is False
        assert plugin.context is None

        assert events == [
            "before_initialize",
            "initialize",
            "after_initialize",
            "before_shutdown",
            "shutdown",
            "after_shutdown",
        ]

    def test_before_shutdown_failure_clears_state(
        self,
        qapp,
    ):
        events = []

        plugin = BaseTestPlugin(
            events,
            before_shutdown_error=RuntimeError(
                "before shutdown failure"
            ),
        )

        plugin.initialize(object())

        with pytest.raises(
            RuntimeError,
            match="before shutdown failure",
        ):
            plugin.shutdown()

        assert plugin.initialized is False
        assert plugin.context is None

        assert events == [
            "before_initialize",
            "initialize",
            "after_initialize",
            "before_shutdown",
            "after_shutdown",
        ]

    def test_after_shutdown_failure_propagates(
        self,
        qapp,
    ):
        events = []

        plugin = BaseTestPlugin(
            events,
            after_shutdown_error=RuntimeError(
                "after shutdown failure"
            ),
        )

        plugin.initialize(object())

        with pytest.raises(
            RuntimeError,
            match="after shutdown failure",
        ):
            plugin.shutdown()

        assert plugin.initialized is False
        assert plugin.context is None

    def test_shutdown_error_is_primary_when_both_shutdown_hooks_fail(
        self,
        qapp,
    ):
        events = []

        shutdown_error = RuntimeError(
            "primary shutdown failure"
        )

        after_shutdown_error = RuntimeError(
            "after shutdown failure"
        )

        plugin = BaseTestPlugin(
            events,
            shutdown_error=shutdown_error,
            after_shutdown_error=after_shutdown_error,
        )

        plugin.initialize(object())

        with pytest.raises(
            RuntimeError,
            match="primary shutdown failure",
        ) as exc_info:
            plugin.shutdown()

        assert exc_info.value is shutdown_error
        assert exc_info.value.__context__ is after_shutdown_error

        assert plugin.initialized is False
        assert plugin.context is None

    def test_shutdown_after_shutdown_runs_after_state_clear(
        self,
        qapp,
    ):
        observations = []

        class ObservingPlugin(BaseTestPlugin):
            def after_shutdown(self):
                observations.append(
                    (
                        self.initialized,
                        self.context,
                    )
                )

        plugin = ObservingPlugin()

        plugin.initialize("context")
        plugin.shutdown()

        assert observations == [
            (
                False,
                None,
            )
        ]

    def test_widget_default_is_none(self, qapp):
        plugin = BaseTestPlugin()

        assert plugin.widget is None

    def test_base_plugin_can_expose_widget(self, qapp):
        widget = QWidget()

        plugin = BaseWidgetPlugin(widget)

        assert plugin.widget is widget


# ============================================================
# CONTRACT VALIDATION
# ============================================================


class TestValidatePlugin:
    def test_valid_plugin_passes(self):
        plugin = ValidPlugin()

        validate_plugin(plugin)

    def test_none_is_invalid(self):
        with pytest.raises(
            PluginContractError,
            match="Plugin cannot be None",
        ):
            validate_plugin(None)

    def test_missing_plugin_id_is_invalid(self):
        with pytest.raises(
            PluginContractError,
            match="string plugin_id",
        ):
            validate_plugin(
                InvalidPluginMissingID()
            )

    def test_empty_plugin_id_is_invalid(self):
        with pytest.raises(
            PluginContractError,
            match="plugin_id cannot be empty",
        ):
            validate_plugin(
                InvalidPluginEmptyID()
            )

    def test_missing_plugin_name_is_invalid(self):
        with pytest.raises(
            PluginContractError,
            match="string plugin_name",
        ):
            validate_plugin(
                InvalidPluginMissingName()
            )

    def test_empty_plugin_name_is_invalid(self):
        with pytest.raises(
            PluginContractError,
            match="plugin_name cannot be empty",
        ):
            validate_plugin(
                InvalidPluginEmptyName()
            )

    def test_missing_plugin_version_is_invalid(self):
        with pytest.raises(
            PluginContractError,
            match="string plugin_version",
        ):
            validate_plugin(
                InvalidPluginMissingVersion()
            )

    def test_empty_plugin_version_is_invalid(self):
        with pytest.raises(
            PluginContractError,
            match="plugin_version cannot be empty",
        ):
            validate_plugin(
                InvalidPluginEmptyVersion()
            )

    def test_missing_initialize_is_invalid(self):
        with pytest.raises(
            PluginContractError,
            match="callable initialize",
        ):
            validate_plugin(
                InvalidPluginMissingInitialize()
            )

    def test_missing_shutdown_is_invalid(self):
        with pytest.raises(
            PluginContractError,
            match="callable shutdown",
        ):
            validate_plugin(
                InvalidPluginMissingShutdown()
            )

    def test_plugin_id_mismatch_is_rejected(self):
        plugin = ValidPlugin()

        with pytest.raises(
            PluginContractError,
            match="Plugin ID mismatch",
        ):
            validate_plugin(
                plugin,
                plugin_id="different.plugin",
            )

    def test_plugin_id_argument_must_be_string(self):
        plugin = ValidPlugin()

        with pytest.raises(TypeError):
            validate_plugin(
                plugin,
                plugin_id=123,
            )

    def test_empty_expected_plugin_id_is_rejected(self):
        plugin = ValidPlugin()

        with pytest.raises(ValueError):
            validate_plugin(
                plugin,
                plugin_id="",
            )

    def test_validation_is_side_effect_free(self):
        plugin = ValidPlugin()

        validate_plugin(plugin)

        assert plugin.initialized is False
        assert plugin.context_received is None
        assert plugin.shutdown_called is False


# ============================================================
# is_plugin
# ============================================================


class TestIsPlugin:
    def test_valid_plugin_returns_true(self):
        assert is_plugin(
            ValidPlugin()
        ) is True

    @pytest.mark.parametrize(
        "plugin",
        [
            None,
            InvalidPluginMissingID(),
            InvalidPluginEmptyID(),
            InvalidPluginMissingName(),
            InvalidPluginEmptyName(),
            InvalidPluginMissingVersion(),
            InvalidPluginEmptyVersion(),
            InvalidPluginMissingInitialize(),
            InvalidPluginMissingShutdown(),
        ],
    )
    def test_invalid_plugin_returns_false(self, plugin):
        assert is_plugin(plugin) is False


# ============================================================
# DEPENDENCY VALIDATION
# ============================================================


class TestPluginDependencies:
    def test_default_dependencies_are_empty(self):
        plugin = ValidPlugin()

        assert plugin_dependencies(plugin) == ()

    def test_valid_dependencies_are_returned(self):
        plugin = MetadataPlugin()

        assert plugin_dependencies(plugin) == (
            "canvas",
            "panels",
        )

    def test_dependencies_must_be_tuple(self):
        plugin = ValidPlugin()
        plugin.plugin_dependencies = ["canvas"]

        with pytest.raises(
            PluginContractError,
            match="must be a tuple",
        ):
            plugin_dependencies(plugin)

    def test_dependency_values_must_be_strings(self):
        plugin = ValidPlugin()
        plugin.plugin_dependencies = (123,)

        with pytest.raises(
            PluginContractError,
            match="must contain strings",
        ):
            plugin_dependencies(plugin)

    def test_empty_dependency_is_rejected(self):
        plugin = ValidPlugin()
        plugin.plugin_dependencies = ("",)

        with pytest.raises(
            PluginContractError,
            match="non-empty strings",
        ):
            plugin_dependencies(plugin)

    def test_duplicate_dependencies_are_rejected(self):
        plugin = ValidPlugin()
        plugin.plugin_dependencies = (
            "canvas",
            "canvas",
        )

        with pytest.raises(
            PluginContractError,
            match="duplicates",
        ):
            plugin_dependencies(plugin)

    def test_self_dependency_is_rejected(self):
        plugin = ValidPlugin()
        plugin.plugin_dependencies = (
            "test.plugin",
        )

        with pytest.raises(
            PluginContractError,
            match="cannot depend on itself",
        ):
            plugin_dependencies(plugin)


# ============================================================
# METADATA EXTRACTION
# ============================================================


class TestPluginMetadataExtraction:
    def test_extracts_metadata(self):
        plugin = MetadataPlugin()

        metadata = plugin_metadata(plugin)

        assert metadata.plugin_id == "test.plugin"
        assert metadata.name == "Test Plugin"
        assert metadata.version == "1.0"
        assert metadata.description == (
            "A metadata test plugin."
        )
        assert metadata.dependencies == (
            "canvas",
            "panels",
        )
        assert metadata.optional is True
        assert metadata.metadata["category"] == "test"
        assert metadata.metadata["author"] == "GridForge"

    def test_missing_optional_metadata_uses_defaults(self):
        plugin = ValidPlugin()

        metadata = plugin_metadata(plugin)

        assert metadata.description == ""
        assert metadata.dependencies == ()
        assert metadata.optional is False
        assert metadata.metadata == {}

    def test_invalid_description_is_rejected(self):
        plugin = ValidPlugin()
        plugin.plugin_description = 123

        with pytest.raises(
            PluginContractError,
            match="plugin_description",
        ):
            plugin_metadata(plugin)

    def test_invalid_optional_flag_is_rejected(self):
        plugin = ValidPlugin()
        plugin.plugin_optional = 1

        with pytest.raises(
            PluginContractError,
            match="plugin_optional",
        ):
            plugin_metadata(plugin)

    def test_invalid_metadata_mapping_is_rejected(self):
        plugin = ValidPlugin()
        plugin.plugin_metadata = []

        with pytest.raises(
            PluginContractError,
            match="plugin_metadata",
        ):
            plugin_metadata(plugin)


# ============================================================
# WIDGET EXTRACTION
# ============================================================


class TestPluginWidget:
    def test_none_plugin_returns_none(self):
        assert plugin_widget(None) is None

    def test_widget_property_returns_qwidget(
        self,
        qapp,
    ):
        widget = QWidget()
        plugin = WidgetPlugin(widget)

        assert plugin_widget(plugin) is widget

    def test_none_widget_returns_none(self, qapp):
        plugin = WidgetPlugin(None)

        assert plugin_widget(plugin) is None

    def test_callable_widget_provider_returns_qwidget(
        self,
        qapp,
    ):
        widget = QWidget()
        plugin = CallableWidgetPlugin(widget)

        assert plugin_widget(plugin) is widget

    def test_callable_widget_provider_returning_none(
        self,
        qapp,
    ):
        plugin = CallableWidgetPlugin(None)

        assert plugin_widget(plugin) is None

    def test_invalid_widget_type_is_rejected(
        self,
        qapp,
    ):
        plugin = InvalidWidgetPlugin()

        with pytest.raises(
            PluginContractError,
            match="not a QWidget",
        ):
            plugin_widget(plugin)

    def test_widget_provider_failure_is_wrapped(
        self,
        qapp,
    ):
        plugin = RaisingWidgetPlugin()

        with pytest.raises(
            PluginContractError,
            match="widget provider could not be accessed",
        ):
            plugin_widget(plugin)


# ============================================================
# SIMPLE HELPERS
# ============================================================


class TestPluginHelpers:
    def test_plugin_id_returns_valid_id(self):
        plugin = ValidPlugin()

        assert plugin_id(plugin) == "test.plugin"

    def test_plugin_id_validates_plugin(self):
        with pytest.raises(
            PluginContractError
        ):
            plugin_id(
                InvalidPluginMissingID()
            )

    def test_plugin_dependencies_validates_plugin(self):
        with pytest.raises(
            PluginContractError
        ):
            plugin_dependencies(
                InvalidPluginMissingID()
            )


# ============================================================
# BASE PLUGIN CONTRACT
# ============================================================


class TestBasePluginContract:
    def test_base_plugin_is_plugin_protocol(self):
        plugin = BaseTestPlugin()

        assert isinstance(
            plugin,
            PluginProtocol,
        )

    def test_base_plugin_has_expected_identity(self):
        plugin = BaseTestPlugin()

        assert plugin.plugin_id == "base.test"
        assert plugin.plugin_name == "Base Test Plugin"
        assert plugin.plugin_version == "1.0"

    def test_base_plugin_passes_contract_validation(self):
        plugin = BaseTestPlugin()

        validate_plugin(plugin)

    def test_base_plugin_is_plugin(self):
        plugin = BaseTestPlugin()

        assert is_plugin(plugin) is True

    def test_base_plugin_context_is_none_before_initialization(
        self,
    ):
        plugin = BaseTestPlugin()

        assert plugin.context is None
        assert plugin.initialized is False

    def test_base_plugin_context_is_available_during_initialization(
        self,
    ):
        context = object()

        plugin = BaseTestPlugin()

        plugin.initialize(context)

        assert plugin.context is context
        assert plugin.context_seen is context


# ============================================================
# CONTRACT BOUNDARY
# ============================================================


class TestContractBoundary:
    def test_validate_plugin_does_not_initialize_plugin(self):
        plugin = ValidPlugin()

        validate_plugin(plugin)

        assert plugin.initialized is False

    def test_plugin_metadata_does_not_initialize_plugin(self):
        plugin = ValidPlugin()

        plugin_metadata(plugin)

        assert plugin.initialized is False

    def test_plugin_dependencies_does_not_initialize_plugin(self):
        plugin = ValidPlugin()

        plugin_dependencies(plugin)

        assert plugin.initialized is False

    def test_plugin_widget_does_not_initialize_plugin(
        self,
        qapp,
    ):
        plugin = WidgetPlugin(
            QWidget()
        )

        plugin_widget(plugin)

        assert plugin.initialized is False
