from __future__ import annotations

import pytest

from core.application.bootstrap import create_application
from core.application.commands.draft_commands import CommitNetworkCommand
from core.application.creation import CreationCommitIntent, CreationCommandPreparer
from core.application.draft.network import (
    DraftConnection,
    DraftEndpointReference,
    DraftEquipment,
    DraftNetwork,
)
from core.network import Network


def _equipment(
    *,
    draft_id: str,
    equipment_type: str,
    command_type: str,
    id_field: str,
    terminal_contract: tuple[str, ...],
    values: dict,
    parameter_mapping: dict[str, str],
    endpoint_mapping: dict[str, str] | None = None,
    placement: tuple[float, float] = (10.0, 20.0),
    endpoints: dict[str, DraftEndpointReference] | None = None,
) -> DraftEquipment:
    return DraftEquipment(
        draft_id=draft_id,
        equipment_type=equipment_type,
        display_name=equipment_type.title(),
        terminal_contract=terminal_contract,
        engineering_data=values,
        endpoints=endpoints or {},
        placement=placement,
        command_type=command_type,
        id_field=id_field,
        parameter_mapping=parameter_mapping,
        endpoint_mapping=endpoint_mapping or {},
    )


def _bus(draft_id: str) -> DraftEquipment:
    return _equipment(
        draft_id=draft_id,
        equipment_type="bus",
        command_type="model.create_bus",
        id_field="bus_id",
        terminal_contract=("bus",),
        values={
            "nominal_voltage_kv": 132.0,
            "frequency_hz": 50.0,
            "in_service": True,
        },
        parameter_mapping={
            "nominal_voltage_kv": "nominal_voltage_kv",
            "frequency_hz": "frequency_hz",
            "in_service": "in_service",
        },
    )


def _transformer(draft_id: str) -> DraftEquipment:
    return _equipment(
        draft_id=draft_id,
        equipment_type="transformer",
        command_type="model.create_transformer",
        id_field="transformer_id",
        terminal_contract=("FROM", "TO"),
        values={
            "r": 0.01,
            "x": 0.05,
            "b": 0.0,
            "impedance_basis": "engineering",
            "impedance_base_voltage_kv": 132.0,
            "rate_mva": 10.0,
            "tap": 1.0,
            "shift": 0.0,
            "name": "Transformer T1",
        },
        parameter_mapping={
            "r": "r",
            "x": "x",
            "b": "b",
            "impedance_basis": "impedance_basis",
            "impedance_base_voltage_kv": "impedance_base_voltage_kv",
            "impedance_base_mva": "impedance_base_mva",
            "rate_mva": "rate_mva",
            "tap": "tap",
            "shift": "shift",
            "name": "name",
        },
        endpoint_mapping={"FROM": "endpoint_from", "TO": "endpoint_to"},
        placement=(40.0, 50.0),
    )


def _breaker(draft_id: str) -> DraftEquipment:
    return _equipment(
        draft_id=draft_id,
        equipment_type="breaker",
        command_type="model.create_breaker",
        id_field="breaker_id",
        terminal_contract=("from", "to"),
        values={
            "voltage_kv": 132.0,
            "current_a": 1000.0,
            "interrupting_ka": 25.0,
            "closed": True,
            "in_service": True,
        },
        parameter_mapping={
            "voltage_kv": "voltage_kv",
            "current_a": "current_a",
            "interrupting_ka": "interrupting_ka",
            "closed": "closed",
            "in_service": "in_service",
        },
    )


def _commit(app, draft: DraftNetwork):
    app.set_draft_network(draft)
    return app.execute(
        CommitNetworkCommand(
            project_id=draft.project_id,
            activation_generation=draft.activation_generation,
            draft_network=draft.to_dict(),
        )
    )


def test_creation_intent_matches_canonical_preparer_for_bus_transformer_breaker():
    preparer = CreationCommandPreparer()

    intents = (
        CreationCommitIntent(
            command_type="model.create_bus",
            id_field="bus_id",
            object_id="bus-b1",
            parameter_mapping=_bus("b1").parameter_mapping,
            endpoint_mapping={},
            values=dict(_bus("b1").engineering_data),
            endpoints={},
            position=(1.0, 2.0),
        ),
        CreationCommitIntent(
            command_type="model.create_transformer",
            id_field="transformer_id",
            object_id="transformer-t1",
            parameter_mapping=_transformer("t1").parameter_mapping,
            endpoint_mapping={},
            values=dict(_transformer("t1").engineering_data),
            endpoints={},
            position=(3.0, 4.0),
        ),
        CreationCommitIntent(
            command_type="model.create_breaker",
            id_field="breaker_id",
            object_id="breaker-k1",
            parameter_mapping=_breaker("k1").parameter_mapping,
            endpoint_mapping={},
            values=dict(_breaker("k1").engineering_data),
            endpoints={},
            position=(5.0, 6.0),
        ),
    )

    commands = tuple(preparer.prepare(intent) for intent in intents)

    assert [command.command_type for command in commands] == [
        "model.create_bus",
        "model.create_transformer",
        "model.create_breaker",
    ]
    assert commands[0].payload["bus_id"] == "bus-b1"
    assert commands[1].payload["transformer_id"] == "transformer-t1"
    assert commands[2].payload["breaker_id"] == "breaker-k1"


def test_commit_prepares_multiple_equipment_deterministically_and_clears_draft():
    app = create_application(Network())
    draft = DraftNetwork("project-1", 1)
    draft.add_equipment(_transformer("t2"))
    draft.add_equipment(_bus("b1"))
    draft.add_equipment(_breaker("k1"))

    result = _commit(app, draft)

    assert result.success
    assert not app.draft_network.equipment
    ids = {element.object_id for element in app.read_network().elements}
    assert "bus-b1" in ids
    assert "breaker-k1" in ids
    assert "transformer-t2" in ids


def test_commit_rejects_missing_required_engineering_data_before_core_mutation():
    app = create_application(Network())
    draft = DraftNetwork("project-2", 1)
    invalid = _transformer("t-invalid")
    invalid = DraftEquipment(
        **{
            **{name: getattr(invalid, name) for name in (
                "draft_id", "equipment_type", "display_name", "terminal_contract",
                "endpoints", "placement", "presentation", "validation_state",
                "command_type", "id_field", "parameter_mapping", "endpoint_mapping",
            )},
            "engineering_data": {"r": 0.01, "x": 0.05},
        }
    )
    draft.add_equipment(invalid)

    with pytest.raises(Exception):
        _commit(app, draft)

    assert app.read_network().elements == ()
    assert len(app.draft_network.equipment) == 1


def test_commit_rejects_core_identity_collision_before_mutation():
    app = create_application(Network())
    draft = DraftNetwork("project-3", 1)
    draft.add_equipment(_bus("b1"))

    # Establish the exact deterministic Core identity expected from the
    # Application commit mapping without using a UI-created Core object.
    app.execute(
        __import__("core.application.commands.model_commands", fromlist=["CreateBusCommand"]).CreateBusCommand(
            bus_id="bus-b1",
            nominal_voltage_kv=132.0,
            frequency_hz=50.0,
        )
    )

    with pytest.raises(Exception):
        _commit(app, draft)

    assert len(app.draft_network.equipment) == 1
    assert len(app.read_network().elements) == 1


def test_draft_endpoint_translation_maps_draft_bus_and_terminal_to_core_identity():
    resolver = __import__(
        "core.application.draft.handlers",
        fromlist=["DraftConnectivityResolver"],
    ).DraftConnectivityResolver()

    bus_endpoint = DraftEndpointReference.bus(
        bus_id="b1",
        attachment_id="attachment-0",
    )
    terminal_endpoint = DraftEndpointReference.terminal(
        draft_id="t1",
        equipment_type="transformer",
        terminal_role="FROM",
    )

    bus_ref = resolver._to_core_endpoint(bus_endpoint, {"b1": "bus-b1", "t1": "transformer-t1"})
    terminal_ref = resolver._to_core_endpoint(
        terminal_endpoint,
        {"b1": "bus-b1", "t1": "transformer-t1"},
    )

    assert bus_ref.to_mapping()["object_id"] == "bus-b1"
    assert terminal_ref.to_mapping()["object_id"] == "transformer-t1"
    assert terminal_ref.to_mapping()["terminal_role"] == "FROM"


def test_valid_draft_connection_commits_as_core_simple_wire():
    app = create_application(Network())
    draft = DraftNetwork("project-4", 1)
    bus = _bus("b1")
    transformer = _transformer("t1")
    draft.add_equipment(bus)
    draft.add_equipment(transformer)
    draft.add_connection(
        DraftConnection(
            connection_id="wire-1",
            source=DraftEndpointReference.bus(
                bus_id="b1",
                attachment_id="attachment-0",
            ),
            target=DraftEndpointReference.terminal(
                draft_id="t1",
                equipment_type="transformer",
                terminal_role="FROM",
            ),
        )
    )

    result = _commit(app, draft)

    assert result.success
    network = app.read_network()
    assert any(
        str(connection.connection_id) == "wire-1"
        for connection in network.simple_wire_connections
    )
    assert not app.draft_network.connections


def test_empty_draft_commit_is_rejected_and_retained():
    app = create_application(Network())
    draft = DraftNetwork("project-5", 1)

    with pytest.raises(Exception):
        _commit(app, draft)

    assert not app.read_network().elements
    assert not draft.equipment
    assert not draft.connections
