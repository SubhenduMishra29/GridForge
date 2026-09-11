# ============================================================
# File: tests/ui/events/test_application_event_projection_path.py
# GridForge V2 — Application Event Projection Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from core.application.event_bus import ApplicationEventBus
from core.application.events import NetworkChanged
from ui.events.sld_update_coordinator import SLDUpdateCoordinator
from ui.events.update_boundary import UIUpdateBoundary


class FakeApplication:
    def __init__(self) -> None:
        self.read_calls = 0

    def read_network(self):
        self.read_calls += 1
        return "network-read-model"


class FakeDocument:
    pass


class FakeSynchronizer:
    def __init__(self) -> None:
        self.calls = []

    def synchronize_network(self, document, read_model):
        self.calls.append((document, read_model))


class FakeCanvas:
    def __init__(self) -> None:
        self.calls = 0

    def refresh(self):
        self.calls += 1


def test_application_event_reaches_sld_projection_without_core_callback():
    bus = ApplicationEventBus()
    application = FakeApplication()
    document = FakeDocument()
    synchronizer = FakeSynchronizer()
    canvas = FakeCanvas()

    coordinator = SLDUpdateCoordinator.__new__(SLDUpdateCoordinator)
    coordinator._application = application
    coordinator._document = document
    coordinator._synchronizer = synchronizer
    coordinator._canvas_refresh = canvas.refresh

    boundary = UIUpdateBoundary(event_bus=bus, refresh=coordinator.refresh)
    boundary.subscribe()

    bus.publish(NetworkChanged(operation="model.create_bus"))

    assert application.read_calls == 1
    assert synchronizer.calls == [(document, "network-read-model")]
    assert canvas.calls == 1
