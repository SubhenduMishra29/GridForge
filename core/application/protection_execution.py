# ============================================================
# File: core/application/protection_execution.py
# GridForge V2 — Protection Application Orchestration
# Author: Subhendu Mishra
# ============================================================

"""Application-owned orchestration for protection output intent."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Iterable

from core.application.command import Command
from core.application.control_dispatch import (
    ControlCommandDispatcher,
    ControlCommandTranslator,
    InvalidApplicationResultError,
)
from core.application.results import ApplicationResult
from core.control.decision import ControlDecision
from core.protection.decision import ProtectionDecision


class StaleProtectionExecutionError(RuntimeError):
    """Active project/configuration provenance changed before command dispatch."""


class ProtectionTargetUnavailableError(ValueError):
    """Explicit action target is absent from the active Core network."""


class StaleProtectionDecisionError(RuntimeError):
    """One decision's dependency token is stale or incomplete; peers may remain valid."""


class PostconditionStatus(str, Enum):
    MATCHED = "matched"
    MISMATCHED = "mismatched"
    UNAVAILABLE_UNSUPPORTED = "unavailable/unsupported"


@dataclass(frozen=True, slots=True)
class ProtectionPostconditionVerification:
    """Typed Core-state postcondition correlated to one dispatched command.

    This records an in-memory Core observation only; it is not physical-device
    acknowledgement and does not cause retries or compensating operations.
    """

    command_id: str
    target_equipment_type: str
    target_equipment_id: str
    action_type: str
    status: PostconditionStatus
    expected_state: str | None = None
    observed_state: str | None = None
    diagnostic: str = ""

    def __post_init__(self) -> None:
        for name in ("command_id", "target_equipment_type", "target_equipment_id", "action_type"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        if not isinstance(self.status, PostconditionStatus):
            object.__setattr__(self, "status", PostconditionStatus(self.status))
        if not isinstance(self.diagnostic, str):
            raise TypeError("diagnostic must be a string.")


@dataclass(frozen=True, slots=True)
class ProtectionActionOutcome:
    """Correlated outcome for one protection decision; feedback is not inferred."""

    protection_decision: ProtectionDecision
    control_decision: ControlDecision | None
    command: Command | None
    application_result: ApplicationResult | None
    status: str
    diagnostic: str = ""
    core_state_observation: str = "unknown/unavailable"
    physical_acknowledgement: str = "unknown/unavailable"
    postcondition_verification: ProtectionPostconditionVerification | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.protection_decision, ProtectionDecision):
            raise TypeError("protection_decision must be a ProtectionDecision.")
        if self.control_decision is not None and not isinstance(self.control_decision, ControlDecision):
            raise TypeError("control_decision must be a ControlDecision or None.")
        if self.command is not None and not isinstance(self.command, Command):
            raise TypeError("command must be a Command or None.")
        if self.application_result is not None and not isinstance(self.application_result, ApplicationResult):
            raise TypeError("application_result must be an ApplicationResult or None.")
        if not isinstance(self.status, str) or not self.status:
            raise ValueError("status must be a non-empty string.")
        if not isinstance(self.diagnostic, str):
            raise TypeError("diagnostic must be a string.")
        if self.postcondition_verification is not None and not isinstance(self.postcondition_verification, ProtectionPostconditionVerification):
            raise TypeError("postcondition_verification must be ProtectionPostconditionVerification or None.")


@dataclass(frozen=True, slots=True)
class ProtectionExecutionResult:
    """Immutable result of one Application-side protection execution."""

    decisions: tuple[ProtectionDecision, ...] = ()
    control_decisions: tuple[ControlDecision, ...] = ()
    commands: tuple[Command, ...] = ()
    application_results: tuple[ApplicationResult, ...] = ()
    diagnostics: tuple[str, ...] = ()
    outcomes: tuple[ProtectionActionOutcome, ...] = ()

    def __post_init__(self) -> None:
        sequence_fields = (
            ("decisions", ProtectionDecision),
            ("control_decisions", ControlDecision),
            ("commands", Command),
            ("application_results", ApplicationResult),
            ("outcomes", ProtectionActionOutcome),
        )
        for name, expected_type in sequence_fields:
            values = getattr(self, name)
            if isinstance(values, (str, bytes)) or not isinstance(values, Iterable):
                raise TypeError(f"{name} must be a sequence of {expected_type.__name__} values.")
            normalized = tuple(values)
            if any(not isinstance(value, expected_type) for value in normalized):
                raise TypeError(f"{name} must contain only {expected_type.__name__} values.")
            object.__setattr__(self, name, normalized)
        diagnostics = self.diagnostics
        if isinstance(diagnostics, (str, bytes)) or not isinstance(diagnostics, Iterable):
            raise TypeError("diagnostics must be a sequence of strings.")
        normalized_diagnostics = tuple(diagnostics)
        if any(not isinstance(value, str) for value in normalized_diagnostics):
            raise TypeError("diagnostics must contain only strings.")
        object.__setattr__(self, "diagnostics", normalized_diagnostics)


class ProtectionExecutionService:
    """Dispatch actionable protection decisions through Control and Application.

    Protection remains an intent producer. The resolver is the explicit
    Application-owned binding from protection identity to a target and action.
    """

    def __init__(
        self,
        dispatcher: ControlCommandDispatcher,
        *,
        action_resolver: Callable[[ProtectionDecision], ControlDecision | None],
        pre_dispatch_guard: Callable[[], None] | None = None,
        decision_guard: Callable[[ProtectionDecision, ControlDecision | None], None] | None = None,
        state_observer: Callable[[ControlDecision, Command, ApplicationResult], ProtectionPostconditionVerification | str] | None = None,
    ) -> None:
        if not isinstance(dispatcher, ControlCommandDispatcher):
            raise TypeError("dispatcher must be a ControlCommandDispatcher.")
        if not callable(action_resolver):
            raise TypeError("action_resolver must be callable.")
        self._dispatcher = dispatcher
        if pre_dispatch_guard is not None and not callable(pre_dispatch_guard):
            raise TypeError("pre_dispatch_guard must be callable or None.")
        self._action_resolver = action_resolver
        self._pre_dispatch_guard = pre_dispatch_guard
        if decision_guard is not None and not callable(decision_guard):
            raise TypeError("decision_guard must be callable or None.")
        self._decision_guard = decision_guard
        if state_observer is not None and not callable(state_observer):
            raise TypeError("state_observer must be callable or None.")
        self._state_observer = state_observer

    @property
    def dispatcher(self) -> ControlCommandDispatcher:
        return self._dispatcher

    def execute(self, decisions: Iterable[ProtectionDecision]) -> ProtectionExecutionResult:
        """Resolve and dispatch decisions with batch-wide and per-element freshness fences."""
        decision_tuple = tuple(decisions)
        for decision in decision_tuple:
            if not isinstance(decision, ProtectionDecision):
                raise TypeError("decisions must contain ProtectionDecision values.")

        control_decisions: list[ControlDecision] = []
        commands: list[Command] = []
        results: list[ApplicationResult] = []
        diagnostics: list[str] = []
        outcomes: list[ProtectionActionOutcome] = []
        dispatched_targets: set[tuple[str, str]] = set()

        def append_batch_rejection(
            start_index: int,
            message: str,
            *,
            current_control_decision: ControlDecision | None = None,
            current_command: Command | None = None,
        ) -> None:
            diagnostics.append(message)
            for pending_index in range(start_index, len(decision_tuple)):
                pending = decision_tuple[pending_index]
                outcomes.append(ProtectionActionOutcome(
                    pending,
                    current_control_decision if pending_index == start_index else None,
                    current_command if pending_index == start_index else None,
                    None,
                    "batch_stale_rejected",
                    message,
                ))

        for index, protection_decision in enumerate(decision_tuple):
            # Batch-wide fences abort the remainder of this execution batch.
            if self._pre_dispatch_guard is not None:
                try:
                    self._pre_dispatch_guard()
                except StaleProtectionExecutionError as exc:
                    append_batch_rejection(
                        index,
                        f"Protection batch aborted before resolution: {exc}",
                    )
                    break

            if not protection_decision.actionable:
                outcomes.append(ProtectionActionOutcome(
                    protection_decision, None, None, None, "not_actionable"
                ))
                continue

            if self._decision_guard is not None:
                try:
                    self._decision_guard(protection_decision, None)
                except StaleProtectionDecisionError as exc:
                    message = (
                        f"Protection decision rejected for '{protection_decision.element_id}' "
                        f"because its dependency token is stale or unavailable: {exc}"
                    )
                    diagnostics.append(message)
                    outcomes.append(ProtectionActionOutcome(
                        protection_decision, None, None, None,
                        "stale_dependency_rejected", message
                    ))
                    continue
                except StaleProtectionExecutionError as exc:
                    append_batch_rejection(
                        index,
                        f"Protection batch aborted because dependency provenance is unclassifiable: {exc}",
                    )
                    break
                except Exception as exc:
                    append_batch_rejection(
                        index,
                        f"Protection batch aborted because the decision guard failed unexpectedly: {type(exc).__name__}: {exc}",
                    )
                    break

            try:
                control_decision = self._action_resolver(protection_decision)
            except ProtectionTargetUnavailableError as exc:
                message = f"Protection target unavailable for '{protection_decision.element_id}': {exc}"
                diagnostics.append(message)
                outcomes.append(ProtectionActionOutcome(
                    protection_decision, None, None, None, "target_unavailable", message
                ))
                continue
            except StaleProtectionExecutionError as exc:
                append_batch_rejection(
                    index,
                    f"Protection batch aborted during action resolution: {exc}",
                )
                break
            except Exception as exc:
                message = (
                    f"Protection action resolution failed for "
                    f"'{protection_decision.element_id}': {exc}"
                )
                diagnostics.append(message)
                outcomes.append(ProtectionActionOutcome(
                    protection_decision, None, None, None, "resolution_failed", message
                ))
                continue

            if control_decision is None:
                message = (
                    f"Protection decision '{protection_decision.element_id}' "
                    "has no configured action target."
                )
                diagnostics.append(message)
                outcomes.append(ProtectionActionOutcome(
                    protection_decision, None, None, None, "target_unavailable", message
                ))
                continue
            if not isinstance(control_decision, ControlDecision):
                raise TypeError("action_resolver must return ControlDecision or None.")

            if self._decision_guard is not None:
                try:
                    self._decision_guard(protection_decision, control_decision)
                except StaleProtectionDecisionError as exc:
                    message = (
                        f"Protection decision rejected after action resolution for "
                        f"'{protection_decision.element_id}': {exc}"
                    )
                    diagnostics.append(message)
                    outcomes.append(ProtectionActionOutcome(
                        protection_decision, control_decision, None, None,
                        "stale_dependency_rejected", message
                    ))
                    continue
                except StaleProtectionExecutionError as exc:
                    append_batch_rejection(
                        index,
                        f"Protection batch aborted after action resolution: {exc}",
                        current_control_decision=control_decision,
                    )
                    break
                except Exception as exc:
                    append_batch_rejection(
                        index,
                        f"Protection batch aborted because the post-resolution decision guard failed unexpectedly: {type(exc).__name__}: {exc}",
                        current_control_decision=control_decision,
                    )
                    break

            target_key = (
                str(control_decision.target_equipment_type).strip().lower(),
                str(control_decision.target_equipment_id).strip(),
            )
            if target_key in dispatched_targets:
                message = (
                    f"Protection action rejected because target "
                    f"'{target_key[0]}:{target_key[1]}' already received an action in this batch."
                )
                diagnostics.append(message)
                outcomes.append(ProtectionActionOutcome(
                    protection_decision, control_decision, None, None,
                    "target_conflict_rejected", message
                ))
                continue

            if self._pre_dispatch_guard is not None:
                try:
                    self._pre_dispatch_guard()
                except StaleProtectionExecutionError as exc:
                    append_batch_rejection(
                        index,
                        f"Protection batch aborted before command translation: {exc}",
                        current_control_decision=control_decision,
                    )
                    break

            try:
                command = ControlCommandTranslator.to_command(control_decision)
            except (TypeError, ValueError) as exc:
                message = (
                    f"Protection command translation failed for "
                    f"'{control_decision.target_equipment_type}:"
                    f"{control_decision.target_equipment_id}': {exc}"
                )
                diagnostics.append(message)
                outcomes.append(ProtectionActionOutcome(
                    protection_decision, control_decision, None, None,
                    "translation_failed", message
                ))
                continue

            if self._decision_guard is not None:
                try:
                    self._decision_guard(protection_decision, control_decision)
                except StaleProtectionDecisionError as exc:
                    message = (
                        f"Protection decision rejected immediately before dispatch for "
                        f"'{protection_decision.element_id}': {exc}"
                    )
                    diagnostics.append(message)
                    outcomes.append(ProtectionActionOutcome(
                        protection_decision, control_decision, command, None,
                        "stale_dependency_rejected", message
                    ))
                    continue
                except StaleProtectionExecutionError as exc:
                    append_batch_rejection(
                        index,
                        f"Protection batch aborted immediately before dispatch: {exc}",
                        current_control_decision=control_decision,
                        current_command=command,
                    )
                    break
                except Exception as exc:
                    append_batch_rejection(
                        index,
                        f"Protection batch aborted because the pre-dispatch decision guard failed unexpectedly: {type(exc).__name__}: {exc}",
                        current_control_decision=control_decision,
                        current_command=command,
                    )
                    break

            if self._pre_dispatch_guard is not None:
                try:
                    self._pre_dispatch_guard()
                except StaleProtectionExecutionError as exc:
                    append_batch_rejection(
                        index,
                        f"Protection batch aborted before dispatch: {exc}",
                        current_control_decision=control_decision,
                        current_command=command,
                    )
                    break

            # Once dispatch is attempted, treat this target as consumed even if
            # the outcome is indeterminate; a second action could conflict with
            # a command that crossed the commit boundary.
            dispatched_targets.add(target_key)
            try:
                result = self._dispatcher.execute_command(command)
            except StaleProtectionExecutionError as exc:
                append_batch_rejection(
                    index,
                    f"Protection batch aborted during dispatch: {exc}",
                    current_control_decision=control_decision,
                    current_command=command,
                )
                break
            except InvalidApplicationResultError as exc:
                message = f"Invalid Application result for command '{command.command_id}': {exc}"
                diagnostics.append(message)
                outcomes.append(ProtectionActionOutcome(
                    protection_decision, control_decision, command, None,
                    "invalid_application_result", message
                ))
                continue
            except Exception as exc:
                message = (
                    f"Protection command dispatch failed for command "
                    f"'{command.command_id}' targeting "
                    f"'{control_decision.target_equipment_type}:"
                    f"{control_decision.target_equipment_id}': {exc}"
                )
                diagnostics.append(message)
                outcomes.append(ProtectionActionOutcome(
                    protection_decision, control_decision, command, None,
                    "dispatch_failed_or_indeterminate", message
                ))
                continue

            if not isinstance(result, ApplicationResult):
                message = (
                    f"Dispatcher returned invalid result type "
                    f"{type(result).__name__} for command '{command.command_id}'."
                )
                diagnostics.append(message)
                outcomes.append(ProtectionActionOutcome(
                    protection_decision, control_decision, command, None,
                    "invalid_application_result", message
                ))
                continue

            control_decisions.append(control_decision)
            commands.append(command)
            results.append(result)
            if result.success:
                status = "application_command_succeeded"
                message = ""
            else:
                status = "application_command_failed"
                message = (
                    f"Protection command '{command.command_id}' returned an "
                    f"unsuccessful ApplicationResult: "
                    f"{result.message or 'no failure message supplied'}"
                )
                diagnostics.append(message)

            core_state_observation = "unknown/unavailable"
            postcondition_verification = None
            if result.success and self._state_observer is not None:
                try:
                    observation = self._state_observer(control_decision, command, result)
                    if isinstance(observation, ProtectionPostconditionVerification):
                        postcondition_verification = observation
                        core_state_observation = (
                            f"{observation.status.value}: {observation.target_equipment_type}:"
                            f"{observation.target_equipment_id}; expected={observation.expected_state!r}; "
                            f"observed={observation.observed_state!r}; {observation.diagnostic}"
                        ).rstrip("; ")
                    elif isinstance(observation, str) and observation.strip():
                        core_state_observation = observation
                    else:
                        core_state_observation = "unknown/unavailable: observer returned no authoritative observation"
                except Exception as exc:
                    core_state_observation = f"unknown/unavailable: readback failed ({type(exc).__name__}: {exc})"

            if result.success:
                if postcondition_verification is None:
                    status = "command_accepted"
                    message = (
                        "Application command succeeded; typed Core postcondition "
                        "verification is unavailable."
                    )
                elif postcondition_verification.status is PostconditionStatus.MATCHED:
                    status = "core_postcondition_matched"
                    message = postcondition_verification.diagnostic
                elif postcondition_verification.status is PostconditionStatus.MISMATCHED:
                    status = "core_postcondition_mismatched"
                    message = postcondition_verification.diagnostic or (
                        "Application command succeeded but the authoritative Core "
                        "postcondition does not match the requested action."
                    )
                    diagnostics.append(message)
                else:
                    status = "postcondition_unavailable_unsupported"
                    message = postcondition_verification.diagnostic or (
                        "Application command succeeded but the requested Core "
                        "postcondition is unavailable or unsupported."
                    )
                    diagnostics.append(message)

            if self._decision_guard is not None:
                try:
                    self._decision_guard(protection_decision, control_decision)
                except (StaleProtectionDecisionError, StaleProtectionExecutionError) as exc:
                    diagnostics.append(
                        f"Post-dispatch dependency changed for element "
                        f"'{protection_decision.element_id}': {exc}"
                    )
                except Exception as exc:
                    diagnostics.append(
                        f"Post-dispatch dependency guard failed for element "
                        f"'{protection_decision.element_id}': {type(exc).__name__}: {exc}"
                    )

            outcomes.append(ProtectionActionOutcome(
                protection_decision, control_decision, command, result, status, message,
                core_state_observation=core_state_observation,
                postcondition_verification=postcondition_verification,
            ))

        return ProtectionExecutionResult(
            decisions=decision_tuple,
            control_decisions=tuple(control_decisions),
            commands=tuple(commands),
            application_results=tuple(results),
            diagnostics=tuple(diagnostics),
            outcomes=tuple(outcomes),
        )


__all__ = [
    "StaleProtectionExecutionError",
    "StaleProtectionDecisionError",
    "ProtectionTargetUnavailableError",
    "PostconditionStatus",
    "ProtectionPostconditionVerification",
    "ProtectionActionOutcome",
    "ProtectionExecutionResult",
    "ProtectionExecutionService",
]
