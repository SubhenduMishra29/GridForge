"""Current-head closure tests for Relay/protection project boundaries."""

import pytest

from core.application.bootstrap import create_application
from core.application.commands.protection_configuration_commands import CreateProtectionConfigurationCommand
from core.application.commands.relay_commands import CreateRelayCommand, DeleteRelayCommand
from core.errors import ResourceError
from core.model.relay import Relay
from core.network import Network
from core.protection.project_configuration import ProtectionFunctionConfiguration


def _network() -> Network:
    return Network()


def _configuration(relay_id: str = "R1") -> ProtectionFunctionConfiguration:
    return ProtectionFunctionConfiguration(
        element_id="OC50",
        relay_id=relay_id,
        function_code="50",
        settings={"pickup": 1.0},
        input_channel_ids={"current": "I-R1"},
    )


def test_protection_configuration_requires_existing_relay_and_blocks_relay_delete():
    application = create_application(_network())

    missing_relay = application.execute(
        CreateProtectionConfigurationCommand(configuration=_configuration("MISSING"))
    )
    assert missing_relay.success is False
    assert isinstance(missing_relay.error, ResourceError)

    created = application.execute(
        CreateRelayCommand(relay_id="R1", relay_type="numeric")
    )
    assert created.success is True

    configured = application.execute(
        CreateProtectionConfigurationCommand(configuration=_configuration())
    )
    assert configured.success is True

    deleted = application.execute(DeleteRelayCommand(relay_id="R1"))
    assert deleted.success is False
    assert application.read_service.element("relay", "R1").object_id == "R1"


def test_close_project_detaches_closed_network_from_application():
    application = create_application(_network())
    assert application.execute(CreateRelayCommand(relay_id="R1", relay_type="numeric")).success

    closed_network = application.project_lifecycle.network
    application.close_project()

    assert application.project_lifecycle.has_project is False
    assert application.project_lifecycle.network is not closed_network
    assert application.read_service.network().elements == ()
    assert application.protection_runtime is None


def test_project_a_protection_state_does_not_leak_into_project_b_and_reopens(tmp_path):
    application = create_application(_network())
    assert application.execute(CreateRelayCommand(relay_id="R1", relay_type="numeric")).success
    assert application.execute(
        CreateProtectionConfigurationCommand(configuration=_configuration())
    ).success

    project_a = tmp_path / "project-a.gridforge"
    application.save_project_as(project_a)
    project_a_id = application.project_lifecycle.context.project_id

    application.new_project("Project B")
    assert application.read_service.network().elements == ()
    assert application.protection_configuration_service.configuration.elements == ()
    assert application.protection_runtime.configuration.project_id == application.project_lifecycle.context.project_id
    assert application.protection_runtime.configuration.project_id != project_a_id

    application.open_project(project_a)
    assert application.read_service.element("relay", "R1").object_id == "R1"
    assert application.protection_configuration_service.configuration.get("OC50").relay_id == "R1"
    assert application.protection_runtime.configuration.project_id == application.project_lifecycle.context.project_id
