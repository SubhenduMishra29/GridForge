from __future__ import annotations

from types import SimpleNamespace

import pytest

from ui.sld.sld_controller import SLDController
from ui.sld.sld_document import SLDDocument
from ui.sld.sld_model import SLDAnnotationBlock, SLDModel, SLDNode, SLDPresentationLayer


class _Application:
    def __init__(self):
        self.commands = []

    def execute(self, command):
        self.commands.append(command)
        return SimpleNamespace(success=True, message="")

    def read_network(self):
        return SimpleNamespace(elements=(), simple_wires=())

    def read_draft_network(self, document_id=None):
        return {"equipment": [], "connections": []}


class _State:
    def __init__(self):
        self.dirty = False
        self.selected_node_ids = set()
        self.selected_connection_ids = set()

    def mark_dirty(self):
        self.dirty = True

    def clear_selection(self):
        self.selected_node_ids.clear()
        self.selected_connection_ids.clear()

    def reset(self):
        self.dirty = False


def _controller(document):
    controller = object.__new__(SLDController)
    controller._active_layer_by_document = {document.document_id: "engineering"}
    controller._require_active_document = lambda: document
    controller._application = _Application()
    controller._require_application = lambda: controller._application
    controller._state = _State()
    return controller


def _document(*, annotations=(), engineering_locked=False, default_locked=False, default_visible=True):
    model = SLDModel()
    model.add_node(SLDNode("node-1"))
    return SLDDocument(
        "sld-layer-annotations",
        model=model,
        annotation_blocks=list(annotations),
        layers=[
            SLDPresentationLayer("default", "Default", visible=default_visible, locked=default_locked, order=0),
            SLDPresentationLayer(
                "engineering", "Engineering",
                locked=engineering_locked, order=1,
            ),
        ],
    )


def test_new_annotation_inherits_active_layer_and_existing_annotation_keeps_layer():
    original = SLDAnnotationBlock(
        "existing", "node-1", ("identity",), layer_id="default",
    )
    document = _document(annotations=(original,))
    controller = _controller(document)

    controller.set_annotation_blocks([
        {"block_id": "new", "node_id": "node-1", "fields": ["identity"]},
        {"block_id": "existing", "node_id": "node-1", "fields": ["identity"]},
    ])

    payload = controller._application.commands[-1].payload["annotation_blocks"]
    assert payload[0]["layer_id"] == "engineering"
    assert payload[1]["layer_id"] == "default"
    assert controller._state.dirty is True


def test_new_annotation_object_default_layer_means_active_authoring_layer():
    document = _document()
    controller = _controller(document)
    block = SLDAnnotationBlock("new", "node-1", ("identity",))

    controller.set_annotation_blocks([block])

    payload = controller._application.commands[-1].payload["annotation_blocks"]
    assert payload[0]["layer_id"] == "engineering"


def test_annotation_changes_on_locked_layer_are_rejected_before_command():
    document = _document(engineering_locked=True)
    controller = _controller(document)

    with pytest.raises(ValueError, match="locked"):
        controller.set_annotation_blocks([
            {"block_id": "new", "node_id": "node-1", "fields": ["identity"]},
        ])

    assert controller._application.commands == []


def test_project_load_clears_transient_layer_selection_even_when_ids_are_reused():
    controller = object.__new__(SLDController)
    controller._active_layer_by_document = {
        "shared-sld-id": "engineering",
        "another-sld-id": "protection",
    }
    reconciled = []
    controller.reconcile_presentation = lambda: reconciled.append(True)

    controller._on_project_loaded(None)

    assert controller._active_layer_by_document == {}
    assert reconciled == [True]


def test_project_close_and_dispose_clear_transient_layer_selection():
    controller = object.__new__(SLDController)
    controller._active_layer_by_document = {"sld": "engineering"}
    controller._state = _State()
    controller._application = None
    controller._document_activation_handler = object()

    controller._on_project_closed(None)
    assert controller._active_layer_by_document == {}
    assert controller._state.dirty is False

    controller._active_layer_by_document["sld"] = "protection"
    controller.dispose()
    assert controller._active_layer_by_document == {}
    assert controller._document_activation_handler is None


def test_active_layer_selection_is_scoped_to_each_document():
    first = SLDDocument(
        "sld-one",
        layers=[
            SLDPresentationLayer("default", "Default", order=0),
            SLDPresentationLayer("engineering", "Engineering", order=1),
        ],
    )
    second = SLDDocument("sld-two")
    controller = object.__new__(SLDController)
    controller._active_layer_by_document = {
        "sld-one": "engineering",
        "sld-two": "default",
    }
    active = [first]
    controller._require_active_document = lambda: active[0]

    assert controller.active_layer_id == "engineering"
    active[0] = second
    assert controller.active_layer_id == "default"
    active[0] = first
    assert controller.active_layer_id == "engineering"


def test_active_layer_recovers_to_visible_unlocked_layer_when_default_is_locked_or_hidden():
    document = _document(default_locked=True)
    controller = _controller(document)
    controller._active_layer_by_document[document.document_id] = "default"

    assert controller.active_layer_id == "engineering"

    hidden_default = _document(default_visible=False)
    controller = _controller(hidden_default)
    controller._active_layer_by_document[hidden_default.document_id] = "default"
    assert controller.active_layer_id == "engineering"


def test_active_layer_fails_closed_when_every_layer_is_hidden_or_locked():
    document = _document(default_locked=True, engineering_locked=True)
    controller = _controller(document)
    controller._active_layer_by_document[document.document_id] = "default"

    with pytest.raises(RuntimeError, match="No visible, unlocked SLD layer"):
        _ = controller.active_layer_id

    assert document.document_id not in controller._active_layer_by_document


def test_delete_selection_routes_mixed_sld_nodes_and_connections_through_one_batch():
    from core.application.commands.selection_commands import DeleteSelectionBatchCommand

    document = _document()
    document.model.add_node(SLDNode("node-2"))
    document.model.create_connection(
        "engineer-wire", "node-1", "node-2",
        properties={"presentation_owner": "engineer"},
    )
    controller = _controller(document)
    controller._state.selected_node_ids = {"node-1"}
    controller._state.selected_connection_ids = {"engineer-wire"}

    assert controller.delete_selection() is True

    assert len(controller._application.commands) == 1
    batch = controller._application.commands[0]
    assert isinstance(batch, DeleteSelectionBatchCommand)
    assert {command.command_type for command in batch.payload["commands"]} == {
        "sld.remove_node", "sld.remove_connection",
    }
    assert batch.payload["document_id"] == document.document_id
    assert controller._state.selected_node_ids == set()
    assert controller._state.selected_connection_ids == set()
    assert controller._state.dirty is True


def test_delete_selection_resolves_draft_node_and_attached_wire_as_one_batch():
    from core.application.commands.selection_commands import DeleteSelectionBatchCommand

    document = _document()
    controller = _controller(document)
    controller._application.read_draft_network = lambda document_id=None: {
        "equipment": [{"draft_id": "draft-1"}],
        "connections": [{
            "connection_id": "draft-wire",
            "source": {"scope": "draft", "object_id": "draft-1"},
            "target": {"scope": "core", "object_id": "bus-1"},
        }],
    }
    controller._state.selected_node_ids = {"draft-1"}

    assert controller.delete_selection() is True

    batch = controller._application.commands[0]
    assert isinstance(batch, DeleteSelectionBatchCommand)
    assert {command.command_type for command in batch.payload["commands"]} == {
        "draft.remove_equipment", "draft.remove_connection",
    }


def test_delete_selection_fails_closed_for_unsupported_core_equipment_type():
    controller = _controller(_document())
    controller._state.selected_node_ids = {"unsupported-node"}
    controller._require_active_document().model.add_node(
        SLDNode("unsupported-node", equipment_id="line-1")
    )
    controller._application.read_network = lambda: SimpleNamespace(
        elements=(SimpleNamespace(object_id="line-1", element_type="LINE"),),
        simple_wires=(),
    )

    with pytest.raises(ValueError, match="not yet supported"):
        controller.delete_selection()

    assert controller._application.commands == []
