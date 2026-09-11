# ============================================================
# File: tests/application/test_c9_protection_read_contract.py
# GridForge V2 — C9 Protection Read Contract Tests
# Author: Subhendu Mishra
# ============================================================

from types import MappingProxyType, SimpleNamespace

from core.application.read_models import ProtectionReadModel, RelayInputBindingReadModel, RelayReadModel
from core.application.read_service import ProtectionReadService
from core.application.application import Application


def relay():
    return SimpleNamespace(
        id="R1",
        name="Relay 1",
        type="OVER_CURRENT",
        function_type="50/51",
        plugin_id="plugin.oc",
        settings={"pickup": 1.2},
        in_service=True,
        enabled=True,
        blocked=False,
        picked_up=True,
        tripped=False,
        input_channels={"Ia": SimpleNamespace(id="CH1"), "Ib": SimpleNamespace(id="CH2")},
    )


def test_relay_projection_is_complete_and_identifier_only():
    read = ProtectionReadService._to_read_model(relay())
    assert read.object_id == "R1"
    assert read.plugin_id == "plugin.oc"
    assert read.settings["pickup"] == 1.2
    assert read.picked_up is True
    assert read.tripped is False
    assert read.input_channel_bindings == (
        RelayInputBindingReadModel("Ia", "CH1"),
        RelayInputBindingReadModel("Ib", "CH2"),
    )
    assert isinstance(read.settings, MappingProxyType)
    assert read.input_channel_bindings[0].channel_id == "CH1"


def test_relay_read_model_does_not_expose_core_channel_objects():
    channel = SimpleNamespace(id="CH1")
    read = ProtectionReadService._to_read_model(SimpleNamespace(
        id="R1", name="Relay", type="VOLTAGE", function_type="27", plugin_id=None,
        settings={}, in_service=True, enabled=True, blocked=False, picked_up=False,
        tripped=False, input_channels={"V": channel},
    ))
    assert read.input_channel_bindings[0].channel_id == "CH1"
    assert read.input_channel_bindings[0] is not channel


def test_application_protection_facade_delegates_to_protection_read_service():
    class StubProtectionReadService:
        def protection(self):
            return ProtectionReadModel(relays=())

        def relay(self, relay_id):
            return RelayReadModel("R1", "Relay", "VOLTAGE", "27", None, {}, True, True, False, False, False)

    class StubCommandManager:
        pass

    # The facade contract is tested independently of Core mutation plumbing.
    application = object.__new__(Application)
    application._protection_read_service = StubProtectionReadService()
    assert application.read_protection().relays == ()
    assert application.read_relay("R1").object_id == "R1"
