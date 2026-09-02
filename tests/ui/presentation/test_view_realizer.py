# ============================================================
# File: tests/ui/presentation/test_view_realizer.py
# GridForge V2 — View Realizer Tests
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from ui.presentation.view_realizer import ViewRealizer
from ui.workspace.view_manager import ViewRecord


def test_realizer_delegates_logical_view_to_factory() -> None:
    created: list[tuple[str, str]] = []

    def factory(view: ViewRecord) -> object:
        created.append((view.view_id, view.view_type))
        return object()

    view = ViewRecord("VIEW-001", "DOC-001", "sld")
    realizer = ViewRealizer(factory)

    result = realizer.realize(view)

    assert result is not None
    assert created == [("VIEW-001", "sld")]


def test_realizer_does_not_modify_view_record() -> None:
    view = ViewRecord("VIEW-001", "DOC-001", "sld")
    realizer = ViewRealizer(lambda _: object())

    realizer.realize(view)

    assert view.view_id == "VIEW-001"
    assert view.document_id == "DOC-001"
    assert view.view_type == "sld"
