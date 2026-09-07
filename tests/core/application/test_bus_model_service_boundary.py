from core.application.services.bus_model_service import BusModelService
from core.application.services.model_service import ModelService
from core.network.network import Network


def test_model_service_uses_specialized_bus_service():
    network = Network()
    service = ModelService(network)

    assert isinstance(service.bus_service, BusModelService)
    assert service.bus_service.network is network


def test_bus_service_is_an_internal_bus_mutation_unit():
    network = Network()
    service = BusModelService(network)

    assert service.network is network
    assert callable(service.create_bus)
    assert callable(service.update_bus)
    assert callable(service.delete_bus)
