"""Public package boundary for the headless GridForge Control subsystem."""

from . import base as _base
from .state import ControlState

# Compatibility export for legacy controller imports.  The canonical
# implementation remains core.control.state.ControlState.
_base.ControlState = ControlState

from .signals import ControlSignal
from .limits import Limit as ControlLimits
from .controller import Controller
from .decision import ControlActionType, ControlDecision
from .action import ControlActionBinding
from .context import ControlExecutionContext
from .engine import ControlEngine, ControlEvaluationResult
from .interlock import ControlInterlock, InterlockResult
from .measurement_input import ControlInput

__all__ = [
    "ControlState",
    "ControlSignal",
    "ControlLimits",
    "Controller",
    "ControlActionType",
    "ControlDecision",
    "ControlActionBinding",
    "ControlExecutionContext",
    "ControlEngine",
    "ControlEvaluationResult",
    "ControlInterlock",
    "InterlockResult",
    "ControlInput",
]
