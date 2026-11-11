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


class _State:
    def __init__(self):
        self.dirty = False

    def mark_dirty(self):
        self.dirty = True

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
