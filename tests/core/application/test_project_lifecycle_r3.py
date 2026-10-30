"""R3 project lifecycle integration tests."""

import pytest

from core.application.bootstrap import create_application
from core.application.project_presentation import ProjectPresentationCollection
from core.application.commands.sld_commands import SetSLDNodePositionCommand
from core.application.services.sld_service import SLDService
from core.model.bus import Bus
from core.network import Network
from ui.sld.sld_document import SLDDocument


def _network() -> Network:
    network = Network()
    network.add_bus(Bus("BUS-001", name="Bus 1", nominal_voltage_kv=132.0))
    network.add_bus(Bus("BUS-002", name="Bus 2", nominal_voltage_kv=33.0))
    return network


def _presentation(project_id: str = "PROJECT-001") -> SLDDocument:
    document = SLDDocument(document_id="SLD-001", name="Main SLD", project_id=project_id)
    document.model.create_node("SLD-NODE-001", "BUS-001", 100.0, 200.0)
    document.model.create_node("SLD-NODE-002", "BUS-002", 400.0, 300.0)
    return document


def _serializer(document: SLDDocument) -> dict:
    # Modified/dirty is transient lifecycle state, not canonical SLD data.
    return document.to_dict()


def _deserializer(data: dict) -> SLDDocument:
    return SLDDocument.from_dict(data)


def _serialize_collection(collection: ProjectPresentationCollection) -> dict:
    return {
        "schema": 1,
        "documents": [document.to_dict() for document in collection.documents],
        "active_document_id": collection.active_document_id,
    }


def _deserialize_collection(data: dict) -> ProjectPresentationCollection:
    documents = tuple(SLDDocument.from_dict(item) for item in data["documents"])
    return ProjectPresentationCollection.ordered(
        documents,
        data["active_document_id"],
    )


def _configure_collection_persistence(application, presentation: SLDDocument) -> None:
    lifecycle = application.project_lifecycle
    lifecycle.configure_presentation_collection_contract(
        serializer=_serialize_collection,
        deserializer=_deserialize_collection,
        activator=lambda _context, _collection: None,
    )
    lifecycle.configure_presentation_collection_snapshot_provider(
        lambda: ProjectPresentationCollection.single(presentation)
    )


def test_save_open_restores_sld_and_reopens_clean(tmp_path):
    application = create_application(_network())
    presentation = _presentation(application.project_lifecycle.context.project_id)
    application.attach_sld_service(SLDService(presentation))
    application.configure_project_presentation(
        presentation=presentation,
        serializer=_serializer,
        deserializer=_deserializer,
    )
    _configure_collection_persistence(application, presentation)

    path = tmp_path / "lifecycle.gridforge"
    application.save_project_as(str(path))
    assert application.is_dirty is False

    result = application.execute(SetSLDNodePositionCommand(node_id="SLD-NODE-001", x=777.0, y=888.0))
    assert result.success is True
    assert application.is_dirty is True

    application.save_project()
    assert application.is_dirty is False
    application.close_project()
    assert application.project_lifecycle.has_project is False

    application.open_project(str(path))
    restored = application.presentation
    assert isinstance(restored, SLDDocument)
    assert restored.model.get_node("SLD-NODE-001").equipment_id == "BUS-001"
    assert restored.model.get_node("SLD-NODE-001").position == (777.0, 888.0)
    assert application.is_dirty is False


def test_failed_presentation_serialization_does_not_mark_project_clean(tmp_path):
    application = create_application(_network())
    presentation = _presentation(application.project_lifecycle.context.project_id)
    application.attach_sld_service(SLDService(presentation))
    application.configure_project_presentation(
        presentation=presentation,
        serializer=_serializer,
        deserializer=_deserializer,
    )
    _configure_collection_persistence(application, presentation)
    path = tmp_path / "lifecycle.gridforge"
    application.save_project_as(str(path))

    result = application.execute(SetSLDNodePositionCommand(node_id="SLD-NODE-001", x=901.0, y=902.0))
    assert result.success is True
    assert application.is_dirty is True

    def failing_serializer(_document: SLDDocument) -> dict:
        raise RuntimeError("serialization failure")

    application.project_lifecycle.configure_presentation_collection_contract(
        serializer=lambda _collection: failing_serializer(_document=presentation),
        deserializer=_deserialize_collection,
        activator=lambda _context, _collection: None,
    )
    with pytest.raises(RuntimeError, match="serialization failure"):
        application.save_project()
    assert application.is_dirty is True
