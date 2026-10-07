# ============================================================
# GridForge V2
# File: tests/core/application/test_draft_inspector_update.py
# Author: Subhendu Mishra
# ============================================================

from __future__ import annotations

from types import SimpleNamespace

from core.application import create_application
from core.application.commands.draft_commands import UpdateDraftEquipmentCommand
from core.application.draft.network import DraftEquipment, DraftNetwork
from core.application.events import DraftChanged
from core.network.network import Network


def _application_with_transformer_draft():
    application = create_application(Network())
    application.set_draft_network(
        DraftNetwork.empty("project-test", 1)
    )
    application.draft_network.add_equipment(
        DraftEquipment(
            draft_id="transformer-draft-1",
            equipment_type="transformer",
            display_name="Transformer",
            terminal_contract=("HV", "LV"),
            engineering_data={"r": 0.01, "x": 0.05, "rate_mva": 10.0},
            placement=(120.0, 80.0),
            command_type="model.create_transformer",
            id_field="transformer_id",
        )
    )
    return application


def test_draft_engineering_intent_becomes_update_draft_command():
    application = _application_with_transformer_draft()
    intent = SimpleNamespace(
        identity_kind="draft",
        element_type="transformer",
        element_id="transformer-draft-1",
        values={"rate_mva": 25.0},
    )

    command = application.prepare_draft_engineering_update(intent)

    assert isinstance(command, UpdateDraftEquipmentCommand)
    assert command.payload["draft_id"] == "transformer-draft-1"
    assert dict(command.payload["changes"]["engineering_data"]) == {
        "r": 0.01,
        "x": 0.05,
        "rate_mva": 25.0,
    }


def test_draft_engineering_update_reaches_draft_network_and_emits_event():
    application = _application_with_transformer_draft()
    events = []
    application.event_bus.subscribe(DraftChanged, events.append)
    before_revision = application.revision

    command = application.prepare_draft_engineering_update(
        SimpleNamespace(
            identity_kind="draft",
            element_type="transformer",
            element_id="transformer-draft-1",
            values={"rate_mva": 25.0},
        )
    )
    result = application.execute(command)

    assert result.success
    updated = application.draft_network.require_equipment("transformer-draft-1")
    assert updated.engineering_data["rate_mva"] == 25.0
    assert updated.placement == (120.0, 80.0)
    assert updated.draft_id == "transformer-draft-1"
    assert application.read_network().elements == ()
    assert len(events) == 1
    assert events[0].metadata["operation"] == "execute"
    assert application.revision == before_revision


def test_draft_engineering_update_rejects_wrong_identity_scope():
    application = _application_with_transformer_draft()

    try:
        application.prepare_draft_engineering_update(
            SimpleNamespace(
                identity_kind="element",
                element_type="transformer",
                element_id="transformer-draft-1",
                values={"rate_mva": 25.0},
            )
        )
    except ValueError as exc:
        assert "draft projection identity" in str(exc)
    else:
        raise AssertionError("Expected draft identity scope validation to fail")
