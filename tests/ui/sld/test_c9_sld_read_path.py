# ============================================================
# File: tests/ui/sld/test_c9_sld_read_path.py
# GridForge V2 — C9 SLD Read Path Tests
# Author: Subhendu Mishra
# ============================================================

from core.application.read_models import ElementReadModel, NetworkReadModel, ProtectionReadModel, RelayReadModel
from ui.sld.sld_projection import SLDProjection
from ui.sld.sld_read_adapter import SLDReadAdapter
from ui.sld.sld_vocabulary import SLD_SUPPORTED_TYPES, semantic_type


def test_canonical_sld_vocabulary_contains_target_types():
    expected = {
        "BUS", "LINE", "CABLE", "TRANSFORMER", "SWITCH", "BREAKER",
        "DISCONNECTOR", "FUSE", "LOAD", "GENERATOR", "SYNCHRONOUS_MACHINE",
        "MOTOR", "SHUNT", "CAPACITOR", "REACTOR", "SOLAR", "BATTERY",
        "GRID", "CT", "PT", "CVT", "RELAY",
    }
    assert SLD_SUPPORTED_TYPES == frozenset(expected)


def test_network_read_adapter_preserves_identity_and_selects_canonical_semantics():
    read_model = ElementReadModel(
        object_id="CT1",
        element_type="current_transformers",
        labels={"name": "CT-1"},
        connectivity_refs=("P1", "P2", "S1", "S2"),
        attributes={"terminal_connectivity": (("P1", "B1"), ("P2", "B2"), ("S1", None), ("S2", None))},
    )

    adapted = SLDReadAdapter().element(read_model)

    assert adapted.object_id == "CT1"
    assert adapted.element_type == "CT"
    assert adapted.connectivity_refs == read_model.connectivity_refs
    assert adapted.attributes["terminal_connectivity"] == read_model.attributes["terminal_connectivity"]


def test_relay_read_adapter_uses_protection_read_source():
    read_model = ProtectionReadModel(relays=(
        RelayReadModel(
            object_id="R1",
            name="Relay 1",
            relay_type="OVER_CURRENT",
            function_type="50/51",
            in_service=True,
            enabled=True,
            blocked=False,
        ),
    ))

    adapted = SLDReadAdapter().protection(read_model)

    assert len(adapted.elements) == 1
    assert adapted.elements[0].object_id == "R1"
    assert adapted.elements[0].element_type == "RELAY"
    assert adapted.elements[0].attributes["function_type"] == "50/51"


def test_sld_projection_preserves_adapter_semantic_type():
    read_model = ElementReadModel(
        object_id="PT1",
        element_type="PT",
        labels={"name": "PT-1"},
        connectivity_refs=(),
        attributes={},
    )

    projection = SLDProjection(read_model)

    assert projection.state.display_type == "PT"


def test_semantic_aliases_are_explicit():
    assert semantic_type("current_transformers") == "CT"
    assert semantic_type("potential_transformers") == "PT"
    assert semantic_type("capacitive_voltage_transformers") == "CVT"
    assert semantic_type("RELAY") == "RELAY"
