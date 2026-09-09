from core.application.commands.model_commands import (
    CreateBranchCommand,
    CreateCableCommand,
    CreateDisconnectorCommand,
    CreateSwitchCommand,
    UpdateGeneratorCommand,
    UpdateShuntCommand,
)
from core.application.endpoint_reference import EndpointReference


def test_two_terminal_create_commands_carry_endpoint_references():
    endpoint_from = EndpointReference("bus", "B1")
    endpoint_to = EndpointReference("bus", "B2")

    branch = CreateBranchCommand(branch_id="BR1", endpoint_from=endpoint_from, endpoint_to=endpoint_to)
    cable = CreateCableCommand(cable_id="C1", endpoint_from=endpoint_from, endpoint_to=endpoint_to)
    switch = CreateSwitchCommand(switch_id="SW1", endpoint_a=endpoint_from, endpoint_b=endpoint_to)
    disconnector = CreateDisconnectorCommand(
        disconnector_id="DS1", voltage_kv=11.0, rated_current_a=630.0,
        endpoint_from=endpoint_from, endpoint_to=endpoint_to,
    )

    assert branch.payload["endpoint_from"] is endpoint_from
    assert branch.payload["endpoint_to"] is endpoint_to
    assert cable.payload["endpoint_from"] is endpoint_from
    assert cable.payload["endpoint_to"] is endpoint_to
    assert switch.payload["endpoint_a"] is endpoint_from
    assert switch.payload["endpoint_b"] is endpoint_to
    assert disconnector.payload["endpoint_from"] is endpoint_from
    assert disconnector.payload["endpoint_to"] is endpoint_to


def test_update_commands_do_not_carry_unsupported_endpoint_mutation():
    generator = UpdateGeneratorCommand(generator_id="G1", p=10.0)
    shunt = UpdateShuntCommand(shunt_id="S1", g_pu=0.1)

    assert "endpoint" not in generator.payload
    assert "endpoint" not in shunt.payload
