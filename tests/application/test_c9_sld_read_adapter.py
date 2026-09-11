# ============================================================
# File: tests/application/test_c9_sld_read_adapter.py
# GridForge V2 — C9 SLD Read Adapter Tests
# Author: Subhendu Mishra
# ============================================================

from core.application.read_models import ProtectionReadModel, RelayInputBindingReadModel, RelayReadModel
from ui.sld.sld_read_adapter import SLDReadAdapter


def test_sld_relay_projection_preserves_protection_associations():
    read = ProtectionReadModel(relays=(RelayReadModel(
        object_id="R1",
        name="Relay 1",
        relay_type="OVER_CURRENT",
        function_type="50/51",
        plugin_id="plugin.oc",
        settings={"pickup": 1.2},
        in_service=True,
        enabled=True,
        blocked=False,
        picked_up=True,
        tripped=False,
        input_channel_bindings=(
            RelayInputBindingReadModel("Ia", "CH1"),
            RelayInputBindingReadModel("Ib", "CH2"),
        ),
    ),))
    result = SLDReadAdapter().protection(read)
    relay = result.elements[0]
    assert relay.element_type == "RELAY"
    assert relay.connectivity_refs == ("CH1", "CH2")
    assert relay.attributes["plugin_id"] == "plugin.oc"
    assert relay.attributes["picked_up"] is True
    assert relay.attributes["tripped"] is False
    assert relay.attributes["input_channel_bindings"] == (("Ia", "CH1"), ("Ib", "CH2"))
