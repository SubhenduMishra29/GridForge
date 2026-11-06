from core.application.services.model_service import ModelService
from core.network.network import Network


def test_model_service_exposes_canonical_bus_service_boundary():
    network = Network()
    service = ModelService(network)

    bus_service = service.bus_service

    assert bus_service.network is network
    assert bus_service is not service
    assert bus_service.__class__.__name__ == "BusModelService"


def test_bus_service_owns_bus_mutation_operations():
    network = Network()
    service = ModelService(network)

    bus_service = service.bus_service

    assert callable(bus_service.create_bus)
    assert callable(bus_service.update_bus)
    assert callable(bus_service.delete_bus)


def test_model_service_remains_the_public_mutation_facade():
    network = Network()
    service = ModelService(network)

    assert callable(service.create_bus)
    assert callable(service.update_bus)
    assert callable(service.delete_bus)


def test_bus_service_is_not_a_second_public_command_authority():
    network = Network()
    service = ModelService(network)

    bus_service = service.bus_service

    assert not hasattr(bus_service, "execute")
    assert not hasattr(bus_service, "undo")
    assert not hasattr(bus_service, "redo")
