from core.application.services.measurement_model_service import MeasurementModelService
from core.application.services.model_service import ModelService
from core.network.network import Network


def test_model_service_exposes_measurement_service_for_network():
    network = Network()
    service = ModelService(network)

    assert isinstance(service.measurement_service, MeasurementModelService)
    assert service.measurement_service.network is network
