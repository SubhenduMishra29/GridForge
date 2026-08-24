"""
GridForge V2 - Control Controller Contract
===========================================

Author:
    Subhendu Mishra

File:
    core/control/controller.py

Purpose
-------
Defines the headless Control-domain orchestration contract.

ControlController composes and evaluates ControlComponent instances.

The controller supports both branches of the Control architecture:

    Dynamic Control
        AVR, Governor, PSS, inverter controllers, plant controllers, etc.

    Logic Control
        contacts, coils, gates, timers, latches, interlocks, sequences, etc.

Architectural Boundary
----------------------
The controller is an orchestration layer.

It does NOT:

    - perform numerical integration
    - solve DAEs
    - own electrical/network truth
    - mutate core/model objects
    - import concrete plugins
    - contain UI logic
    - contain canvas/layout state

The ownership chain is:

    Application / Simulation
            |
            v
    ControlController
            |
            +--> ControlComponent
            |
            +--> ControlState
            |
            +--> SignalSet
            |
            v
    ControlResult

For Dynamic Control, derivatives are returned to the surrounding
simulation/solver boundary. Integration remains owned by the frozen
core/solver/dynamics layer.

For Logic Control, evaluation produces discrete outputs/state changes
without converting the logic system into a numerical solver.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from typing import Any

from .base import (
    ControlComponent,
    ControlKind,
    ControlResult,
    ControlSignal,
    ControlState,
    Inputs,
    SignalValue,
    State,
)
from .signals import SignalSet


# ============================================================================
# ERRORS
# ============================================================================


class ControllerError(RuntimeError):
    """Base ControlController error."""


class ControllerConfigurationError(ControllerError):
    """Invalid controller configuration."""


class DuplicateComponentError(ControllerConfigurationError):
    """Raised when a component ID is registered twice."""


class UnknownComponentError(ControllerError):
    """Raised when a component cannot be found."""


class ComponentOrderError(ControllerConfigurationError):
    """Raised when component ordering is invalid."""


class ControllerEvaluationError(ControllerError):
    """Raised when component evaluation fails."""


class SignalRoutingError(ControllerError):
    """Raised when component signal routing fails."""


# ============================================================================
# COMPONENT RECORD
# ============================================================================


@dataclass(frozen=True)
class ControlComponentRecord:
    """
    Immutable registration record for one ControlComponent.

    The record contains orchestration metadata only.

    It does not own the component's engineering semantics.
    """

    component: ControlComponent
    order: int

    def __post_init__(self) -> None:
        if not isinstance(
            self.component,
            ControlComponent,
        ):
            raise ControllerConfigurationError(
                "component must implement ControlComponent."
            )

        if self.order < 0:
            raise ControllerConfigurationError(
                "component order cannot be negative."
            )

    @property
    def component_id(self) -> str:
        """Return the component's stable ID."""

        return self.component.component_id

    @property
    def component_type(self) -> str:
        """Return the engineering component type."""

        return self.component.component_type

    @property
    def control_kind(self) -> ControlKind:
        """Return the Control branch."""

        return self.component.control_kind


# ============================================================================
# EVALUATION RECORD
# ============================================================================


@dataclass(frozen=True)
class ComponentEvaluation:
    """
    Result of evaluating one component.

    This is an orchestration record, not a solver result.
    """

    component_id: str
    component_type: str
    control_kind: ControlKind
    result: ControlResult

    @property
    def outputs(self) -> Mapping[str, SignalValue]:
        """Return component outputs."""

        return self.result.outputs

    @property
    def derivatives(
        self,
    ) -> Mapping[str, float] | None:
        """Return derivatives when supplied by a dynamic component."""

        return self.result.derivatives

    @property
    def time(self) -> float:
        """Return evaluation time."""

        return self.result.time


# ============================================================================
# CONTROLLER
# ============================================================================


class ControlController:
    """
    Headless Control-domain composition and orchestration object.

    Components are evaluated in deterministic registration order.

    The controller maintains local ControlState for registered
    components, but it does not integrate that state.

    A component may therefore be:

        Dynamic
            state + derivatives + outputs

        Logic
            optional persistent state + outputs

    Example
    -------

        controller = ControlController()

        controller.register(avr)
        controller.register(pss)
        controller.register(governor)

        result = controller.evaluate(
            time=0.0,
            inputs={
                "avr": {
                    "Vt": 1.02,
                    "Vref": 1.00,
                },
                ...
            },
        )
    """

    def __init__(
        self,
        components: Iterable[ControlComponent] | None = None,
    ) -> None:
        self._records: dict[
            str,
            ControlComponentRecord,
        ] = {}

        self._states: dict[
            str,
            Mapping[str, SignalValue],
        ] = {}

        self._order_counter = 0

        if components is not None:
            for component in components:
                self.register(component)

    # ========================================================================
    # COMPONENT REGISTRATION
    # ========================================================================

    def register(
        self,
        component: ControlComponent,
        *,
        order: int | None = None,
        initial_state: Mapping[str, SignalValue] | None = None,
    ) -> None:
        """
        Register one ControlComponent.

        Parameters
        ----------
        component:
            Component implementing the ControlComponent contract.

        order:
            Optional explicit deterministic execution order.

        initial_state:
            Optional validated local initial state.

        Raises
        ------
        DuplicateComponentError
            If the component ID is already registered.
        """

        if not isinstance(
            component,
            ControlComponent,
        ):
            raise ControllerConfigurationError(
                "Only ControlComponent instances can be registered."
            )

        component_id = str(
            component.component_id
        ).strip()

        if not component_id:
            raise ControllerConfigurationError(
                "Component ID cannot be empty."
            )

        if component_id in self._records:
            raise DuplicateComponentError(
                f"Component '{component_id}' "
                "is already registered."
            )

        if order is None:
            order = self._order_counter

        order = int(order)

        if order < 0:
            raise ComponentOrderError(
                "Component order cannot be negative."
            )

        if any(
            record.order == order
            for record in self._records.values()
        ):
            raise ComponentOrderError(
                f"Component order '{order}' is already occupied."
            )

        state = self._build_initial_state(
            component,
            initial_state,
        )

        self._records[
            component_id
        ] = ControlComponentRecord(
            component=component,
            order=order,
        )

        self._states[
            component_id
        ] = state

        self._order_counter = max(
            self._order_counter,
            order + 1,
        )

    def unregister(
        self,
        component_id: str,
    ) -> ControlComponent:
        """
        Remove and return a registered component.

        The controller does not destroy external references to the
        component.
        """

        component_id = str(
            component_id
        )

        record = self._records.pop(
            component_id,
            None,
        )

        if record is None:
            raise UnknownComponentError(
                f"Unknown component '{component_id}'."
            )

        self._states.pop(
            component_id,
            None,
        )

        return record.component

    def clear(self) -> None:
        """
        Remove all registered components and local states.
        """

        self._records.clear()
        self._states.clear()
        self._order_counter = 0

    # ========================================================================
    # COMPONENT ACCESS
    # ========================================================================

    def contains(
        self,
        component_id: str,
    ) -> bool:
        """Return True when the component is registered."""

        return str(component_id) in self._records

    def get(
        self,
        component_id: str,
    ) -> ControlComponent:
        """Return a registered component."""

        component_id = str(
            component_id
        )

        try:
            return self._records[
                component_id
            ].component
        except KeyError as exc:
            raise UnknownComponentError(
                f"Unknown component '{component_id}'."
            ) from exc

    def record(
        self,
        component_id: str,
    ) -> ControlComponentRecord:
        """Return a component registration record."""

        component_id = str(
            component_id
        )

        try:
            return self._records[
                component_id
            ]
        except KeyError as exc:
            raise UnknownComponentError(
                f"Unknown component '{component_id}'."
            ) from exc

    def components(
        self,
    ) -> tuple[ControlComponent, ...]:
        """
        Return components in deterministic execution order.
        """

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
    ) -> tuple[ControlComponentRecord, ...]:
        """
        Return registration records in deterministic order.
        """

        return tuple(
            sorted(
                self._records.values(),
                key=lambda record: (
                    record.order,
                    record.component_id,
                ),
            )
        )

    def __iter__(self) -> Iterator[ControlComponent]:
        return iter(
            self.components()
        )

    def __len__(self) -> int:
        return len(
            self._records
        )

    # ========================================================================
    # STATE MANAGEMENT
    # ========================================================================

    def state(
        self,
        component_id: str,
    ) -> Mapping[str, SignalValue]:
        """
        Return a detached local state mapping.
        """

        component_id = str(
            component_id
        )

        if component_id not in self._states:
            raise UnknownComponentError(
                f"Unknown component '{component_id}'."
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
        Mapping[str, SignalValue],
    ]:
        """
        Return detached local states for all components.
        """

        return {
            component_id: dict(state)
            for component_id, state
            in self._states.items()
        }

    def set_state(
        self,
        component_id: str,
        state: Mapping[str, SignalValue],
    ) -> None:
        """
        Replace the local state of one registered component.

        This does not integrate the state.
        """

        component = self.get(
            component_id
        )

        normalized = component.validate_state(
            state
        )

        self._states[
            str(component_id)
        ] = normalized

    def reset(
        self,
        *,
        component_id: str | None = None,
        inputs: Mapping[
            str,
            Inputs,
        ] | None = None,
    ) -> Mapping[
        str,
        Mapping[str, SignalValue],
    ]:
        """
        Reset all components or one component.

        ``inputs`` may contain component-specific initialisation inputs.

        Returns
        -------
        Mapping
            Detached state mapping after reset.
        """

        if component_id is not None:
            component_id = str(
                component_id
            )

            component = self.get(
                component_id
            )

            component_inputs = dict(
                (inputs or {}).get(
                    component_id,
                    {},
                )
            )

            self._states[
                component_id
            ] = self._build_initial_state(
                component,
                None,
                inputs=component_inputs,
            )

            return {
                component_id: dict(
                    self._states[
                        component_id
                    ]
                )
            }

        for record in self.records():
            component_inputs = dict(
                (inputs or {}).get(
                    record.component_id,
                    {},
                )
            )

            self._states[
                record.component_id
            ] = self._build_initial_state(
                record.component,
                None,
                inputs=component_inputs,
            )

        return self.states()

    # ========================================================================
    # EVALUATION
    # ========================================================================

    def evaluate(
        self,
        *,
        time: float,
        inputs: Mapping[
            str,
            Inputs | SignalSet,
        ] | None = None,
        update_state: bool = False,
    ) -> Mapping[
        str,
        ComponentEvaluation,
    ]:
        """
        Evaluate every registered Control component.

        Parameters
        ----------
        time:
            Explicit evaluation time.

        inputs:
            Mapping:

                component_id -> input mapping

            or:

                component_id -> SignalSet

        update_state:
            When True, a component result may supply state values through
            the optional ``state`` entry in diagnostics.

            This is intentionally conservative. Numerical integration
            must never occur here.

        Returns
        -------
        Mapping[str, ComponentEvaluation]
            Deterministically ordered component evaluations.

        Notes
        -----
        Components are evaluated independently using the states currently
        held by this controller.

        Cross-component routing should be resolved by the surrounding
        application/simulation orchestration layer rather than by making
        this class aware of electrical topology.
        """

        normalized_time = float(
            time
        )

        if not _is_finite(
            normalized_time
        ):
            raise ControllerEvaluationError(
                "Evaluation time must be finite."
            )

        input_map = inputs or {}

        results: dict[
            str,
            ComponentEvaluation,
        ] = {}

        for record in self.records():
            component = record.component
            component_id = record.component_id

            raw_inputs = input_map.get(
                component_id,
                {},
            )

            if isinstance(
                raw_inputs,
                SignalSet,
            ):
                component_inputs = raw_inputs.to_dict()
            else:
                component_inputs = dict(
                    raw_inputs
                )

            state = self.state(
                component_id
            )

            try:
                result = component.evaluate(
                    state=state,
                    inputs=component_inputs,
                    time=normalized_time,
                )
            except Exception as exc:
                raise ControllerEvaluationError(
                    f"Evaluation failed for "
                    f"component '{component_id}'."
                ) from exc

            if not isinstance(
                result,
                ControlResult,
            ):
                raise ControllerEvaluationError(
                    f"Component '{component_id}' "
                    "returned an invalid ControlResult."
                )

            evaluation = ComponentEvaluation(
                component_id=component_id,
                component_type=component.component_type,
                control_kind=component.control_kind,
                result=result,
            )

            results[
                component_id
            ] = evaluation

            if update_state:
                self._apply_non_integrating_state_update(
                    component_id,
                    result,
                )

        return results

    def evaluate_component(
        self,
        component_id: str,
        *,
        time: float,
        inputs: Inputs | SignalSet | None = None,
    ) -> ComponentEvaluation:
        """
        Evaluate one registered component.
        """

        component = self.get(
            component_id
        )

        if isinstance(
            inputs,
            SignalSet,
        ):
            component_inputs = inputs.to_dict()
        else:
            component_inputs = dict(
                inputs or {}
            )

        state = self.state(
            component_id
        )

        try:
            result = component.evaluate(
                state=state,
                inputs=component_inputs,
                time=float(time),
            )
        except Exception as exc:
            raise ControllerEvaluationError(
                f"Evaluation failed for "
                f"component '{component_id}'."
            ) from exc

        if not isinstance(
            result,
            ControlResult,
        ):
            raise ControllerEvaluationError(
                f"Component '{component_id}' "
                "returned an invalid ControlResult."
            )

        return ComponentEvaluation(
            component_id=component.component_id,
            component_type=component.component_type,
            control_kind=component.control_kind,
            result=result,
        )

    # ========================================================================
    # BRANCH FILTERING
    # ========================================================================

    def dynamic_components(
        self,
    ) -> tuple[ControlComponent, ...]:
        """
        Return registered Dynamic Control components.
        """

        return tuple(
            component
            for component in self.components()
            if component.control_kind
            is ControlKind.DYNAMIC
        )

    def logic_components(
        self,
    ) -> tuple[ControlComponent, ...]:
        """
        Return registered Logic Control components.
        """

        return tuple(
            component
            for component in self.components()
            if component.control_kind
            is ControlKind.LOGIC
        )

    # ========================================================================
    # SIGNAL COLLECTION
    # ========================================================================

    def output_signals(
        self,
        evaluations: Mapping[
            str,
            ComponentEvaluation,
        ],
    ) -> Mapping[
        str,
        Mapping[str, SignalValue],
    ]:
        """
        Collect component outputs into a detached mapping.

        No cross-component mutation occurs.
        """

        return {
            component_id: dict(
                evaluation.outputs
            )
            for component_id, evaluation
            in evaluations.items()
        }

    def derivatives(
        self,
        evaluations: Mapping[
            str,
            ComponentEvaluation,
        ],
    ) -> Mapping[
        str,
        Mapping[str, float],
    ]:
        """
        Collect derivatives produced by Dynamic Control components.

        Logic components normally contribute no derivatives.

        This method does NOT integrate derivatives.
        """

        result: dict[
            str,
            Mapping[str, float],
        ] = {}

        for component_id, evaluation in (
            evaluations.items()
        ):
            derivatives = (
                evaluation.derivatives
            )

            if derivatives is None:
                continue

            result[
                component_id
            ] = dict(
                derivatives
            )

        return result

    # ========================================================================
    # DIAGNOSTICS
    # ========================================================================

    def diagnostics(
        self,
    ) -> Mapping[str, Any]:
        """
        Return serializable controller diagnostics.
        """

        records = self.records()

        return {
            "component_count": len(
                records
            ),
            "dynamic_component_count": len(
                self.dynamic_components()
            ),
            "logic_component_count": len(
                self.logic_components()
            ),
            "components": [
                {
                    "component_id":
                        record.component_id,
                    "component_type":
                        record.component_type,
                    "control_kind":
                        record.control_kind.value,
                    "order":
                        record.order,
                }
                for record in records
            ],
        }

    def summary(
        self,
    ) -> Mapping[str, Any]:
        """
        Return a serializable controller summary.
        """

        return self.diagnostics()

    # ========================================================================
    # INTERNAL HELPERS
    # ========================================================================

    @staticmethod
    def _build_initial_state(
        component: ControlComponent,
        supplied: Mapping[
            str,
            SignalValue,
        ] | None,
        *,
        inputs: Inputs | None = None,
    ) -> Mapping[
        str,
        SignalValue,
    ]:
        """
        Build and validate component initial state.
        """

        if supplied is not None:
            return component.validate_state(
                supplied
            )

        try:
            initial = component.initial_state(
                inputs or {}
            )
        except Exception as exc:
            raise ControllerConfigurationError(
                f"Unable to create initial state "
                f"for component '{component.component_id}'."
            ) from exc

        return component.validate_state(
            initial
        )

    def _apply_non_integrating_state_update(
        self,
        component_id: str,
        result: ControlResult,
    ) -> None:
        """
        Apply an explicitly supplied state update without integration.

        The common ControlResult currently does not expose a dedicated
        state-update field. Therefore this method intentionally does
        nothing.

        Dynamic numerical state updates belong to the solver boundary.

        Future Logic Control contracts may introduce explicit discrete
        state transitions without changing this numerical boundary.
        """

        # Intentionally no-op.
        #
        # This method exists to make the ownership boundary explicit:
        #
        #   ControlController != numerical integrator
        #
        # It must not infer new state from derivatives.
        return


# ============================================================================
# PUBLIC EXPORTS
# ============================================================================

__all__ = [
    "ControllerError",
    "ControllerConfigurationError",
    "DuplicateComponentError",
    "UnknownComponentError",
    "ComponentOrderError",
    "ControllerEvaluationError",
    "SignalRoutingError",
    "ControlComponentRecord",
    "ComponentEvaluation",
    "ControlController",
]
