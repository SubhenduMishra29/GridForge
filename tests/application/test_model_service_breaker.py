from core.application.services.model_service import ModelService
from core.application.services.switching_model_service import SwitchingModelService
from core.network.network import Network


class FakeSwitchingService:
    def __init__(self):
        self.calls = []

    def _record(self, method, **kwargs):
        self.calls.append((method, kwargs))
        return method

    def create_breaker(self, **kwargs):
        return self._record("create_breaker", **kwargs)

    def update_breaker(self, **kwargs):
        return self._record("update_breaker", **kwargs)

    def delete_breaker(self, **kwargs):
        return self._record("delete_breaker", **kwargs)

    def open_breaker(self, **kwargs):
        return self._record("open_breaker", **kwargs)

    def close_breaker(self, **kwargs):
        return self._record("close_breaker", **kwargs)

    def trip_breaker(self, **kwargs):
        return self._record("trip_breaker", **kwargs)

    def put_breaker_in_service(self, **kwargs):
        return self._record("put_breaker_in_service", **kwargs)

    def take_breaker_out_of_service(self, **kwargs):
        return self._record("take_breaker_out_of_service", **kwargs)


def test_model_service_exposes_switching_service_for_breaker():
    network = Network()
    service = ModelService(network)

    assert isinstance(service.switching_service, SwitchingModelService)
    assert service.switching_service.network is network


def test_model_service_breaker_facade_delegates_all_operations():
    service = ModelService(Network())
    fake = FakeSwitchingService()
    service._switching_service = fake

    transaction = object()
    endpoint_from = object()
    endpoint_to = object()

    assert service.create_breaker(
        breaker_id="br-1",
        endpoint_from=endpoint_from,
        endpoint_to=endpoint_to,
        name="Breaker 1",
        in_service=True,
        closed=True,
        failed=False,
        voltage_kv=11.0,
        current_a=100.0,
        interrupting_ka=25.0,
        transaction=transaction,
    ) == "create_breaker"
    assert service.update_breaker(
        breaker_id="br-1",
        name="Updated",
        in_service=False,
        closed=False,
        failed=True,
        voltage_kv=12.0,
        current_a=110.0,
        interrupting_ka=30.0,
        transaction=transaction,
    ) == "update_breaker"
    assert service.delete_breaker(breaker_id="br-1", transaction=transaction) == "delete_breaker"
    assert service.open_breaker(breaker_id="br-1", transaction=transaction) == "open_breaker"
    assert service.close_breaker(breaker_id="br-1", transaction=transaction) == "close_breaker"
    assert service.trip_breaker(breaker_id="br-1", transaction=transaction) == "trip_breaker"
    assert service.put_breaker_in_service(breaker_id="br-1", transaction=transaction) == "put_breaker_in_service"
    assert service.take_breaker_out_of_service(breaker_id="br-1", transaction=transaction) == "take_breaker_out_of_service"

    assert [method for method, _ in fake.calls] == [
        "create_breaker",
        "update_breaker",
        "delete_breaker",
        "open_breaker",
        "close_breaker",
        "trip_breaker",
        "put_breaker_in_service",
        "take_breaker_out_of_service",
    ]
