from core.application.services.model_service import ModelService
from core.application.services.pt_model_service import PTModelService
from core.application.transaction import Transaction
from core.model.pt import PT
from core.network.network import Network


def test_pt_has_canonical_network_membership_and_service_boundary():
    network = Network()
    service = PTModelService(network)
    transaction = Transaction()
    result = service.create_pt(pt_id="PT1", transaction=transaction)
    assert isinstance(result.value, PT)
    assert network.potential_transformers == (result.value,)
    assert network.get_by_id("pt", "PT1") is result.value
    assert isinstance(ModelService(network).pt_service, PTModelService)


def test_pt_delete_uses_network_lifecycle():
    network = Network()
    service = PTModelService(network)
    transaction = Transaction()
    result = service.create_pt(pt_id="PT1", transaction=transaction)
    service.delete_pt(pt_id="PT1", transaction=transaction)
    assert network.potential_transformers == ()
    assert result.value is not None
