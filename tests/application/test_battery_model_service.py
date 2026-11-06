from core.application.services.battery_model_service import BatteryModelService
from core.application.transaction import Transaction
from core.model.battery import Battery
from core.network.network import Network


def test_battery_service_create_registers_battery_and_supports_rollback():
    network = Network()
    service = BatteryModelService(network)
    transaction = Transaction()

    result = service.create_battery(
        battery_id="BAT-1",
        name="Battery 1",
        p_mw=2.0,
        q_mvar=0.5,
        max_charge_mw=3.0,
        max_discharge_mw=4.0,
        energy_capacity_mwh=10.0,
        soc=0.6,
        transaction=transaction,
    )

    assert isinstance(result.value, Battery)
    assert network.get_by_id("battery", "BAT-1") is result.value
    assert transaction.undo_count == 1

    transaction.rollback()
    assert network.batteries == ()


def test_battery_service_update_registers_inverse_state_change():
    network = Network()
    service = BatteryModelService(network)
    create_tx = Transaction()
    battery = service.create_battery(
        battery_id="BAT-2",
        name="Battery 2",
        p_mw=1.0,
        q_mvar=0.2,
        max_charge_mw=2.0,
        max_discharge_mw=3.0,
        energy_capacity_mwh=8.0,
        soc=0.5,
        transaction=create_tx,
    ).value
    create_tx.commit()

    transaction = Transaction()
    service.update_battery(
        battery_id="BAT-2",
        name="Updated",
        p_mw=2.0,
        soc=0.7,
        transaction=transaction,
    )

    assert battery.name == "Updated"
    assert battery.p_mw == 2.0
    assert battery.soc == 0.7
    assert transaction.undo_count == 1

    transaction.rollback()
    assert battery.name == "Battery 2"
    assert battery.p_mw == 1.0
    assert battery.soc == 0.5


def test_battery_service_delete_and_rollback_restore_registration():
    network = Network()
    service = BatteryModelService(network)
    create_tx = Transaction()
    battery = service.create_battery(
        battery_id="BAT-3",
        energy_capacity_mwh=5.0,
        transaction=create_tx,
    ).value
    create_tx.commit()

    transaction = Transaction()
    service.delete_battery(battery_id="BAT-3", transaction=transaction)
    assert network.batteries == ()

    transaction.rollback()
    assert network.get_by_id("battery", "BAT-3") is battery


def test_battery_service_lifecycle_state_has_inverse_operation():
    network = Network()
    service = BatteryModelService(network)
    create_tx = Transaction()
    battery = service.create_battery(
        battery_id="BAT-4",
        transaction=create_tx,
    ).value
    create_tx.commit()

    transaction = Transaction()
    service.take_battery_out_of_service(
        battery_id="BAT-4",
        transaction=transaction,
    )
    assert battery.in_service is False
    transaction.rollback()
    assert battery.in_service is True


def test_battery_service_rejects_empty_update():
    network = Network()
    service = BatteryModelService(network)
    create_tx = Transaction()
    service.create_battery(battery_id="BAT-5", transaction=create_tx)
    create_tx.commit()

    transaction = Transaction()
    try:
        service.update_battery(battery_id="BAT-5", transaction=transaction)
    except Exception as exc:
        assert "mutable" in str(exc).lower()
    else:
        raise AssertionError("Expected empty Battery update to be rejected")
