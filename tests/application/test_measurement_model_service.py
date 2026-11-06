from core.application.services.measurement_model_service import MeasurementModelService
from core.application.transaction import Transaction
from core.model.ct import CurrentTransformer
from core.model.cvt import CapacitiveVoltageTransformer
from core.network.network import Network


def test_network_registers_ct_and_cvt_and_supports_canonical_lookup():
    network = Network()
    ct = CurrentTransformer("ct-1")
    cvt = CapacitiveVoltageTransformer("cvt-1")

    network.add_current_transformer(ct)
    network.add_capacitive_voltage_transformer(cvt)

    assert network.current_transformers == (ct,)
    assert network.capacitive_voltage_transformers == (cvt,)
    assert network.get_by_id("ct", "ct-1") is ct
    assert network.get_by_id("cvt", "cvt-1") is cvt


def test_measurement_service_owns_ct_lifecycle():
    network = Network()
    service = MeasurementModelService(network)
    tx = Transaction()

    result = service.create_current_transformer(
        ct_id="ct-1",
        name="CT-1",
        primary_rated_current_a=400.0,
        secondary_rated_current_a=5.0,
        transaction=tx,
    )

    assert result.value is network.current_transformers[0]
    assert isinstance(result.value, CurrentTransformer)
    assert result.value.primary_rated_current_a == 400.0

    service.update_current_transformer(
        ct_id="ct-1",
        primary_rated_current_a=600.0,
        accuracy_class="5P20",
        transaction=tx,
    )
    assert result.value.primary_rated_current_a == 600.0
    assert result.value.accuracy_class == "5P20"

    service.take_current_transformer_out_of_service(ct_id="ct-1", transaction=tx)
    assert result.value.in_service is False

    service.delete_current_transformer(ct_id="ct-1", transaction=tx)
    assert network.current_transformers == ()


def test_measurement_service_owns_cvt_lifecycle():
    network = Network()
    service = MeasurementModelService(network)
    tx = Transaction()

    result = service.create_capacitive_voltage_transformer(
        cvt_id="cvt-1",
        name="CVT-1",
        rated_primary_voltage_kv=132.0,
        rated_secondary_voltage_v=110.0,
        transaction=tx,
    )

    assert result.value is network.capacitive_voltage_transformers[0]
    assert isinstance(result.value, CapacitiveVoltageTransformer)
    assert result.value.rated_primary_voltage_kv == 132.0

    service.update_capacitive_voltage_transformer(
        cvt_id="cvt-1",
        rated_primary_voltage_kv=220.0,
        accuracy_class="0.2",
        transaction=tx,
    )
    assert result.value.rated_primary_voltage_kv == 220.0
    assert result.value.accuracy_class == "0.2"

    service.take_capacitive_voltage_transformer_out_of_service(
        cvt_id="cvt-1", transaction=tx
    )
    assert result.value.in_service is False

    service.delete_capacitive_voltage_transformer(
        cvt_id="cvt-1", transaction=tx
    )
    assert network.capacitive_voltage_transformers == ()
