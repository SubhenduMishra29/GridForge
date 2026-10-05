from __future__ import annotations

from types import SimpleNamespace

import pytest

from core.application.services.sld_service import SLDService
from core.application.transaction import Transaction
from ui.sld.sld_document import SLDDocument


def _document() -> SLDDocument:
    document = SLDDocument("test:sld", project_id="test")
    document.model.create_node("node-a", equipment_id="eq-a")
    document.model.create_node("node-b", equipment_id="eq-b")
    return document


def _connection(document: SLDDocument, *, owner: str = "engineer", core_id: str | None = "SWC-1"):
    properties = {
        "connection_kind": "SIMPLE_WIRE",
        "presentation_owner": owner,
        "lifecycle_state": "BOUND",
    }
    if core_id is not None:
        properties["core_connection_id"] = core_id
    if owner == "engineer":
        properties["route_owner"] = "engineer"
    return document.model.create_connection(
        connection_id="sld-wire-SWC-1",
        source_node_id="node-a",
        target_node_id="node-b",
        source_endpoint={
            "kind": "equipment",
            "node_id": "node-a",
            "equipment_id": "eq-a",
            "equipment_type": "bus",
            "terminal_role": "HV",
        },
        target_endpoint={
            "kind": "equipment",
            "node_id": "node-b",
            "equipment_id": "eq-b",
            "equipment_type": "bus",
            "terminal_role": "HV",
        },
        route={"ownership": "engineer", "routing_mode": "manual", "points": [[1, 2]]},
        properties=properties,
    )


def test_engineer_owned_delete_clears_core_binding_and_preserves_orphan_snapshot() -> None:
    document = _document()
    connection = _connection(document)
    before = connection.to_dict()
    service = SLDService(document)
    transaction = Transaction()

    assert service.reconcile_connection_delete(connection_id="SWC-1", transaction=transaction) == "ORPHANED"

    orphan = document.model.get_connection("sld-wire-SWC-1")
    assert orphan.properties["lifecycle_state"] == "ORPHANED"
    assert "core_connection_id" not in orphan.properties
    assert orphan.source_endpoint is None
    assert orphan.target_endpoint is None
    assert orphan.route.to_dict() == before["route"]
    assert orphan.properties["presentation_owner"] == "engineer"

    transaction.rollback()
    assert document.model.get_connection("sld-wire-SWC-1").to_dict() == before


def test_projection_owned_delete_removes_companion_and_undo_restores_it() -> None:
    document = _document()
    connection = _connection(document, owner="projection")
    connection.properties["projection_source"] = "core_reconciliation"
    before = connection.to_dict()
    service = SLDService(document)
    transaction = Transaction()

    assert service.reconcile_connection_delete(connection_id="SWC-1", transaction=transaction) == "REMOVED"
    assert document.model.get_connection_optional("sld-wire-SWC-1") is None

    transaction.rollback()
    assert document.model.get_connection("sld-wire-SWC-1").to_dict() == before


def test_orphan_is_ignored_by_simple_wire_projection_reconciliation() -> None:
    document = _document()
    connection = _connection(document)
    service = SLDService(document)
    delete_tx = Transaction()
    service.reconcile_connection_delete(connection_id="SWC-1", transaction=delete_tx)

    network = SimpleNamespace(connectivity=SimpleNamespace(connections=()))
    rollback = service.reconcile_simple_wire_projection(network)

    orphan = document.model.get_connection("sld-wire-SWC-1")
    assert orphan.properties["lifecycle_state"] == "ORPHANED"
    assert "core_connection_id" not in orphan.properties

    rollback()


def test_bound_missing_core_is_still_an_error() -> None:
    document = _document()
    _connection(document)
    service = SLDService(document)
    network = SimpleNamespace(connectivity=SimpleNamespace(connections=()))

    with pytest.raises(ValueError, match="no authoritative Core connection"):
        service.reconcile_simple_wire_projection(network)


def test_orphan_with_stale_core_binding_is_rejected_as_corrupt() -> None:
    document = _document()
    connection = _connection(document)
    connection.properties["lifecycle_state"] = "ORPHANED"
    service = SLDService(document)
    network = SimpleNamespace(connectivity=SimpleNamespace(connections=()))

    with pytest.raises(ValueError, match="must not retain an active Core connection binding"):
        service.reconcile_simple_wire_projection(network)
