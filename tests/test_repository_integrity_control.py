# ============================================================
# File: tests/test_repository_integrity_control.py
# GridForge V2 — Repository Integrity Regression Tests
# Author: Subhendu Mishra
# ============================================================

import math

import pytest

from core.application.events import __all__ as EVENT_EXPORTS
from core.control.base import ControlComponent, ControlKind, ControlSignal
from core.control.controller import ControlController, ControllerEvaluationError
from core.application.read_models import EngineeringParameterReadModel
from ui.creation.creation_context import CreationDraft


class _FiniteTestComponent(ControlComponent):
    @property
    def component_id(self) -> str:
        return "integrity-test"

    @property
    def component_type(self) -> str:
        return "integrity_test"

    @property
    def control_kind(self) -> ControlKind:
        return ControlKind.LOGIC

    def input_definition(self):
        return ()

    def output_definition(self):
        return (ControlSignal("ok", required=False),)

    def output(self, state, inputs, time):
        return {"ok": True}


def test_controller_accepts_finite_time():
    controller = ControlController([_FiniteTestComponent()])
    result = controller.evaluate(time=0.0)
    assert result["integrity-test"].time == 0.0


@pytest.mark.parametrize("time", [math.nan, math.inf, -math.inf])
def test_controller_rejects_non_finite_time(time):
    controller = ControlController([_FiniteTestComponent()])
    with pytest.raises(ControllerEvaluationError, match="finite"):
        controller.evaluate(time=time)


def test_application_event_exports_resolve():
    namespace = {}
    for name in EVENT_EXPORTS:
        namespace[name] = getattr(__import__("core.application.events", fromlist=[name]), name)
        assert namespace[name] is not None


def test_affected_annotation_types_are_importable():
    assert EngineeringParameterReadModel.__name__ == "EngineeringParameterReadModel"
    assert CreationDraft.__name__ == "CreationDraft"
