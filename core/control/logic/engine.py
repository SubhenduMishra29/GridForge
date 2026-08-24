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

The engine evaluates a collection of LogicControlComponent instances,
propagates discrete signals, manages discrete state, detects dependency
cycles, and collects logic events.

Architectural Boundary
----------------------
    UI Logic Layout / Editing Canvas
                    |
                    | commands / DTOs
                    v
             Application Layer
                    |
                    v
               LogicEngine
                    |
             Logic Components
                    |
                    v
             Control Domain

This module does NOT:

    - provide a UI
    - know about graphics/layout
    - own canvas connections
    - mutate core/model
    - perform numerical integration
    - solve DAEs
    - import concrete plugins
    - contain AVR/PSS/Governor behavior

The engine is concerned only with discrete Logic Control execution.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any

from .base import (
    LogicControlComponent,
    LogicControlError,
    LogicControlResult,
    LogicEvent,
    LogicEventType,
)


# ============================================================================
# ERRORS
# ============================================================================


class LogicEngineError(LogicControlError):
    """Base LogicEngine error."""


class LogicEngineConfigurationError(
    LogicEngineError,
):
    """Invalid engine configuration."""


class DuplicateLogicComponentError(
    LogicEngineConfigurationError,
):
    """A component with the same ID is already registered."""


class UnknownLogicComponentError(
    LogicEngineError,
):
    """Requested logic component does not exist."""


class LogicDependencyError(
    LogicEngineConfigurationError,
):
    """Invalid logic dependency."""


class LogicCycleError(
    LogicDependencyError,
):
    """A combinational dependency cycle was detected."""


class LogicEvaluationError(
    LogicEngineError,
):
    """Logic evaluation failed."""


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
    Logic evaluation modes.

    SINGLE_PASS
        Evaluate the configured dependency order once.

    PROPAGATE
        Re-evaluate dependency levels until the network reaches a stable
        discrete state, subject to the configured iteration limit.
    """

    SINGLE_PASS = "single_pass"
    PROPAGATE = "propagate"


# ============================================================================
# DATA CONTRACTS
# ============================================================================


@dataclass(frozen=True)
class LogicDependency:
    """
    Explicit dependency declaration.

    ``source_component`` produces the signal consumed by
    ``target_component``.

    The engine treats dependencies as execution constraints. The actual
    engineering meaning of the signal remains owned by the components.
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
class LogicComponentRecord:
    """
    Immutable registration record.
    """

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
    """
    Immutable evaluation record for one logic component.
    """

    component_id: str
    result: LogicControlResult

    @property
    def outputs(self) -> Mapping[str, Any]:
        return self.result.outputs

    @property
    def state(self) -> Mapping[str, Any]:
        return self.result.state

    @property
    def events(self) -> tuple[LogicEvent, ...]:
        return tuple(
            self.result.events
        )


@dataclass(frozen=True)
class LogicEngineResult:
    """
    Complete result of one LogicEngine evaluation.
    """

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
    events: tuple[LogicEvent, ...]
    stable: bool
    iterations: int
    diagnostics: Mapping[str, Any] = field(
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
# LOGIC ENGINE
# ============================================================================


class LogicEngine:
    """
    Headless discrete Logic Control execution engine.

    The engine owns:

        - component registration
        - explicit dependency metadata
        - local discrete state
        - signal snapshots
        - deterministic execution order

    The engine does not own:

        - graphical topology
        - SLD/logic canvas layout
        - electrical model state
        - numerical solver state

    Dependencies must be explicitly declared. The engine does not infer
    graph topology from arbitrary component internals.
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
                f"Invalid evaluation mode: {mode!r}"
            ) from exc

        if int(max_iterations) <= 0:
            raise LogicEngineConfigurationError(
                "max_iterations must be greater than zero."
            )

        self._max_iterations = int(
            max_iterations
        )

        self._records: dict[
            str,
            LogicComponentRecord,
        ] = {}

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
    # CONFIGURATION
    # ========================================================================

    @property
    def mode(self) -> LogicEvaluationMode:
        """Return the current evaluation mode."""

        return self._mode

    @property
    def max_iterations(self) -> int:
        """Return the propagation iteration limit."""

        return self._max_iterations

    def set_mode(
        self,
        mode: LogicEvaluationMode,
    ) -> None:
        """Change evaluation mode."""

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
                f"Invalid evaluation mode: {mode!r}"
            ) from exc

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
        """
        Register a logic component.

        Registration does not imply any graphical placement.
        """

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

        order = int(
            order
        )

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

        normalized_state = self._validate_state(
            component,
            state,
        )

        self._records[
            component_id
        ] = LogicComponentRecord(
            component=component,
            order=order,
        )

        self._states[
            component_id
        ] = normalized_state

        self._signals.setdefault(
            component_id,
            {},
        )

        self._order_counter = max(
            self._order_counter,
            order + 1,
        )

        self._validate_dependencies()

    def unregister(
        self,
        component_id: str,
    ) -> LogicControlComponent:
        """
        Unregister a component.

        Dependencies referring to the component are also removed.
        """

        component_id = str(
            component_id
        )

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

        self._dependencies = [
            dependency
            for dependency
            in self._dependencies
            if dependency.source_component
            != component_id
            and dependency.target_component
            != component_id
        ]

        return record.component

    def clear(self) -> None:
        """Remove all components, dependencies, state and signals."""

        self._records.clear()
        self._dependencies.clear()
        self._states.clear()
        self._signals.clear()
        self._order_counter = 0

    # ========================================================================
    # ACCESS
    # ========================================================================

    def contains(
        self,
        component_id: str,
    ) -> bool:
        return str(
            component_id
        ) in self._records

    def get(
        self,
        component_id: str,
    ) -> LogicControlComponent:
        component_id = str(
            component_id
        )

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
        """Return components in deterministic order."""

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
        """Return registration records."""

        return tuple(
            sorted(
                self._records.values(),
                key=lambda record: (
                    record.order,
                    record.component_id,
                ),
            )
        )

    def __iter__(self) -> Iterator[
        LogicControlComponent
    ]:
        return iter(
            self.components()
        )

    def __len__(self) -> int:
        return len(
            self._records
        )

    # ========================================================================
    # DEPENDENCIES
    # ========================================================================

    def add_dependency(
        self,
        source_component: str,
        target_component: str,
    ) -> LogicDependency:
        """
        Add an explicit component dependency.

        The source is evaluated before the target.
        """

        dependency = LogicDependency(
            source_component=source_component,
            target_component=target_component,
        )

        if not self.contains(
            dependency.source_component
        ):
            raise UnknownLogicComponentError(
                f"Unknown source component "
                f"'{dependency.source_component}'."
            )

        if not self.contains(
            dependency.target_component
        ):
            raise UnknownLogicComponentError(
                f"Unknown target component "
                f"'{dependency.target_component}'."
            )

        if dependency in self._dependencies:
            return dependency

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
    ) -> None:
        """
        Remove an explicit dependency.
        """

        source = str(
            source_component
        )

        target = str(
            target_component
        )

        self._dependencies = [
            dependency
            for dependency
            in self._dependencies
            if not (
                dependency.source_component == source
                and dependency.target_component == target
            )
        ]

    def dependencies(
        self,
    ) -> tuple[LogicDependency, ...]:
        """Return immutable dependency snapshot."""

        return tuple(
            self._dependencies
        )

    def execution_order(
        self,
    ) -> tuple[
        LogicControlComponent,
        ...,
    ]:
        """
        Return a deterministic topological execution order.

        Explicit dependencies take precedence over registration order.
        Registration order breaks ties.
        """

        self._validate_dependencies()

        component_ids = [
            record.component_id
            for record in self.records()
        ]

        position = {
            component_id: index
            for index, component_id
            in enumerate(
                component_ids
            )
        }

        adjacency: dict[
            str,
            set[str],
        ] = {
            component_id: set()
            for component_id
            in component_ids
        }

        indegree: dict[
            str,
            int,
        ] = {
            component_id: 0
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

            if target not in adjacency:
                raise UnknownLogicComponentError(
                    f"Unknown target component "
                    f"'{target}'."
                )

            if target not in adjacency[source]:
                adjacency[source].add(
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
            key=position.__getitem__,
        )

        result: list[str] = []

        while ready:
            current = ready.pop(
                0
            )

            result.append(
                current
            )

            for target in sorted(
                adjacency[current],
                key=position.__getitem__,
            ):
                indegree[target] -= 1

                if indegree[target] == 0:
                    ready.append(
                        target
                    )

            ready.sort(
                key=position.__getitem__
            )

        if len(result) != len(
            component_ids
        ):
            raise LogicCycleError(
                "Logic dependency graph contains "
                "a cycle."
            )

        return tuple(
            self.get(
                component_id
            )
            for component_id in result
        )

    # ========================================================================
    # STATE
    # ========================================================================

    def state(
        self,
        component_id: str,
    ) -> Mapping[str, Any]:
        component_id = str(
            component_id
        )

        if component_id not in self._states:
            raise UnknownLogicComponentError(
                f"Unknown logic component "
                f"'{component_id}'."
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
        component = self.get(
            component_id
        )

        self._states[
            str(component_id)
        ] = self._validate_state(
            component,
            dict(state),
        )

    def reset(
        self,
        *,
        component_id: str | None = None,
    ) -> Mapping[
        str,
        Mapping[str, Any],
    ]:
        """
        Reset one or all logic components.
        """

        if component_id is not None:
            component_id = str(
                component_id
            )

            component = self.get(
                component_id
            )

            self._states[
                component_id
            ] = self._validate_state(
                component,
                dict(
                    component.reset_logic()
                ),
            )

            return {
                component_id: dict(
                    self._states[
                        component_id
                    ]
                )
            }

        for component in self.components():
            component_id = str(
                component.component_id
            )

            self._states[
                component_id
            ] = self._validate_state(
                component,
                dict(
                    component.reset_logic()
                ),
            )

        self._signals = {
            component_id: {}
            for component_id
            in self._records
        }

        return self.states()

    # ========================================================================
    # SIGNAL SNAPSHOT
    # ========================================================================

    def signals(
        self,
    ) -> Mapping[
        str,
        Mapping[str, Any],
    ]:
        """
        Return detached component output signals.
        """

        return {
            component_id: dict(
                values
            )
            for component_id, values
            in self._signals.items()
        }

    def set_external_signals(
        self,
        signals: Mapping[
            str,
            Mapping[str, Any],
        ],
    ) -> None:
        """
        Set external input snapshots.

        This does not mutate component state.
        """

        self._signals = {
            str(component_id): dict(
                values
            )
            for component_id, values
            in signals.items()
        }

    # ========================================================================
    # EVALUATION
    # ========================================================================

    def evaluate(
        self,
        *,
        time: float,
        inputs: Mapping[
            str,
            Mapping[str, Any],
        ] | None = None,
        mode: LogicEvaluationMode | None = None,
        commit_state: bool = True,
    ) -> LogicEngineResult:
        """
        Evaluate the complete logic network.

        ``inputs`` contains explicit external inputs per component.

        Component-to-component propagation uses the current output
        snapshot. The engine deliberately does not invent a signal
        mapping between arbitrary output and input names; explicit
        dependencies establish ordering, while external/application
        orchestration supplies signal mappings.

        In PROPAGATE mode the network is evaluated repeatedly until the
        output/state snapshot stabilizes or ``max_iterations`` is reached.
        """

        time = _finite_float(
            time,
            "time",
        )

        evaluation_mode = (
            self._mode
            if mode is None
            else (
                mode
                if isinstance(
                    mode,
                    LogicEvaluationMode,
                )
                else LogicEvaluationMode(
                    mode
                )
            )
        )

        external_inputs = {
            str(component_id): dict(
                values
            )
            for component_id, values
            in (inputs or {}).items()
        }

        if evaluation_mode is (
            LogicEvaluationMode.SINGLE_PASS
        ):
            return self._evaluate_once(
                time=time,
                inputs=external_inputs,
                commit_state=commit_state,
            )

        return self._evaluate_until_stable(
            time=time,
            inputs=external_inputs,
            commit_state=commit_state,
        )

    def _evaluate_once(
        self,
        *,
        time: float,
        inputs: Mapping[
            str,
            Mapping[str, Any],
        ],
        commit_state: bool,
    ) -> LogicEngineResult:
        evaluations: dict[
            str,
            LogicComponentEvaluation,
        ] = {}

        next_states = {
            component_id: dict(
                state
            )
            for component_id, state
            in self._states.items()
        }

        next_signals = {
            component_id: dict(
                values
            )
            for component_id, values
            in self._signals.items()
        }

        events: list[
            LogicEvent
        ] = []

        for component in self.execution_order():
            component_id = str(
                component.component_id
            )

            component_inputs = dict(
                inputs.get(
                    component_id,
                    {},
                )
            )

            # Outputs from dependencies are exposed under a dedicated
            # namespace. This avoids accidental collision with external
            # inputs and keeps routing deterministic.
            dependency_inputs = (
                self._dependency_signals(
                    component_id,
                    next_signals,
                )
            )

            component_inputs = self._merge_inputs(
                dependency_inputs,
                component_inputs,
            )

            current_state = dict(
                next_states[
                    component_id
                ]
            )

            try:
                result = component.evaluate_logic(
                    current_state,
                    component_inputs,
                    time,
                )
            except Exception as exc:
                raise LogicEvaluationError(
                    f"Evaluation failed for "
                    f"logic component "
                    f"'{component_id}'."
                ) from exc

            if not isinstance(
                result,
                LogicControlResult,
            ):
                raise LogicEvaluationError(
                    f"Logic component "
                    f"'{component_id}' returned "
                    "an invalid LogicControlResult."
                )

            try:
                component.validate_logic_result(
                    result
                )
            except Exception as exc:
                raise LogicEvaluationError(
                    f"Invalid result from "
                    f"logic component "
                    f"'{component_id}'."
                ) from exc

            evaluations[
                component_id
            ] = LogicComponentEvaluation(
                component_id=component_id,
                result=result,
            )

            next_states[
                component_id
            ] = dict(
                result.state
            )

            next_signals[
                component_id
            ] = dict(
                result.outputs
            )

            events.extend(
                result.events
            )

        if commit_state:
            self._states = {
                component_id: dict(
                    state
                )
                for component_id, state
                in next_states.items()
            }

            self._signals = {
                component_id: dict(
                    values
                )
                for component_id, values
                in next_signals.items()
            }

        return LogicEngineResult(
            time=time,
            evaluations=evaluations,
            signals=next_signals,
            states=next_states,
            events=tuple(events),
            stable=True,
            iterations=1,
            diagnostics={
                "mode":
                    LogicEvaluationMode.SINGLE_PASS.value,
                "component_count":
                    len(evaluations),
            },
        )

    def _evaluate_until_stable(
        self,
        *,
        time: float,
        inputs: Mapping[
            str,
            Mapping[str, Any],
        ],
        commit_state: bool,
    ) -> LogicEngineResult:
        previous_signals = {
            component_id: dict(
                values
            )
            for component_id, values
            in self._signals.items()
        }

        previous_states = {
            component_id: dict(
                state
            )
            for component_id, state
            in self._states.items()
        }

        final_result: LogicEngineResult | None = None

        for iteration in range(
            1,
            self._max_iterations + 1,
        ):
            result = self._evaluate_once(
                time=time,
                inputs=inputs,
                commit_state=False,
            )

            signals_changed = (
                result.signals
                != previous_signals
            )

            states_changed = (
                result.states
                != previous_states
            )

            final_result = LogicEngineResult(
                time=result.time,
                evaluations=result.evaluations,
                signals=result.signals,
                states=result.states,
                events=result.events,
                stable=not (
                    signals_changed
                    or states_changed
                ),
                iterations=iteration,
                diagnostics={
                    **dict(
                        result.diagnostics
                    ),
                    "mode":
                        LogicEvaluationMode.PROPAGATE.value,
                    "stable":
                        not (
                            signals_changed
                            or states_changed
                        ),
                },
            )

            if not (
                signals_changed
                or states_changed
            ):
                if commit_state:
                    self._states = {
                        component_id: dict(
                            state
                        )
                        for component_id, state
                        in result.states.items()
                    }

                    self._signals = {
                        component_id: dict(
                            values
                        )
                        for component_id, values
                        in result.signals.items()
                    }

                return final_result

            previous_signals = {
                component_id: dict(
                    values
                )
                for component_id, values
                in result.signals.items()
            }

            previous_states = {
                component_id: dict(
                    state
                )
                for component_id, state
                in result.states.items()
            }

        raise LogicEvaluationError(
            "Logic network did not reach a stable "
            f"state within {self._max_iterations} "
            "iterations."
        )

    # ========================================================================
    # DEPENDENCY SIGNALS
    # ========================================================================

    def _dependency_signals(
        self,
        target_component: str,
        signals: Mapping[
            str,
            Mapping[str, Any],
        ],
    ) -> dict[str, Any]:
        """
        Collect output snapshots from dependencies.

        Names are namespaced as:

            '<source_component>.<output_name>'

        This avoids assuming that an output name is globally unique.
        """

        result: dict[
            str,
            Any,
        ] = {}

        for dependency in self._dependencies:
            if (
                dependency.target_component
                != target_component
            ):
                continue

            source = dependency.source_component

            for name, value in signals.get(
                source,
                {},
            ).items():
                key = (
                    f"{source}.{name}"
                )

                if key in result:
                    raise LogicSignalError(
                        f"Duplicate routed signal "
                        f"'{key}' for target "
                        f"'{target_component}'."
                    )

                result[key] = value

        return result

    @staticmethod
    def _merge_inputs(
        dependency_inputs: Mapping[
            str,
            Any,
        ],
        external_inputs: Mapping[
            str,
            Any,
        ],
    ) -> dict[str, Any]:
        """
        Merge dependency and explicit external inputs.

        Explicit external inputs take precedence only when the names do
        not collide with dependency namespace keys.
        """

        merged = dict(
            dependency_inputs
        )

        for name, value in external_inputs.items():
            if name in merged:
                raise LogicSignalError(
                    f"Input '{name}' conflicts with "
                    "a dependency-routed signal."
                )

            merged[name] = value

        return merged

    # ========================================================================
    # VALIDATION
    # ========================================================================

    def _validate_dependencies(
        self,
    ) -> None:
        for dependency in self._dependencies:
            if not self.contains(
                dependency.source_component
            ):
                raise UnknownLogicComponentError(
                    f"Unknown dependency source "
                    f"'{dependency.source_component}'."
                )

            if not self.contains(
                dependency.target_component
            ):
                raise UnknownLogicComponentError(
                    f"Unknown dependency target "
                    f"'{dependency.target_component}'."
                )

        self.execution_order()

    @staticmethod
    def _validate_state(
        component: LogicControlComponent,
        state: Mapping[
            str,
            Any,
        ],
    ) -> dict[str, Any]:
        try:
            normalized = component.validate_state(
                state
            )
        except Exception as exc:
            raise LogicStateUpdateError(
                f"Invalid state for logic component "
                f"'{component.component_id}'."
            ) from exc

        return dict(
            normalized
        )

    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================

    def diagnostics(
        self,
    ) -> Mapping[str, Any]:
        """
        Return serializable engine diagnostics.
        """

        return {
            "component_count":
                len(self),
            "dependency_count":
                len(self._dependencies),
            "evaluation_mode":
                self.mode.value,
            "max_iterations":
                self.max_iterations,
            "execution_order": [
                component.component_id
                for component
                in self.execution_order()
            ],
            "components": [
                {
                    "component_id":
                        record.component_id,
                    "component_type":
                        record.component_type,
                    "order":
                        record.order,
                    "state_size":
                        record.component.logic_state_size,
                }
                for record
                in self.records()
            ],
            "dependencies": [
                {
                    "source":
                        dependency.source_component,
                    "target":
                        dependency.target_component,
                }
                for dependency
                in self._dependencies
            ],
        }

    def summary(
        self,
    ) -> Mapping[str, Any]:
        """Return the engine diagnostic summary."""

        return self.diagnostics()


# ============================================================================
# HELPERS
# ============================================================================


def _finite_float(
    value: float,
    name: str,
) -> float:
    try:
        result = float(
            value
        )
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise LogicEngineConfigurationError(
            f"{name} must be numeric."
        ) from exc

    if not math.isfinite(
        result
    ):
        raise LogicEngineConfigurationError(
            f"{name} must be finite."
        )

    return result


# ============================================================================
# PUBLIC EXPORTS
# ============================================================================

__all__ = [
    "LogicEvaluationMode",
    "LogicDependency",
    "LogicComponentRecord",
    "LogicComponentEvaluation",
    "LogicEngineResult",
    "LogicEngine",
    "LogicEngineError",
    "LogicEngineConfigurationError",
    "DuplicateLogicComponentError",
    "UnknownLogicComponentError",
    "LogicDependencyError",
    "LogicCycleError",
    "LogicEvaluationError",
    "LogicSignalError",
    "LogicStateUpdateError",
]
