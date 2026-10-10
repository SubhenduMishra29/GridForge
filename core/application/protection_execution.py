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
class ProtectionExecutionResult:
    """Immutable result of one Application-side protection execution."""

    decisions: tuple[ProtectionDecision, ...] = ()
    control_decisions: tuple[ControlDecision, ...] = ()
    commands: tuple[Command, ...] = ()
    application_results: tuple[ApplicationResult, ...] = ()
    diagnostics: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        sequence_fields = (
            ("decisions", ProtectionDecision),
            ("control_decisions", ControlDecision),
            ("commands", Command),
            ("application_results", ApplicationResult),
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
    Application-owned binding from protection identity to a physical target
    and action; this service does not assume that the target is a breaker.
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
        """Translate actionable protection decisions into Control intents and dispatch them."""
        decision_tuple = tuple(decisions)
        control_decisions: list[ControlDecision] = []
        commands: list[Command] = []
        results: list[ApplicationResult] = []
        diagnostics: list[str] = []

        for protection_decision in decision_tuple:
            if not isinstance(protection_decision, ProtectionDecision):
                raise TypeError("decisions must contain ProtectionDecision values.")
            if not protection_decision.actionable:
                continue

            try:
                control_decision = self._action_resolver(protection_decision)
            except Exception as exc:
                diagnostics.append(
                    f"Protection action resolution failed for '{protection_decision.element_id}': {exc}"
                )
                continue

            if control_decision is None:
                diagnostics.append(
                    f"Protection decision '{protection_decision.element_id}' has no configured action target."
                )
                continue
            if not isinstance(control_decision, ControlDecision):
                raise TypeError("action_resolver must return ControlDecision or None.")

            try:
                command = ControlCommandTranslator.to_command(control_decision)
                result = self._dispatcher.execute(control_decision)
            except Exception as exc:
                diagnostics.append(
                    f"Protection action execution failed for "
                    f"'{control_decision.target_equipment_type}:{control_decision.target_equipment_id}': {exc}"
                )
                continue

            control_decisions.append(control_decision)
            commands.append(command)
            results.append(result)

        return ProtectionExecutionResult(
            decisions=decision_tuple,
            control_decisions=tuple(control_decisions),
            commands=tuple(commands),
            application_results=tuple(results),
            diagnostics=tuple(diagnostics),
        )


__all__ = ["ProtectionExecutionResult", "ProtectionExecutionService"]
