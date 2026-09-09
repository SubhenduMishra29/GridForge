from core.application.services.model_service import ModelService


class _FakeShuntService:
    def __init__(self) -> None:
        self.calls = []

    def create_capacitor(self, **kwargs):
        self.calls.append(("create_capacitor", kwargs))
        return "created"

    def update_capacitor(self, **kwargs):
        self.calls.append(("update_capacitor", kwargs))
        return "updated"

    def delete_capacitor(self, **kwargs):
        self.calls.append(("delete_capacitor", kwargs))
        return "deleted"

    def put_capacitor_in_service(self, **kwargs):
        self.calls.append(("put_capacitor_in_service", kwargs))
        return "in_service"

    def take_capacitor_out_of_service(self, **kwargs):
        self.calls.append(("take_capacitor_out_of_service", kwargs))
        return "out_of_service"


def _facade():
    service = ModelService.__new__(ModelService)
    fake = _FakeShuntService()
    service._shunt_service = fake
    return service, fake


def test_model_service_exposes_capacitor_compatibility_lifecycle():
    service, fake = _facade()
    transaction = object()

    assert service.create_capacitor(
        capacitor_id="C1", endpoint="BUS1", transaction=transaction
    ) == "created"
    assert service.update_capacitor(
        capacitor_id="C1", q_mvar=5.0, transaction=transaction
    ) == "updated"
    assert service.delete_capacitor(
        capacitor_id="C1", transaction=transaction
    ) == "deleted"
    assert service.put_capacitor_in_service(
        capacitor_id="C1", transaction=transaction
    ) == "in_service"
    assert service.take_capacitor_out_of_service(
        capacitor_id="C1", transaction=transaction
    ) == "out_of_service"

    assert [name for name, _ in fake.calls] == [
        "create_capacitor",
        "update_capacitor",
        "delete_capacitor",
        "put_capacitor_in_service",
        "take_capacitor_out_of_service",
    ]
