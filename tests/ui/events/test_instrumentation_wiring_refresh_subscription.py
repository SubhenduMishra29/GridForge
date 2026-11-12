from core.application.events import InstrumentationWiringChanged
from ui.events.control_update_coordinator import _CONTROL_EVENTS
from ui.events.sld_update_coordinator import SLDUpdateCoordinator
from ui.protection.protection_workspace import ProtectionWorkspace


def test_all_engineering_projections_subscribe_to_instrumentation_wiring_changes():
    assert InstrumentationWiringChanged in SLDUpdateCoordinator.event_types
    assert InstrumentationWiringChanged in _CONTROL_EVENTS
    assert InstrumentationWiringChanged in ProtectionWorkspace._EVENT_TYPES
