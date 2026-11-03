"""Disconnector engineering-configuration command contract regressions."""

from core.application.commands.model_commands import (
    CreateDisconnectorCommand,
    UpdateDisconnectorCommand,
)
from core.application.services.switching_model_service import SwitchingModelService
from core.application.transaction import Transaction
from core.network.network import Network


def test_disconnector_create_command_keeps_unknown_operating_time_and_carries_normal_state() -> None:
    command = CreateDisconnectorCommand(
        disconnector_id="DS-1",
        voltage_kv=11.0,
        rated_current_a=630.0,
        normally_closed=False,
    )

    assert command.payload["operating_time"] is None
    assert command.payload["normally_closed"] is False


def test_disconnector_update_command_exposes_normal_state() -> None:
    command = UpdateDisconnectorCommand(
        disconnector_id="DS-1",
        normally_closed=False,
    )

    assert command.payload["normally_closed"] is False


def test_disconnector_application_service_preserves_optional_operating_time_and_normal_state() -> None:
    network = Network()
    service = SwitchingModelService(network)
    transaction = Transaction()

    service.create_disconnector(
        disconnector_id="DS-1",
        voltage_kv=11.0,
        rated_current_a=630.0,
        normally_closed=False,
        transaction=transaction,
    )

    disconnector = network.disconnectors[0]
    assert disconnector.operating_time is None
    assert disconnector.normally_closed is False

    service.update_disconnector(
        disconnector_id="DS-1",
        operating_time=2.4,
        normally_closed=True,
        transaction=transaction,
    )

    assert disconnector.operating_time == 2.4
    assert disconnector.normally_closed is True

    transaction.rollback()
    assert network.disconnectors == ()
