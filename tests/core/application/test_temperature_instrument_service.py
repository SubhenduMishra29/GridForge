from core.application.services.temperature_instrument_service import TemperatureInstrumentService
from core.model import TemperatureInstrumentInventory


def test_temperature_service_project_activation_and_restore():
    service = TemperatureInstrumentService()
    previous = service.activate(None)
    assert service.project_id is None
    service.restore_state(previous)
    assert service.inventory == TemperatureInstrumentInventory()
