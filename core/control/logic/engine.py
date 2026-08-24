"""
GridForge V2 - Logic Control Engine
====================================

Author:
    Subhendu Mishra

File:
    core/control/logic/engine.py

Purpose
-------
Headless execution engine for the Logic Control branch.

The engine owns:

    - Logic component registration
    - explicit logical signal connections
    - deterministic evaluation ordering
    - discrete component state
    - signal snapshots
    - event collection
    - propagation/stability evaluation

Architectural boundary
-----------------------
The Logic Engine is a Core Control service.

The UI logic-layout/editing canvas may create and edit logical
connections, but it never owns their electrical/control semantics.

A logical connection is explicitly:

    source_component.source_output
                    |
                    v
             target_component.target_input

A dependency is an execution-order relationship and is NOT itself
a signal connection.

The engine does not:

    - import UI code
    - import plugins
    - mutate core/model
    - own graphics/layout
    - perform numerical integration
    - solve electrical equations
    - infer UI wires from graphics
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any

from .base import (
    LogicControlComponent,
    LogicControlError,
    LogicControlResult,
    LogicEvent,
)


# ============================================================================
# ERRORS
# ============================================================================


class LogicEngineError(LogicControlError):
    """Base LogicEngine error."""


class LogicEngineConfigurationError(
    LogicEngineError,
):
    """Invalid LogicEngine configuration."""


class DuplicateLogicComponentError(
    LogicEngineConfigurationError,
):
    """A component ID is already registered."""


class UnknownLogicComponentError(
    LogicEngineError,
):
    """A referenced component does not exist."""


class LogicDependencyError(
    LogicEngineConfigurationError,
):
    """Invalid execution dependency."""


class LogicCycleError(
    LogicDependencyError,
):
    """A cyclic dependency graph was detected."""


class LogicConnectionError(
    LogicEngineConfigurationError,
):
    """Invalid logical signal connection."""


class DuplicateLogicConnectionError(
    LogicConnectionError,
):
    """A target input already has a source connection."""


class LogicEvaluationError(
    LogicEngineError,
):
    """Logic component evaluation failed."""


class LogicSignalError(
    LogicEngineError,
):
    """Logic signal propagation failed."""


class LogicStateUpdateError(
    LogicEngineError,
):
    """Logic state update failed."""


# ============================================================================
# ENUMERATIONS
# ============================================================================


class LogicEvaluationMode(str, Enum):
    """
    Logic evaluation mode.

    SINGLE_PASS
        Evaluate each component once in deterministic topological order.

    PROPAGATE
        Re-evaluate the network until the observable signal/state snapshot
        stabilizes or max_iterations is reached.
    """

    SINGLE_PASS = "single_pass"
    PROPAGATE = "propagate"


# ============================================================================
# DATA CONTRACTS
# ============================================================================


@dataclass(frozen=True)
class LogicDependency:
    """
    Explicit execution-order dependency.

    This does NOT transfer a signal.

    It means only:

        source_component evaluates before target_component.
    """

    source_component: str
    target_component: str

    def __post_init__(self) -> None:
        source = str(
            self.source_component
        ).strip()

        target = str(
            self.target_component
        ).strip()

        if not source:
            raise LogicDependencyError(
                "source_component cannot be empty."
            )

        if not target:
            raise LogicDependencyError(
                "target_component cannot be empty."
            )

        if source == target:
            raise LogicCycleError(
                f"Self-dependency detected for '{source}'."
            )

        object.__setattr__(
            self,
            "source_component",
            source,
        )

        object.__setattr__(
            self,
            "target_component",
            target,
        )


@dataclass(frozen=True)
class LogicConnection:
    """
    Explicit logical signal connection.

    Example:

        AND1.OUT -> COIL1.IN

    is represented as:

        LogicConnection(
            source_component="AND1",
            source_output="OUT",
            target_component="COIL1",
            target_input="IN",
        )

    This is the authoritative Core representation of a logical wire.
    """

    source_component: str
    source_output: str
    target_component: str
    target_input: str

    def __post_init__(self) -> None:
        values = {
            "source_component": self.source_component,
            "source_output": self.source_output,
            "target_component": self.target_component,
            "target_input": self.target_input,
        }

        normalized: dict[str, str] = {}

        for key, value in values.items():
            value = str(value).strip()

            if not value:
                raise LogicConnectionError(
                    f"{key} cannot be empty."
                )

            normalized[key] = value

        if (
            normalized["source_component"]
            == normalized["target_component"]
            and normalized["source_output"]
            == normalized["target_input"]
        ):
            raise LogicConnectionError(
                "A logical connection cannot connect a signal to itself."
            )

        for key, value in normalized.items():
            object.__setattr__(
                self,
                key,
                value,
            )


@dataclass(frozen=True)
class LogicComponentRecord:
    """Immutable component registration record."""

    component: LogicControlComponent
    order: int

    def __post_init__(self) -> None:
        if not isinstance(
            self.component,
            LogicControlComponent,
        ):
            raise LogicEngineConfigurationError(
                "component must be a LogicControlComponent."
            )

        if self.order < 0:
            raise LogicEngineConfigurationError(
                "component order cannot be negative."
            )

    @property
    def component_id(self) -> str:
        return str(
            self.component.component_id
        )

    @property
    def component_type(self) -> str:
        return str(
            self.component.component_type
        )


@dataclass(frozen=True)
class LogicComponentEvaluation:
    """Immutable evaluation record for one component."""

    component_id: str
    result: LogicControlResult

    @property
    def outputs(
        self,
    ) -> Mapping[str, Any]:
        return self.result.outputs

    @property
    def state(
        self,
    ) -> Mapping[str, Any]:
        return self.result.state

    @property
    def events(
        self,
    ) -> tuple[LogicEvent, ...]:
        return tuple(
            self.result.events
        )


@dataclass(frozen=True)
class LogicEngineResult:
    """Complete result of one LogicEngine evaluation."""

    time: float

    evaluations: Mapping[
        str,
        LogicComponentEvaluation,
    ]

    signals: Mapping[
        str,
        Mapping[str, Any],
    ]

    states: Mapping[
        str,
        Mapping[str, Any],
    ]

    events: tuple[
        LogicEvent,
        ...

    ]

    stable: bool
    iterations: int

    diagnostics: Mapping[
        str,
        Any,
    ] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        time = _finite_float(
            self.time,
            "time",
        )

        object.__setattr__(
            self,
            "time",
            time,
        )

        object.__setattr__(
            self,
            "evaluations",
            dict(
                self.evaluations
            ),
        )

        object.__setattr__(
            self,
            "signals",
            {
                str(component_id): dict(
                    values
                )
                for component_id, values
                in self.signals.items()
            },
        )

        object.__setattr__(
            self,
            "states",
            {
                str(component_id): dict(
                    values
                )
                for component_id, values
                in self.states.items()
            },
        )

        object.__setattr__(
            self,
            "events",
            tuple(
                self.events
            ),
        )

        object.__setattr__(
            self,
            "iterations",
            int(
                self.iterations
            ),
        )

        object.__setattr__(
            self,
            "diagnostics",
            dict(
                self.diagnostics
            ),
        )


# ============================================================================
# ENGINE
# ============================================================================


class LogicEngine:
    """
    Headless deterministic Logic Control execution engine.

    Important distinction
    ---------------------
    A LogicConnection transfers a signal.

    A LogicDependency constrains evaluation order.

    A connection automatically creates the corresponding execution
    dependency:

        source -> target

    but the two contracts remain separate.
    """

    def __init__(
        self,
        components: Iterable[
            LogicControlComponent
        ] | None = None,
        *,
        mode: LogicEvaluationMode = (
            LogicEvaluationMode.SINGLE_PASS
        ),
        max_iterations: int = 32,
    ) -> None:
        try:
            self._mode = (
                mode
                if isinstance(
                    mode,
                    LogicEvaluationMode,
                )
                else LogicEvaluationMode(
                    mode
                )
            )
        except ValueError as exc:
            raise LogicEngineConfigurationError(
                f"Invalid evaluation mode: {mode!r}."
            ) from exc

        max_iterations = int(
            max_iterations
        )

        if max_iterations <= 0:
            raise LogicEngineConfigurationError(
                "max_iterations must be greater than zero."
            )

        self._max_iterations = (
            max_iterations
        )

        self._records: dict[
            str,
            LogicComponentRecord,
        ] = {}

        self._connections: list[
            LogicConnection
        ] = []

        self._dependencies: list[
            LogicDependency
        ] = []

        self._states: dict[
            str,
            dict[str, Any],
        ] = {}

        self._signals: dict[
            str,
            dict[str, Any],
        ] = {}

        self._order_counter = 0

        if components is not None:
            for component in components:
                self.register(
                    component
                )

    # ========================================================================
    # PROPERTIES
    # ========================================================================

    @property
    def mode(
        self,
    ) -> LogicEvaluationMode:
        return self._mode

    @property
    def max_iterations(
        self,
    ) -> int:
        return self._max_iterations

    # ========================================================================
    # COMPONENT REGISTRATION
    # ========================================================================

    def register(
        self,
        component: LogicControlComponent,
        *,
        order: int | None = None,
        initial_state: Mapping[
            str,
            Any,
        ] | None = None,
    ) -> None:
        """Register one Logic Control component."""

        if not isinstance(
            component,
            LogicControlComponent,
        ):
            raise LogicEngineConfigurationError(
                "Only LogicControlComponent instances "
                "can be registered."
            )

        component_id = str(
            component.component_id
        ).strip()

        if not component_id:
            raise LogicEngineConfigurationError(
                "Logic component ID cannot be empty."
            )

        if component_id in self._records:
            raise DuplicateLogicComponentError(
                f"Logic component '{component_id}' "
                "is already registered."
            )

        if order is None:
            order = self._order_counter

        order = int(order)

        if order < 0:
            raise LogicEngineConfigurationError(
                "Component order cannot be negative."
            )

        if any(
            record.order == order
            for record in self._records.values()
        ):
            raise LogicEngineConfigurationError(
                f"Component order '{order}' "
                "is already occupied."
            )

        if initial_state is None:
            state = dict(
                component.initial_state()
            )
        else:
            state = dict(
                initial_state
            )

        try:
            normalized_state = (
                component.validate_state(
                    state
                )
            )
        except Exception as exc:
            raise LogicStateUpdateError(
                f"Invalid initial state for "
                f"'{component_id}'."
            ) from exc

        self._records[
            component_id
        ] = LogicComponentRecord(
            component=component,
            order=order,
        )

        self._states[
            component_id
        ] = dict(
            normalized_state
        )

        self._signals.setdefault(
            component_id,
            {},
        )

        self._order_counter = max(
            self._order_counter,
            order + 1,
        )

        self._validate_all_graph_contracts()

    def unregister(
        self,
        component_id: str,
    ) -> LogicControlComponent:
        """Unregister a component and its graph references."""

        component_id = str(
            component_id
        ).strip()

        record = self._records.pop(
            component_id,
            None,
        )

        if record is None:
            raise UnknownLogicComponentError(
                f"Unknown logic component "
                f"'{component_id}'."
            )

        self._states.pop(
            component_id,
            None,
        )

        self._signals.pop(
            component_id,
            None,
        )

        self._connections = [
            connection
            for connection
            in self._connections
            if (
                connection.source_component
                != component_id
                and connection.target_component
                != component_id
            )
        ]

        self._dependencies = [
            dependency
            for dependency
            in self._dependencies
            if (
                dependency.source_component
                != component_id
                and dependency.target_component
                != component_id
            )
        ]

        return record.component

    def clear(
        self,
    ) -> None:
        """Clear all components and graph/state information."""

        self._records.clear()
        self._connections.clear()
        self._dependencies.clear()
        self._states.clear()
        self._signals.clear()
        self._order_counter = 0

    # ========================================================================
    # COMPONENT ACCESS
    # ========================================================================

    def contains(
        self,
        component_id: str,
    ) -> bool:
        return (
            str(component_id).strip()
            in self._records
        )

    def get(
        self,
        component_id: str,
    ) -> LogicControlComponent:
        component_id = str(
            component_id
        ).strip()

        try:
            return self._records[
                component_id
            ].component
        except KeyError as exc:
            raise UnknownLogicComponentError(
                f"Unknown logic component "
                f"'{component_id}'."
            ) from exc

    def components(
        self,
    ) -> tuple[
        LogicControlComponent,
        ...,
    ]:
        records = sorted(
            self._records.values(),
            key=lambda record: (
                record.order,
                record.component_id,
            ),
        )

        return tuple(
            record.component
            for record in records
        )

    def records(
        self,
    ) -> tuple[
        LogicComponentRecord,
        ...,
    ]:
        return tuple(
            sorted(
                self._records.values(),
                key=lambda record: (
                    record.order,
                    record.component_id,
                ),
            )
        )

    def __iter__(
        self,
    ) -> Iterator[
        LogicControlComponent
    ]:
        return iter(
            self.components()
        )

    def __len__(
        self,
    ) -> int:
        return len(
            self._records
        )

    # ========================================================================
    # LOGICAL CONNECTIONS
    # ========================================================================

    def connect(
        self,
        source_component: str,
        source_output: str,
        target_component: str,
        target_input: str,
    ) -> LogicConnection:
        """
        Create an explicit source-output -> target-input connection.

        Example:

            engine.connect(
                "AND1",
                "OUT",
                "COIL1",
                "IN",
            )

        The target input may have only one upstream source.
        """

        connection = LogicConnection(
            source_component=source_component,
            source_output=source_output,
            target_component=target_component,
            target_input=target_input,
        )

        self._validate_connection_endpoints(
            connection
        )

        if connection in self._connections:
            return connection

        for existing in self._connections:
            if (
                existing.target_component
                == connection.target_component
                and existing.target_input
                == connection.target_input
            ):
                raise DuplicateLogicConnectionError(
                    f"Input "
                    f"'{connection.target_component}."
                    f"{connection.target_input}' "
                    "already has a source connection."
                )

        self._connections.append(
            connection
        )

        dependency = LogicDependency(
            source_component=(
                connection.source_component
            ),
            target_component=(
                connection.target_component
            ),
        )

        if dependency not in self._dependencies:
            self._dependencies.append(
                dependency
            )

        try:
            self._validate_all_graph_contracts()
        except Exception:
            self._connections.remove(
                connection
            )

            if dependency in self._dependencies:
                self._dependencies.remove(
                    dependency
                )

            raise

        return connection

    def disconnect(
        self,
        source_component: str,
        source_output: str,
        target_component: str,
        target_input: str,
    ) -> bool:
        """Remove one explicit logical connection."""

        connection = LogicConnection(
            source_component=source_component,
            source_output=source_output,
            target_component=target_component,
            target_input=target_input,
        )

        if connection not in self._connections:
            return False

        self._connections.remove(
            connection
        )

        self._rebuild_connection_dependencies()

        return True

    def connections(
        self,
    ) -> tuple[
        LogicConnection,
        ...,
    ]:
        """Return all logical signal connections."""

        return tuple(
            self._connections
        )

    def connection_for_input(
        self,
        target_component: str,
        target_input: str,
    ) -> LogicConnection | None:
        """Return the source connection feeding a target input."""

        target_component = str(
            target_component
        ).strip()

        target_input = str(
            target_input
        ).strip()

        for connection in self._connections:
            if (
                connection.target_component
                == target_component
                and connection.target_input
                == target_input
            ):
                return connection

        return None

    # ========================================================================
    # EXECUTION DEPENDENCIES
    # ========================================================================

    def add_dependency(
        self,
        source_component: str,
        target_component: str,
    ) -> LogicDependency:
        """
        Add an execution-order dependency.

        This is intentionally separate from ``connect()``.
        """

        dependency = LogicDependency(
            source_component=source_component,
            target_component=target_component,
        )

        self._validate_component_exists(
            dependency.source_component
        )

        self._validate_component_exists(
            dependency.target_component
        )

        if dependency not in self._dependencies:
            self._dependencies.append(
                dependency
            )

        try:
            self._validate_dependencies()
        except Exception:
            self._dependencies.remove(
                dependency
            )
            raise

        return dependency

    def remove_dependency(
        self,
        source_component: str,
        target_component: str,
    ) -> bool:
        dependency = LogicDependency(
            source_component=source_component,
            target_component=target_component,
        )

        if dependency not in self._dependencies:
            return False

        self._dependencies.remove(
            dependency
        )

        return True

    def dependencies(
        self,
    ) -> tuple[
        LogicDependency,
        ...,
    ]:
        return tuple(
            self._dependencies
        )

    # ========================================================================
    # STATE
    # ========================================================================

    def state(
        self,
        component_id: str,
    ) -> Mapping[str, Any]:
        """Return a copy of one component's current state."""

        component_id = str(
            component_id
        ).strip()

        self._validate_component_exists(
            component_id
        )

        return dict(
            self._states[
                component_id
            ]
        )

    def states(
        self,
    ) -> Mapping[
        str,
        Mapping[str, Any],
    ]:
        """Return a copy of all component states."""

        return {
            component_id: dict(
                state
            )
            for component_id, state
            in self._states.items()
        }

    def set_state(
        self,
        component_id: str,
        state: Mapping[str, Any],
    ) -> None:
        """Replace one component's persistent logic state."""

        component = self.get(
            component_id
        )

        try:
            normalized = (
                component.validate_state(
                    state
                )
            )
        except Exception as exc:
            raise LogicStateUpdateError(
                f"Invalid state for "
                f"'{component_id}'."
            ) from exc

        self._states[
            component_id
        ] = dict(
            normalized
        )

    def reset(
        self,
    ) -> None:
        """Reset every registered component to its initial logic state."""

        for record in self.records():
            component = record.component
            component_id = record.component_id

            try:
                state = component.reset()
                normalized = (
                    component.validate_state(
                        state
                    )
                )
            except Exception as exc:
                raise LogicStateUpdateError(
                    f"Failed to reset "
                    f"'{component_id}'."
                ) from exc

            self._states[
                component_id
            ] = dict(
                normalized
            )

            self._signals[
                component_id
            ] = {}

    # ========================================================================
    # EVALUATION
    # ========================================================================

    def evaluate(
        self,
        time: float,
        external_inputs: Mapping[
            str,
            Mapping[str, Any],
        ] | None = None,
    ) -> LogicEngineResult:
        """
        Evaluate the complete Logic network.

        ``external_inputs`` contains only inputs supplied from outside
        the registered Logic network.

        Example:

            {
                "START": {
                    "IN": True,
                }
            }

        Connected inputs are resolved automatically from upstream
        component outputs.
        """

        time = _finite_float(
            time,
            "time",
        )

        external = self._normalize_external_inputs(
            external_inputs
        )

        self._validate_all_graph_contracts()

        if self._mode is LogicEvaluationMode.SINGLE_PASS:
            return self._evaluate_pass(
                time=time,
                external_inputs=external,
                iteration=1,
            )

        return self._evaluate_propagated(
            time=time,
            external_inputs=external,
        )

    def evaluate_once(
        self,
        time: float,
        external_inputs: Mapping[
            str,
            Mapping[str, Any],
        ] | None = None,
    ) -> LogicEngineResult:
        """Force exactly one deterministic evaluation pass."""

        time = _finite_float(
            time,
            "time",
        )

        external = self._normalize_external_inputs(
            external_inputs
        )

        self._validate_all_graph_contracts()

        return self._evaluate_pass(
            time=time,
            external_inputs=external,
            iteration=1,
        )

    # ========================================================================
    # SINGLE PASS
    # ========================================================================

    def _evaluate_pass(
        self,
        *,
        time: float,
        external_inputs: Mapping[
            str,
            Mapping[str, Any],
        ],
        iteration: int,
    ) -> LogicEngineResult:
        previous_states = self.states()
        previous_signals = self._signal_snapshot()

        evaluations: dict[
            str,
            LogicComponentEvaluation,
        ] = {}

        events: list[
            LogicEvent
        ] = []

        for component in self._evaluation_order():
            component_id = str(
                component.component_id
            )

            inputs = self._resolve_component_inputs(
                component,
                external_inputs,
                evaluations,
            )

            try:
                control_result = component.evaluate(
                    self._states[
                        component_id
                    ],
                    inputs,
                    time,
                )
            except Exception as exc:
                raise LogicEvaluationError(
                    f"Logic evaluation failed for "
                    f"'{component_id}'."
                ) from exc

            logic_result = (
                self._logic_result_from_control_result(
                    component,
                    control_result,
                    time,
                )
            )

            evaluations[
                component_id
            ] = LogicComponentEvaluation(
                component_id=component_id,
                result=logic_result,
            )

            self._states[
                component_id
            ] = dict(
                logic_result.state
            )

            self._signals[
                component_id
            ] = dict(
                logic_result.outputs
            )

            events.extend(
                logic_result.events
            )

        stable = (
            previous_states
            == self.states()
            and previous_signals
            == self._signal_snapshot()
        )

        return LogicEngineResult(
            time=time,
            evaluations=evaluations,
            signals=self._signal_snapshot(),
            states=self.states(),
            events=tuple(events),
            stable=stable,
            iterations=iteration,
            diagnostics={
                "mode": self._mode.value,
            },
        )

    # ========================================================================
    # PROPAGATION
    # ========================================================================

    def _evaluate_propagated(
        self,
        *,
        time: float,
        external_inputs: Mapping[
            str,
            Mapping[str, Any],
        ],
    ) -> LogicEngineResult:
        last_result: LogicEngineResult | None = None

        for iteration in range(
            1,
            self._max_iterations + 1,
        ):
            result = self._evaluate_pass(
                time=time,
                external_inputs=external_inputs,
                iteration=iteration,
            )

            last_result = result

            if result.stable:
                return result

        if last_result is None:
            raise LogicEvaluationError(
                "Logic propagation produced no result."
            )

        return LogicEngineResult(
            time=last_result.time,
            evaluations=last_result.evaluations,
            signals=last_result.signals,
            states=last_result.states,
            events=last_result.events,
            stable=False,
            iterations=self._max_iterations,
            diagnostics={
                **dict(
                    last_result.diagnostics
                ),
                "warning": (
                    "Logic network did not stabilize "
                    "within max_iterations."
                ),
            },
        )

    # ========================================================================
    # INPUT RESOLUTION
    # ========================================================================

    def _resolve_component_inputs(
        self,
        component: LogicControlComponent,
        external_inputs: Mapping[
            str,
            Mapping[str, Any],
        ],
        evaluations: Mapping[
            str,
            LogicComponentEvaluation,
        ],
    ) -> dict[str, Any]:
        """
        Resolve one component's inputs.

        Resolution order:

            1. externally supplied input
            2. explicit logical connection
            3. component-defined default, if non-required
            4. otherwise validation failure

        An explicit connection always has authority over an externally
        supplied value for the same target input.
        """

        component_id = str(
            component.component_id
        )

        supplied = dict(
            external_inputs.get(
                component_id,
                {},
            )
        )

        result = dict(
            supplied
        )

        for connection in self._connections:
            if (
                connection.target_component
                != component_id
            ):
                continue

            source_id = (
                connection.source_component
            )

            source_evaluation = evaluations.get(
                source_id
            )

            if source_evaluation is None:
                raise LogicSignalError(
                    f"Source component "
                    f"'{source_id}' has not been evaluated "
                    f"before target '{component_id}'."
                )

            outputs = source_evaluation.outputs

            if (
                connection.source_output
                not in outputs
            ):
                raise LogicSignalError(
                    f"Source output "
                    f"'{source_id}."
                    f"{connection.source_output}' "
                    "does not exist in the evaluation result."
                )

            result[
                connection.target_input
            ] = outputs[
                connection.source_output
            ]

        try:
            return component.validate_inputs(
                result
            )
        except Exception as exc:
            raise LogicSignalError(
                f"Unable to resolve inputs for "
                f"'{component_id}'."
            ) from exc

    # ========================================================================
    # EVALUATION ORDER
    # ========================================================================

    def _evaluation_order(
        self,
    ) -> tuple[
        LogicControlComponent,
        ...,
    ]:
        """
        Return deterministic topological evaluation order.

        Explicit dependencies and logical connections both participate
        in ordering.

        Registration order is used to break otherwise independent ties.
        """

        component_ids = set(
            self._records
        )

        indegree = {
            component_id: 0
            for component_id
            in component_ids
        }

        outgoing = {
            component_id: set()
            for component_id
            in component_ids
        }

        for dependency in self._dependencies:
            source = (
                dependency.source_component
            )
            target = (
                dependency.target_component
            )

            if target not in outgoing[source]:
                outgoing[source].add(
                    target
                )
                indegree[target] += 1

        records_by_id = self._records

        ready = sorted(
            (
                component_id
                for component_id, degree
                in indegree.items()
                if degree == 0
            ),
            key=lambda component_id: (
                records_by_id[
                    component_id
                ].order,
                component_id,
            ),
        )

        ordered_ids: list[str] = []

        while ready:
            current = ready.pop(0)

            ordered_ids.append(
                current
            )

            next_nodes = sorted(
                outgoing[current],
                key=lambda component_id: (
                    records_by_id[
                        component_id
                    ].order,
                    component_id,
                ),
            )

            for target in next_nodes:
                indegree[target] -= 1

                if indegree[target] == 0:
                    ready.append(
                        target
                    )

            ready.sort(
                key=lambda component_id: (
                    records_by_id[
                        component_id
                    ].order,
                    component_id,
                )
            )

        if len(
            ordered_ids
        ) != len(
            component_ids
        ):
            raise LogicCycleError(
                "Logic dependency graph contains a cycle."
            )

        return tuple(
            self._records[
                component_id
            ].component
            for component_id
            in ordered_ids
        )

    # ========================================================================
    # RESULT ADAPTATION
    # ========================================================================

    @staticmethod
    def _logic_result_from_control_result(
        component: LogicControlComponent,
        control_result: Any,
        time: float,
    ) -> LogicControlResult:
        """
        Recover the LogicControlResult contract from the common
        ControlResult adapter.

        LogicControlComponent.evaluate() stores authoritative Logic
        state/events in ControlResult.diagnostics.
        """

        diagnostics = dict(
            getattr(
                control_result,
                "diagnostics",
                {},
            )
            or {}
        )

        if "logic_state" not in diagnostics:
            raise LogicEvaluationError(
                f"'{component.component_id}' "
                "did not provide logic_state "
                "in its ControlResult diagnostics."
            )

        state = dict(
            diagnostics[
                "logic_state"
            ]
        )

        raw_events = diagnostics.get(
            "logic_events",
            (),
        )

        events = tuple(
            raw_events
        )

        for event in events:
            if not isinstance(
                event,
                LogicEvent,
            ):
                raise LogicEvaluationError(
                    f"'{component.component_id}' "
                    "returned an invalid LogicEvent."
                )

        return LogicControlResult(
            outputs=dict(
                control_result.outputs
            ),
            state=state,
            time=float(
                getattr(
                    control_result,
                    "time",
                    time,
                )
            ),
            events=events,
            diagnostics={
                key: value
                for key, value
                in diagnostics.items()
                if key
                not in {
                    "logic_state",
                    "logic_events",
                }
            },
        )

    # ========================================================================
    # GRAPH VALIDATION
    # ========================================================================

    def _validate_all_graph_contracts(
        self,
    ) -> None:
        self._validate_dependencies()

        for connection in self._connections:
            self._validate_connection_endpoints(
                connection
            )

    def _validate_dependencies(
        self,
    ) -> None:
        component_ids = set(
            self._records
        )

        for dependency in self._dependencies:
            if (
                dependency.source_component
                not in component_ids
            ):
                raise UnknownLogicComponentError(
                    f"Unknown dependency source "
                    f"'{dependency.source_component}'."
                )

            if (
                dependency.target_component
                not in component_ids
            ):
                raise UnknownLogicComponentError(
                    f"Unknown dependency target "
                    f"'{dependency.target_component}'."
                )

        self._topological_ids()

    def _validate_connection_endpoints(
        self,
        connection: LogicConnection,
    ) -> None:
        source = self.get(
            connection.source_component
        )

        target = self.get(
            connection.target_component
        )

        if (
            connection.source_output
            not in source.output_names
        ):
            raise LogicConnectionError(
                f"Unknown source output "
                f"'{connection.source_component}."
                f"{connection.source_output}'."
            )

        if (
            connection.target_input
            not in target.input_names
        ):
            raise LogicConnectionError(
                f"Unknown target input "
                f"'{connection.target_component}."
                f"{connection.target_input}'."
            )

        source_signal = next(
            signal
            for signal
            in source.output_definition()
            if signal.name
            == connection.source_output
        )

        target_signal = next(
            signal
            for signal
            in target.input_definition()
            if signal.name
            == connection.target_input
        )

        if not _compatible_signal_types(
            source_signal.value_type,
            target_signal.value_type,
        ):
            raise LogicConnectionError(
                f"Incompatible connection "
                f"'{connection.source_component}."
                f"{connection.source_output}' -> "
                f"'{connection.target_component}."
                f"{connection.target_input}': "
                f"{source_signal.value_type.__name__} "
                f"cannot feed "
                f"{target_signal.value_type.__name__}."
            )

        for existing in self._connections:
            if existing == connection:
                continue

            if (
                existing.target_component
                == connection.target_component
                and existing.target_input
                == connection.target_input
            ):
                raise DuplicateLogicConnectionError(
                    f"Target input "
                    f"'{connection.target_component}."
                    f"{connection.target_input}' "
                    "already has a source."
                )

    def _rebuild_connection_dependencies(
        self,
    ) -> None:
        """
        Rebuild only the dependency edges automatically generated by
        logical connections.

        Explicit dependencies are retained.
        """

        connection_edges = {
            (
                connection.source_component,
                connection.target_component,
            )
            for connection
            in self._connections
        }

        explicit = [
            dependency
            for dependency
            in self._dependencies
            if (
                dependency.source_component,
                dependency.target_component,
            )
            not in {
                (
                    connection.source_component,
                    connection.target_component,
                )
                for connection
                in self._connections
            }
        ]

        self._dependencies = explicit

        for source, target in sorted(
            connection_edges
        ):
            self._dependencies.append(
                LogicDependency(
                    source_component=source,
                    target_component=target,
                )
            )

    def _topological_ids(
        self,
    ) -> tuple[str, ...]:
        """Validate dependency acyclicity."""

        component_ids = set(
            self._records
        )

        indegree = {
            component_id: 0
            for component_id
            in component_ids
        }

        outgoing = {
            component_id: set()
            for component_id
            in component_ids
        }

        for dependency in self._dependencies:
            source = (
                dependency.source_component
            )
            target = (
                dependency.target_component
            )

            if target not in outgoing[source]:
                outgoing[source].add(
                    target
                )
                indegree[target] += 1

        ready = sorted(
            (
                component_id
                for component_id, degree
                in indegree.items()
                if degree == 0
            ),
            key=lambda component_id: (
                self._records[
                    component_id
                ].order,
                component_id,
            ),
        )

        result: list[str] = []

        while ready:
            current = ready.pop(0)

            result.append(
                current
            )

            for target in sorted(
                outgoing[current]
            ):
                indegree[target] -= 1

                if indegree[target] == 0:
                    ready.append(
                        target
                    )

            ready.sort(
                key=lambda component_id: (
                    self._records[
                        component_id
                    ].order,
                    component_id,
                )
            )

        if len(result) != len(
            component_ids
        ):
            raise LogicCycleError(
                "Logic dependency graph contains a cycle."
            )

        return tuple(
            result
        )

    # ========================================================================
    # SNAPSHOTS
    # ========================================================================

    def signals(
        self,
    ) -> Mapping[
        str,
        Mapping[str, Any],
    ]:
        """Return the latest output snapshot."""

        return self._signal_snapshot()

    def _signal_snapshot(
        self,
    ) -> dict[
        str,
        dict[str, Any],
    ]:
        return {
            component_id: dict(
                outputs
            )
            for component_id, outputs
            in self._signals.items()
        }

    # ========================================================================
    # EXTERNAL INPUTS
    # ========================================================================

    def _normalize_external_inputs(
        self,
        external_inputs: Mapping[
            str,
            Mapping[str, Any],
        ] | None,
    ) -> dict[
        str,
        dict[str, Any],
    ]:
        if external_inputs is None:
            return {}

        result: dict[
            str,
            dict[str, Any],
        ] = {}

        for component_id, inputs in (
            external_inputs.items()
        ):
            component_id = str(
                component_id
            ).strip()

            self._validate_component_exists(
                component_id
            )

            if inputs is None:
                raise LogicSignalError(
                    f"External inputs for "
                    f"'{component_id}' cannot be None."
                )

            result[
                component_id
            ] = dict(
                inputs
            )

        return result

    # ========================================================================
    # VALIDATION HELPERS
    # ========================================================================

    def _validate_component_exists(
        self,
        component_id: str,
    ) -> None:
        component_id = str(
            component_id
        ).strip()

        if component_id not in self._records:
            raise UnknownLogicComponentError(
                f"Unknown logic component "
                f"'{component_id}'."
            )


# ============================================================================
# HELPERS
# ============================================================================


def _finite_float(
    value: float,
    name: str,
) -> float:
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise LogicEngineConfigurationError(
            f"{name} must be numeric."
        ) from exc

    if not math.isfinite(result):
        raise LogicEngineConfigurationError(
            f"{name} must be finite."
        )

    return result


def _compatible_signal_types(
    source_type: type,
    target_type: type,
) -> bool:
    """
    Validate domain-level signal compatibility.

    Boolean logic must remain Boolean.

    Numeric signals may feed numeric inputs.

    No implicit Boolean/numeric conversion is performed.
    """

    if source_type is bool:
        return target_type is bool

    if target_type is bool:
        return False

    if source_type in (
        int,
        float,
    ) and target_type in (
        int,
        float,
    ):
        return True

    return source_type is target_type


__all__ = [
    "LogicEngine",
    "LogicEvaluationMode",
    "LogicDependency",
    "LogicConnection",
    "LogicComponentRecord",
    "LogicComponentEvaluation",
    "LogicEngineResult",
    "LogicEngineError",
    "LogicEngineConfigurationError",
    "DuplicateLogicComponentError",
    "UnknownLogicComponentError",
    "LogicDependencyError",
    "LogicCycleError",
    "LogicConnectionError",
    "DuplicateLogicConnectionError",
    "LogicEvaluationError",
    "LogicSignalError",
    "LogicStateUpdateError",
]
