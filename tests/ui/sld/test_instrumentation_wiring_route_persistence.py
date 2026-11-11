from __future__ import annotations

from ui.sld.sld_document import SLDDocument
from ui.sld.sld_model import SLDRoute
from ui.sld.sld_route_edit_controller import SLDRouteEditController


def test_instrumentation_route_geometry_is_document_presentation_state_and_round_trips():
    document = SLDDocument("sld-1", project_id="project-1")
    document.set_instrumentation_wiring_route(
        "CABLE_CORE", "core-1", 1, ((20.0, 30.0), (40.0, 30.0)),
    )

    serialized = document.to_dict()
    restored = SLDDocument.from_dict(serialized)

    route = SLDRoute.from_dict(
        restored.instrumentation_wiring_routes()["CABLE_CORE:core-1:1"]
    )
    assert route.routing_mode == "manual"
    assert route.ownership == "engineer"
    assert route.points == ((20.0, 30.0), (40.0, 30.0))
    assert restored.model.connection_count == 0


def test_clearing_physical_route_override_returns_to_automatic_routing():
    document = SLDDocument("sld-1", project_id="project-1")
    document.set_instrumentation_wiring_route(
        "PANEL_WIRE", "wire-1", 1, ((10.0, 20.0),),
    )
    document.clear_instrumentation_wiring_route("PANEL_WIRE", "wire-1", 1)

    assert document.instrumentation_wiring_routes() == {}


def test_route_edit_controller_uses_document_route_api_without_core_command():
    class Controller:
        def __init__(self):
            self.calls = []

        def set_instrumentation_wiring_route(self, *args):
            self.calls.append(args)

    controller = Controller()
    editor = SLDRouteEditController(controller)
    request = {
        "instrumentation_wiring": True,
        "carrier_kind": "CABLE_CORE",
        "carrier_id": "core-1",
        "segment_index": 2,
        "core_connection_id": None,
        "points": ((11.0, 22.0), (33.0, 44.0)),
    }

    editor.handle_route_edit_request(request)

    assert controller.calls == [
        ("CABLE_CORE", "core-1", 2, ((11.0, 22.0), (33.0, 44.0))),
    ]
