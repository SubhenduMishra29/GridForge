"""Public package boundary for the headless GridForge Control subsystem."""

from . import base as _base
from .state import ControlState

# The canonical implementation is ControlController in controller.py.
_base.ControlState = ControlState

from .signals import ControlSignal
from .limits import Limit as ControlLimits
from .controller import ControlController
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
    "ControlController",
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
