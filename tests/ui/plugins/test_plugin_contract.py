from __future__ import annotations

import pytest

from ui.plugins.plugin_contract import (
    Plugin,
    plugin_id_of,
    supports_plugin_contract,
    validate_plugin,
)


class ValidPlugin:
    plugin_id = "test.plugin"

    def __init__(self) -> None:
        self.context = None
        self.shutdown_called = False

    def initialize(self, context):
        self.context = context
        return "initialized"

    def shutdown(self):
        self.shutdown_called = True


class MissingIdPlugin:
    def initialize(self, context):
        return None

    def shutdown(self):
        return None


class EmptyIdPlugin:
    plugin_id = ""

    def initialize(self, context):
        return None

    def shutdown(self):
        return None


class MissingInitializePlugin:
    plugin_id = "invalid"

    def shutdown(self):
        return None


class MissingShutdownPlugin:
    plugin_id = "invalid"

    def initialize(self, context):
        return None


def test_valid_plugin_satisfies_canonical_contract() -> None:
    plugin = ValidPlugin()

    assert isinstance(plugin, Plugin)
    validate_plugin(plugin)
    assert plugin_id_of(plugin) == "test.plugin"
    assert supports_plugin_contract(plugin) is True


def test_plugin_lifecycle_is_behavioral_contract() -> None:
    plugin = ValidPlugin()
    context = object()

    assert plugin.initialize(context) == "initialized"
    assert plugin.context is context

    plugin.shutdown()
    assert plugin.shutdown_called is True


@pytest.mark.parametrize(
    "plugin",
    [
        MissingIdPlugin(),
        EmptyIdPlugin(),
        MissingInitializePlugin(),
        MissingShutdownPlugin(),
    ],
)
def test_invalid_plugin_contracts_are_rejected(plugin) -> None:
    assert supports_plugin_contract(plugin) is False
    with pytest.raises((TypeError, ValueError)):
        validate_plugin(plugin)


def test_expected_plugin_id_is_checked() -> None:
    with pytest.raises(ValueError, match="identifier mismatch"):
        validate_plugin(ValidPlugin(), plugin_id="other.plugin")
