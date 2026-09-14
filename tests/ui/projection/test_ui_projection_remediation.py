from __future__ import annotations

from types import SimpleNamespace
from uuid import uuid4

from core.application.event_bus import ApplicationEventBus
from core.application.events import (
    ApplicationEvent,
    ElementCreated,
    ProjectClosed,
    ProjectLoaded,
    StudyCompleted,
    StudyStarted,
    ValidationChanged,
)
from core.application.validation import ValidationIssue, ValidationResult, ValidationSeverity, ValidationSummary
from core.application.study import StudyResult
from ui.events.update_boundary import UIUpdateBoundary
from ui.projection.element_list_projection import ElementListProjection
from ui.projection.project_hierarchy_projection import ProjectHierarchyProjection
from ui.projection.study_projection import StudyProjection
from ui.projection.ui_projection_coordinator import UIProjectionCoordinator
from ui.projection.validation_projection import ValidationProjection


class _Panel:
    def __init__(self) -> None:
        self.rows = ()
        self.messages = ()
        self.cases = ()
        self.hierarchy = None

    def set_rows(self, rows) -> None:
        self.rows = tuple(rows)

    def set_messages(self, messages) -> None:
        self.messages = tuple(messages)

    def set_cases(self, cases) -> None:
        self.cases = tuple(cases)

    def set_hierarchy(self, hierarchy) -> None:
        self.hierarchy = hierarchy

    def clear_hierarchy(self) -> None:
        self.hierarchy = None


class _Application:
    def __init__(self) -> None:
        self.network = SimpleNamespace(elements=())
        self.validation = None
        self.results = {}

    def read_network(self):
        return self.network

    def read_validation(self):
        return self.validation

    def study_result(self, study_id):
        return self.results.get(study_id)


class _Adapter:
    def __init__(self) -> None:
        self.state = SimpleNamespace(
            project=SimpleNamespace(project_id="p1", name="Project A"),
            document=SimpleNamespace(document_id="d1", name="SLD", document_type="sld"),
            workspace_id="sld",
            view_id="main",
        )
        self.handlers = []

    def subscribe(self, handler) -> None:
        self.handlers.append(handler)

    def unsubscribe(self, handler) -> None:
        self.handlers.remove(handler)


def test_ui_update_boundary_is_single_application_ingress_and_disposes_coordinator():
    bus = ApplicationEventBus()
    seen = []

    class Projection:
        event_types = (ApplicationEvent,)

        def refresh(self, event) -> None:
            seen.append(event)

        def dispose(self) -> None:
            seen.append("disposed")

    coordinator = UIProjectionCoordinator(projections=(Projection(),))
    boundary = UIUpdateBoundary(event_bus=bus, projection_coordinator=coordinator)
    boundary.subscribe()
    bus.publish(ElementCreated(element_id="e1", element_type="BUS"))
    assert len(seen) == 1
    boundary.dispose()
    assert seen[-1] == "disposed"
    bus.publish(ElementCreated(element_id="e2", element_type="BUS"))
    assert len(seen) == 2


def test_coordinator_delivers_one_refresh_when_interests_overlap():
    seen = []

    class Projection:
        event_types = (ApplicationEvent, ElementCreated)

        def refresh(self, event) -> None:
            seen.append(event)

    coordinator = UIProjectionCoordinator(projections=(Projection(),))
    coordinator.handle(ElementCreated(element_id="e1", element_type="BUS"))
    assert len(seen) == 1


def test_element_list_uses_application_read_model_and_deterministic_name():
    application = _Application()
    application.network = SimpleNamespace(elements=(
        SimpleNamespace(object_id="1", element_type="BUS", labels={"type": "Bus", "name": "Bus A"}),
        SimpleNamespace(object_id="2", element_type="LINE", labels={"type": "Line"}),
    ))
    panel = _Panel()
    projection = ElementListProjection(application=application, panel=panel)
    projection.refresh(ElementCreated(element_id="1", element_type="BUS"))
    assert panel.rows[0]["name"] == "Bus A"
    assert panel.rows[1]["name"] == "Line"
    projection.refresh(ProjectClosed())
    assert panel.rows == ()


def test_project_hierarchy_refreshes_from_adapter_and_clears_on_close():
    adapter = _Adapter()
    panel = _Panel()
    projection = ProjectHierarchyProjection(adapter=adapter, panel=panel)
    assert panel.hierarchy["project"]["name"] == "Project A"
    projection.refresh(ProjectClosed())
    assert panel.hierarchy is None
    projection.dispose()
    assert adapter.handlers == []


def test_validation_projection_reads_structured_application_result():
    application = _Application()
    application.validation = ValidationResult(
        model_revision=4,
        topology_revision=5,
        issues=(ValidationIssue(
            code="BAD_BUS",
            message="Invalid bus",
            severity=ValidationSeverity.ERROR,
            element_id="bus-1",
            element_type="BUS",
        ),),
        summary=ValidationSummary(errors=1, warnings=0, infos=0),
    )
    panel = _Panel()
    projection = ValidationProjection(application=application, panel=panel)
    assert "BAD_BUS" in panel.messages[1]
    projection.refresh(ProjectClosed())
    assert panel.messages == ()


def test_study_projection_tracks_started_and_completed_application_state():
    application = _Application()
    panel = _Panel()
    projection = StudyProjection(application=application, panel=panel)
    study_id = uuid4()
    projection.refresh(StudyStarted(metadata={"study_id": str(study_id), "study_type": "power_flow"}))
    assert "started" in panel.cases[0]
    application.results[study_id] = StudyResult(
        study_id=study_id,
        study_type="power_flow",
        status="completed",
        value={"converged": True},
    )
    projection.refresh(StudyCompleted(metadata={"study_id": str(study_id), "study_type": "power_flow"}))
    assert "completed" in panel.cases[0]
    projection.refresh(ProjectClosed())
    assert panel.cases == ()
