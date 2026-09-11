# ============================================================
# File: tests/core/application/test_c9_read_services.py
# GridForge V2 — C9 Read-Side Tests
# Author: Subhendu Mishra
# ============================================================

from types import SimpleNamespace

import pytest

from core.application.read_service import NetworkReadService, ProtectionReadService
from core.model.bus import Bus
from core.model.ct import CurrentTransformer
from core.model.cvt import CapacitiveVoltageTransformer
from core.model.pt import PT
from core.model.relay import Relay
from core.network.network import Network
from core.protection.protection_element import ProtectionElement
from core.protection.protection_system import ProtectionSystem


class _Function:
    def evaluate(self, context):
        raise AssertionError("evaluation is not part of this read-side test")


def _network_with_instrument_transformers():
    network = Network()
    bus_a = Bus("B1", name="Bus 1")
    bus_b = Bus("B2", name="Bus 2")
    network.add_bus(bus_a)
    network.add_bus(bus_b)
    ct = CurrentTransformer("CT1", name="CT-1", p1_endpoint=bus_a, p2_endpoint=bus_b)
    pt = PT("PT1", name="PT-1", primary_a=bus_a, primary_b=bus_b)
    cvt = CapacitiveVoltageTransformer("CVT1", name="CVT-1", h1_endpoint=bus_a, h2_endpoint=bus_b)
    network.add_current_transformer(ct)
    network.add_potential_transformer(pt)
    network.add_capacitive_voltage_transformer(cvt)
    return network


def test_network_read_includes_ct_pt_cvt_with_four_terminal_connectivity():
    snapshot = NetworkReadService(_network_with_instrument_transformers()).network()
    by_type = {element.element_type: element for element in snapshot.elements}
    assert "current_transformers" in by_type
    assert "potential_transformers" in by_type
    assert "capacitive_voltage_transformers" in by_type
    ct = by_type["current_transformers"]
    assert ct.attributes["ratio"] == pytest.approx(20.0)
    assert len(ct.attributes["terminal_connectivity"]) == 4
    assert {role for role, _ in ct.attributes["terminal_connectivity"]} == {"P1", "P2", "S1", "S2"}
    pt = by_type["potential_transformers"]
    assert pt.attributes["ratio"] == pytest.approx(100.0)
    assert len(pt.attributes["terminal_connectivity"]) == 4
    cvt = by_type["capacitive_voltage_transformers"]
    assert cvt.attributes["ratio"] == pytest.approx(2000.0)
    assert len(cvt.attributes["terminal_connectivity"]) == 4


def test_network_read_snapshot_is_immutable():
    snapshot = NetworkReadService(_network_with_instrument_transformers()).network()
    element = snapshot.elements[-1]
    with pytest.raises(TypeError):
        element.attributes["new"] = "forbidden"


def test_protection_read_uses_authoritative_relay_without_network_registration():
    relay = Relay("R1", "OVER_CURRENT", name="Relay 1", function_type="50/51", plugin_id="plugin.oc", settings={"pickup": 1.2})
    system = ProtectionSystem()
    system.add_element(ProtectionElement("PE1", relay, _Function(), "OVERCURRENT"))
    snapshot = ProtectionReadService(system).protection()
    assert len(snapshot.relays) == 1
    read_relay = snapshot.relays[0]
    assert read_relay.object_id == relay.id
    assert read_relay.name == relay.name
    assert read_relay.relay_type == relay.type
    assert read_relay.function_type == relay.function_type
    assert read_relay.plugin_id == "plugin.oc"
    assert read_relay.settings["pickup"] == pytest.approx(1.2)
    assert read_relay.picked_up is False
    assert read_relay.tripped is False
    assert not hasattr(read_relay, "decision")


def test_relay_read_model_is_immutable():
    relay = Relay("R1", "OVER_CURRENT")
    system = ProtectionSystem()
    system.add_element(ProtectionElement("PE1", relay, _Function(), "OVERCURRENT"))
    read_relay = ProtectionReadService(system).relay("R1")
    with pytest.raises(AttributeError):
        read_relay.name = "changed"
