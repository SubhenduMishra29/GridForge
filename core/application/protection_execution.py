# ============================================================
# File: core/application/protection_execution.py
# GridForge V2 — Protection Application Orchestration
# Author: Subhendu Mishra
# ============================================================

"""Application-owned orchestration for protection output intent."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from core.application.command import Command
from core.application.control_dispatch import ControlCommandDispatcher, ControlCommandTranslator
from core.application.results import ApplicationResult
from core.control.decision import ControlDecision
from core.protection.decision import ProtectionDecision


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
    ) -> None:
        if not isinstance(dispatcher, ControlCommandDispatcher):
            raise TypeError("dispatcher must be a ControlCommandDispatcher.")
        if not callable(action_resolver):
            raise TypeError("action_resolver must be callable.")
        self._dispatcher = dispatcher
        self._action_resolver = action_resolver

    @property
    def dispatcher(self) -> ControlCommandDispatcher:
        return self._dispatcher

    def execute(self, decisions: Iterable[ProtectionDecision]) -> ProtectionExecutionResult:
        """Translate each actionable decision once and retain its exact dispatch outcome."""
        decision_tuple = tuple(decisions)
        control_decisions: list[ControlDecision] = []
        commands: list[Command] = []
        results: list[ApplicationResult] = []
        diagnostics: list[str] = []
        outcomes: list[ProtectionActionOutcome] = []

        for protection_decision in decision_tuple:
            if not isinstance(protection_decision, ProtectionDecision):
                raise TypeError("decisions must contain ProtectionDecision values.")
            if not protection_decision.actionable:
                outcomes.append(ProtectionActionOutcome(
                    protection_decision, None, None, None, "not_actionable"
                ))
                continue

            try:
                control_decision = self._action_resolver(protection_decision)
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

            try:
                result = self._dispatcher.execute_command(command)
            except Exception as exc:
                # Dispatch may have crossed the commit boundary before an
                # exception (for example, history publication failure). Do not
                # claim success or fabricate an ApplicationResult.
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

            # Dispatcher validates result type; this defensive check preserves
            # accurate attribution if a subclass violates that contract.
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
            outcomes.append(ProtectionActionOutcome(
                protection_decision, control_decision, command, result, status, message
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
    "ProtectionActionOutcome",
    "ProtectionExecutionResult",
    "ProtectionExecutionService",
]
