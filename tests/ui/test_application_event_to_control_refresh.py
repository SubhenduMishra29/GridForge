from __future__ import annotations

from core.application.bootstrap import create_application
from core.application.commands.control_commands import AddControlComponent
from core.network.network import Network
from ui.canvas.control_canvas import ControlCanvas
from ui.events.control_update_coordinator import ControlUpdateCoordinator
from core.application.events import ApplicationEvent


def test_application_control_event_reaches_control_canvas_refresh_path():
    application = create_application(Network())
    canvas = ControlCanvas()
    refresh_calls = []

    coordinator = ControlUpdateCoordinator(
        application=application,
        canvas=canvas,
        canvas_refresh=lambda: refresh_calls.append(True),
    )
    application.event_bus.subscribe(ApplicationEvent, coordinator.refresh)

    result = application.execute(
        AddControlComponent(
            component_id="contact-1",
            component_type="normally_open_contact",
            rung_id="rung-1",
        )
    )

    assert result.success is True
    assert refresh_calls == [True]
    assert canvas.control_read_model is not None
    assert any(component.component_id == "contact-1" for component in canvas.control_read_model.components)

    coordinator.dispose()
